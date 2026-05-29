"""
Bâtiments du repaire (base secrète du joueur).

Distincts des `data/buildings.py` (qui décrivent les bâtiments des PORTS
existants). Ici, ce sont les structures que le joueur ÉRIGE lui-même sur
son repaire, à partir de matières premières et de pièces de huit, et qui
demandent du TEMPS et des HOMMES (garnison) pour être bâties puis exploitées.

Trois leviers d'effet :

  1. PASSIF D'INFRASTRUCTURE — lus en continu par le Hideout :
        storage_bonus  : capacité de stockage supplémentaire
        garrison_bonus : hommes que le repaire peut héberger en plus
        defense        : points de défense contre les raids

  2. PRODUCTION (`recipe`) — appliquée à chaque tour par le Hideout, si
     assez d'hommes de garnison sont libres et les intrants disponibles :
        {"in": {res: q, ...}, "out": {bien: q, ...}, "workers": n}

  3. SERVICE (`VISIT_HANDLERS[id]`) — interaction quand le joueur gère le
     repaire en personne (caréner, couler des canons, distribuer du rhum,
     marchander au marché noir, etc.).

Un même bâtiment peut cumuler production automatique ET service (la
distillerie produit du rhum chaque tour, et permet d'en distribuer à
l'équipage lors d'une visite).

Arbre de dépendances (`requires`) volontairement léger :
    quai → charpenterie → (fonderie, armurerie) ; quai → batterie ;
    entrepôt → marché noir.

Convention d'image : assets/images/base/<building_id>.png (repli possible
sur la scène générique du repaire ; le jeu reste jouable sans illustration).
"""

import random

from data.resources import (
    RESOURCES, GOODS, label as item_label, base_price,
    roll_market_factor, sell_unit_price, buy_unit_price, haggle,
)


# ===================================================================
# Catalogue
# ===================================================================
# NB : "cost" inclut toujours "gold" ; les autres clés sont des
# matières premières (cf. data/resources.RESOURCES).

BASE_BUILDINGS = {

    # ---- Infrastructure -------------------------------------------
    "quai": {
        "id": "quai",
        "name": "Quai & cale de carénage",
        "category": "infra",
        "description": (
            "Appontement et plage de carénage. Permet de coucher le navire "
            "sur le flanc pour gratter la coque et la réparer à bon compte."
        ),
        "cost": {"gold": 250, "bois": 20, "pierre": 10},
        "build_turns": 2, "workers": 3,
        "requires": [],
        "storage_bonus": 40,
        "passive_label": "Carénage possible · +40 de stockage",
    },
    "entrepot": {
        "id": "entrepot",
        "name": "Entrepôt",
        "category": "infra",
        "description": (
            "Magasin couvert et sec. Décuple ce que le repaire peut garder "
            "en réserve : matières premières comme biens manufacturés."
        ),
        "cost": {"gold": 200, "bois": 25, "pierre": 15},
        "build_turns": 2, "workers": 2,
        "requires": [],
        "storage_bonus": 250,
        "passive_label": "+250 de capacité de stockage",
    },
    "baraquements": {
        "id": "baraquements",
        "name": "Baraquements",
        "category": "infra",
        "description": (
            "Cases, hamacs et cuisine commune. Permet de laisser davantage "
            "d'hommes à terre pour bâtir, produire et défendre le repaire."
        ),
        "cost": {"gold": 150, "bois": 20},
        "build_turns": 2, "workers": 2,
        "requires": [],
        "garrison_bonus": 40,
        "passive_label": "+40 hommes hébergeables (garnison)",
    },
    "batterie": {
        "id": "batterie",
        "name": "Vigie & batterie côtière",
        "category": "defense",
        "description": (
            "Guérite de vigie et redoute armée de pièces en barbette, qui "
            "commande la passe. Dissuade et repousse les chasseurs de pirates."
        ),
        "cost": {"gold": 600, "pierre": 40, "fer": 20, "poudre": 15},
        "build_turns": 3, "workers": 4,
        "requires": ["quai"],
        "defense": 8,
        "passive_label": "+8 défense · alerte des raids",
    },

    # ---- Ateliers de production -----------------------------------
    "charpenterie": {
        "id": "charpenterie",
        "name": "Atelier de charpentier",
        "category": "production",
        "description": (
            "Établi, scies, étuve à courber les bordages. Répare et regrée "
            "le navire à terre, bien moins cher qu'au chantier d'un port."
        ),
        "cost": {"gold": 300, "bois": 15, "fer": 10},
        "build_turns": 2, "workers": 3,
        "requires": ["quai"],
        "passive_label": "Réparation de coque à bas coût (bois)",
    },
    "distillerie": {
        "id": "distillerie",
        "name": "Distillerie (guildive)",
        "category": "production",
        "description": (
            "Alambic et cuves. Transforme la mélasse en rhum — qu'on revend "
            "cher, ou qu'on sert à l'équipage pour soutenir le moral."
        ),
        "cost": {"gold": 350, "bois": 15, "fer": 8},
        "build_turns": 2, "workers": 3,
        "requires": [],
        "recipe": {"in": {"melasse": 3}, "out": {"rhum": 4}, "workers": 3},
        "passive_label": "Mélasse → rhum (chaque tour) · distribution possible",
    },
    "cuisines": {
        "id": "cuisines",
        "name": "Cuisines & boucan",
        "category": "production",
        "description": (
            "Grils de boucan pour fumer le bœuf sauvage et la tortue. "
            "Constitue des réserves de longue conservation pour le bord."
        ),
        "cost": {"gold": 150, "bois": 12},
        "build_turns": 1, "workers": 2,
        "requires": [],
        # Pas d'intrant : la garnison chasse le bétail marron alentour.
        "recipe": {"in": {}, "out": {"boucan": 3}, "workers": 2},
        "rate_key": "boucan_rate",
        "passive_label": "Produit de la viande boucanée · embarquable en vivres",
    },
    "fonderie": {
        "id": "fonderie",
        "name": "Forge & fonderie",
        "category": "production",
        "description": (
            "Bas fourneau et moules. Coule boulets et mitraille à partir du "
            "fer ; permet aussi de fondre et monter une pièce sur le navire."
        ),
        "cost": {"gold": 500, "fer": 25, "pierre": 20},
        "build_turns": 3, "workers": 4,
        "requires": ["charpenterie"],
        "recipe": {"in": {"fer": 3}, "out": {"boulets": 4}, "workers": 4},
        "passive_label": "Fer → boulets (chaque tour) · fonte de canons",
    },
    "armurerie": {
        "id": "armurerie",
        "name": "Armurerie",
        "category": "production",
        "description": (
            "Râteliers, meules et établis. Fabrique et entretient coutelas, "
            "piques et mousquets pour armer l'équipage à l'abordage."
        ),
        "cost": {"gold": 400, "fer": 18, "bois": 12},
        "build_turns": 2, "workers": 3,
        "requires": ["charpenterie"],
        "recipe": {"in": {"fer": 2, "bois": 1}, "out": {"armes": 2}, "workers": 3},
        "passive_label": "Fer + bois → armes · armement de l'équipage",
    },

    # ---- Services -------------------------------------------------
    "estaminet": {
        "id": "estaminet",
        "name": "Estaminet du repaire",
        "category": "service",
        "description": (
            "Cabaret de planches et de barriques. On y boit, on y entend "
            "les rumeurs, et l'on y débauche des bras de passage."
        ),
        "cost": {"gold": 200, "bois": 15},
        "build_turns": 1, "workers": 2,
        "requires": [],
        "passive_label": "Moral de la garnison · recrutement local · rumeurs",
    },
    "tripot": {
        "id": "tripot",
        "name": "Tripot",
        "category": "service",
        "description": (
            "Dés, cartes et paris. La maison prélève sa part sur le jeu de "
            "la garnison — mais le jeu échauffe parfois les esprits."
        ),
        "cost": {"gold": 150, "bois": 10},
        "build_turns": 1, "workers": 1,
        "requires": [],
        "income": {"per_garrison": 1.1},
        "passive_label": "Revenu de jeu (selon la garnison) · paris au passage",
    },
    "infirmerie": {
        "id": "infirmerie",
        "name": "Infirmerie",
        "category": "service",
        "description": (
            "Cabane du chirurgien : charpie, eau-de-vie, instruments. On y "
            "remet sur pied les blessés et l'on y soigne les fiévreux."
        ),
        "cost": {"gold": 300, "bois": 15, "toile": 10},
        "build_turns": 2, "workers": 2,
        "requires": [],
        "passive_label": "Soins des blessés · réduit les pertes au repaire",
    },
    "marche_noir": {
        "id": "marche_noir",
        "name": "Marché noir",
        "category": "service",
        "description": (
            "Réseau de receleurs sans état d'âme. Achète vos matières et vos "
            "biens, vend ce qui manque — à des cours qui varient chaque jour."
        ),
        "cost": {"gold": 350, "bois": 15, "pierre": 10},
        "build_turns": 2, "workers": 2,
        "requires": ["entrepot"],
        "passive_label": "Achat/vente de ressources & biens (cours variables)",
    },
}


def get_building(bid: str) -> dict:
    return BASE_BUILDINGS[bid]


def list_buildings() -> list:
    return list(BASE_BUILDINGS.values())


def producing_buildings(built_ids):
    """Itère (bid, bdef) des bâtiments construits qui ont une `recipe`,
    dans un ordre de priorité stable."""
    order = ["cuisines", "distillerie", "armurerie", "fonderie"]
    for bid in order:
        if bid in built_ids and "recipe" in BASE_BUILDINGS[bid]:
            yield bid, BASE_BUILDINGS[bid]


def cost_str(bdef: dict) -> str:
    """Libellé lisible du coût d'un bâtiment."""
    parts = [f"{bdef['cost']['gold']} P8"]
    for k, v in bdef["cost"].items():
        if k == "gold":
            continue
        parts.append(f"{v} {item_label(k).split(' ')[0].lower()}")
    return ", ".join(parts)


# ===================================================================
# Services interactifs (visite du repaire)
# ===================================================================
# Signature commune : fn(base, state, ui)

def _visit_quai(base, state, ui):
    """Carénage : réparer la coque à terre, à bas coût en pièces, en
    consommant du bois (et un peu de cordage pour le regréement)."""
    ship = state.ship
    damage = ship["hull_max"] - ship["hull_current"]
    if damage <= 0:
        ui.info("La coque est saine. Rien à caréner.")
        return
    bois_dispo = base.resources.get("bois", 0)
    # 1 point de coque = 1 bois + 2 P8 de main-d'œuvre (vs 6 P8 au port).
    max_by_bois = bois_dispo
    max_by_gold = state.gold // 2
    repairable = min(damage, max_by_bois, max_by_gold)
    if repairable <= 0:
        ui.fail("Il faut du bois en réserve et quelques pièces pour caréner.")
        return
    qty = ui.ask_int(
        f"Caréner combien de points de coque ? (1 bois + 2 P8/pt, max {repairable})",
        min_val=0, max_val=repairable,
    )
    if qty <= 0:
        return
    base.resources["bois"] -= qty
    state.gold -= qty * 2
    ship["hull_current"] = min(ship["hull_max"], ship["hull_current"] + qty)
    ui.success(f"Coque carénée de {qty} points. Le navire est comme neuf… ou presque.")


def _visit_charpenterie(base, state, ui):
    """Refonte plus poussée : regréer (toile/cordage) pour un petit gain de
    coque supplémentaire et un coup de propre général."""
    if not base.has("quai"):
        ui.info("Sans cale de carénage, l'atelier ne peut tirer le navire au sec.")
        return
    ui.info("Le maître charpentier propose une remise en état complète.")
    needs = {"bois": 8, "cordage": 4}
    have = all(base.resources.get(k, 0) >= v for k, v in needs.items())
    cost_gold = 60
    options = []
    if have and state.gold >= cost_gold:
        options.append(("Refonte complète (8 bois, 4 cordage, 60 P8 → +12 coque)", "refit"))
    options.append(("Laisser tomber", "leave"))
    if ui.choose("À l'atelier :", options) == "refit":
        for k, v in needs.items():
            base.resources[k] -= v
        state.gold -= cost_gold
        ship = state.ship
        ship["hull_current"] = min(ship["hull_max"], ship["hull_current"] + 12)
        state.morale = min(100, state.morale + 2)
        ui.success("Bordages neufs, gréement revu. Coque +12.")


def _visit_distillerie(base, state, ui):
    """Distribuer du rhum produit pour remonter le moral du bord."""
    stock = base.goods.get("rhum", 0)
    if stock <= 0:
        ui.info("Les cuves sont vides. Il faut de la mélasse et un peu de patience.")
        return
    give = min(stock, max(1, stock))
    options = [
        (f"Embarquer tout le rhum ({stock}) — moral à bord +{min(20, stock)}", "load"),
        ("Le garder pour la vente", "keep"),
    ]
    if ui.choose("À la distillerie :", options) == "load":
        base.goods["rhum"] -= give
        state.morale = min(100, state.morale + min(20, give))
        ui.success(f"{give} mesures de rhum embarquées. L'équipage trinque à votre santé.")


def _visit_cuisines(base, state, ui):
    """Embarquer la viande boucanée comme vivres pour la prochaine sortie."""
    stock = base.goods.get("boucan", 0)
    if stock <= 0:
        ui.info("Les grils sont froids. Laissez la garnison chasser quelques tours.")
        return
    # 1 boucan ≈ 2 unités de vivres embarquées.
    room = 100 - state.supplies
    embarkable = min(stock, max(0, room // 2))
    if embarkable <= 0:
        ui.info("Les cales à vivres sont déjà pleines.")
        return
    qty = ui.ask_int(
        f"Embarquer combien de viande boucanée ? (1 → 2 vivres, max {embarkable})",
        min_val=0, max_val=embarkable,
    )
    if qty <= 0:
        return
    base.goods["boucan"] -= qty
    state.supplies = min(100, state.supplies + qty * 2)
    ui.success(f"{qty} charges de boucan embarquées. +{qty * 2} vivres.")


def _visit_fonderie(base, state, ui):
    """Fondre et monter une pièce supplémentaire sur le navire (capé)."""
    ship = state.ship
    cap = ship["guns"] + 6
    if ship["guns"] >= cap:
        ui.info("Le navire porte déjà tout ce que ses ponts peuvent souffrir.")
        return
    need_fer, need_boulets, cost_gold = 6, 4, 120
    can = (base.resources.get("fer", 0) >= need_fer
           and base.goods.get("boulets", 0) >= need_boulets
           and state.gold >= cost_gold)
    options = []
    if can:
        options.append(
            (f"Couler et monter une pièce ({need_fer} fer, {need_boulets} boulets, {cost_gold} P8)",
             "mount"))
    else:
        ui.info(f"Il faut {need_fer} fer, {need_boulets} boulets et {cost_gold} P8.")
    options.append(("Repartir", "leave"))
    if options and ui.choose("À la fonderie :", options) == "mount":
        base.resources["fer"] -= need_fer
        base.goods["boulets"] -= need_boulets
        state.gold -= cost_gold
        ship["guns"] += 1
        ui.success(f"Pièce montée. Le navire aligne désormais {ship['guns']} canons.")


def _visit_armurerie(base, state, ui):
    """Armer l'équipage : consommer des armes pour un bonus de combat
    temporaire (drapeau de quelques tours)."""
    stock = base.goods.get("armes", 0)
    if stock < 3:
        ui.info("Pas assez d'armes en magasin pour équiper une bordée.")
        return
    options = [
        ("Armer l'équipage (3 armes → combat renforcé 4 tours)", "arm"),
        ("Laisser au magasin", "leave"),
    ]
    if ui.choose("À l'armurerie :", options) == "arm":
        base.goods["armes"] -= 3
        state.flags["base_armed_until"] = state.turn + 4
        ui.success("Coutelas affûtés, mousquets chargés. Bonus de combat pour 4 tours.")


def _visit_infirmerie(base, state, ui):
    """Soigner : récupérer une partie des hommes manquants (vers crew_max),
    moyennant pièces et toile (charpie)."""
    ship = state.ship
    missing = ship["crew_max"] - state.crew
    if missing <= 0:
        ui.info("L'équipage est au complet. Le chirurgien se repose.")
        return
    toile = base.resources.get("toile", 0)
    # 1 homme remis sur pied = 5 P8 + 1 toile (charpie), plafonné à 10.
    healable = min(missing, toile, state.gold // 5, 10)
    if healable <= 0:
        ui.fail("Il faut de la toile pour la charpie et quelques pièces.")
        return
    qty = ui.ask_int(
        f"Soigner et réembarquer combien d'hommes ? (5 P8 + 1 toile, max {healable})",
        min_val=0, max_val=healable,
    )
    if qty <= 0:
        return
    base.resources["toile"] -= qty
    state.gold -= qty * 5
    state.crew += qty
    ui.success(f"{qty} hommes soignés rejoignent le rôle d'équipage.")


def _visit_estaminet(base, state, ui):
    """Boire (moral + rumeur) ou débaucher des bras de passage (or → crew)."""
    options = [
        ("Tournée générale (30 P8 → moral, rumeur)", "drink"),
        ("Débaucher des marins de passage", "recruit"),
        ("Repartir", "leave"),
    ]
    choice = ui.choose("À l'estaminet :", options)
    if choice == "drink":
        if state.gold < 30:
            ui.fail("Même le tafia se paie, capitaine.")
            return
        state.gold -= 30
        state.morale = min(100, state.morale + 6)
        rumeurs = [
            "Un négrier de la Royal African remontera la côte sous peu.",
            "Une frégate de la Navy a quitté la Jamaïque cap au sud.",
            "On dit qu'un galion isolé attend son convoi à Carthagène.",
            "Le receleur de Nassau paie le rhum au prix fort cette saison.",
        ]
        ui.info(f"Un gabier ivre lâche : « {random.choice(rumeurs)} »")
    elif choice == "recruit":
        ship = state.ship
        room = ship["crew_max"] - state.crew
        if room <= 0:
            ui.info("Le navire est plein ; nul besoin de bras de plus.")
            return
        available = random.randint(2, 8)
        price_per = 7
        affordable = min(available, room, state.gold // price_per)
        if affordable <= 0:
            ui.fail("Personne ne signe à ce prix ce soir.")
            return
        qty = ui.ask_int(
            f"Débaucher combien d'hommes ? ({price_per} P8/homme, {available} de passage, max {affordable})",
            min_val=0, max_val=affordable,
        )
        if qty <= 0:
            return
        state.gold -= qty * price_per
        state.crew += qty
        ui.success(f"{qty} hommes signent les Articles à l'estaminet.")


def _visit_tripot(base, state, ui):
    """Jouer en personne : mise à risque, gain ou perte selon un tirage."""
    options = [
        ("Miser 50 P8 aux dés", 50),
        ("Miser 150 P8 aux dés", 150),
        ("S'abstenir", 0),
    ]
    mise = ui.choose("Au tripot :", options)
    if not mise:
        return
    if state.gold < mise:
        ui.fail("Vous n'avez pas de quoi tenir une telle mise.")
        return
    state.gold -= mise
    roll = random.random()
    if roll < 0.45:
        gain = int(mise * 2)
        state.gold += gain
        ui.success(f"Les dés vous sourient ! Vous ramassez {gain} P8.")
    elif roll < 0.55:
        state.gold += mise
        ui.info("Partie nulle. Vous récupérez votre mise.")
    else:
        ui.fail(f"La chance vous tourne le dos. {mise} P8 envolés.")


def _visit_marche_noir(base, state, ui):
    """Marché noir : vendre matières et biens, acheter des matières —
    à des cours qui varient à chaque visite, avec marchandage possible."""
    factor = roll_market_factor()
    trade_bonus = float(base.mods.get("trade_bonus", 0.0))
    ui.info(f"Cours du jour : coefficient {factor:+.2f}"
            + (f" (bonus de place +{trade_bonus:.2f})" if trade_bonus else ""))

    while True:
        ui.divider()
        ui.info("Au marché noir :")
        options = [
            ("Vendre des biens manufacturés", "sell_goods"),
            ("Vendre des matières premières", "sell_res"),
            ("Acheter des matières premières", "buy_res"),
            ("Repartir", "leave"),
        ]
        choice = ui.choose("Que faites-vous ?", options)
        if choice == "leave":
            return
        if choice in ("sell_goods", "sell_res"):
            pool = GOODS if choice == "sell_goods" else RESOURCES
            store = base.goods if choice == "sell_goods" else base.resources
            sellable = [(iid, store.get(iid, 0)) for iid in pool if store.get(iid, 0) > 0]
            if not sellable:
                ui.info("Rien à vendre dans cette catégorie.")
                continue
            opts = [(f"{item_label(iid)} — {n} en stock "
                     f"(~{sell_unit_price(iid, factor, trade_bonus)} P8/u)", iid)
                    for iid, n in sellable]
            opts.append(("Retour", None))
            iid = ui.choose("Vendre quoi ?", opts)
            if iid is None:
                continue
            have = store.get(iid, 0)
            qty = ui.ask_int(f"Vendre combien de {item_label(iid)} ? (max {have})",
                             min_val=0, max_val=have)
            if qty <= 0:
                continue
            gross = sell_unit_price(iid, factor, trade_bonus) * qty
            skill = (state.get_effective_bonus("leadership")
                     + state.get_effective_bonus("discipline"))
            net, issue = haggle(gross, skill)
            store[iid] -= qty
            state.gold += net
            msg = {"gagné": "Vous tenez bon sur le prix.",
                   "perdu": "Le receleur rogne sa marge.",
                   "neutre": "Marché conclu sans éclat."}[issue]
            ui.success(f"+{net} P8 pour {qty} {item_label(iid)}. {msg}")
        elif choice == "buy_res":
            opts = [(f"{item_label(iid)} (~{buy_unit_price(iid, factor)} P8/u)", iid)
                    for iid in RESOURCES]
            opts.append(("Retour", None))
            iid = ui.choose("Acheter quoi ?", opts)
            if iid is None:
                continue
            unit = buy_unit_price(iid, factor)
            room = base.free_space()
            max_buy = min(room, state.gold // unit)
            if max_buy <= 0:
                ui.fail("Pas de place en magasin, ou pas assez en caisse.")
                continue
            qty = ui.ask_int(f"Acheter combien de {item_label(iid)} ? "
                             f"({unit} P8/u, max {max_buy})",
                             min_val=0, max_val=max_buy)
            if qty <= 0:
                continue
            state.gold -= qty * unit
            added = base.add_resource(iid, qty)
            ui.success(f"{added} {item_label(iid)} rentrés en magasin "
                       f"(−{qty * unit} P8).")


VISIT_HANDLERS = {
    "quai": _visit_quai,
    "charpenterie": _visit_charpenterie,
    "distillerie": _visit_distillerie,
    "cuisines": _visit_cuisines,
    "fonderie": _visit_fonderie,
    "armurerie": _visit_armurerie,
    "infirmerie": _visit_infirmerie,
    "estaminet": _visit_estaminet,
    "tripot": _visit_tripot,
    "marche_noir": _visit_marche_noir,
}
