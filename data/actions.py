"""
Actions disponibles au joueur à chaque tour.

Modifications par rapport à la version précédente :
  - Les sous-actions de port appliquent les bonus passifs des compagnons
    (recruit_discount, repair_discount, fence_bonus, supply_savings).
  - **Nouvelle mécanique de taverne** : le menu de taverne ne propose plus
    que « Boire avec l'équipage » et « Quitter ». L'offre de cadeau à
    l'hôtesse passe désormais par une RENCONTRE ALÉATOIRE déclenchée
    après avoir bu (voir `_tavern_hostess_encounter`). Le portrait de
    l'hôtesse est affiché pendant toute la rencontre. La chaîne se
    poursuit visite après visite jusqu'au seuil d'affection, où la
    rencontre suivante propose le recrutement et clôt la chaîne.
  - L'action « Inspecter » permet en plus de consulter le portrait et
    la fiche détaillée de chaque compagnon recruté.
"""

import random
from data.events import pick_event
from data.ports import get_port, list_ports
from data.port_events import maybe_trigger_port_event
from data.companions import get_tavern_keeper


# -------------------------------------------------------------------
# Constantes — rencontre avec l'hôtesse
# -------------------------------------------------------------------

# Probabilité de base que l'hôtesse rejoigne le joueur à sa table
# après que celui-ci a bu avec l'équipage.
HOSTESS_ENCOUNTER_CHANCE_BASE  = 0.50
# Bonus par cadeau déjà offert (l'hôtesse s'enhardit).
HOSTESS_ENCOUNTER_CHANCE_BONUS = 0.10
# Plafond avant seuil ; au seuil atteint, la rencontre est garantie.
HOSTESS_ENCOUNTER_CHANCE_CAP   = 0.80


# -------------------------------------------------------------------
# Consommation de vivres avec économies de cuisinier / Mahalia
# -------------------------------------------------------------------

def _consume_supplies(state, base):
    saved = state.get_modifier("supply_savings", 0.0)
    real = max(0, int(round(base * (1.0 - saved))))
    state.supplies = max(0, state.supplies - real)
    return real


# -------------------------------------------------------------------
# Actions en mer
# -------------------------------------------------------------------

def _action_sail(state, ui):
    ui.show_scene("actions", "sail")
    ui.info("Vous prenez le large…")
    state.advance_turn()
    state.in_port = False
    state.current_port = None
    _consume_supplies(state, max(1, state.crew // 20))
    event = pick_event(state)
    if event:
        ui.event_banner(event["title"])
        event["resolve"](state, ui)
    else:
        ui.info("La traversée se passe sans incident notable.")


def _action_patrol_route(state, ui):
    ui.show_scene("actions", "patrol")
    routes = [
        ("Route des galions (Carthagène → La Havane)", 1.3, 1.4),
        ("Détroit de Floride", 1.2, 1.2),
        ("Côtes des Carolines", 1.0, 0.9),
        ("Sound de Madagascar (mer Rouge)", 1.5, 1.5),
    ]
    options = [(r[0], i) for i, r in enumerate(routes)]
    options.append(("Annuler", -1))
    idx = ui.choose("Quelle route voulez-vous patrouiller ?", options)
    if idx == -1:
        return
    route = routes[idx]
    ui.info(f"Cap sur : {route[0]}")
    state.advance_turn()
    state.in_port = False
    state.current_port = None
    _consume_supplies(state, max(2, state.crew // 15))

    for _ in range(2):
        event = pick_event(state)
        if event:
            ui.event_banner(event["title"])
            event["resolve"](state, ui)
            if state.game_over:
                return


# -------------------------------------------------------------------
# Visite de port
# -------------------------------------------------------------------

def _action_visit_port(state, ui):
    ports = list_ports()
    options = [(p["name"] + f"  [{p['region']}]", p["id"]) for p in ports]
    options.append(("Annuler", None))
    port_id = ui.choose("Vers quel port mettez-vous le cap ?", options)
    if port_id is None:
        return
    port = get_port(port_id)

    # --- Détection d'une grande traversée Caraïbes ↔ océan Indien ---
    from data.voyages import region_of_port, trigger_long_voyage
    last_region = state.flags.get("last_region", "caribbean")
    dest_region = region_of_port(port_id)

    if dest_region and dest_region != last_region:
        # Grande traversée : Caraïbes ↔ Sainte-Marie, dans les deux sens.
        min_supplies = 40
        if state.supplies < min_supplies or state.crew < state.ship["crew_min"]:
            ui.fail(
                f"Vivres ({state.supplies}/100) ou équipage ({state.crew} hommes, "
                f"minimum {state.ship['crew_min']}) insuffisants pour une telle "
                "traversée. Refaites-vous d'abord à terre."
            )
            return

        trigger_long_voyage(state, ui, port_id, origin_region=last_region)
        if state.game_over:
            return

        # Arrivée à destination
        state.in_port = True
        state.current_port = port
        ui.show_scene("ports", port_id, "main")
        ui.success(f"Après plusieurs mois de mer, vous mouillez à {port['name']}.")

        maybe_trigger_port_event(state, ui, port_id)
        if state.game_over:
            return

        _port_menu(state, ui, port)

        state.flags["last_region"] = dest_region
        state.in_port = False
        state.current_port = None
        return

    # --- Trajet court (intra-Caraïbes) : comportement original ---
    ui.info(f"Cap sur {port['name']}…")
    state.advance_turn()
    _consume_supplies(state, max(1, state.crew // 20))

    if port["hostility"] >= 5 and random.random() < port["hostility"] / 15:
        ui.fail(
            f"À l'approche de {port['name']}, des navires de garde sortent du port. "
            "Vous devez fuir avant d'avoir mouillé."
        )
        hull_loss = random.randint(5, 20)
        state.ship["hull_current"] = max(0, state.ship["hull_current"] - hull_loss)
        return

    state.in_port = True
    state.current_port = port
    ui.show_scene("ports", port_id, "main")
    ui.success(f"Vous mouillez à {port['name']}.")

    maybe_trigger_port_event(state, ui, port_id)
    if state.game_over:
        return

    _port_menu(state, ui, port)

    state.flags["last_region"] = dest_region or last_region
    state.in_port = False
    state.current_port = None


def _port_menu(state, ui, port):
    from data.buildings import get_buildings
    pid = port["id"]
    while True:
        ui.show_scene("ports", pid, "main")
        ui.divider()
        ui.info(f"Vous êtes à {port['name']}. Que faites-vous ?")
        options = []
        # Services génériques
        if "supplies" in port["services"]:
            options.append(("Acheter des vivres", "supplies"))
        if "recruit" in port["services"]:
            options.append(("Recruter des hommes", "recruit"))
        if "repair" in port["services"]:
            options.append(("Caréner et réparer", "repair"))
        if "fence" in port["services"]:
            options.append(("Vendre du butin", "fence"))
        if "tavern" in port["services"]:
            options.append(("Passer à la taverne", "tavern"))
        if "shipyard" in port["services"]:
            options.append(("Aller au chantier naval", "shipyard"))
        # Bâtiments spécifiques au port
        buildings = [b for b in get_buildings(pid) if b["available"](state)]
        for b in buildings:
            options.append((b["name"], f"bldg:{b['id']}"))
        options.append(("Lever l'ancre", "leave"))

        choice = ui.choose("Action :", options)
        if choice == "leave":
            return

        # Bâtiment particulier ?
        if isinstance(choice, str) and choice.startswith("bldg:"):
            bid = choice[5:]
            building = next(b for b in buildings if b["id"] == bid)
            ui.show_scene("ports", pid, bid)
            ui.info(building["description"])
            building["interact"](state, ui)
            continue

        # Sinon, sous-action de port standard
        ui.show_scene("ports", pid, choice)

        if choice == "supplies":
            _port_buy_supplies(state, ui, port)
        elif choice == "recruit":
            _port_recruit(state, ui, port)
        elif choice == "repair":
            _port_repair(state, ui, port)
        elif choice == "fence":
            _port_fence(state, ui, port)
        elif choice == "tavern":
            _port_tavern(state, ui, port)
        elif choice == "shipyard":
            _port_shipyard(state, ui, port)


def _port_buy_supplies(state, ui, port):
    price = port["supply_price"]
    max_buy = state.gold // price
    if max_buy == 0:
        ui.fail("Pas un sou pour acheter de quoi nourrir l'équipage.")
        return
    qty = ui.ask_int(
        f"Combien d'unités de vivres acheter ? ({price} pièces l'unité, max {max_buy})",
        min_val=0, max_val=max_buy,
    )
    state.gold -= qty * price
    state.supplies = min(100, state.supplies + qty)
    ui.success(f"Vous embarquez {qty} unités de vivres.")


def _port_recruit(state, ui, port):
    max_for_ship = state.ship["crew_max"]
    if state.crew >= max_for_ship:
        ui.fail("Le navire est plein. Aucun matelot supplémentaire ne tiendrait.")
        return
    available = random.randint(2, 12)
    base_price = 8
    discount = state.get_modifier("recruit_discount", 0.0)
    price_per_man = max(1, int(round(base_price * (1.0 - discount))))
    if discount > 0:
        ui.info(f"(Tarif négocié : {price_per_man} P8/homme au lieu de {base_price})")
    affordable = min(available, max_for_ship - state.crew, state.gold // price_per_man)
    if affordable == 0:
        ui.fail("Personne ne signera les Articles à vos conditions.")
        return
    qty = ui.ask_int(
        f"Combien d'hommes recruter ? ({price_per_man} pièces / homme — "
        f"{available} disponibles, max {affordable})",
        min_val=0, max_val=affordable,
    )
    state.gold -= qty * price_per_man
    state.crew += qty
    ui.success(f"{qty} hommes signent les Articles.")


def _port_repair(state, ui, port):
    damage = state.ship["hull_max"] - state.ship["hull_current"]
    if damage == 0:
        ui.info("La coque est intacte. Rien à faire.")
        return
    base_price = 6
    discount = state.get_modifier("repair_discount", 0.0)
    price_per_pt = max(1, int(round(base_price * (1.0 - discount))))
    if discount > 0:
        ui.info(f"(Tarif charpentier : {price_per_pt} P8/point au lieu de {base_price})")
    max_repair = min(damage, state.gold // price_per_pt)
    qty = ui.ask_int(
        f"Combien de points de coque réparer ? ({price_per_pt} pièces / pt, max {max_repair})",
        min_val=0, max_val=max_repair,
    )
    state.gold -= qty * price_per_pt
    state.ship["hull_current"] = min(state.ship["hull_max"], state.ship["hull_current"] + qty)
    ui.success(f"Coque réparée de {qty} points. Le maître charpentier est satisfait.")


def _port_fence(state, ui, port):
    if state.loot == 0:
        ui.fail("Aucun butin à recéler.")
        return
    rate = port["fence_rate"] + state.get_modifier("fence_bonus", 0.0)
    rate = min(rate, 0.95)
    sale_value = int(state.loot * rate)
    confirm = ui.choose(
        f"Vous avez {state.loot} pièces de butin brut. Le receleur en propose {sale_value} "
        f"(taux {int(rate*100)}%). Vendre ?",
        [("Vendre tout", True), ("Garder", False)],
    )
    if confirm:
        state.gold += sale_value
        state.loot = 0
        ui.success(f"+{sale_value} pièces de huit en caisse.")


# -------------------------------------------------------------------
# Taverne — boire avec l'équipage déclenche éventuellement la
# rencontre avec l'hôtesse
# -------------------------------------------------------------------

def _port_tavern(state, ui, port):
    """Menu de taverne. Très simple : boire ou partir. Tout ce qui
    concerne l'hôtesse passe par la rencontre aléatoire déclenchée
    après avoir bu."""
    pid = port["id"]
    waitress = get_tavern_keeper(pid)

    ui.show_scene("ports", pid, "tavern")

    # Petit aperçu de l'état d'affection (sans dévoiler l'hôtesse elle-même).
    if waitress and not state.has_companion(waitress["id"]):
        affection = state.affection_for(pid)
        threshold = waitress["recruitment"]["gifts_needed"]
        nick = f" « {waitress['nickname']} »" if waitress.get("nickname") else ""
        if affection == 0:
            ui.info(
                f"L'hôtesse — {waitress['name']}{nick} — sert au comptoir. "
                "Elle ne s'attable pas avec n'importe qui."
            )
        elif affection < threshold:
            ui.info(
                f"{waitress['name']}{nick} vous reconnaît du coin de l'œil. "
                f"(Affection {affection}/{threshold})"
            )
        else:
            ui.info(
                f"{waitress['name']}{nick} guette discrètement votre arrivée. "
                f"(Affection {affection}/{threshold})"
            )

    options = [
        ("Boire avec l'équipage", "drink"),
        ("Quitter la taverne", "leave"),
    ]
    choice = ui.choose("À la taverne :", options)
    if choice == "drink":
        _tavern_drink(state, ui, port)


def _tavern_drink(state, ui, port):
    """Le joueur boit avec l'équipage. Coût d'un tour, moral en hausse,
    quelques désertions possibles ; PUIS, chance que l'hôtesse vienne
    s'asseoir à sa table (rencontre aléatoire, voir plus bas)."""
    state.advance_turn()
    state.morale = min(100, state.morale + 5)
    ui.narrate(
        "L'équipage envahit les tavernes du port. Rhum, parties de dés, "
        "fillettes faciles. Au matin, certains hommes manquent à l'appel."
    )
    # Désertion modulée par bonus
    base_desertion = random.randint(0, max(1, state.crew // 30))
    reduction = state.get_modifier("desertion_reduction", 0.0)
    deserters = max(0, int(round(base_desertion * (1.0 - reduction))))
    if deserters:
        state.crew = max(0, state.crew - deserters)
        ui.info(f"{deserters} hommes ont déserté pendant la nuit.")
    elif base_desertion > 0 and reduction > 0:
        ui.info("Le quartier-maître a su retenir les hommes — aucune désertion.")

    # === Rencontre éventuelle avec l'hôtesse de la taverne ===
    waitress = get_tavern_keeper(port["id"])
    if waitress and not state.has_companion(waitress["id"]):
        affection = state.affection_for(port["id"])
        threshold = waitress["recruitment"]["gifts_needed"]
        if affection >= threshold:
            # Au seuil : la rencontre est garantie. La chaîne va se clore.
            chance = 1.0
        else:
            chance = min(
                HOSTESS_ENCOUNTER_CHANCE_CAP,
                HOSTESS_ENCOUNTER_CHANCE_BASE
                + HOSTESS_ENCOUNTER_CHANCE_BONUS * affection,
            )
        if random.random() < chance:
            _tavern_hostess_encounter(state, ui, port, waitress)
            return

    # Sinon, possibilité d'une rumeur classique.
    event = pick_event(state)
    if event and event["id"] == "tavern_rumor":
        event["resolve"](state, ui)


def _tavern_hostess_encounter(state, ui, port, waitress):
    """Rencontre aléatoire avec l'hôtesse, déclenchée après avoir bu.

    - Affiche son portrait pour toute la durée de la rencontre.
    - Avant le seuil : permet d'offrir un seul cadeau, qui fait monter
      l'affection d'un point. Reculer (« Prendre congé ») coûte juste
      la chance manquée — pas de tour ni de pièce dépensés en plus.
    - Au seuil atteint (affection >= gifts_needed) : permet de proposer
      à l'hôtesse de quitter le port. Si elle accepte, elle rejoint
      l'équipage et la chaîne d'événements s'arrête définitivement
      pour ce port.

    Cohérence historique : les cadeaux suivent la personnalité et le
    rang de chaque hôtesse (toile d'Hollande, tabac de Virginie,
    émeraudes de Muzo, papier de Hollande, etc.). Cf. data/companions.py.
    """
    pid = port["id"]
    affection = state.affection_for(pid)
    threshold = waitress["recruitment"]["gifts_needed"]

    # Portrait affiché pendant toute la rencontre.
    ui.show_scene("companions", waitress["id"])
    nick = f" « {waitress['nickname']} »" if waitress.get("nickname") else ""
    ui.event_banner(f"Une rencontre avec {waitress['name']}{nick}")

    # Dialogue propre au stade d'affection.
    dialogues = waitress["recruitment"].get("encounter_dialogues", [])
    if dialogues:
        idx = min(affection, len(dialogues) - 1)
        ui.narrate(dialogues[idx])
    else:
        # Fallback si une hôtesse n'a pas (encore) de dialogues définis.
        ui.narrate(waitress["recruitment"].get(
            "intro",
            f"{waitress['name']} s'assoit en face de vous, sans un mot.",
        ))

    cost = waitress["recruitment"]["gift_cost"]
    gift_flavor = waitress["recruitment"]["gift_flavor"]

    options = []
    if affection >= threshold:
        options.append(
            (f"Lui proposer de quitter le port avec vous", "recruit"))
    elif state.gold >= cost:
        options.append(
            (f"Lui offrir {gift_flavor} ({cost} P8)", "gift"))
    else:
        ui.info(
            f"Il faudrait {cost} pièces de huit pour un présent qu'elle "
            f"accepterait — votre bourse est trop maigre ce soir."
        )
    options.append(("Prendre congé sans rien lui offrir", "leave"))

    choice = ui.choose("Que faites-vous ?", options)

    if choice == "gift":
        state.gold -= cost
        state.increase_affection(pid)
        new_aff = state.affection_for(pid)
        # On réaffiche le portrait pour qu'il reste visible
        # pendant la réaction de l'hôtesse.
        ui.show_scene("companions", waitress["id"])
        ui.success(
            f"Vous lui glissez {gift_flavor}. "
            f"{waitress['name']} l'accepte d'un signe de tête bref. "
            f"(Affection {new_aff}/{threshold})"
        )
        if new_aff >= threshold:
            ui.narrate(
                "Son regard, lorsqu'il croise le vôtre une dernière fois "
                "avant que vous quittiez la salle, dit assez : la prochaine "
                "fois sera la bonne."
            )

    elif choice == "recruit":
        # Délègue au moment de proposition (qui ajoute le compagnon
        # et clôt définitivement la chaîne d'événements pour ce port).
        _tavern_propose(state, ui, port, waitress)

    # « leave » : rien ne se passe, le joueur ressort de la rencontre.


def _tavern_propose(state, ui, port, waitress):
    """Recrutement effectif de l'hôtesse. Fin de la chaîne d'événements."""
    ui.show_scene("companions", waitress["id"])
    ui.narrate(waitress["recruitment"]["accept"])
    state.add_companion(waitress)
    ui.success(
        f"{waitress['name']} rejoint l'équipage en tant que "
        f"{waitress['role']}.   {waitress['bonus_label']}"
    )


# -------------------------------------------------------------------
# Chantier
# -------------------------------------------------------------------

def _port_shipyard(state, ui, port):
    from data.ships import list_all_ships
    ui.info("Le chantier propose plusieurs navires d'occasion :")
    available = [s for s in list_all_ships() if s["id"] != state.ship["id"]]
    options = [
        (f"{s['name']:<20} — {s['cost']} pièces  ({s['guns']} canons, {s['crew_max']} hommes max)",
         s["id"])
        for s in available
    ]
    options.append(("Annuler", None))
    new_id = ui.choose("Quel navire achetez-vous ?", options)
    if new_id is None:
        return
    new_ship_data = next(s for s in available if s["id"] == new_id)
    if state.gold < new_ship_data["cost"]:
        ui.fail("Vous n'avez pas les fonds.")
        return
    if state.crew < new_ship_data["crew_min"]:
        ui.fail(
            f"Ce navire exige au moins {new_ship_data['crew_min']} hommes pour être manœuvré. "
            f"Vous n'en avez que {state.crew}."
        )
        return
    state.gold -= new_ship_data["cost"]
    state.ship = _instantiate_ship(new_ship_data)
    ui.success(f"Vous prenez le commandement du {state.ship['name']}.")
    ui.show_scene("ships", state.ship["id"])


def _instantiate_ship(ship_data):
    inst = dict(ship_data)
    inst["hull_max"] = inst["hull"] * 10
    inst["hull_current"] = inst["hull_max"]
    return inst


# -------------------------------------------------------------------
# Autres actions
# -------------------------------------------------------------------

def _action_distribute_booty(state, ui):
    ui.show_scene("actions", "distribute")
    if state.gold < 50:
        ui.fail("Pas assez en caisse pour une distribution. L'équipage le saurait.")
        return
    share = min(state.gold, max(50, state.crew * 3))
    state.gold -= share
    morale_gain = 15 + share // 30
    state.morale = min(100, state.morale + morale_gain)
    ui.success(
        f"Vous distribuez {share} pièces de huit selon les Articles. "
        f"Le moral monte (+{morale_gain})."
    )


def _action_inspect(state, ui):
    """Inspecte la situation de bord et permet de consulter le portrait
    de chaque compagnon recruté. Action gratuite (n'avance pas le tour)."""
    state.render_status(ui)
    if not state.companions:
        return

    ui.divider()
    ui.info("Détail des compagnons :")
    for c in state.companions:
        nick = f" « {c['nickname']} »" if c.get("nickname") else ""
        ui.info(f"  • {c['name']}{nick} — {c['role']}")
        ui.info(f"    {c['bonus_label']}")

    # Boucle d'exploration des portraits.
    from core.ui import _wrap
    while True:
        options = [(f"Voir {c['name']}", c["id"]) for c in state.companions]
        options.append(("Retour", None))
        choice = ui.choose("Consulter le portrait d'un compagnon ?", options)
        if choice is None:
            return

        comp = next(c for c in state.companions if c["id"] == choice)
        ui.show_scene("companions", comp["id"])
        nick = f" « {comp['nickname']} »" if comp.get("nickname") else ""
        ui.title(f"{comp['name']}{nick}")
        ui.info(f"Rôle    : {comp['role']}")
        if comp.get("period"):
            ui.info(f"Période : {comp['period']}")
        ui.info(f"Bonus   : {comp['bonus_label']}")
        bio = comp.get("biography", "")
        if bio:
            ui.info("")
            for line in _wrap(bio, 70):
                ui.info(line)


def _action_rest(state, ui):
    ui.show_scene("actions", "rest")
    state.advance_turn()
    _consume_supplies(state, max(2, state.crew // 10))
    state.morale = min(100, state.morale + 8)
    repair = state.ship["hull_max"] // 10
    state.ship["hull_current"] = min(state.ship["hull_max"], state.ship["hull_current"] + repair)
    ui.narrate(
        "Vous trouvez une crique discrète, jetez l'ancre. L'équipage répare "
        "ce qui peut l'être, calfate, chasse et pêche."
    )
    ui.success(f"Moral +8, coque +{repair}, vivres consommés.")


# -------------------------------------------------------------------
# Catalogue
# -------------------------------------------------------------------

ACTIONS = [
    {"id": "sail",       "label": "Naviguer (1 tour, événement aléatoire)",
     "available": lambda s: True, "execute": _action_sail},
    {"id": "patrol",     "label": "Patrouiller une route commerciale",
     "available": lambda s: s.crew >= s.ship["crew_min"] // 2, "execute": _action_patrol_route},
    {"id": "port",       "label": "Visiter un port",
     "available": lambda s: True, "execute": _action_visit_port},
    {"id": "rest",       "label": "Hivernage / repos en crique",
     "available": lambda s: True, "execute": _action_rest},
    {"id": "distribute", "label": "Distribuer le butin (selon les Articles)",
     "available": lambda s: s.gold >= 50, "execute": _action_distribute_booty},
    {"id": "inspect",    "label": "Inspecter l'état du navire et de l'équipage",
     "available": lambda s: True, "execute": _action_inspect},
]


def list_actions(state):
    return [a for a in ACTIONS if a["available"](state)]

# Branchement du module "repaire" (purement additif).
# Import diff\u00e9r\u00e9 ici pour \u00e9viter tout cycle avec base_actions <-> actions.
from data.base_actions import BASE_ACTIONS as _BASE_ACTIONS
ACTIONS.extend(_BASE_ACTIONS)