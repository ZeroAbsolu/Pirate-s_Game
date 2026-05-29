"""
Actions du joueur liées au repaire (base secrète).

Ce module est volontairement séparé de data/actions.py pour rester
purement ADDITIF : il expose BASE_ACTIONS, que data/actions.py concatène
à son catalogue. Aucune fonction existante n'est modifiée ici, ce qui
évite toute collision avec d'autres extensions (p. ex. voyages.py).

Deux actions principales :
  - « Fonder un repaire »  : disponible tant qu'aucun repaire n'existe.
  - « Rejoindre le repaire » : navigue jusqu'à la base, restitue le
    rapport d'activité, gère un éventuel raid, puis ouvre le menu de gestion.

Le menu de gestion permet de construire des bâtiments, déplacer des
hommes entre le navire et la garnison, décharger les matières premières
rapportées dans la cale, et utiliser les services des bâtiments bâtis.
"""

import random

from core.base import Hideout, LOCATIONS, list_locations
from data.base_buildings import (
    BASE_BUILDINGS, VISIT_HANDLERS, get_building, cost_str,
)
from data.resources import label as item_label


FOUND_GOLD = 300          # mise de fond pour établir un repaire
FOUND_MIN_DEPOSIT = 6     # hommes minimum laissés sur place


# -------------------------------------------------------------------
# Consommation de vivres (réplique locale, pour ne pas importer
# data/actions au chargement — évite les imports circulaires)
# -------------------------------------------------------------------

def _consume_supplies(state, base):
    saved = state.get_modifier("supply_savings", 0.0)
    real = max(0, int(round(base * (1.0 - saved))))
    state.supplies = max(0, state.supplies - real)
    return real


# -------------------------------------------------------------------
# Fonder un repaire
# -------------------------------------------------------------------

def _action_found_base(state, ui):
    ui.title("Fonder un repaire")
    ship = state.ship
    if state.gold < FOUND_GOLD:
        ui.fail(f"Il faut {FOUND_GOLD} P8 pour établir un repaire digne de ce nom.")
        return
    max_deposit = state.crew - ship["crew_min"]
    if max_deposit < FOUND_MIN_DEPOSIT:
        ui.fail(
            "Vous n'avez pas assez d'hommes : il faut pouvoir en laisser au "
            f"moins {FOUND_MIN_DEPOSIT} à terre tout en gardant de quoi "
            "manœuvrer le navire.")
        return

    ui.narrate(
        "Un repaire, c'est une plage cachée, une passe que l'on est seul à "
        "connaître, et des hommes pour la tenir. Où jetez-vous l'ancre pour "
        "de bon ?")
    options = [(loc["name"], loc["id"]) for loc in list_locations()]
    options.append(("Renoncer", None))
    loc_id = ui.choose("Quel mouillage choisissez-vous ?", options)
    if loc_id is None:
        return
    ui.info(LOCATIONS[loc_id]["blurb"])

    confirm = ui.choose(
        f"Établir le repaire ici pour {FOUND_GOLD} P8 ? (la traversée et "
        "l'installation prennent un tour)",
        [("Oui, c'est ici", "yes"), ("Non, réfléchir encore", "no")],
    )
    if confirm != "yes":
        return

    men = ui.ask_int(
        f"Combien d'hommes laissez-vous pour fonder la garnison ? "
        f"(min {FOUND_MIN_DEPOSIT}, max {max_deposit})",
        min_val=FOUND_MIN_DEPOSIT, max_val=max_deposit,
    )
    if men < FOUND_MIN_DEPOSIT:
        ui.info("Trop peu d'hommes — vous renoncez pour l'instant.")
        return

    name = ui.ask_text("Donnez un nom à votre repaire (laissez vide pour le nom par défaut) :")

    # Installation : on dépense le tour de traversée et d'aménagement.
    state.advance_turn()
    _consume_supplies(state, max(1, state.crew // 18))

    state.gold -= FOUND_GOLD
    state.crew -= men
    base = Hideout(loc_id, name=name or None, founded_turn=state.turn)
    base.garrison = men
    state.base = base

    # Décharger d'éventuelles matières déjà transportées dans la cale.
    moved = _unload_hold_into_base(state, base)

    ui.show_scene("base", "main")
    ui.success(
        f"« {base.name} » est fondé sur {base.location_name}. {men} hommes y "
        "restent, hache et pelle en main.")
    if moved:
        ui.info("Les matières rapportées dans la cale sont débarquées au magasin.")
    ui.info("Revenez-y construire, produire, et mettre vos prises à l'abri.")


# -------------------------------------------------------------------
# Rejoindre et gérer le repaire
# -------------------------------------------------------------------

def _action_visit_base(state, ui):
    base = state.base
    ui.info(f"Cap sur {base.name}…")
    state.advance_turn()
    supply_cost = max(1, state.crew // 18)
    supply_cost = int(round(supply_cost * float(base.mods.get("supply_cost", 1.0))))
    _consume_supplies(state, supply_cost)

    state.in_port = False
    state.current_port = None

    ui.show_scene("base", "main")
    ui.title(base.name)
    base.resolve_arrival(state, ui)
    if state.game_over:
        return

    _base_menu(state, ui, base)


def _base_menu(state, ui, base):
    while True:
        ui.show_scene("base", "main")
        ui.divider()
        for line in base.summary_lines():
            ui.info(line)
        ui.divider()

        options = [
            ("Construire un bâtiment", "build"),
            ("Déposer / reprendre des hommes", "men"),
        ]
        if _hold_total(state) > 0:
            options.append(("Décharger les matières de la cale", "unload"))

        # Services des bâtiments construits (ordre du catalogue).
        for bid in BASE_BUILDINGS:
            if base.has(bid) and bid in VISIT_HANDLERS:
                options.append((BASE_BUILDINGS[bid]["name"], f"svc:{bid}"))

        options.append(("Lever l'ancre", "leave"))

        choice = ui.choose("Au repaire :", options)
        if choice == "leave":
            return
        if choice == "build":
            _build_menu(state, ui, base)
        elif choice == "men":
            _manage_men(state, ui, base)
        elif choice == "unload":
            moved = _unload_hold_into_base(state, base)
            if moved:
                ui.success(f"{moved} unités débarquées au magasin.")
            else:
                ui.info("Rien à décharger, ou magasin plein.")
        elif isinstance(choice, str) and choice.startswith("svc:"):
            bid = choice[4:]
            ui.show_scene("base", bid)
            VISIT_HANDLERS[bid](base, state, ui)


def _build_menu(state, ui, base):
    while True:
        options = []
        for bid, bdef in BASE_BUILDINGS.items():
            ok, reason = base.can_build(bid)
            if not ok:
                # On n'affiche pas ce qui est déjà bâti / en chantier ;
                # on signale les prérequis manquants.
                if reason.startswith("requiert"):
                    options.append((f"{bdef['name']} — {reason}", f"locked:{bid}"))
                continue
            tag = "" if base.affordable(bid, state) else "  (ressources manquantes)"
            options.append((
                f"{bdef['name']} [{cost_str(bdef)}, {bdef['build_turns']}t]{tag}",
                bid,
            ))
        if not options:
            ui.info("Rien de nouveau à bâtir pour l'instant.")
            return
        options.append(("Retour", None))

        choice = ui.choose("Construire quoi ?", options)
        if choice is None:
            return
        if isinstance(choice, str) and choice.startswith("locked:"):
            ui.info("Bâtissez d'abord les prérequis indiqués.")
            continue

        bid = choice
        bdef = BASE_BUILDINGS[bid]
        ui.info(bdef["description"])
        if not base.affordable(bid, state):
            miss = base.missing_for(bid, state)
            parts = []
            for k, v in miss.items():
                parts.append(f"{v} {('P8' if k == 'gold' else item_label(k))}")
            ui.fail("Il manque : " + ", ".join(parts) + ".")
            continue
        confirm = ui.choose(
            f"Lancer le chantier « {bdef['name']} » pour {cost_str(bdef)} "
            f"({bdef['build_turns']} tours, {bdef.get('workers', 3)} hommes requis) ?",
            [("Oui", "yes"), ("Non", "no")],
        )
        if confirm == "yes":
            base.start_build(bid, state)
            ui.success(
                f"Chantier ouvert : « {bdef['name']} ». Il avancera tant que la "
                f"garnison fournit {bdef.get('workers', 3)} bras.")
            if base.garrison < bdef.get("workers", 3):
                ui.info("Attention : la garnison est trop faible — le chantier "
                        "n'avancera pas tant que vous n'aurez pas laissé d'hommes.")


def _manage_men(state, ui, base):
    ship = state.ship
    ui.info(f"À bord : {state.crew} hommes (min {ship['crew_min']} pour manœuvrer, "
            f"max {ship['crew_max']}).")
    ui.info(f"À terre : {base.garrison}/{base.garrison_cap()} hommes.")

    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Déposer des hommes à terre", "deposit"),
            ("Reprendre des hommes à bord", "withdraw"),
            ("Retour", None),
        ],
    )
    if choice == "deposit":
        max_dep = min(state.crew - ship["crew_min"],
                      base.garrison_cap() - base.garrison)
        if max_dep <= 0:
            ui.fail("Impossible : soit le navire serait sous-armé, soit le "
                    "repaire est plein. Bâtissez des baraquements pour héberger plus.")
            return
        n = ui.ask_int(f"Déposer combien d'hommes ? (max {max_dep})",
                       min_val=0, max_val=max_dep)
        if n > 0:
            state.crew -= n
            base.garrison += n
            ui.success(f"{n} hommes rejoignent la garnison du repaire.")
    elif choice == "withdraw":
        max_wd = min(base.garrison, ship["crew_max"] - state.crew)
        if max_wd <= 0:
            ui.fail("Aucun homme à reprendre, ou le navire est déjà plein.")
            return
        n = ui.ask_int(f"Reprendre combien d'hommes ? (max {max_wd})",
                       min_val=0, max_val=max_wd)
        if n > 0:
            base.garrison -= n
            state.crew += n
            ui.success(f"{n} hommes rembarquent. Le repaire se vide d'autant.")


# -------------------------------------------------------------------
# Cale du navire (matières premières transportées)
# -------------------------------------------------------------------

def _hold_total(state) -> int:
    hold = getattr(state, "cargo_hold", None) or {}
    return sum(hold.values())


def _unload_hold_into_base(state, base) -> int:
    """Transvase la cale du navire dans le magasin du repaire (borné par
    la capacité). Renvoie le total réellement débarqué."""
    hold = getattr(state, "cargo_hold", None)
    if not hold:
        return 0
    moved = 0
    for rid in list(hold):
        qty = hold[rid]
        if qty <= 0:
            continue
        added = base.add_resource(rid, qty)
        hold[rid] -= added
        moved += added
        if hold[rid] <= 0:
            del hold[rid]
    return moved


# -------------------------------------------------------------------
# Catalogue d'actions exporté vers data/actions.py
# -------------------------------------------------------------------

BASE_ACTIONS = [
    {
        "id": "found_base",
        "label": f"Fonder un repaire ({FOUND_GOLD} P8 + des hommes)",
        "available": lambda s: (getattr(s, "base", None) is None
                                and s.gold >= FOUND_GOLD
                                and s.crew - s.ship["crew_min"] >= FOUND_MIN_DEPOSIT),
        "execute": _action_found_base,
    },
    {
        "id": "visit_base",
        "label": "Rejoindre le repaire",
        "available": lambda s: getattr(s, "base", None) is not None,
        "execute": _action_visit_base,
    },
]
