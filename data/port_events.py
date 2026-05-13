"""
Événements déclenchés à l'arrivée dans un port spécifique.

Chaque port a sa liste d'événements possibles, tirée au sort à l'arrivée
(probabilité globale : voir PORT_EVENT_CHANCE).

Pour AJOUTER un événement de port :
    1. Écrire la fonction `_resolve_xxx(state, ui)`.
    2. L'ajouter dans la liste PORT_EVENTS[<port_id>].

Champs d'un événement :
    id          : identifiant
    title       : titre affiché
    weight      : poids (probabilité relative)
    conditions  : fonction(state) -> bool   (filtre supplémentaire — date,
                  réputation, drapeau d'événement…)
    resolve     : fonction(state, ui)
    image       : illustration (optionnelle)
"""

import random


# Probabilité qu'un événement de port se déclenche à l'arrivée.
PORT_EVENT_CHANCE = 0.65


# -------------------------------------------------------------------
# TORTUGA (1630-1700) — repaire flibustier sous tolérance française
# -------------------------------------------------------------------

def _tortuga_audience_ogeron(state, ui):
    """Bertrand d'Ogeron a été gouverneur de Tortue / Saint-Domingue 1665-1675.
    Il a régularisé la flibuste en délivrant des commissions et en organisant
    la société des Frères de la Côte."""
    ui.narrate(
        "Un valet en livrée vous fait demander à la résidence du gouverneur "
        "Bertrand d'Ogeron. Le Sieur veut connaître les nouveaux capitaines "
        "qui mouillent sur son île. Il vous offre un verre de vin de Bordeaux."
    )
    choice = ui.choose(
        "Que lui répondez-vous ?",
        [
            ("Accepter une commission de course contre l'Espagnol", "commission"),
            ("Refuser poliment — vous tenez à votre liberté", "decline"),
        ],
    )
    if choice == "commission":
        state.flags["commission_francaise"] = True
        state.gold += 100
        ui.success(
            "D'Ogeron vous remet un brevet, 100 pièces d'avance, et exige "
            "le cinquième du butin sur les prises espagnoles. La réputation "
            "auprès des autres puissances grimpe."
        )
        state.reputation = max(0, state.reputation - 1)
    else:
        ui.info(
            "Vous quittez la résidence sans engagement. D'Ogeron sourit : "
            "« Vous reviendrez peut-être. » Le moral de l'équipage monte un peu."
        )
        state.morale = min(100, state.morale + 3)


def _tortuga_tavern_brawl(state, ui):
    ui.narrate(
        "À la Cayonne, l'équipage cherche du rhum. Un boucanier ivre vous "
        "provoque en duel pour une affaire d'honneur obscure."
    )
    choice = ui.choose(
        "Comment réagissez-vous ?",
        [
            ("Accepter le duel", "duel"),
            ("Faire intervenir le quartier-maître", "diffuse"),
        ],
    )
    if choice == "duel":
        roll = random.random() + state.captain["bonus"].get("combat", 0) * 0.1
        if roll > 0.55:
            state.reputation += 2
            state.morale = min(100, state.morale + 8)
            ui.success("Trois coups de coutelas, l'autre s'écroule. Votre nom court les baraques.")
        else:
            crew_lost = 0
            state.morale = max(0, state.morale - 10)
            ui.fail("Vous prenez une vilaine entaille au flanc. Humiliation publique.")
    else:
        ui.info("Le quartier-maître sépare les deux hommes. L'incident s'éteint sans gloire.")


def _tortuga_boucaniers(state, ui):
    """Les boucaniers d'Hispaniola fumaient la viande de bœufs sauvages
    sur des grils nommés « boucans » (mot tupi). Ils étaient une réserve
    de recrues pour la flibuste."""
    ui.narrate(
        "Une troupe de boucaniers descend des collines d'Hispaniola, sales, "
        "armés de leurs longs fusils. Ils sentent le boucan. Six d'entre eux "
        "veulent embarquer."
    )
    choice = ui.choose(
        "Les enrôlez-vous ?",
        [
            ("Oui, sans solde mais avec une part complète", "yes"),
            ("Non, ils m'ont l'air trop indépendants", "no"),
        ],
    )
    if choice == "yes":
        if state.crew + 6 <= state.ship["crew_max"]:
            state.crew += 6
            state.morale = min(100, state.morale + 5)
            ui.success("Six boucaniers signent les Articles. Tireurs d'élite.")
        else:
            state.gold += 30
            ui.info("Le navire est plein. Ils acceptent 30 pièces pour le tuyau d'un mouillage.")
    else:
        ui.info("Ils s'en vont vers un autre capitaine.")


# -------------------------------------------------------------------
# PORT ROYAL (1655-1692) — base anglaise détruite le 7 juin 1692
# -------------------------------------------------------------------

def _portroyal_modyford(state, ui):
    """Thomas Modyford, gouverneur 1664-1671, commissionnait Morgan."""
    ui.narrate(
        "Sir Thomas Modyford vous reçoit à Spanish Town. Cravate de dentelle, "
        "verre de madère. Il évoque les bénéfices d'une expédition contre "
        "Portobelo ou Maracaibo — bien sûr, sous commission royale."
    )
    choice = ui.choose(
        "Acceptez-vous la commission anglaise ?",
        [
            ("Oui — la course est plus rémunératrice que la piraterie", "yes"),
            ("Non — pas question de partager avec la Couronne", "no"),
        ],
    )
    if choice == "yes":
        state.flags["commission_anglaise"] = True
        state.gold += 150
        state.reputation = max(0, state.reputation - 2)
        ui.success(
            "Vous êtes désormais corsaire au service de Sa Majesté. "
            "150 pièces d'avance, et la Navy fermera les yeux."
        )
    else:
        ui.info("Modyford vous congédie froidement. Mauvais ami à se faire.")
        state.flags["snub_modyford"] = True


def _portroyal_earthquake_warning(state, ui):
    """Précurseurs du séisme de juin 1692 : les contemporains rapportent
    de petites secousses dans les semaines précédentes."""
    if state.current_date().year < 1692:
        return  # cohérence historique
    ui.narrate(
        "Une secousse fait tinter les verres dans la taverne. Un vieux "
        "ministre presbytérien vous met en garde : « Cette ville sera "
        "engloutie pour ses péchés. » Vous riez avec les autres."
    )
    state.flags["earthquake_warning"] = True
    if random.random() < 0.4:
        ui.fail(
            "Au matin du 7 juin, une seconde secousse, plus violente. "
            "Une partie du quai s'effondre dans le port. Votre navire prend "
            "l'eau — il fallait écouter le pasteur."
        )
        damage = random.randint(15, 30)
        state.ship["hull_current"] = max(0, state.ship["hull_current"] - damage)


def _portroyal_recruit_rush(state, ui):
    ui.narrate(
        "Trois marchands jamaïcains ont licencié leurs équipages : la guerre "
        "menace et ils préfèrent désarmer. Une vingtaine de matelots cherchent "
        "à signer des Articles."
    )
    available = min(15, state.ship["crew_max"] - state.crew)
    if available <= 0:
        ui.info("Votre navire est déjà plein. Vous passez votre tour.")
        return
    price = 6 * available
    choice = ui.choose(
        f"Engager {available} hommes pour {price} pièces ?",
        [("Oui", "yes"), ("Non", "no")],
    )
    if choice == "yes" and state.gold >= price:
        state.gold -= price
        state.crew += available
        ui.success(f"{available} hommes signent. L'équipage est étoffé.")
    elif choice == "yes":
        ui.fail("Pas assez de fonds. Les matelots haussent les épaules.")


# -------------------------------------------------------------------
# NASSAU (1706-1718) — République des Pirates
# -------------------------------------------------------------------

def _nassau_flying_gang(state, ui):
    """Le « Flying Gang » : Hornigold, Jennings, Vane, Teach, Rackham…
    Conseil informel des capitaines de Nassau."""
    if state.current_date().year > 1718:
        return  # plus de Flying Gang après l'arrivée de Rogers
    ui.narrate(
        "Sur la plage, autour d'un feu, le Flying Gang tient conseil. "
        "Hornigold, Jennings et un certain Edward Teach discutent d'une "
        "expédition contre les sloops français de la Martinique."
    )
    choice = ui.choose(
        "Vous joindre à eux ?",
        [
            ("Oui — partir en consort pour une grosse prise", "join"),
            ("Non — chacun pour soi", "decline"),
        ],
    )
    if choice == "join":
        state.advance_turn()
        booty = random.randint(200, 500)
        cargo = random.randint(150, 350)
        crew_lost = random.randint(2, 6)
        state.gold += booty
        state.loot += cargo
        state.crew = max(0, state.crew - crew_lost)
        state.reputation += 2
        ui.success(
            f"L'expédition tourne bien. Part de butin : {booty} pièces, "
            f"{cargo} de cargaison. {crew_lost} hommes perdus dans la mêlée."
        )
    else:
        ui.info("Vous gardez votre indépendance. Hornigold hoche la tête, dépité.")


def _nassau_woodes_rogers(state, ui):
    """Juillet 1718 : Woodes Rogers arrive à Nassau avec 4 frégates et le
    pardon royal de George Ier en main."""
    if state.current_date().year < 1718:
        return
    ui.narrate(
        "À l'aube du 22 juillet 1718, quatre vaisseaux de Sa Majesté "
        "Britannique entrent dans la passe de Nassau. À leur tête : Woodes "
        "Rogers, nouveau gouverneur des Bahamas, le pardon royal en poche."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Accepter le pardon royal (Act of Grace)", "pardon"),
            ("Lever l'ancre immédiatement pour fuir", "flee"),
            ("Saborder un brûlot et tenter une sortie héroïque", "fight"),
        ],
    )
    if choice == "pardon":
        state.flags["pardoned"] = True
        state.game_over = True
        state.victory = True
        ui.success(
            "Vous prêtez serment. Vous gardez la vie, l'or, et la peau intacte. "
            "Plus tard, Hornigold deviendra chasseur de pirates pour Rogers."
        )
    elif choice == "flee":
        if state.ship["speed"] >= 7:
            ui.success("Votre navire est rapide. Vous gagnez le large avant l'engagement.")
            state.reputation += 1
        else:
            damage = random.randint(20, 40)
            crew_lost = random.randint(5, 15)
            state.ship["hull_current"] = max(0, state.ship["hull_current"] - damage)
            state.crew = max(0, state.crew - crew_lost)
            ui.fail(f"Les canons des frégates trouvent leur cible. Coque -{damage}, {crew_lost} morts.")
    else:  # fight
        ui.fail(
            "Le brûlot s'enflamme trop tôt. Sortie ratée. Vous perdez beaucoup, "
            "mais votre légende s'écrit."
        )
        damage = random.randint(30, 50)
        crew_lost = random.randint(10, 20)
        state.ship["hull_current"] = max(0, state.ship["hull_current"] - damage)
        state.crew = max(0, state.crew - crew_lost)
        state.reputation += 3


def _nassau_articles_election(state, ui):
    """Pratique attestée : élection démocratique du quartier-maître."""
    ui.narrate(
        "Sur la plage, l'équipage tient une assemblée. On propose de revoir "
        "les Articles : nouvelle clef de partage, nouveau quartier-maître. "
        "C'est la règle de la côte."
    )
    choice = ui.choose(
        "Quelle position défendez-vous ?",
        [
            ("Articles plus égalitaires (parts équivalentes)", "equal"),
            ("Maintenir l'ordre — part double au capitaine", "captain"),
        ],
    )
    if choice == "equal":
        state.morale = min(100, state.morale + 12)
        ui.success("L'équipage approuve à l'unanimité. Moral en flèche.")
    else:
        if state.captain["bonus"].get("leadership", 0) >= 2:
            ui.info("Votre autorité l'emporte. L'équipage grogne mais cède.")
            state.morale = max(0, state.morale - 3)
        else:
            state.morale = max(0, state.morale - 12)
            ui.fail("Mauvais calcul. Trois hommes désertent pour un autre navire.")
            state.crew = max(0, state.crew - 3)


# -------------------------------------------------------------------
# ÎLE SAINTE-MARIE (1690-1720) — Madagascar, comptoir Baldridge
# -------------------------------------------------------------------

def _saintemarie_baldridge(state, ui):
    """Adam Baldridge tenait un comptoir financé depuis New York par
    Frederick Philipse. Il vendait vivres et armes aux pirates."""
    if state.current_date().year > 1697:
        return  # Baldridge est chassé en 1697
    ui.narrate(
        "Adam Baldridge vous reçoit dans son comptoir, perché sur la baie. "
        "Vivres frais, poudre, rhum — mais à des prix new-yorkais."
    )
    cost = 80
    choice = ui.choose(
        f"Acheter un assortiment complet pour {cost} pièces (+30 vivres, +5 moral) ?",
        [("Oui", "yes"), ("Non", "no")],
    )
    if choice == "yes" and state.gold >= cost:
        state.gold -= cost
        state.supplies = min(100, state.supplies + 30)
        state.morale = min(100, state.morale + 5)
        ui.success("Baldridge se frotte les mains. Vos cales se remplissent.")
    elif choice == "yes":
        ui.fail("Vous n'avez pas la somme. Baldridge éclate de rire.")


def _saintemarie_pirate_round(state, ui):
    """La « Pirate Round » : route Atlantique → mer Rouge contre les
    navires moghols. Henry Avery l'inaugure en 1695."""
    ui.narrate(
        "Un capitaine américain, déserteur d'un convoi de la East India "
        "Company, vous propose de partir en consort vers le détroit de Bab "
        "el-Mandeb : les pèlerins de La Mecque transportent des fortunes."
    )
    choice = ui.choose(
        "Vous lancez-vous dans la Pirate Round ?",
        [
            ("Oui — l'aventure et l'or des Moghols", "yes"),
            ("Non — trop loin de mes bases", "no"),
        ],
    )
    if choice == "yes":
        for _ in range(3):
            state.advance_turn()
        state.supplies = max(0, state.supplies - 40)
        roll = random.random()
        if roll < 0.4:
            gain = random.randint(800, 1600)
            cargo = random.randint(500, 1000)
            state.gold += gain
            state.loot += cargo
            state.reputation += 3
            ui.success(
                f"Vous prenez une prise moghole de premier rang : {gain} pièces "
                f"d'or, {cargo} de soie et d'épices."
            )
        elif roll < 0.75:
            crew_lost = random.randint(5, 12)
            state.crew = max(0, state.crew - crew_lost)
            ui.info(
                f"La traversée est dure. {crew_lost} hommes meurent de fièvre "
                "ou d'accidents, sans prise notable."
            )
        else:
            crew_lost = random.randint(15, 25)
            damage = random.randint(20, 40)
            state.crew = max(0, state.crew - crew_lost)
            state.ship["hull_current"] = max(0, state.ship["hull_current"] - damage)
            ui.fail(
                "Une escorte armée de l'Empire moghol fond sur vous. "
                f"Pertes lourdes : {crew_lost} hommes, coque -{damage}."
            )


# -------------------------------------------------------------------
# LA HAVANE (espagnol, hostile)
# -------------------------------------------------------------------

def _havane_garrison_alert(state, ui):
    ui.narrate(
        "Les sentinelles du Morro vous repèrent à la lunette. Une chaloupe "
        "armée se détache du quai. L'asiento espagnol ne plaisante pas."
    )
    choice = ui.choose(
        "Action immédiate :",
        [
            ("Lever l'ancre dans l'instant", "flee"),
            ("Brandir des papiers hollandais (bluff)", "bluff"),
        ],
    )
    if choice == "flee":
        ui.success("Vous gagnez le large à temps. Aucune perte.")
    else:
        if random.random() < 0.4:
            ui.success("Le bluff passe. L'officier salue et repart.")
        else:
            damage = random.randint(15, 30)
            crew_lost = random.randint(3, 8)
            state.ship["hull_current"] = max(0, state.ship["hull_current"] - damage)
            state.crew = max(0, state.crew - crew_lost)
            ui.fail(f"L'officier flaire la supercherie. Vous fuyez sous le feu : -{damage} coque, {crew_lost} morts.")


def _havane_corrupt_official(state, ui):
    if state.loot <= 0:
        return
    ui.narrate(
        "Un fonctionnaire de l'asiento vous fait passer un mot : il rachète "
        "discrètement votre cargaison à 90% de sa valeur, sans poser de questions."
    )
    sale = int(state.loot * 0.9)
    choice = ui.choose(
        f"Vendre les {state.loot} unités de butin pour {sale} pièces ?",
        [("Oui", "yes"), ("Non", "no")],
    )
    if choice == "yes":
        state.gold += sale
        state.loot = 0
        ui.success(f"+{sale} pièces de huit. Personne n'a rien vu.")


# -------------------------------------------------------------------
# CHARLESTON (Caroline, anglais — permissif puis hostile)
# -------------------------------------------------------------------

def _charleston_blackbeard_siege(state, ui):
    """En mai 1718, Barbe-Noire a bloqué Charleston pendant une semaine
    et exigé une rançon en médicaments."""
    if state.current_date().year != 1718:
        return
    ui.narrate(
        "Le port est en effervescence. Edward Teach, dit Barbe-Noire, bloque "
        "la rade depuis cinq jours. Il exige un coffre de médicaments contre "
        "la libération des notables capturés."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Proposer vos services aux autorités contre Teach", "hunt"),
            ("Profiter du chaos pour faire vos affaires discrètement", "trade"),
        ],
    )
    if choice == "hunt":
        state.flags["pirate_hunter"] = True
        state.reputation = max(0, state.reputation - 1)
        ui.info(
            "Les autorités vous fournissent vivres et poudre. Vous voilà "
            "désigné comme « renégat retourné »."
        )
        state.supplies = min(100, state.supplies + 20)
    else:
        gain = random.randint(50, 150)
        state.gold += gain
        ui.success(f"Dans la confusion, vous écoulez quelques marchandises. +{gain} pièces.")


def _charleston_convoy_intel(state, ui):
    ui.narrate(
        "Un commis du port, soûl, laisse échapper : un convoi de cinq "
        "marchands part dans dix jours pour Bristol, chargé de riz et d'indigo."
    )
    state.flags["heard_convoy"] = True
    ui.info("(Renseignement noté — augmente vos chances à la prochaine patrouille.)")


# -------------------------------------------------------------------
# PETIT-GOÂVE (Saint-Domingue, français)
# -------------------------------------------------------------------

def _petitgoave_ducasse(state, ui):
    """Jean-Baptiste du Casse, gouverneur de Saint-Domingue 1691-1700,
    organisa les expéditions de flibustiers contre la Jamaïque (1694) et
    Carthagène (1697)."""
    ui.narrate(
        "Jean du Casse vous reçoit à Petit-Goâve. Le gouverneur monte une "
        "expédition royale : il veut des flibustiers expérimentés. "
        "Cible : Carthagène des Indes."
    )
    choice = ui.choose(
        "Vous joignez-vous à l'expédition ?",
        [
            ("Oui — la prise du siècle, sous commission française", "yes"),
            ("Non — pas envie de partager avec Pointis et la marine du Roi", "no"),
        ],
    )
    if choice == "yes":
        for _ in range(2):
            state.advance_turn()
        booty = random.randint(400, 900)
        cargo = random.randint(300, 700)
        crew_lost = random.randint(8, 20)
        state.gold += booty
        state.loot += cargo
        state.crew = max(0, state.crew - crew_lost)
        state.reputation += 2
        ui.success(
            f"Le sac de Carthagène vous rapporte {booty} pièces et {cargo} de cargaison. "
            f"{crew_lost} hommes laissés sur le rempart."
        )
    else:
        ui.info("Du Casse hausse les épaules. D'autres répondront.")


def _petitgoave_engages(state, ui):
    """« Engagés » : système des trente-six mois, main-d'œuvre liée."""
    ui.narrate(
        "Sur le port, des engagés à peine débarqués cherchent à s'évader "
        "de leur contrat de trente-six mois. Cinq d'entre eux veulent "
        "signer vos Articles."
    )
    if state.crew + 5 <= state.ship["crew_max"]:
        state.crew += 5
        ui.success("Cinq engagés rejoignent vos rangs. Vous n'avez pas le temps de finir le rhum.")
    else:
        ui.info("Votre navire est plein. Vous leur donnez quelques pièces et l'adresse d'un autre capitaine.")
        state.gold = max(0, state.gold - 10)


# -------------------------------------------------------------------
# Recrutements de compagnons spécifiques aux ports
# -------------------------------------------------------------------

def _nassau_israel_hands(state, ui):
    if state.has_companion("israel_hands"):
        return
    from data.companions import get_companion
    h = get_companion("israel_hands")
    ui.show_scene("companions", "israel_hands")
    ui.narrate(h["recruitment"]["intro"])
    choice = ui.choose(
        f"Engager {h['name']} comme maître canonnier ?",
        [
            ("Oui — un servant des pièces aguerri", "yes"),
            ("Non — il pue le bois de potence", "no"),
        ],
    )
    if choice == "yes":
        state.add_companion(h)
        ui.success(f"{h['name']} embarque. {h['bonus_label']}")


def _portroyal_kennedy(state, ui):
    if state.has_companion("walter_kennedy"):
        return
    from data.companions import get_companion
    k = get_companion("walter_kennedy")
    ui.show_scene("companions", "walter_kennedy")
    ui.narrate(k["recruitment"]["intro"])
    choice = ui.choose(
        "Le nommer quartier-maître ?",
        [
            ("Oui — l'équipage votera, mais il convaincra", "yes"),
            ("Non — sa loyauté est un pari", "no"),
        ],
    )
    if choice == "yes":
        state.add_companion(k)
        ui.success(f"{k['name']} prend ses fonctions. {k['bonus_label']}")


def _petitgoave_boudin(state, ui):
    if state.has_companion("jean_boudin"):
        return
    from data.companions import get_companion
    b = get_companion("jean_boudin")
    ui.show_scene("companions", "jean_boudin")
    ui.narrate(b["recruitment"]["intro"])
    choice = ui.choose(
        f"Embaucher {b['name']} comme cuisinier de bord ?",
        [
            ("Oui — le ventre des hommes vous remerciera", "yes"),
            ("Non — un cuisinier de plus n'est pas une mêlée", "no"),
        ],
    )
    if choice == "yes":
        state.add_companion(b)
        ui.success(f"{b['name']} s'installe à la cambuse. {b['bonus_label']}")


def _tortuga_vieux_tom(state, ui):
    if state.has_companion("vieux_tom_buccaneer"):
        return
    from data.companions import get_companion
    t = get_companion("vieux_tom_buccaneer")
    ui.show_scene("companions", "vieux_tom_buccaneer")
    ui.narrate(t["recruitment"]["intro"])
    choice = ui.choose(
        "L'enrôler ?",
        [
            ("Oui — un tireur des bois est précieux", "yes"),
            ("Non — il est trop vieux", "no"),
        ],
    )
    if choice == "yes":
        state.add_companion(t)
        ui.success(f"{t['name']} signe les Articles. {t['bonus_label']}")


# -------------------------------------------------------------------
# Catalogue par port
# -------------------------------------------------------------------

PORT_EVENTS = {
    "tortuga": [
        {
            "id": "tortuga_ogeron",
            "title": "Audience chez d'Ogeron",
            "weight": 4,
            "conditions": lambda s: 1665 <= s.current_date().year <= 1675,
            "resolve": _tortuga_audience_ogeron,
            "image": "assets/images/evt_ogeron.png",
        },
        {
            "id": "tortuga_brawl",
            "title": "Querelle à la Cayonne",
            "weight": 5,
            "conditions": lambda s: True,
            "resolve": _tortuga_tavern_brawl,
            "image": "assets/images/evt_brawl.png",
        },
        {
            "id": "tortuga_boucaniers",
            "title": "Boucaniers descendus des hauteurs",
            "weight": 5,
            "conditions": lambda s: True,
            "resolve": _tortuga_boucaniers,
            "image": "assets/images/evt_boucaniers.png",
        },
        {
            "id": "tortuga_vieux_tom",
            "title": "Un vieux boucanier au comptoir",
            "weight": 3,
            "conditions": lambda s: not s.has_companion("vieux_tom_buccaneer"),
            "resolve": _tortuga_vieux_tom,
        },
    ],
    "port_royal": [
        {
            "id": "portroyal_modyford",
            "title": "Réception chez Modyford",
            "weight": 4,
            "conditions": lambda s: 1664 <= s.current_date().year <= 1671,
            "resolve": _portroyal_modyford,
            "image": "assets/images/evt_modyford.png",
        },
        {
            "id": "portroyal_quake",
            "title": "Secousses suspectes",
            "weight": 3,
            "conditions": lambda s: s.current_date().year >= 1692 and not s.flags.get("earthquake_warning"),
            "resolve": _portroyal_earthquake_warning,
            "image": "assets/images/evt_quake.png",
        },
        {
            "id": "portroyal_recruit",
            "title": "Marins disponibles",
            "weight": 5,
            "conditions": lambda s: True,
            "resolve": _portroyal_recruit_rush,
            "image": "assets/images/evt_recruit.png",
        },
        {
            "id": "portroyal_kennedy",
            "title": "Un Londonien cherche un capitaine",
            "weight": 3,
            "conditions": lambda s: not s.has_companion("walter_kennedy"),
            "resolve": _portroyal_kennedy,
        },
    ],
    "nassau": [
        {
            "id": "nassau_flying_gang",
            "title": "Conseil du Flying Gang",
            "weight": 5,
            "conditions": lambda s: s.current_date().year <= 1718,
            "resolve": _nassau_flying_gang,
            "image": "assets/images/evt_flying_gang.png",
        },
        {
            "id": "nassau_rogers",
            "title": "Arrivée de Woodes Rogers",
            "weight": 4,
            "conditions": lambda s: s.current_date().year >= 1718 and not s.flags.get("pardoned"),
            "resolve": _nassau_woodes_rogers,
            "image": "assets/images/evt_rogers.png",
        },
        {
            "id": "nassau_articles",
            "title": "Vote des Articles",
            "weight": 3,
            "conditions": lambda s: True,
            "resolve": _nassau_articles_election,
            "image": "assets/images/evt_articles.png",
        },
        {
            "id": "nassau_israel_hands",
            "title": "Israel Hands cherche un canon",
            "weight": 3,
            "conditions": lambda s: (s.current_date().year >= 1718
                                     and not s.has_companion("israel_hands")),
            "resolve": _nassau_israel_hands,
        },
    ],
    "ile_sainte_marie": [
        {
            "id": "saintemarie_baldridge",
            "title": "Comptoir d'Adam Baldridge",
            "weight": 5,
            "conditions": lambda s: s.current_date().year <= 1697,
            "resolve": _saintemarie_baldridge,
            "image": "assets/images/evt_baldridge.png",
        },
        {
            "id": "saintemarie_round",
            "title": "Proposition de Pirate Round",
            "weight": 4,
            "conditions": lambda s: s.crew >= 40,
            "resolve": _saintemarie_pirate_round,
            "image": "assets/images/evt_round.png",
        },
    ],
    "la_havane": [
        {
            "id": "havane_alert",
            "title": "Garnison en alerte",
            "weight": 6,
            "conditions": lambda s: True,
            "resolve": _havane_garrison_alert,
            "image": "assets/images/evt_havane.png",
        },
        {
            "id": "havane_corrupt",
            "title": "Fonctionnaire vénal",
            "weight": 3,
            "conditions": lambda s: s.loot > 0,
            "resolve": _havane_corrupt_official,
            "image": "assets/images/evt_corrupt.png",
        },
    ],
    "charleston": [
        {
            "id": "charleston_siege",
            "title": "Blocus de Barbe-Noire",
            "weight": 4,
            "conditions": lambda s: s.current_date().year == 1718,
            "resolve": _charleston_blackbeard_siege,
            "image": "assets/images/evt_siege.png",
        },
        {
            "id": "charleston_convoy",
            "title": "Rumeur de convoi",
            "weight": 5,
            "conditions": lambda s: True,
            "resolve": _charleston_convoy_intel,
            "image": "assets/images/evt_convoy.png",
        },
    ],
    "saint_domingue": [
        {
            "id": "petitgoave_ducasse",
            "title": "Expédition de du Casse",
            "weight": 4,
            "conditions": lambda s: 1691 <= s.current_date().year <= 1700,
            "resolve": _petitgoave_ducasse,
            "image": "assets/images/evt_ducasse.png",
        },
        {
            "id": "petitgoave_engages",
            "title": "Engagés en fuite",
            "weight": 5,
            "conditions": lambda s: True,
            "resolve": _petitgoave_engages,
            "image": "assets/images/evt_engages.png",
        },
        {
            "id": "petitgoave_boudin",
            "title": "Cuisinier sur le carreau",
            "weight": 3,
            "conditions": lambda s: not s.has_companion("jean_boudin"),
            "resolve": _petitgoave_boudin,
        },
    ],
}


def pick_port_event(state, port_id):
    """Tire un événement applicable pour ce port, ou None."""
    candidates = [
        e for e in PORT_EVENTS.get(port_id, [])
        if e["conditions"](state)
    ]
    if not candidates:
        return None
    weights = [e["weight"] for e in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]


def maybe_trigger_port_event(state, ui, port_id):
    """À appeler au moment où le joueur jette l'ancre dans un port.

    L'illustration suit la convention de chemins :
        assets/images/ports/<port_id>/event_<event_id>.png
    avec repli automatique sur la scène principale du port si l'image
    n'existe pas (cf. core/ui.TextUI._resolve_scene).
    """
    if random.random() > PORT_EVENT_CHANCE:
        return
    event = pick_port_event(state, port_id)
    if event is None:
        return
    ui.event_banner(event["title"])
    ui.show_scene("port_events", port_id, event["id"])
    event["resolve"](state, ui)
