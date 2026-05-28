"""
Grandes traversées : Caraïbes ⇄ océan Indien (Sainte-Marie).

Module dédié au franchissement de l'océan, qui prend historiquement
4 à 6 mois pour la « Pirate Round » (c. 1690-1720) selon les sources
du repository (Avery, Tew, Kidd ; réseau Baldridge-Philipse).

Au lieu d'un simple changement de port en un tour, le déplacement
entre les Antilles et Sainte-Marie traverse 4-5 segments géographiques,
chacun générant 1-4 événements aléatoires :

    Atlantique sud  →  [Côte de Guinée]  →  Cap de Bonne-Espérance
                    →  Canal du Mozambique  →  Approche

Le segment de Guinée est optionnel (choix initial du joueur).
La direction (outbound = vers Sainte-Marie / return = vers les Antilles)
filtre certains événements (Baldridge, frégate de la Navy, retour à
Nassau, etc.).

**CONCEPTION DES ÉVÉNEMENTS** : chaque événement présente AU MOINS deux
choix au joueur. Aucun événement n'applique d'effet destructif sans
laisser au capitaine une marge de manœuvre — il peut toujours payer en
or, en temps, en moral ou en vivres pour atténuer les dégâts. Une
tempête peut être affrontée, fuyée ou contournée ; un convoi ennemi
peut être attaqué, évité ou suivi ; une épidémie peut être confinée,
soignée ou ignorée. C'est au joueur d'arbitrer selon l'état de son
navire.

Intégration :
    - data/actions.py:_action_visit_port  appelle trigger_long_voyage()
      quand la destination franchit l'océan.
    - state.flags["last_region"] mémorise la dernière région visitée
      ("caribbean" ou "overseas"). Défaut : "caribbean".

Pour AJOUTER un événement de traversée :
    1. Écrire `_resolve_voy_xxx(state, ui)` avec un `ui.choose(...)`.
    2. L'ajouter dans VOYAGE_EVENTS[<segment_id>].
"""

import random


# =================================================================
# Géographie : appartenance régionale des ports
# =================================================================

CARIBBEAN_PORT_IDS = {
    "tortuga", "port_royal", "nassau",
    "la_havane", "charleston", "saint_domingue",
}

OVERSEAS_PORT_IDS = {
    "ile_sainte_marie",
}


def region_of_port(port_id: str):
    """Renvoie 'caribbean', 'overseas' ou None."""
    if port_id in CARIBBEAN_PORT_IDS:
        return "caribbean"
    if port_id in OVERSEAS_PORT_IDS:
        return "overseas"
    return None


# =================================================================
# Segments de la traversée
# =================================================================

SEGMENTS = [
    {"id": "atlantic",   "name": "Atlantique sud",         "sub": "Alizés et Pot-au-noir",         "events_count": (2, 4)},
    {"id": "guinea",     "name": "Côte de Guinée",         "sub": "Côte des Esclaves et comptoirs", "events_count": (1, 3), "optional": True},
    {"id": "cape",       "name": "Cap de Bonne-Espérance", "sub": "« Cap des Tempêtes »",           "events_count": (2, 3)},
    {"id": "mozambique", "name": "Canal du Mozambique",    "sub": "Comores et côte swahili",        "events_count": (1, 3)},
    {"id": "approach",   "name": "Approche du mouillage",  "sub": "Côte malgache ou Antilles",      "events_count": (1, 2)},
]


# =================================================================
# Helpers internes
# =================================================================

def _spend(state, *, turns: int, supplies_factor: float = 1.0):
    """Avance N tours et consomme les vivres correspondants.

    Le coût en vivres par tour suit la règle de data/actions.py
    (≈ crew // 20 unités par tour). `supplies_factor` ajuste à la
    hausse pour les segments éprouvants (tempête, fièvre) ou à la
    baisse pour les escales (cuisinier qui fait du frais).
    """
    base = max(1, state.crew // 20)
    per_turn = max(1, int(round(base * supplies_factor)))
    saved = state.get_modifier("supply_savings", 0.0)
    per_turn = max(1, int(round(per_turn * (1.0 - saved))))
    for _ in range(turns):
        state.advance_turn()
        state.supplies = max(0, state.supplies - per_turn)


def _yield_prisoners(state, ui, pool, n, source):
    """Ajoute n prisonniers tirés du pool donné."""
    from data.prisoners import make_prisoner, PRISONER_TYPES
    taken = []
    for _ in range(n):
        ptype = random.choice(pool)
        state.prisoners.append(make_prisoner(ptype, source=source))
        taken.append(ptype)
    labels = ", ".join(f"1 {PRISONER_TYPES[t]['label']}" for t in taken)
    ui.info(f"Prisonniers retenus à bord : {labels}.")


def _apply_damage(state, *, hull=0, crew=0, morale=0, supplies=0, gold=0, loot=0):
    """Applique un lot d'effets, clamp implicite."""
    if hull:
        state.ship["hull_current"] = max(0, state.ship["hull_current"] - hull)
    if crew:
        state.crew = max(0, state.crew - crew)
    if morale:
        state.morale = max(0, min(100, state.morale - morale)) if morale > 0 else min(100, state.morale - morale)
    if supplies:
        state.supplies = max(0, min(100, state.supplies - supplies)) if supplies > 0 else min(100, state.supplies - supplies)
    if gold:
        state.gold = max(0, state.gold - gold) if gold > 0 else state.gold - gold
    if loot:
        state.loot = max(0, state.loot - loot) if loot > 0 else state.loot - loot


# =================================================================
# ÉVÉNEMENTS — ATLANTIQUE SUD
# =================================================================

def _resolve_voy_doldrums(state, ui):
    ui.show_scene("events", "voy_doldrums")
    ui.narrate(
        "Le vent tombe d'un coup. Les voiles pendent comme du linge mouillé. "
        "Pris dans les calmes équatoriaux, l'équipage compte les barriques "
        "d'eau qui s'allègent."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Attendre que le vent revienne (3-5 jours, vivres et moral)", "wait"),
            ("Remorquer le navire à la chaloupe (1-2 jours, équipage épuisé)", "tow"),
            ("Alléger en jetant du lest par-dessus bord (perte de cale)", "jettison"),
        ],
    )
    if choice == "wait":
        _spend(state, turns=random.randint(3, 5), supplies_factor=1.4)
        state.morale = max(0, state.morale - 10)
        ui.info("Vivres entamés. Moral -10.")
    elif choice == "tow":
        _spend(state, turns=random.randint(1, 2), supplies_factor=1.5)
        state.crew = max(0, state.crew - max(1, state.crew // 30))
        state.morale = max(0, state.morale - 4)
        ui.info("Vous gagnez du temps mais les rameurs sont à bout.")
    else:
        lost = min(state.loot, 80) if state.loot > 0 else min(state.gold, 60)
        if state.loot > 0:
            state.loot -= lost
            ui.info(f"Vous jetez {lost} unités de butin à la mer. Le navire allège.")
        else:
            state.gold = max(0, state.gold - lost)
            ui.info(f"Vous sacrifiez du matériel pour {lost} P8 de valeur.")
        _spend(state, turns=2)


def _resolve_voy_atlantic_storm(state, ui):
    ui.show_scene("events", "voy_atlantic_storm")
    ui.narrate(
        "Le ciel noircit en moins d'une heure. Un grain tropical s'abat. "
        "Le grand hunier menace de céder."
    )
    choice = ui.choose(
        "Comment l'affrontez-vous ?",
        [
            ("Fuir vent arrière (rapide, peu de dégâts mais hors route)", "run"),
            ("Mettre à la cape sous tourmentine (gros dégâts mais maintien du cap)", "heave_to"),
            ("Ferler tout et prier (équipage épuisé, dégâts moyens)", "bare_poles"),
        ],
    )
    if choice == "run":
        _apply_damage(state, hull=5, morale=4)
        _spend(state, turns=random.randint(2, 3), supplies_factor=1.1)
        ui.info("Coque -5, moral -4, mais vous restez dans la course.")
    elif choice == "heave_to":
        _apply_damage(state, hull=18, crew=2, morale=8)
        _spend(state, turns=1)
        ui.info("Coque -18, 2 hommes à la mer, moral -8.")
    else:
        _apply_damage(state, hull=10, crew=1, morale=5)
        _spend(state, turns=2, supplies_factor=1.2)
        ui.info("Coque -10, 1 homme perdu, moral -5.")


def _resolve_voy_slaver(state, ui):
    ui.show_scene("events", "voy_slaver")
    ui.narrate(
        "Une voile à l'horizon. Trois ponts, grilles sur le faux-pont, "
        "l'odeur perceptible à trois encablures. Un négrier."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Arraisonner", "attack"),
            ("Pister et frapper de nuit (combat plus facile, temps perdu)", "stalk"),
            ("Laisser passer", "ignore"),
        ],
    )
    if choice == "ignore":
        _spend(state, turns=1)
        return
    combat = state.get_effective_bonus("combat") * 4
    bonus_stalk = 25 if choice == "stalk" else 0
    if choice == "stalk":
        _spend(state, turns=1)
    strength = state.crew + combat + random.randint(0, 20) + bonus_stalk

    if strength < 35:
        _apply_damage(state, crew=random.randint(3, 7), hull=8)
        ui.fail("L'équipage du négrier résiste mieux qu'attendu.")
        _spend(state, turns=2)
        return

    gold = random.randint(150, 350)
    state.gold += gold
    _apply_damage(state, crew=random.randint(1, 4))
    state.morale = min(100, state.morale + 3)
    state.reputation += 1
    ui.success(f"Prise faite. +{gold} P8.")
    _spend(state, turns=2)

    from data.prisoners import make_prisoner
    captives = random.randint(15, 45)
    sub = ui.choose(
        f"Que faites-vous des {captives} captifs africains ?",
        [
            ("Briser les fers — proposer les Articles", "liberate"),
            ("Garder en cale pour vente", "hold"),
            ("Déposer à la côte la plus proche", "release"),
        ],
    )
    if sub == "liberate":
        joiners = min(state.ship["crew_max"] - state.crew,
                      int(captives * random.uniform(0.45, 0.65)))
        state.crew += joiners
        state.morale = min(100, state.morale + 12)
        state.reputation += 1
        state.flags["liberated_slaves"] = state.flags.get("liberated_slaves", 0) + captives
        ui.success(f"{joiners} signent les Articles.")
    elif sub == "hold":
        for _ in range(captives):
            state.prisoners.append(make_prisoner("enslaved_african", source="négrier capturé en mer"))
        state.morale = max(0, state.morale - 5)
        ui.info(f"{captives} captifs dans l'entrepont.")
    else:
        state.morale = min(100, state.morale + 6)
        state.flags["liberated_slaves"] = state.flags.get("liberated_slaves", 0) + captives
        _spend(state, turns=1)
        ui.success("Cap sur la côte la plus proche.")


def _resolve_voy_spanish_galleon(state, ui):
    ui.show_scene("events", "voy_spanish_galleon")
    ui.narrate(
        "Une masse imposante émerge de la brume : un galion espagnol "
        "séparé de sa flotte. Sa cale regorge d'argent du Potosí — "
        "ses canons grondent."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Abordage frontal (lourd risque)", "attack"),
            ("Le canonner à distance puis aborder (long, coque exposée)", "broadside"),
            ("Laisser passer", "ignore"),
        ],
    )
    if choice == "ignore":
        _spend(state, turns=1)
        return

    combat = state.get_effective_bonus("combat") * 5
    if choice == "broadside":
        _apply_damage(state, hull=12)
        bonus = 30
        _spend(state, turns=1)
    else:
        bonus = 0

    strength = state.crew + combat + random.randint(-10, 20) + bonus

    if strength < 80:
        _apply_damage(state, hull=20 if choice == "broadside" else 30,
                      crew=random.randint(8, 18), morale=12)
        ui.fail("L'abordage tourne mal. Le galion s'éloigne en boitant.")
        _spend(state, turns=2)
        return

    gold = random.randint(600, 1200)
    cargo = random.randint(300, 600)
    state.gold += gold
    state.loot += cargo
    _apply_damage(state, crew=random.randint(5, 12), morale=-15)
    state.reputation += 3
    ui.success(f"Le galion se rend. +{gold} P8, +{cargo} de cargaison.")
    _yield_prisoners(state, ui,
                     ["noble_passenger", "noble_lady", "navy_officer", "clergy"],
                     n=random.randint(2, 4), source="galion espagnol")
    _spend(state, turns=3)


def _resolve_voy_scurvy(state, ui):
    if state.has_trait("scurvy_resist"):
        ui.narrate("Mahalia distribue ses tisanes d'écorces de quinquina. Pas un mort.")
        _spend(state, turns=1)
        return
    ui.show_scene("events", "voy_scurvy")
    ui.narrate(
        "Les gencives saignent, les dents bougent, les jambes enflent. "
        "Le scorbut s'installe."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Distribuer les derniers agrumes de réserve (-15 vivres)", "citrus"),
            ("Rationner sévèrement (-15 moral, sauve l'équipage)", "ration"),
            ("Pousser jusqu'à l'escale (lourdes pertes)", "push"),
        ],
    )
    save = state.get_modifier("crew_save_chance", 0.0)
    if choice == "citrus":
        if state.supplies < 15:
            ui.fail("Plus de vivres frais. Les mesures sont symboliques.")
            _apply_damage(state, crew=max(1, state.crew // 14), morale=8)
        else:
            state.supplies -= 15
            losses = max(1, state.crew // 25)
            if save > 0 and random.random() < save:
                losses = 0
                ui.info("Le chirurgien renforce l'efficacité du traitement.")
            _apply_damage(state, crew=losses, morale=2)
            ui.success(f"Le mal recule. {losses} morts seulement.")
        _spend(state, turns=2)
    elif choice == "ration":
        _apply_damage(state, crew=max(1, state.crew // 20), morale=15)
        ui.info("Les hommes maigrissent mais survivent.")
        _spend(state, turns=2, supplies_factor=0.5)
    else:
        losses = max(2, state.crew // 10)
        if save > 0 and random.random() < save:
            losses = losses // 2
        _apply_damage(state, crew=losses, morale=12)
        ui.fail(f"{losses} hommes succombent.")
        _spend(state, turns=2)


def _resolve_voy_azores(state, ui):
    ui.show_scene("events", "voy_azores")
    ui.narrate(
        "Vous touchez Terceira. Les autorités portugaises soupçonnent "
        "— mais l'or graisse les rouages."
    )
    options = [
        ("Acheter eau et vivres ouvertement (80 P8, +30 vivres)", "open"),
        ("Aiguade nocturne discrète (10 P8, +15 vivres, +5 moral)", "stealth"),
        ("Repartir aussitôt sans rien acheter", "leave"),
    ]
    choice = ui.choose("Que faites-vous ?", options)
    if choice == "open" and state.gold >= 80:
        state.gold -= 80
        state.supplies = min(100, state.supplies + 30)
        state.morale = min(100, state.morale + 5)
        ui.success("-80 P8, vivres +30, moral +5.")
    elif choice == "open":
        ui.fail("Pas les 80 P8.")
    elif choice == "stealth":
        if state.gold < 10:
            ui.fail("Même cette somme manque. Aiguade ratée.")
        else:
            state.gold -= 10
            state.supplies = min(100, state.supplies + 15)
            state.morale = min(100, state.morale + 5)
            ui.success("Aiguade réussie. Vivres +15, moral +5.")
    _spend(state, turns=2, supplies_factor=0.3)


def _resolve_voy_cape_verde(state, ui):
    ui.show_scene("events", "voy_cape_verde")
    ui.narrate(
        "Les îles du Cap-Vert servent d'aiguade depuis deux siècles. "
        "Les Portugais ferment les yeux contre un peu d'argent."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Plein ravitaillement (60 P8, +25 vivres, +4 moral)", "full"),
            ("Eau seulement (10 P8, +10 vivres)", "water"),
            ("Aiguade clandestine sur une plage déserte (risque, gratuit)", "stealth"),
        ],
    )
    if choice == "full" and state.gold >= 60:
        state.gold -= 60
        state.supplies = min(100, state.supplies + 25)
        state.morale = min(100, state.morale + 4)
        ui.success("Plein fait.")
    elif choice == "water" and state.gold >= 10:
        state.gold -= 10
        state.supplies = min(100, state.supplies + 10)
        ui.success("Eau embarquée.")
    elif choice == "stealth":
        if random.random() < 0.7:
            state.supplies = min(100, state.supplies + 18)
            ui.success("Aiguade gratuite réussie. Vivres +18.")
        else:
            _apply_damage(state, crew=random.randint(1, 3))
            ui.fail("Une milice portugaise tire à la mousqueterie. Quelques morts.")
    else:
        ui.fail("Pas les fonds nécessaires.")
    _spend(state, turns=2, supplies_factor=0.3)


def _resolve_voy_desertion(state, ui):
    ui.show_scene("events", "voy_desertion")
    ui.narrate(
        "Au petit matin, la chaloupe a disparu. Trois hommes manquent à "
        "l'appel — ils ont préféré tenter leur chance à terre."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Lancer la poursuite avec la seconde chaloupe (1 jour, récupération possible)", "pursue"),
            ("Faire pendre un suspect pour l'exemple (-moral, ferme les rangs)", "example"),
            ("Laisser couler — bon débarras", "ignore"),
        ],
    )
    reduction = state.get_modifier("desertion_reduction", 0.0)
    base = max(1, int(round(3 * (1.0 - reduction))))
    if choice == "pursue":
        _spend(state, turns=1)
        if random.random() < 0.5:
            ui.success("Vous les rattrapez. Tous ramenés aux fers.")
            state.morale = max(0, state.morale - 3)
        else:
            _apply_damage(state, crew=base, morale=6)
            ui.fail(f"Trop tard. {base} hommes définitivement perdus.")
    elif choice == "example":
        _apply_damage(state, crew=base + 1, morale=12)
        state.flags["last_region"] = state.flags.get("last_region", "caribbean")
        ui.info(f"{base + 1} hommes en moins. Discipline rétablie, à un prix.")
    else:
        _apply_damage(state, crew=base, morale=4)
        ui.info(f"{base} déserteurs perdus.")
    _spend(state, turns=1 if choice != "pursue" else 0)


def _resolve_voy_calm_sailing(state, ui):
    ui.show_scene("events", "voy_calm_sailing")
    ui.narrate(
        "Les alizés tiennent. Le navire file ses huit nœuds. L'équipage "
        "a du temps libre."
    )
    choice = ui.choose(
        "Comment occupez-vous l'équipage ?",
        [
            ("Exercice aux pièces (combat affûté, moral neutre)", "drill"),
            ("Repos et grog (moral en hausse)", "rest"),
            ("Calfatage et révision du gréement (coque +5)", "maintenance"),
        ],
    )
    if choice == "drill":
        state.flags["voyage_combat_drilled"] = state.turn + 2
        ui.success("Servants des pièces aguerris pour les jours qui viennent.")
    elif choice == "rest":
        state.morale = min(100, state.morale + 8)
        ui.success("Moral +8.")
    else:
        state.ship["hull_current"] = min(state.ship["hull_max"],
                                         state.ship["hull_current"] + 5)
        ui.success("Coque +5.")
    _spend(state, turns=random.randint(2, 3))


# =================================================================
# ÉVÉNEMENTS — CÔTE DE GUINÉE
# =================================================================

def _resolve_voy_whydah_raid(state, ui):
    ui.show_scene("events", "voy_whydah_raid")
    ui.narrate(
        "Le comptoir négrier de Whydah est mal défendu cette saison. "
        "Une descente nocturne sur l'entrepôt rapporterait poudre d'or et ivoire."
    )
    choice = ui.choose(
        "Plan d'attaque ?",
        [
            ("Raid massif à l'aube (gros butin, lourdes pertes)", "raid"),
            ("Infiltration nocturne par un détachement (modéré, peu de pertes)", "stealth"),
            ("Passer son chemin", "leave"),
        ],
    )
    if choice == "raid":
        gold = random.randint(500, 900)
        _apply_damage(state, crew=random.randint(5, 10), hull=8)
        state.gold += gold
        state.supplies = min(100, state.supplies + 15)
        state.reputation += 2
        ui.success(f"+{gold} P8, +15 vivres. Bon prix payé en hommes.")
        _spend(state, turns=2)
    elif choice == "stealth":
        gold = random.randint(250, 450)
        _apply_damage(state, crew=random.randint(1, 3))
        state.gold += gold
        state.reputation += 1
        ui.success(f"+{gold} P8. Quelques blessés seulement.")
        _spend(state, turns=2)
    else:
        _spend(state, turns=1)


def _resolve_voy_african_king(state, ui):
    ui.show_scene("events", "voy_african_king")
    ui.narrate(
        "Un envoyé du royaume d'Allada propose un marché : poudre et "
        "mousquets contre vivres frais et renseignements."
    )
    choice = ui.choose(
        "Que troquez-vous ?",
        [
            ("Marché plein (200 P8, +35 vivres, +tuyau)", "full"),
            ("Échange modeste (50 P8, +15 vivres)", "small"),
            ("Refuser poliment", "refuse"),
        ],
    )
    if choice == "full" and state.gold >= 200:
        state.gold -= 200
        state.supplies = min(100, state.supplies + 35)
        state.morale = min(100, state.morale + 5)
        state.flags["allada_tip"] = True
        ui.success("Marché conclu. Tuyau sur un comptoir mal gardé.")
    elif choice == "small" and state.gold >= 50:
        state.gold -= 50
        state.supplies = min(100, state.supplies + 15)
        ui.success("Vivres embarqués.")
    elif choice in ("full", "small"):
        ui.fail("Pas les fonds nécessaires.")
    _spend(state, turns=3 if choice == "full" else 2)


def _resolve_voy_wic_warship(state, ui):
    ui.show_scene("events", "voy_wic_warship")
    ui.narrate(
        "Un bâtiment de la West-Indische Compagnie patrouille devant "
        "Elmina. Coque massive, batterie supérieure à la vôtre."
    )
    speed = state.ship["speed"] + state.get_effective_bonus("speed_bonus")
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Cap au large à toute voile", "outrun"),
            ("Se réfugier dans un estuaire à mangrove (temps, sûr)", "hide"),
            ("Hisser pavillon hollandais (bluff)", "bluff"),
        ],
    )
    if choice == "outrun":
        if speed + random.randint(1, 6) >= 10:
            ui.success("Vous le semez avant la nuit.")
        else:
            _apply_damage(state, hull=12, crew=random.randint(3, 6), morale=6)
            ui.fail("Le hollandais tire. Coque -12.")
        _spend(state, turns=2)
    elif choice == "hide":
        ui.success("Cachés dans la mangrove. Les moustiques mordent mais le hollandais passe.")
        _spend(state, turns=3)
        if random.random() < 0.3:
            _apply_damage(state, crew=1)
            ui.info("Un homme reste dans la fièvre des marais.")
    else:
        rep_factor = max(0.2, 0.5 - 0.05 * state.reputation)
        if random.random() < rep_factor:
            ui.success("Papiers exhibés. Ils passent leur route.")
        else:
            _apply_damage(state, hull=15, crew=random.randint(4, 8))
            ui.fail("Le bluff échoue. Bordée reçue.")
        _spend(state, turns=1)


def _resolve_voy_malaria(state, ui):
    ui.show_scene("events", "voy_malaria")
    ui.narrate(
        "Les miasmes des estuaires font leur œuvre. La fièvre tertiaire "
        "frappe sans distinction."
    )
    choice = ui.choose(
        "Comment réagissez-vous ?",
        [
            ("Confiner les malades en cale (sauve l'équipage, -moral)", "quarantine"),
            ("Acheter du quinquina à un comptoir (60 P8, -2 morts seulement)", "quinine"),
            ("Pousser sans rien faire (lourdes pertes)", "push"),
        ],
    )
    save = state.get_modifier("crew_save_chance", 0.0)
    if choice == "quarantine":
        losses = max(1, state.crew // 18)
        _apply_damage(state, crew=losses, morale=10)
        ui.info(f"{losses} morts. L'équipage sain est préservé.")
    elif choice == "quinine":
        if state.gold >= 60:
            state.gold -= 60
            losses = max(1, state.crew // 25)
            _apply_damage(state, crew=losses, morale=4)
            ui.success(f"Quinquina à temps. {losses} morts seulement.")
        else:
            ui.fail("Pas les 60 P8. La fièvre continue.")
            losses = max(2, state.crew // 12)
            if save > 0 and random.random() < save:
                losses = losses // 2
            _apply_damage(state, crew=losses, morale=10)
    else:
        losses = max(2, state.crew // 12)
        if save > 0 and random.random() < save:
            losses = losses // 2
            ui.info("Le chirurgien en sauve la moitié.")
        _apply_damage(state, crew=losses, morale=10)
    _spend(state, turns=2)


def _resolve_voy_african_recruits(state, ui):
    ui.show_scene("events", "voy_african_recruits")
    ui.narrate(
        "Des déserteurs du fort de Cape Coast et deux marins krou se "
        "présentent. Connaissance des côtes, langues locales."
    )
    available = state.ship["crew_max"] - state.crew
    if available <= 0:
        ui.info("Le navire est plein.")
        choice = ui.choose(
            "Que leur dites-vous ?",
            [
                ("Donner 20 P8 et l'adresse d'un autre capitaine", "pay"),
                ("Refuser sèchement", "refuse"),
            ],
        )
        if choice == "pay" and state.gold >= 20:
            state.gold -= 20
            state.morale = min(100, state.morale + 2)
        _spend(state, turns=1)
        return
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Tous les engager (4-6 hommes)", "all"),
            ("Choisir seulement les krou expérimentés (2 hommes, fiables)", "selective"),
            ("Refuser", "refuse"),
        ],
    )
    if choice == "all":
        n = min(available, random.randint(4, 6))
        state.crew += n
        state.morale = min(100, state.morale + 4)
        ui.success(f"{n} hommes signent les Articles.")
    elif choice == "selective":
        n = min(available, 2)
        state.crew += n
        state.morale = min(100, state.morale + 3)
        state.flags["voyage_combat_drilled"] = state.turn + 3
        ui.success(f"{n} marins krou rejoignent. Ils connaissent leur métier.")
    _spend(state, turns=1)


def _resolve_voy_rac_intercept(state, ui):
    ui.show_scene("events", "voy_rac_intercept")
    ui.narrate(
        "Le pavillon de la Royal African Company apparaît. La Compagnie "
        "défend son monopole."
    )
    speed = state.ship["speed"] + state.get_effective_bonus("speed_bonus")
    combat = state.get_effective_bonus("combat")
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Fuir vers le large", "flee"),
            ("Engager le combat", "fight"),
            ("Offrir un présent pour faire la paix (150 P8)", "bribe"),
        ],
    )
    if choice == "flee":
        if speed + random.randint(0, 4) >= 8:
            ui.success("Vous les semez.")
        else:
            _apply_damage(state, hull=15)
            ui.fail("Coque -15.")
    elif choice == "fight":
        if combat >= 2 or random.random() > 0.4:
            gain = random.randint(200, 400)
            state.gold += gain
            state.reputation += 2
            _apply_damage(state, crew=random.randint(4, 9))
            ui.success(f"Frégate prise. +{gain} P8.")
        else:
            _apply_damage(state, hull=25, crew=random.randint(8, 15))
            ui.fail("Coup dur.")
    else:
        if state.gold >= 150:
            state.gold -= 150
            ui.success("Le capitaine empoche et lève le canon.")
        else:
            ui.fail("Pas les 150 P8. Il faut combattre.")
            _apply_damage(state, hull=15, crew=random.randint(5, 10))
    _spend(state, turns=2)


def _resolve_voy_pirate_brother(state, ui):
    ui.show_scene("events", "voy_pirate_brother")
    ui.narrate(
        "Un autre pavillon noir au large. Un équipage flibustier déjà "
        "installé sur la côte. Le capitaine vous hèle."
    )
    choice = ui.choose(
        "Comment l'abordez-vous ?",
        [
            ("Échange de nouvelles autour du rhum", "share"),
            ("Lui proposer une consort (deux mois ensemble)", "consort"),
            ("Saluer brièvement et continuer", "wave"),
        ],
    )
    if choice == "share":
        state.morale = min(100, state.morale + 5)
        state.flags["surat_intel"] = True
        ui.success("Moral +5. Renseignement sur les flottes mogholes.")
    elif choice == "consort":
        for _ in range(2):
            state.advance_turn()
        roll = random.random()
        if roll < 0.5:
            gain = random.randint(250, 500)
            state.gold += gain
            state.reputation += 1
            ui.success(f"Consort prospère. +{gain} P8.")
        elif roll < 0.85:
            ui.info("Quelques petites prises seulement.")
            state.gold += 60
        else:
            _apply_damage(state, crew=random.randint(3, 8), morale=8)
            ui.fail("Il vous trahit en pleine prise.")
    _spend(state, turns=1)


def _resolve_voy_african_calm(state, ui):
    ui.show_scene("events", "voy_african_calm")
    ui.narrate(
        "Petite navigation côtière, comptoirs amicaux. Vous pouvez "
        "occuper l'équipage."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Faire le plein de bois et d'eau (+15 vivres)", "water"),
            ("Calfatage (coque +8)", "careen"),
            ("Repos (moral +6)", "rest"),
        ],
    )
    if choice == "water":
        state.supplies = min(100, state.supplies + 15)
    elif choice == "careen":
        state.ship["hull_current"] = min(state.ship["hull_max"],
                                         state.ship["hull_current"] + 8)
    else:
        state.morale = min(100, state.morale + 6)
    _spend(state, turns=2, supplies_factor=0.5)


# =================================================================
# ÉVÉNEMENTS — CAP DE BONNE-ESPÉRANCE
# =================================================================

def _resolve_voy_cape_storm(state, ui):
    ui.show_scene("events", "voy_cape_storm")
    ui.narrate(
        "Le « Cap des Tempêtes » mérite son nom. Vent à décorner les bœufs, "
        "mer démontée, le navire roule sous chaque lame. Le mât de misaine "
        "craque déjà."
    )
    choice = ui.choose(
        "Comment passez-vous le grain ?",
        [
            ("Cape sèche à mât bas (gros dégâts, position tenue)", "bare"),
            ("Plein sud dans les Quarantièmes (échappe à la tempête, autre danger)", "south"),
            ("Cap sur Saldanha (détour, plus sûr)", "saldanha"),
        ],
    )
    if choice == "bare":
        _apply_damage(state, hull=random.randint(15, 25), crew=random.randint(2, 5), morale=10)
        ui.info("Le navire tient, mais à peine.")
        _spend(state, turns=random.randint(2, 4), supplies_factor=1.2)
    elif choice == "south":
        _apply_damage(state, hull=8, crew=random.randint(1, 2), morale=6)
        ui.info("Vous échappez à la tempête principale, mais le froid mord.")
        _spend(state, turns=random.randint(3, 5), supplies_factor=1.3)
        state.flags["voyage_south_route"] = True
    else:  # saldanha
        _apply_damage(state, hull=5)
        ui.success("Détour vers Saldanha. Coque -5 seulement.")
        _spend(state, turns=random.randint(4, 6))
        # On arrive à Saldanha, opportunité de ravitailler
        if state.gold >= 50:
            sub = ui.choose(
                "À Saldanha, des Khoïkhoï proposent du bétail vif (50 P8, +30 vivres) :",
                [("Acheter", "yes"), ("Repartir", "no")],
            )
            if sub == "yes":
                state.gold -= 50
                state.supplies = min(100, state.supplies + 30)
                state.morale = min(100, state.morale + 6)
                ui.success("Vivres +30, moral +6.")


def _resolve_voy_voc_patrol(state, ui):
    ui.show_scene("events", "voy_voc_patrol")
    ui.narrate(
        "Le Cap est hollandais depuis 1652. Une frégate de la VOC croise "
        "au large."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Détour large (3 jours, sûr)", "detour"),
            ("Pavillon hollandais et papiers falsifiés", "bluff"),
            ("Cap nocturne sur le large des Aiguilles (risqué)", "night"),
        ],
    )
    if choice == "detour":
        _spend(state, turns=3, supplies_factor=1.1)
        ui.info("Détour propre. Aucun dégât.")
    elif choice == "bluff":
        rep_factor = max(0.3, 0.6 - 0.06 * state.reputation)
        if random.random() < rep_factor:
            ui.success("Bluff réussi.")
            _spend(state, turns=1)
        else:
            _apply_damage(state, hull=12, crew=random.randint(3, 6))
            ui.fail("Bluff démasqué. Bordée reçue.")
            _spend(state, turns=1)
    else:
        if random.random() < 0.6:
            ui.success("Vous passez de nuit, le hollandais ne voit rien.")
        else:
            _apply_damage(state, hull=8)
            ui.info("Échouage léger sur un haut-fond. Coque -8.")
        _spend(state, turns=1)


def _resolve_voy_saldanha(state, ui):
    ui.show_scene("events", "voy_saldanha")
    ui.narrate(
        "À l'écart du Cap, la baie de Saldanha offre un mouillage discret. "
        "Des Khoïkhoï tendent du bétail vif. Un Hollandais déserteur "
        "propose ses services."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Acheter du bétail (50 P8, +30 vivres, +8 moral)", "cattle"),
            ("Engager le déserteur hollandais (gratuit, +1 pilote informel)", "hire"),
            ("Repartir au plus vite", "leave"),
        ],
    )
    if choice == "cattle":
        if state.gold >= 50:
            state.gold -= 50
            state.supplies = min(100, state.supplies + 30)
            state.morale = min(100, state.morale + 8)
            ui.success("Vivres +30, moral +8.")
        else:
            state.supplies = min(100, state.supplies + 5)
            ui.fail("Pas les 50 P8.")
    elif choice == "hire":
        if state.crew < state.ship["crew_max"]:
            state.crew += 1
            state.flags["dutch_pilot"] = True
            ui.success("+1 homme, connaissance des routes hollandaises de l'océan Indien.")
        else:
            ui.info("Navire plein.")
    _spend(state, turns=3, supplies_factor=0.3)


def _resolve_voy_agulhas(state, ui):
    ui.show_scene("events", "voy_agulhas")
    ui.narrate(
        "Le courant chaud des Aiguilles vous porte mais le brouillard "
        "s'épaissit. Une côte invisible, des récifs partout."
    )
    if state.flags.get("dutch_pilot") or state.flags.get("sakalava_pilot"):
        ui.success("Votre pilote local trace la passe.")
        _spend(state, turns=1)
        return
    choice = ui.choose(
        "Comment manœuvrez-vous ?",
        [
            ("Coller à la côte pour profiter du courant (hull -10)", "coast"),
            ("Pousser au large (3 jours perdus)", "offshore"),
            ("Avancer à la sonde, lentement (1 jour perdu, sûr)", "sound"),
        ],
    )
    if choice == "coast":
        _apply_damage(state, hull=10, morale=3)
        ui.fail("La quille touche deux fois. Coque -10.")
        _spend(state, turns=1)
    elif choice == "offshore":
        _spend(state, turns=3, supplies_factor=1.1)
    else:
        _spend(state, turns=2)


def _resolve_voy_indiaman_convoy(state, ui):
    ui.show_scene("events", "voy_indiaman_convoy")
    ui.narrate(
        "Beaucoup de voiles. C'est un convoi de l'East India Company, "
        "lourd et bien escorté."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Le laisser passer", "leave"),
            ("Pister un traînard pendant la nuit", "shadow"),
            ("Engager le navire le plus faible (très risqué)", "attack"),
        ],
    )
    if choice == "leave":
        state.morale = max(0, state.morale - 4)
        _spend(state, turns=1)
    elif choice == "shadow":
        _spend(state, turns=2)
        if random.random() < 0.4:
            gain = random.randint(150, 400)
            state.gold += gain
            ui.success(f"Un traînard isolé, vite pris. +{gain} P8.")
        else:
            ui.info("Aucun traînard ne se détache. Vous décrochez.")
    else:
        combat = state.get_effective_bonus("combat") * 4
        strength = state.crew + combat + random.randint(-10, 20)
        if strength >= 100:
            gain = random.randint(400, 800)
            state.gold += gain
            state.loot += random.randint(200, 400)
            state.reputation += 2
            _apply_damage(state, crew=random.randint(10, 20), hull=20)
            ui.success(f"Prise d'un Indiaman. +{gain} P8.")
        else:
            _apply_damage(state, hull=35, crew=random.randint(15, 25), morale=15)
            ui.fail("Escorte trop forte. Décrochage forcé.")
        _spend(state, turns=2)


def _resolve_voy_roaring_forties(state, ui):
    ui.show_scene("events", "voy_roaring_forties")
    ui.narrate(
        "Plonger plein sud dans les Quarantièmes accélère la traversée. "
        "Le vent y est fort et régulier — et glacé."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Pousser à fond (rapide, froid mortel)", "push"),
            ("Remonter au nord (sûr, lent)", "north"),
            ("Distribuer le rhum pour tenir les hommes (-20 vivres équiv.)", "rum"),
        ],
    )
    if choice == "push":
        _apply_damage(state, hull=10, crew=2, morale=8)
        _spend(state, turns=1)
        ui.info("Deux morts de froid. Mais vous avancez.")
    elif choice == "north":
        _spend(state, turns=3, supplies_factor=1.1)
    else:
        if state.supplies >= 20:
            state.supplies -= 20
            state.morale = min(100, state.morale + 4)
            _apply_damage(state, hull=6, crew=1)
            _spend(state, turns=1)
            ui.success("Le rhum tient les hommes. Un seul mort.")
        else:
            ui.fail("Plus de rhum.")
            _apply_damage(state, hull=10, crew=2, morale=8)
            _spend(state, turns=1)


def _resolve_voy_good_passage(state, ui):
    ui.show_scene("events", "voy_good_passage")
    ui.narrate(
        "Contre toute attente, le Cap est clément. Les vents portent, "
        "pas de tempête, pas de patrouille."
    )
    choice = ui.choose(
        "Comment exploitez-vous cette accalmie ?",
        [
            ("Service de prières (moral +15)", "prayer"),
            ("Calfatage rapide (coque +8)", "careen"),
            ("Drill aux pièces pour les Mozambiques (combat affûté)", "drill"),
        ],
    )
    if choice == "prayer":
        state.morale = min(100, state.morale + 15)
    elif choice == "careen":
        state.ship["hull_current"] = min(state.ship["hull_max"],
                                         state.ship["hull_current"] + 8)
        state.morale = min(100, state.morale + 6)
    else:
        state.flags["voyage_combat_drilled"] = state.turn + 3
        state.morale = min(100, state.morale + 4)
    _spend(state, turns=2, supplies_factor=0.7)


# =================================================================
# ÉVÉNEMENTS — CANAL DU MOZAMBIQUE
# =================================================================

def _resolve_voy_anjouan(state, ui):
    ui.show_scene("events", "voy_anjouan")
    ui.narrate(
        "Les Comores, refuge habituel. Le sultan d'Anjouan tolère les "
        "flibustiers contre paiement. D'autres équipages mouillent dans la baie."
    )
    choice = ui.choose(
        "Que faites-vous à terre ?",
        [
            ("Plein assortiment (120 P8, +35 vivres, +12 moral, renseignements)", "full"),
            ("Mouillage rapide, eau seulement (20 P8, +10 vivres)", "quick"),
            ("Acheter les services d'un pilote local (60 P8)", "pilot"),
        ],
    )
    if choice == "full" and state.gold >= 120:
        state.gold -= 120
        state.supplies = min(100, state.supplies + 35)
        state.morale = min(100, state.morale + 12)
        state.flags["anjouan_intel"] = True
        ui.success("Anjouan vous accueille bien.")
    elif choice == "quick" and state.gold >= 20:
        state.gold -= 20
        state.supplies = min(100, state.supplies + 10)
        ui.success("Aiguade faite.")
    elif choice == "pilot" and state.gold >= 60:
        state.gold -= 60
        state.flags["sakalava_pilot"] = True
        ui.success("Un pilote comorien s'embarque. Les récifs n'auront plus de secret.")
    else:
        ui.fail("Pas les fonds.")
    _spend(state, turns=3, supplies_factor=0.2)


def _resolve_voy_swahili(state, ui):
    ui.show_scene("events", "voy_swahili")
    ui.narrate(
        "Un boutre swahili remonte vers Kilwa, chargé d'ivoire et "
        "d'ambre gris. L'équipage est mince."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("L'arraisonner", "attack"),
            ("Le héler et lui proposer un échange (-50 P8, vivres et bois)", "trade"),
            ("Le laisser passer", "leave"),
        ],
    )
    if choice == "attack":
        gain = random.randint(300, 500)
        state.gold += gain
        state.supplies = min(100, state.supplies + 5)
        state.morale = min(100, state.morale + 6)
        state.reputation += 1
        ui.success(f"+{gain} P8.")
        _spend(state, turns=1)
    elif choice == "trade":
        if state.gold >= 50:
            state.gold -= 50
            state.supplies = min(100, state.supplies + 20)
            state.morale = min(100, state.morale + 3)
            ui.success("Échange honnête. +20 vivres.")
        else:
            ui.fail("Pas les 50 P8.")
        _spend(state, turns=1)
    else:
        _spend(state, turns=1)


def _resolve_voy_omani_sambouk(state, ui):
    ui.show_scene("events", "voy_omani_sambouk")
    ui.narrate(
        "Un sambouk d'Oman, sur la route Mascate-Mozambique. Épices, "
        "toiles de Surat, quelques pèlerins en route vers La Mecque."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Aborder", "attack"),
            ("Parlementer (-80 P8 contre des épices et un sauf-conduit)", "parley"),
            ("Laisser passer", "leave"),
        ],
    )
    if choice == "attack":
        gain = random.randint(200, 400)
        state.gold += gain
        _apply_damage(state, crew=random.randint(0, 2))
        state.reputation += 1
        _yield_prisoners(state, ui,
                         ["merchant_captain", "clergy", "merchant_lady"],
                         n=random.randint(1, 3), source="sambouk omanais")
        _spend(state, turns=2)
        ui.success(f"+{gain} P8.")
    elif choice == "parley":
        if state.gold >= 80:
            state.gold -= 80
            state.loot += 150
            state.flags["omani_safe_pass"] = True
            ui.success("Sauf-conduit en règle. +150 cargaison.")
        else:
            ui.fail("Pas les 80 P8.")
        _spend(state, turns=2)
    else:
        _spend(state, turns=1)


def _resolve_voy_portuguese_mozambique(state, ui):
    ui.show_scene("events", "voy_portuguese_mozambique")
    ui.narrate(
        "L'Ilha de Moçambique reste possession portugaise. Une corvette "
        "patrouille les approches."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Contourner par le large (3 jours)", "wide"),
            ("Approche nocturne risquée (1 jour, hull -8)", "night"),
            ("Hisser pavillon français (bluff)", "bluff"),
        ],
    )
    if choice == "wide":
        _spend(state, turns=3, supplies_factor=1.1)
    elif choice == "night":
        _apply_damage(state, hull=8)
        _spend(state, turns=1)
    else:
        if random.random() < 0.5:
            ui.success("Le pavillon français passe. Les Portugais saluent.")
            _spend(state, turns=1)
        else:
            _apply_damage(state, hull=10, crew=random.randint(2, 4))
            ui.fail("Bluff éventé.")
            _spend(state, turns=1)


def _resolve_voy_tropical_fever(state, ui):
    if state.has_trait("scurvy_resist"):
        ui.narrate("Mahalia distribue ses tisanes. La fièvre passe sans victime.")
        state.morale = max(0, state.morale - 3)
        _spend(state, turns=1)
        return
    ui.show_scene("events", "voy_tropical_fever")
    ui.narrate(
        "La fièvre tropicale frappe. Le chirurgien fait ce qu'il peut, "
        "c'est-à-dire peu."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Confinement strict (sauve équipage, -moral)", "isolate"),
            ("Saignées et purges (mieux pour le moral, dur sur l'équipage)", "bleed"),
            ("Plantes locales si Mahalia n'est pas à bord (-20 vivres)", "herbs"),
        ],
    )
    save = state.get_modifier("crew_save_chance", 0.0)
    if choice == "isolate":
        _apply_damage(state, crew=max(1, state.crew // 18), morale=10)
    elif choice == "bleed":
        losses = max(2, state.crew // 12)
        if save > 0 and random.random() < save:
            losses = losses // 2
        _apply_damage(state, crew=losses, morale=4)
    else:
        if state.supplies >= 20:
            state.supplies -= 20
            _apply_damage(state, crew=max(1, state.crew // 20), morale=4)
            ui.success("Les plantes prennent. Pertes minimes.")
        else:
            ui.fail("Pas assez de vivres pour acheter aux indigènes.")
            _apply_damage(state, crew=max(2, state.crew // 12), morale=8)
    _spend(state, turns=2)


def _resolve_voy_monsoon(state, ui):
    ui.show_scene("events", "voy_monsoon")
    ui.narrate(
        "La mousson n'est pas la bonne. Le navire louvoie, perd du temps."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Forcer au louvoyage (5 jours, gréement usé)", "tack"),
            ("Attendre la renverse à l'abri (10 jours, vivres entamés)", "wait"),
            ("Route alternative par le sud des Comores (3 jours, hors carte)", "alternate"),
        ],
    )
    if choice == "tack":
        _apply_damage(state, hull=4, morale=5)
        _spend(state, turns=5, supplies_factor=1.1)
    elif choice == "wait":
        state.morale = max(0, state.morale - 3)
        _spend(state, turns=10, supplies_factor=1.2)
    else:
        if random.random() < 0.7:
            _spend(state, turns=3)
            ui.success("Route inconnue mais le vent porte.")
        else:
            _apply_damage(state, hull=12)
            _spend(state, turns=3)
            ui.fail("Récif non cartographié. Coque -12.")


def _resolve_voy_mughal_pilgrim(state, ui):
    ui.show_scene("events", "voy_mughal_pilgrim")
    ui.narrate(
        "Un grand vaisseau du Moghol revient de La Mecque, chargé d'or "
        "et de marchands. Faiblement armé pour sa taille."
    )
    choice = ui.choose(
        "Plan d'attaque ?",
        [
            ("Abordage frontal", "frontal"),
            ("Approche par le travers, salves puis abordage", "broadside"),
            ("Le laisser — pas envie de risquer", "leave"),
        ],
    )
    if choice == "leave":
        _spend(state, turns=1)
        return
    combat = state.get_effective_bonus("combat") * 4
    bonus = 25 if choice == "broadside" else 0
    if choice == "broadside":
        _apply_damage(state, hull=8)
    strength = state.crew + combat + random.randint(0, 30) + bonus

    if strength < 90:
        _apply_damage(state, hull=15, crew=random.randint(8, 15), morale=10)
        ui.fail("L'escorte arrive.")
        _spend(state, turns=2)
        return
    gold = random.randint(900, 1600)
    cargo = random.randint(400, 800)
    state.gold += gold
    state.loot += cargo
    _apply_damage(state, crew=random.randint(6, 14), morale=-20)
    state.reputation += 4
    ui.success(f"Prise du siècle. +{gold} P8, +{cargo} cargaison.")
    _yield_prisoners(state, ui,
                     ["noble_passenger", "noble_lady", "merchant_lady", "clergy"],
                     n=random.randint(3, 6), source="pèlerinage moghol")
    _spend(state, turns=3)


def _resolve_voy_easy_sailing(state, ui):
    ui.show_scene("events", "voy_easy_sailing")
    ui.narrate(
        "Le canal est calme. La côte africaine défile à tribord. "
        "Pêche abondante."
    )
    choice = ui.choose(
        "Comment occupez-vous l'équipage ?",
        [
            ("Pêche et séchage de poisson (+15 vivres)", "fish"),
            ("Repos prolongé (moral +8)", "rest"),
            ("Préparation des armes pour Madagascar (combat affûté)", "drill"),
        ],
    )
    if choice == "fish":
        state.supplies = min(100, state.supplies + 15)
    elif choice == "rest":
        state.morale = min(100, state.morale + 8)
    else:
        state.flags["voyage_combat_drilled"] = state.turn + 3
    _spend(state, turns=2, supplies_factor=0.5)


# =================================================================
# ÉVÉNEMENTS — APPROCHE FINALE
# =================================================================

def _resolve_voy_betsimisaraka(state, ui):
    ui.show_scene("events", "voy_betsimisaraka")
    ui.narrate(
        "Des pirogues malgaches approchent. Le clan betsimisaraka "
        "contrôle la côte est. Que leur envoyez-vous comme signal ?"
    )
    choice = ui.choose(
        "Quel accueil leur réservez-vous ?",
        [
            ("Pavillon de la côte et présents (-30 P8, +amitié)", "gifts"),
            ("Pavillon noir hissé (intimidation, dépend de la réputation)", "flag"),
            ("Rien — passer son chemin", "ignore"),
        ],
    )
    if choice == "gifts":
        if state.gold >= 30:
            state.gold -= 30
            state.morale = min(100, state.morale + 6)
            state.flags["betsimisaraka_friend"] = True
            ui.success("Échange de salutations. Amitié des Betsimisaraka.")
        else:
            ui.fail("Pas les 30 P8.")
    elif choice == "flag":
        if state.reputation >= 3:
            state.morale = min(100, state.morale + 4)
            ui.success("Les pirogues s'écartent respectueusement.")
        else:
            _apply_damage(state, crew=random.randint(1, 3))
            ui.fail("Volée de javelots. Quelques blessés.")
    else:
        state.morale = max(0, state.morale - 2)
    _spend(state, turns=1)


def _resolve_voy_pirate_rival(state, ui):
    ui.show_scene("events", "voy_pirate_rival")
    ui.narrate(
        "Un sloop bat pavillon noir devant Sainte-Marie. Un autre "
        "équipage déjà installé. La concurrence pour le butin local commence."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Parlementer (-50 P8, partage négocié)", "parley"),
            ("Démontrer la supériorité au canon (intimidation)", "show"),
            ("Mouiller à l'écart, accepter la cohabitation", "share"),
        ],
    )
    if choice == "parley":
        if state.gold >= 50:
            state.gold -= 50
            state.morale = min(100, state.morale + 4)
            state.flags["sainte_marie_pact"] = True
            ui.success("Accord signé sous le rhum. Partage clair.")
        else:
            ui.fail("Pas les 50 P8.")
    elif choice == "show":
        intim = state.get_effective_bonus("intimidation")
        if intim >= 2 or state.reputation >= 4:
            state.reputation += 1
            ui.success("Le rival lève les voiles.")
        else:
            _apply_damage(state, hull=6, morale=4)
            ui.fail("Le rival ne se laisse pas faire. Échange de bordées.")
    else:
        state.morale = max(0, state.morale - 3)
    _spend(state, turns=1)


def _resolve_voy_royal_navy_hunter(state, ui):
    if state.current_date().year < 1696:
        return _resolve_voy_safe_arrival(state, ui)
    ui.show_scene("events", "voy_royal_navy_hunter")
    ui.narrate(
        "Depuis 1696, la Couronne a juré la perte de la Pirate Round. "
        "Une frégate de la Royal Navy croise au large de Tamatave."
    )
    speed = state.ship["speed"] + state.get_effective_bonus("speed_bonus")
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Fuir vers les criques malgaches", "flee"),
            ("Pavillon de complaisance", "bluff"),
            ("Combattre", "fight"),
            ("Se cacher dans une mangrove (4 jours, sûr)", "hide"),
        ],
    )
    if choice == "flee":
        if speed + random.randint(1, 5) >= 9:
            ui.success("Vous gagnez les criques.")
        else:
            _apply_damage(state, hull=20, crew=random.randint(5, 12))
    elif choice == "bluff":
        if random.random() < 0.4 + 0.1 * (3 - min(3, state.reputation)):
            ui.success("Bluff réussi.")
        else:
            _apply_damage(state, hull=25, crew=random.randint(8, 15))
            ui.fail("Bluff démasqué.")
    elif choice == "fight":
        _apply_damage(state, hull=35, crew=random.randint(15, 25), morale=15)
        state.reputation += 2
        ui.fail("Sortie héroïque mais coûteuse.")
    else:
        _spend(state, turns=4, supplies_factor=1.2)
        ui.success("Cachés. La frégate passe sans vous voir.")
        return
    _spend(state, turns=2)


def _resolve_voy_malagasy_reefs(state, ui):
    ui.show_scene("events", "voy_malagasy_reefs")
    ui.narrate(
        "La côte est de Madagascar n'est pas cartographiée. Le pilote tâtonne."
    )
    if state.flags.get("sakalava_pilot"):
        ui.success("Votre pilote sakalava connaît la passe.")
        _spend(state, turns=1)
        return
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Engager un pilote local (60 P8)", "pilot"),
            ("Avancer à la sonde, lentement (2 jours)", "sound"),
            ("Pousser à travers (récifs)", "push"),
        ],
    )
    if choice == "pilot" and state.gold >= 60:
        state.gold -= 60
        state.flags["sakalava_pilot"] = True
        ui.success("Pilote engagé.")
        _spend(state, turns=1)
    elif choice == "pilot":
        ui.fail("Pas les 60 P8. Il faut choisir autrement.")
        _spend(state, turns=2)
    elif choice == "sound":
        _spend(state, turns=2)
    else:
        _apply_damage(state, hull=12, morale=5)
        _spend(state, turns=1)


def _resolve_voy_baldridge_welcome(state, ui):
    if state.current_date().year > 1697:
        return _resolve_voy_safe_arrival(state, ui)
    ui.show_scene("events", "voy_baldridge")
    ui.narrate(
        "Adam Baldridge tient le comptoir. Tout s'achète, tout se vend, "
        "à des prix new-yorkais."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Assortiment complet (250 P8, vivres au plein, +15 moral)", "full"),
            ("Vivres et eau (100 P8, +30 vivres, +5 moral)", "supplies"),
            ("Repartir sans rien acheter", "leave"),
        ],
    )
    if choice == "full" and state.gold >= 250:
        state.gold -= 250
        state.supplies = 100
        state.morale = min(100, state.morale + 15)
        ui.success("Cale au plein.")
    elif choice == "supplies" and state.gold >= 100:
        state.gold -= 100
        state.supplies = min(100, state.supplies + 30)
        state.morale = min(100, state.morale + 5)
        ui.success("Vivres +30.")
    elif choice in ("full", "supplies"):
        ui.fail("Pas les fonds.")
    _spend(state, turns=2, supplies_factor=0.2)


def _resolve_voy_caribbean_landfall(state, ui):
    ui.show_scene("events", "voy_caribbean_landfall")
    ui.narrate(
        "Après des mois de mer, la silhouette familière des Antilles "
        "émerge. La route est faite."
    )
    choice = ui.choose(
        "Comment annoncez-vous l'arrivée ?",
        [
            ("Salve de tous les canons (+poudre, moral +15)", "salute"),
            ("Distribution d'un acompte sur le butin (-50 P8, moral +20)", "share"),
            ("Approche discrète", "quiet"),
        ],
    )
    if choice == "salute":
        state.morale = min(100, state.morale + 15)
    elif choice == "share" and state.gold >= 50:
        state.gold -= 50
        state.morale = min(100, state.morale + 20)
    else:
        state.morale = min(100, state.morale + 5)
    _spend(state, turns=1)


def _resolve_voy_spanish_patrol(state, ui):
    ui.show_scene("events", "voy_spanish_patrol")
    ui.narrate(
        "Une frégate espagnole croise au vent des îles. Elle protège la Carrera."
    )
    choice = ui.choose(
        "Quel détour ?",
        [
            ("Cap au nord par le détroit de Floride (2 jours, sûr)", "florida"),
            ("Cap au sud par le passage de Mona (3 jours, sûr)", "mona"),
            ("Bluff sous pavillon hollandais", "bluff"),
        ],
    )
    if choice == "florida":
        _spend(state, turns=2)
    elif choice == "mona":
        _spend(state, turns=3, supplies_factor=1.1)
    else:
        if random.random() < 0.5:
            ui.success("Les Espagnols passent au large.")
        else:
            _apply_damage(state, hull=10, crew=random.randint(2, 5))
            ui.fail("Bluff démasqué.")
        _spend(state, turns=1)


def _resolve_voy_safe_arrival(state, ui):
    ui.show_scene("events", "voy_safe_arrival")
    ui.narrate("L'approche se fait sans encombre.")
    choice = ui.choose(
        "Que faites-vous avant de mouiller ?",
        [
            ("Inspecter la rade (+1 tour, renseignement)", "scout"),
            ("Mouiller directement", "anchor"),
        ],
    )
    if choice == "scout":
        state.flags["voyage_landfall_scouted"] = True
        _spend(state, turns=2)
    else:
        _spend(state, turns=1)
    state.morale = min(100, state.morale + 6)


# =================================================================
# CATALOGUE
# =================================================================

VOYAGE_EVENTS = {
    "atlantic": [
        {"id": "voy_doldrums",         "title": "Pot-au-noir",        "weight": 18, "direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_doldrums},
        {"id": "voy_atlantic_storm",   "title": "Coup de tabac",      "weight": 14, "direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_atlantic_storm},
        {"id": "voy_slaver",           "title": "Négrier isolé",      "weight": 10, "direction": "both",
         "conditions": lambda s: s.crew >= 30, "resolve": _resolve_voy_slaver},
        {"id": "voy_spanish_galleon",  "title": "Galion attardé",     "weight": 6,  "direction": "return",
         "conditions": lambda s: s.crew >= 50, "resolve": _resolve_voy_spanish_galleon},
        {"id": "voy_scurvy",           "title": "Scorbut",            "weight": 12, "direction": "both",
         "conditions": lambda s: s.supplies < 55, "resolve": _resolve_voy_scurvy},
        {"id": "voy_azores",           "title": "Escale aux Açores",  "weight": 8,  "direction": "return",
         "conditions": lambda s: True, "resolve": _resolve_voy_azores},
        {"id": "voy_cape_verde",       "title": "Mouillage au Cap-Vert","weight": 8,"direction": "outbound",
         "conditions": lambda s: True, "resolve": _resolve_voy_cape_verde},
        {"id": "voy_desertion",        "title": "Désertion",          "weight": 8,  "direction": "both",
         "conditions": lambda s: s.morale < 50, "resolve": _resolve_voy_desertion},
        {"id": "voy_calm_sailing",     "title": "Vents portants",     "weight": 22, "direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_calm_sailing},
    ],
    "guinea": [
        {"id": "voy_whydah_raid",      "title": "Raid sur Whydah",    "weight": 10, "direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_whydah_raid},
        {"id": "voy_african_king",     "title": "Négoce avec un roi", "weight": 14, "direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_african_king},
        {"id": "voy_wic_warship",      "title": "Croiseur hollandais","weight": 10, "direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_wic_warship},
        {"id": "voy_malaria",          "title": "Fièvre des marais",  "weight": 15, "direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_malaria},
        {"id": "voy_african_recruits", "title": "Recrues volontaires","weight": 10, "direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_african_recruits},
        {"id": "voy_rac_intercept",    "title": "Frégate de la RAC",  "weight": 8,  "direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_rac_intercept},
        {"id": "voy_pirate_brother",   "title": "Frère de la côte",   "weight": 8,  "direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_pirate_brother},
        {"id": "voy_african_calm",     "title": "Cabotage paisible",  "weight": 18, "direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_african_calm},
    ],
    "cape": [
        {"id": "voy_cape_storm",       "title": "Tempête du Cap",     "weight": 25, "direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_cape_storm},
        {"id": "voy_voc_patrol",       "title": "Croisière de la VOC","weight": 12, "direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_voc_patrol},
        {"id": "voy_saldanha",         "title": "Escale à Saldanha",  "weight": 14, "direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_saldanha},
        {"id": "voy_agulhas",          "title": "Courant des Aiguilles","weight": 14,"direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_agulhas},
        {"id": "voy_indiaman_convoy",  "title": "Convoi des Indes",   "weight": 10, "direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_indiaman_convoy},
        {"id": "voy_roaring_forties",  "title": "Quarantièmes rugissants","weight": 8,"direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_roaring_forties},
        {"id": "voy_good_passage",     "title": "Bon passage",        "weight": 16, "direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_good_passage},
    ],
    "mozambique": [
        {"id": "voy_anjouan",          "title": "Escale à Anjouan",   "weight": 20, "direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_anjouan},
        {"id": "voy_swahili",          "title": "Marchand swahili",   "weight": 14, "direction": "both",
         "conditions": lambda s: s.crew >= 30, "resolve": _resolve_voy_swahili},
        {"id": "voy_omani_sambouk",    "title": "Sambouk omanais",    "weight": 12, "direction": "both",
         "conditions": lambda s: s.crew >= 30, "resolve": _resolve_voy_omani_sambouk},
        {"id": "voy_portuguese_mozambique","title": "Vigie portugaise","weight": 10,"direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_portuguese_mozambique},
        {"id": "voy_tropical_fever",   "title": "Fièvre tropicale",   "weight": 12, "direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_tropical_fever},
        {"id": "voy_monsoon",          "title": "Mousson contraire",  "weight": 10, "direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_monsoon},
        {"id": "voy_mughal_pilgrim",   "title": "Pèlerins moghols",   "weight": 6,  "direction": "both",
         "conditions": lambda s: s.crew >= 50, "resolve": _resolve_voy_mughal_pilgrim},
        {"id": "voy_easy_sailing",     "title": "Mer d'huile",        "weight": 16, "direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_easy_sailing},
    ],
    "approach": [
        {"id": "voy_betsimisaraka",    "title": "Pirogue betsimisaraka","weight": 16,"direction": "outbound",
         "conditions": lambda s: True, "resolve": _resolve_voy_betsimisaraka},
        {"id": "voy_pirate_rival",     "title": "Concurrence à l'ancrage","weight": 12,"direction": "outbound",
         "conditions": lambda s: True, "resolve": _resolve_voy_pirate_rival},
        {"id": "voy_royal_navy_hunter","title": "Frégate de Sa Majesté","weight": 10,"direction": "outbound",
         "conditions": lambda s: s.current_date().year >= 1696, "resolve": _resolve_voy_royal_navy_hunter},
        {"id": "voy_malagasy_reefs",   "title": "Récifs malgaches",   "weight": 12, "direction": "outbound",
         "conditions": lambda s: True, "resolve": _resolve_voy_malagasy_reefs},
        {"id": "voy_baldridge",        "title": "Comptoir de Baldridge","weight": 18,"direction": "outbound",
         "conditions": lambda s: s.current_date().year <= 1697, "resolve": _resolve_voy_baldridge_welcome},
        {"id": "voy_caribbean_landfall","title": "Terre en vue",      "weight": 18, "direction": "return",
         "conditions": lambda s: True, "resolve": _resolve_voy_caribbean_landfall},
        {"id": "voy_spanish_patrol",   "title": "Patrouille espagnole","weight": 8, "direction": "return",
         "conditions": lambda s: True, "resolve": _resolve_voy_spanish_patrol},
        {"id": "voy_safe_arrival",     "title": "Mouillage paisible", "weight": 12, "direction": "both",
         "conditions": lambda s: True, "resolve": _resolve_voy_safe_arrival},
    ],
}


# =================================================================
# Sélection et déclenchement
# =================================================================

def pick_voyage_event(state, segment_id: str, direction: str):
    """Tire au sort un événement applicable pour ce segment et ce sens."""
    eligible = [
        e for e in VOYAGE_EVENTS.get(segment_id, [])
        if e["direction"] in ("both", direction) and e["conditions"](state)
    ]
    if not eligible:
        return None
    weights = [e["weight"] for e in eligible]
    return random.choices(eligible, weights=weights, k=1)[0]


def iter_voyage_event_ids():
    """Pour core/images.py : tous les ids d'événements de voyage."""
    for events in VOYAGE_EVENTS.values():
        for e in events:
            yield e["id"]


def trigger_long_voyage(state, ui, destination_port_id: str,
                        origin_region: str = "caribbean"):
    """
    Déclenche la grande traversée Caraïbes ⇄ océan Indien.

    Chaque événement présente au moins deux choix au joueur. Le temps
    ne s'écoule pas tant que le joueur n'a pas choisi sa réaction.
    """
    dest_region = region_of_port(destination_port_id)
    direction = "outbound" if dest_region == "overseas" else "return"

    if direction == "outbound":
        origin_label, dest_label = "les Antilles", "Sainte-Marie"
    else:
        origin_label, dest_label = "Sainte-Marie", "les Antilles"

    ui.title(f"Grande traversée : {origin_label} → {dest_label}")
    ui.narrate(
        "Vous mettez le cap au long. Plusieurs mois de mer attendent "
        "l'équipage avant la prochaine terre. Chaque incident appellera "
        "votre décision."
    )

    route_choice = ui.choose(
        "Quelle route empruntez-vous ?",
        [
            ("Route directe (Atlantique → Cap → Mozambique)", "direct"),
            ("Cabotage par la côte de Guinée (plus long, plus de prises)", "cabotage"),
        ],
    )
    skip_guinea = (route_choice == "direct")

    segments = list(SEGMENTS)
    if skip_guinea:
        segments = [s for s in segments if not s.get("optional")]
    if direction == "return":
        segments = list(reversed(segments))

    for seg in segments:
        ui.divider()
        ui.event_banner(f"{seg['name']} — {seg['sub']}")
        n_events = random.randint(*seg["events_count"])
        for _ in range(n_events):
            if state.game_over:
                return
            event = pick_voyage_event(state, seg["id"], direction)
            if event is None:
                _spend(state, turns=2)
                continue
            ui.event_banner(event["title"])
            event["resolve"](state, ui)
            state.check_defeat(ui)
            if state.game_over:
                return

    ui.divider()
    ui.success(f"La terre est en vue : {dest_label}.")
