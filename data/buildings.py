"""
Bâtiments particuliers par port.

Chaque port définit une liste de bâtiments (au-delà des services génériques
supplies/recruit/repair/fence/tavern/shipyard). Ces bâtiments donnent accès
à des interactions thématiques : marché aux esclaves de Tortuga, asiento
de La Havane, camp de boucanage, palais du gouverneur de Port Royal, etc.

Convention d'image : chaque bâtiment a son propre fond de scène
   assets/images/ports/<port_id>/<building_id>.png

Pour AJOUTER un bâtiment : créer la fonction `_interact_xxx` et inscrire
l'entrée dans BUILDINGS[<port_id>].
"""

import random
from data.prisoners import (
    PRISONER_TYPES, count_by_type,
    filter_enslaved, filter_non_enslaved,
    value_for_engage, value_for_ransom, value_for_slave_market,
)


# =================================================================
# TORTUGA — flibustier français, sous d'Ogeron puis du Casse
# =================================================================

def _interact_captif_market(state, ui):
    """Marché aux engagés et captifs de Tortuga (sous tolérance française).

    Notes historiques : Bertrand d'Ogeron a tenté de régulariser le système
    des engagés à 36 mois ; les flibustiers y vendaient leurs prises
    humaines, principalement issues d'attaques contre les Espagnols.
    """
    if not state.prisoners:
        ui.info("Le marché est vide. Vous n'avez personne à vendre.")
        return
    _market_menu(state, ui,
        title="Marché aux engagés et captifs de Tortuga",
        accept_enslaved=True,
        slave_rep_factor=1.0,
        engage_rate=1.0)


def _interact_boucan_camp(state, ui):
    """Camp de boucanage : viande fumée des bœufs d'Hispaniola."""
    ui.narrate(
        "L'odeur de viande fumée se sent depuis la grève. Des boucaniers "
        "torse nu retournent les quartiers de bœuf sur les grils ; un "
        "vieux nègre maron tient l'inventaire."
    )
    options = []
    bundle_cost = 60
    bundle_supplies = 25
    if state.gold >= bundle_cost:
        options.append(
            (f"Acheter un baril de viande fumée ({bundle_supplies} vivres, {bundle_cost} P8)",
             "buy_meat"))
    options.append(("Embaucher 2 tireurs boucaniers pour la prochaine sortie (40 P8)",
                    "hire_marksmen"))
    options.append(("Repartir", "leave"))
    choice = ui.choose("Au camp :", options)

    if choice == "buy_meat" and state.gold >= bundle_cost:
        state.gold -= bundle_cost
        state.supplies = min(100, state.supplies + bundle_supplies)
        ui.success(f"+{bundle_supplies} vivres en cale.")
    elif choice == "hire_marksmen":
        if state.gold < 40:
            ui.fail("Pas assez en caisse.")
        else:
            state.gold -= 40
            state.flags["boucanier_marksmen"] = state.turn + 4   # actif 4 tours
            ui.success("Deux tireurs des bois embarqueront avec vous (combat boosté pendant 4 tours).")


# =================================================================
# PORT ROYAL — colonie anglaise, prospérité 1655-1692
# =================================================================

def _interact_vendue_bridge_street(state, ui):
    """Marché public de Bridge Street (Vendue). Port Royal était un débouché
    majeur de la traite anglaise vers la Jamaïque jusqu'au séisme de 1692."""
    if not state.prisoners:
        ui.info("Aucun captif à vendre.")
        return
    _market_menu(state, ui,
        title="Vendue de Bridge Street, Port Royal",
        accept_enslaved=True,
        slave_rep_factor=1.0,
        engage_rate=1.1)


def _interact_governor_palace(state, ui):
    """Palais du gouverneur (Modyford, Lynch ou successeur)."""
    year = state.current_date().year
    if year <= 1671:
        gov = "Sir Thomas Modyford"
    elif year <= 1684:
        gov = "Sir Thomas Lynch"
    else:
        gov = "le gouverneur en exercice"
    ui.narrate(
        f"Une livrée vous introduit auprès de {gov}. Madère, gravures de "
        "Londres, tapis de Smyrne. La conversation est ce qu'elle doit être."
    )
    options = [
        ("Présenter ses respects (don de 100 P8)", "tribute"),
        ("Solliciter une lettre de marque (si pas déjà commissionné)", "commission"),
        ("Prendre congé", "leave"),
    ]
    choice = ui.choose("Que faites-vous ?", options)
    if choice == "tribute":
        if state.gold >= 100:
            state.gold -= 100
            state.flags["portroyal_friend"] = True
            ui.success("Le gouverneur accepte le présent. La garnison fermera les yeux.")
        else:
            ui.fail("Vous n'avez pas 100 pièces pour un tel geste. Le gouverneur s'en aperçoit.")
            state.reputation = max(0, state.reputation - 1)
    elif choice == "commission":
        if state.flags.get("commission_anglaise"):
            ui.info("Vous êtes déjà au service de Sa Majesté.")
        else:
            state.flags["commission_anglaise"] = True
            state.gold += 150
            state.reputation = max(0, state.reputation - 2)
            ui.success("Commission scellée. 150 pièces d'avance.")


def _interact_military_hospital(state, ui):
    """Hôpital militaire de Port Royal (existait dès 1670)."""
    if state.crew >= state.ship["crew_max"]:
        ui.info("Votre équipage est au complet. Pas de blessés à soigner.")
        return
    damage = state.ship["crew_max"] - state.crew
    cost_per_man = 4
    treatable = min(damage, state.gold // cost_per_man, 10)
    if treatable <= 0:
        ui.fail("Pas de fonds pour les chirurgiens.")
        return
    qty = ui.ask_int(
        f"Combien d'hommes soigner ? ({cost_per_man} P8/homme, max {treatable})",
        min_val=0, max_val=treatable,
    )
    state.gold -= qty * cost_per_man
    state.crew += qty
    ui.success(f"{qty} blessés remis sur pied et signent les Articles.")


# =================================================================
# NASSAU — République des pirates 1706-1718
# =================================================================

def _interact_articles_tree(state, ui):
    """L'arbre des Articles : lieu d'assemblée pirate à Nassau."""
    ui.narrate(
        "Le grand sablier sous l'arbre. Des capitaines, des quartiers-maîtres "
        "y discutent l'application des Articles. On vous fait signe."
    )
    options = [
        ("Tenir conseil — possibilité de renégocier les Articles", "council"),
        ("Écouter les rumeurs", "rumor"),
        ("Repartir", "leave"),
    ]
    choice = ui.choose("Sous l'arbre :", options)
    if choice == "council":
        # Trade morale (re-vote) for discipline
        if state.morale < 60:
            state.morale = min(100, state.morale + 12)
            ui.success("Le conseil réécrit les Articles. Moral renfloué.")
        else:
            state.morale = min(100, state.morale + 4)
            ui.info("Les Articles tiennent. Quelques retouches. Léger gain de moral.")
    elif choice == "rumor":
        rumors = [
            "Hornigold a refusé une commission espagnole.",
            "Charles Vane chasse seul depuis l'éviction de Rackham.",
            "Un sloop sortira de la Floride à la prochaine lune.",
            "La frégate Pearl mouille devant Charleston.",
        ]
        ui.info(f"On murmure : « {random.choice(rumors)} »")
        if "convoy" in random.choice(rumors).lower():
            state.flags["heard_convoy"] = True


def _interact_weapon_cache(state, ui):
    """Cache d'armes : achat de canons supplémentaires (capé)."""
    current = state.ship["guns"]
    cap = state.ship["guns"] + 6   # max +6 par-dessus le standard du navire
    if current >= cap:
        ui.info("Vous ne pouvez plus monter davantage de pièces sur ce navire.")
        return
    cost = 80
    if state.gold < cost:
        ui.fail(f"Un canon coûte {cost} P8. Vous n'avez pas la somme.")
        return
    choice = ui.choose(
        f"Acheter et monter un canon supplémentaire pour {cost} P8 ?",
        [("Oui", "yes"), ("Non", "no")],
    )
    if choice == "yes":
        state.gold -= cost
        state.ship["guns"] += 1
        ui.success(f"Pièce installée. Vous avez désormais {state.ship['guns']} canons.")


# =================================================================
# ÎLE SAINTE-MARIE — Madagascar 1690-1720
# =================================================================

def _interact_village_sakalava(state, ui):
    """Échanges avec les Sakalava, peuple côtier malgache."""
    ui.narrate(
        "Les pirogues à balanciers viennent à votre rencontre. Le roi "
        "sakalava de Boina envoie son émissaire — il troque, à condition "
        "qu'on respecte les usages."
    )
    options = [
        ("Troquer de la poudre contre des épices (+30 vivres, -30 P8 équiv.)", "spices"),
        ("Engager un pilote local des côtes malgaches (60 P8)", "pilot"),
        ("Repartir poliment", "leave"),
    ]
    choice = ui.choose("Au village :", options)
    if choice == "spices":
        if state.gold >= 30:
            state.gold -= 30
            state.supplies = min(100, state.supplies + 30)
            state.morale = min(100, state.morale + 3)
            ui.success("Épices et fruits embarqués. L'équipage approuve.")
        else:
            ui.fail("Vous n'avez pas de quoi troquer.")
    elif choice == "pilot":
        if state.gold >= 60 and not state.flags.get("sakalava_pilot"):
            state.gold -= 60
            state.flags["sakalava_pilot"] = True
            ui.success("Un pilote sakalava embarque. Les courants du Mozambique n'auront plus de secret.")
        elif state.flags.get("sakalava_pilot"):
            ui.info("Vous avez déjà un pilote local à bord.")
        else:
            ui.fail("Pas les 60 pièces.")


# =================================================================
# LA HAVANE — Asiento espagnol (hostile)
# =================================================================

def _interact_asiento(state, ui):
    """Asiento : monopole espagnol de la traite, accordé à des compagnies
    étrangères (génoises puis anglaises). Vendre ici rapporte gros mais
    expose à des représailles."""
    enslaved = filter_enslaved(state.prisoners)
    if not enslaved:
        ui.info("L'Asiento ne traite qu'avec ceux qui ont du fret humain à vendre.")
        return
    ui.narrate(
        "Vous abordez discrètement les commissaires de l'Asiento. Les prix "
        "y sont les plus hauts des Caraïbes — mais une cargaison vendue ici "
        "se sait dans toute la mer."
    )
    _market_menu(state, ui,
        title="Asiento de La Havane",
        accept_enslaved=True,
        accept_non_enslaved=False,
        slave_rep_factor=2.5,   # réputation chute deux fois et demie plus vite
        slave_price_factor=1.6,
        engage_rate=1.0)


# =================================================================
# CHARLESTON — Caroline anglaise
# =================================================================

def _interact_charleston_vendue(state, ui):
    """Vendue coloniale. La Caroline accueillait son propre marché aux
    esclaves depuis 1670, surtout après l'essor du riz et de l'indigo."""
    if not state.prisoners:
        ui.info("Vous n'avez personne à vendre à la vendue.")
        return
    _market_menu(state, ui,
        title="Vendue de Charles Town",
        accept_enslaved=True,
        slave_rep_factor=1.2,
        engage_rate=1.0)


def _interact_huguenot_quarter(state, ui):
    """Quartier huguenot — Huguenots français réfugiés en Caroline après 1685."""
    ui.narrate(
        "Le quartier huguenot bruisse de français à l'accent saintongeais. "
        "Un négociant d'origine rochelaise vous reçoit dans son entrepôt."
    )
    options = [
        ("Acheter de la poudre et du plomb de qualité (50 P8, +15 vivres équivalent combat)", "buy_powder"),
        ("Engager 3 huguenots francophones (60 P8)", "hire"),
        ("Repartir", "leave"),
    ]
    choice = ui.choose("Au quartier huguenot :", options)
    if choice == "buy_powder":
        if state.gold >= 50:
            state.gold -= 50
            state.flags["huguenot_powder"] = state.turn + 4
            ui.success("Poudre fine en cale. Bonus de combat pour les 4 prochains tours.")
        else:
            ui.fail("Pas les 50 pièces.")
    elif choice == "hire":
        if state.gold >= 60 and state.crew + 3 <= state.ship["crew_max"]:
            state.gold -= 60
            state.crew += 3
            ui.success("Trois huguenots signent les Articles — disciplinés et lettrés.")
        elif state.crew + 3 > state.ship["crew_max"]:
            ui.fail("Le navire est trop plein.")
        else:
            ui.fail("Pas les 60 pièces.")


# =================================================================
# PETIT-GOÂVE — Saint-Domingue française
# =================================================================

def _interact_sugar_estate(state, ui):
    """Habitation sucrière. Les plantations de Saint-Domingue achetaient
    volontiers le rhum et le sucre brut ramenés des prises antillaises."""
    if state.loot < 50:
        ui.info("L'intendant veut de la cargaison en gros. Vous n'avez pas assez de butin brut.")
        return
    # Recèlement à taux préférentiel pour le butin brut spécifiquement
    bonus_rate = 0.85
    sale = int(state.loot * bonus_rate)
    choice = ui.choose(
        f"L'habitation rachète tout votre butin à 85% ({state.loot} → {sale} P8). Vendre ?",
        [("Oui", "yes"), ("Non", "no")],
    )
    if choice == "yes":
        state.gold += sale
        state.loot = 0
        ui.success(f"+{sale} pièces de huit. Marché conclu avec l'intendant.")


def _interact_du_casse_residence(state, ui):
    """Résidence du gouverneur du Casse (1691-1700)."""
    year = state.current_date().year
    if not (1691 <= year <= 1700):
        ui.info("Le gouverneur du Casse n'est pas à Petit-Goâve cette année-là.")
        return
    ui.narrate(
        "Jean-Baptiste du Casse vous reçoit. Le gouverneur cherche toujours "
        "des capitaines pour la course contre les Anglais et les Hollandais."
    )
    options = [
        ("Solliciter une commission française", "commission"),
        ("Promettre une part des prises pour soutien logistique (+50 vivres)", "supplies"),
        ("Repartir", "leave"),
    ]
    choice = ui.choose("Chez du Casse :", options)
    if choice == "commission":
        if not state.flags.get("commission_francaise"):
            state.flags["commission_francaise"] = True
            state.gold += 100
            state.reputation = max(0, state.reputation - 1)
            ui.success("Brevet signé. 100 P8 d'avance.")
        else:
            ui.info("Vous êtes déjà commissionné.")
    elif choice == "supplies":
        state.supplies = min(100, state.supplies + 50)
        state.flags["debt_du_casse"] = state.flags.get("debt_du_casse", 0) + 100
        ui.success("Vivres embarqués. Du Casse note la dette.")


# =================================================================
# Marché générique (utilisé par les marchés aux captifs)
# =================================================================

def _market_menu(state, ui, *, title, accept_enslaved=True, accept_non_enslaved=True,
                 slave_rep_factor=1.0, slave_price_factor=1.0, engage_rate=1.0):
    """Menu de marché aux captifs.

    Options :
      - Envoyer une lettre de rançon (notables, marchands, dames) :
        retire le prisonnier du bord, encaissement après quelques tours,
        forte rentabilité. C'est la voie principale pour les notables.
      - Vendre comme engagé (matelots, prisonniers communs) : faible
        gain immédiat, faible coût moral.
      - Vendre les captifs africains au marché aux esclaves : fort gain
        mais lourd coût moral et de réputation.
      - Quitter.

    Conscient des enjeux moraux : chaque vente d'un captif enslaved
    coûte du moral à l'équipage (les Articles de plusieurs équipages
    pirates, dont celui de Sam Bellamy, étaient hostiles à la traite),
    et de la réputation auprès des ports non-esclavagistes.
    """
    from data.prisoners import (
        ransom_delay_turns, value_for_ransom, value_for_engage,
        value_for_slave_market, filter_enslaved, filter_non_enslaved,
        filter_ransomable, PRISONER_TYPES, count_by_type,
    )

    while True:
        if not state.prisoners:
            ui.info("Vous n'avez plus de captifs.")
            return

        ui.divider()
        ui.info(title)
        counts = count_by_type(state.prisoners)
        ui.info("Vous détenez :")
        for type_id, n in counts.items():
            ui.info(f"  • {n} × {PRISONER_TYPES[type_id]['label']}")

        options = []

        enslaved = filter_enslaved(state.prisoners)
        non_enslaved = filter_non_enslaved(state.prisoners)
        ransomable = filter_ransomable(state.prisoners)

        if ransomable:
            est = sum((PRISONER_TYPES[p["type"]]["ransom_value"][0]
                       + PRISONER_TYPES[p["type"]]["ransom_value"][1]) // 2
                      for p in ransomable)
            options.append((
                f"Envoyer des lettres de rançon pour {len(ransomable)} notable(s)  "
                f"(≈ {est} P8 après quelques mois)",
                "ransom",
            ))

        if accept_non_enslaved and non_enslaved:
            est = sum((PRISONER_TYPES[p["type"]]["engage_value"][0]
                       + PRISONER_TYPES[p["type"]]["engage_value"][1]) // 2
                      for p in non_enslaved)
            est = int(est * engage_rate)
            options.append((
                f"Vendre les {len(non_enslaved)} captifs comme engagés (≈ {est} P8, paiement immédiat)",
                "sell_engages",
            ))

        if accept_enslaved and enslaved:
            proto = PRISONER_TYPES["enslaved_african"]
            lo, hi = proto["slave_price"]
            avg = (lo + hi) // 2
            est_total = int(len(enslaved) * avg * slave_price_factor)
            morale_loss = proto["morale_cost_sell"] * len(enslaved)
            rep_loss = int((len(enslaved) // 5) * slave_rep_factor)
            options.append((
                f"Vendre les {len(enslaved)} captifs africains au marché aux esclaves  "
                f"(≈ {est_total} P8, moral -{morale_loss}, réputation -{rep_loss})",
                "sell_enslaved",
            ))

        options.append(("Quitter le marché", "leave"))

        choice = ui.choose("Que faites-vous ?", options)

        if choice == "leave":
            return

        if choice == "ransom":
            total_amount = 0
            for p in list(ransomable):
                amount = value_for_ransom(p)
                due_turn = state.turn + ransom_delay_turns()
                state.pending_ransoms.append({
                    "prisoner": p,
                    "due_turn": due_turn,
                    "amount": amount,
                })
                total_amount += amount
                state.prisoners.remove(p)
            ui.success(
                f"Lettres expédiées pour {len(ransomable)} captif(s). "
                f"Les rançons (≈ {total_amount} P8 au total) parviendront "
                f"d'ici quelques mois, port par port."
            )
            ui.info(
                "Les notables sont escortés à terre sous bonne garde, en "
                "attendant leur famille."
            )

        elif choice == "sell_engages":
            total = sum(value_for_engage(p) for p in non_enslaved)
            total = int(total * engage_rate)
            state.gold += total
            state.morale = max(0, state.morale - 2)
            state.prisoners = [p for p in state.prisoners if p["is_enslaved"]]
            ui.success(f"+{total} pièces de huit pour les engagements de 36 mois.")

        elif choice == "sell_enslaved":
            total = sum(value_for_slave_market(p) for p in enslaved)
            total = int(total * slave_price_factor)
            state.gold += total
            morale_loss = PRISONER_TYPES["enslaved_african"]["morale_cost_sell"] * len(enslaved)
            rep_loss = int((len(enslaved) // 5) * slave_rep_factor)
            state.morale = max(0, state.morale - morale_loss)
            state.reputation = max(0, state.reputation - rep_loss)
            state.flags["sold_enslaved"] = state.flags.get("sold_enslaved", 0) + len(enslaved)
            state.prisoners = [p for p in state.prisoners if not p["is_enslaved"]]
            ui.success(
                f"+{total} pièces de huit. L'équipage encaisse — certains baissent les yeux. "
                f"Moral -{morale_loss}, réputation -{rep_loss}."
            )


# =================================================================
# Bordel — lieu de débauche (Port Royal, Tortuga)
# =================================================================
# Port Royal était surnommée « Sodom of the New World » (Cordingly,
# Under the Black Flag) ; les bordels constituaient une partie
# significative de l'économie portuaire. À Tortuga, les « femmes du Roi »
# envoyées par Colbert au XVIIᵉ formaient une autre catégorie.

def _interact_brothel(state, ui):
    from data.prisoners import (
        filter_female, value_for_brothel,
        BROTHEL_MORALE_COST, BROTHEL_REP_COST_PER_3,
    )

    while True:
        ui.divider()
        ui.narrate(
            "Lampes basses, rhum coupé, musiciens fatigués. La maison "
            "tient table jusqu'au matin."
        )

        options = []
        spend_cost = 40
        if state.gold >= spend_cost:
            options.append(
                (f"Régaler l'équipage ({spend_cost} P8 — moral, rumeurs)", "spend"))

        female_prisoners = filter_female(state.prisoners)
        if female_prisoners:
            n = len(female_prisoners)
            # Estimation à mi-fourchette
            est = sum(((60 + 100) // 2) for _ in female_prisoners)
            morale_loss = BROTHEL_MORALE_COST * n
            rep_loss = n // 3 * BROTHEL_REP_COST_PER_3
            options.append((
                f"Vendre les {n} captives à la maison "
                f"(≈ {est} P8 forfaitaires, moral -{morale_loss}, réputation -{rep_loss})",
                "sell",
            ))

        options.append(("Repartir", "leave"))

        choice = ui.choose("Que faites-vous ?", options)
        if choice == "leave":
            return

        if choice == "spend":
            state.gold -= spend_cost
            state.morale = min(100, state.morale + 8)
            rumors = [
                "Un Indiaman fera escale à Charleston dans le mois.",
                "Une frégate de la Royal Navy patrouille au nord de Cuba.",
                "On dit qu'un capitaine portugais cache son or à Sainte-Marie.",
                "Le gouverneur de la Jamaïque promet 500 P8 pour la tête de tout pirate.",
            ]
            import random as _r
            ui.info(f"Une fille glisse une rumeur entre deux verres : "
                    f"« {_r.choice(rumors)} »")

        elif choice == "sell":
            # Tarif forfaitaire bas — bien moins lucratif qu'une rançon.
            total = sum(value_for_brothel(p) for p in female_prisoners)
            n = len(female_prisoners)
            morale_loss = BROTHEL_MORALE_COST * n
            rep_loss = (n // 3) * BROTHEL_REP_COST_PER_3
            state.gold += total
            state.morale = max(0, state.morale - morale_loss)
            state.reputation = max(0, state.reputation - rep_loss)
            state.flags["sold_to_brothel"] = state.flags.get("sold_to_brothel", 0) + n
            # On retire les femmes (non-enslaved) de la liste des prisonniers
            state.prisoners = [
                p for p in state.prisoners
                if not (p.get("gender") == "F" and not p["is_enslaved"])
            ]
            ui.success(
                f"+{total} pièces de huit. Le tenancier ne discute pas le prix. "
                f"Plusieurs hommes de l'équipage quittent la salle sans boire."
            )
            ui.info(
                "(Note : les notables auraient rapporté beaucoup plus en rançon.)"
            )


# =================================================================
# Catalogue par port
# =================================================================

BUILDINGS = {
    "tortuga": [
        {
            "id": "captif_market",
            "name": "Marché aux engagés et captifs",
            "description": "Tribune publique près du quai. Ouvert aux flibustiers.",
            "available": lambda s: True,
            "interact": _interact_captif_market,
        },
        {
            "id": "boucan_camp",
            "name": "Camp de boucanage",
            "description": "Grils fumants, viande de bœuf sauvage d'Hispaniola.",
            "available": lambda s: True,
            "interact": _interact_boucan_camp,
        },
        {
            "id": "brothel",
            "name": "Maison de la Cayonne",
            "description": "Bordel et tripot du port. Achète des captives à bas prix.",
            "available": lambda s: True,
            "interact": _interact_brothel,
        },
    ],
    "port_royal": [
        {
            "id": "vendue",
            "name": "Vendue de Bridge Street",
            "description": "Marché public anglais (engagés et captifs).",
            "available": lambda s: True,
            "interact": _interact_vendue_bridge_street,
        },
        {
            "id": "governor_palace",
            "name": "Palais du gouverneur",
            "description": "Résidence officielle. Audience sur invitation.",
            "available": lambda s: True,
            "interact": _interact_governor_palace,
        },
        {
            "id": "military_hospital",
            "name": "Hôpital militaire",
            "description": "Chirurgiens d'armée — soignent les blessés moyennant finance.",
            "available": lambda s: True,
            "interact": _interact_military_hospital,
        },
        {
            "id": "brothel",
            "name": "Maison de Bear Garden Lane",
            "description": "« Sodom of the New World » — tripots, dés, filles publiques.",
            "available": lambda s: True,
            "interact": _interact_brothel,
        },
    ],
    "nassau": [
        {
            "id": "articles_tree",
            "name": "Arbre des Articles",
            "description": "Lieu d'assemblée des capitaines pirates de Nassau.",
            "available": lambda s: s.current_date().year <= 1718,
            "interact": _interact_articles_tree,
        },
        {
            "id": "weapon_cache",
            "name": "Cache d'armes",
            "description": "Canons et poudre détournés des navires marchands.",
            "available": lambda s: True,
            "interact": _interact_weapon_cache,
        },
    ],
    "ile_sainte_marie": [
        {
            "id": "village_sakalava",
            "name": "Village sakalava",
            "description": "Comptoir d'échanges avec le royaume sakalava du Boina.",
            "available": lambda s: True,
            "interact": _interact_village_sakalava,
        },
    ],
    "la_havane": [
        {
            "id": "asiento",
            "name": "Asiento espagnol",
            "description": "Bureau du monopole. N'achète que des captifs africains.",
            "available": lambda s: True,
            "interact": _interact_asiento,
        },
    ],
    "charleston": [
        {
            "id": "vendue_charleston",
            "name": "Vendue de Charles Town",
            "description": "Marché public — esclaves, engagés, marchandises de prise.",
            "available": lambda s: True,
            "interact": _interact_charleston_vendue,
        },
        {
            "id": "huguenot_quarter",
            "name": "Quartier huguenot",
            "description": "Comptoir des Français réfugiés. Poudre fine, recrues.",
            "available": lambda s: True,
            "interact": _interact_huguenot_quarter,
        },
    ],
    "saint_domingue": [
        {
            "id": "sugar_estate",
            "name": "Habitation sucrière",
            "description": "Plantation. Rachète le butin brut à bon prix.",
            "available": lambda s: True,
            "interact": _interact_sugar_estate,
        },
        {
            "id": "du_casse_residence",
            "name": "Résidence du gouverneur du Casse",
            "description": "Audience pour commissions de course (1691-1700).",
            "available": lambda s: 1691 <= s.current_date().year <= 1700,
            "interact": _interact_du_casse_residence,
        },
    ],
}


def get_buildings(port_id: str) -> list:
    """Renvoie les bâtiments du port, filtrés par disponibilité."""
    return [b for b in BUILDINGS.get(port_id, [])]
