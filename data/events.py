"""
Événements aléatoires en mer et au port.

Chaque événement déclare une scène d'illustration via son `id` :
l'image attendue est `assets/images/events/<id>.png`. Les événements
purement portuaires (rumeurs, négoce) n'appellent pas de scène.

ORGANISATION DU FICHIER
    1. Helpers communs (butin, guerres, captifs).
    2. Résolutions `_resolve_xxx(state, ui)`, REGROUPÉES PAR FAMILLE
       (voir les bannières de section ci-dessous).
    3. Catalogue `EVENTS`, lui aussi regroupé par famille, puis `pick_event`.

FAMILLES D'ÉVÉNEMENTS
    - Mer, météo & présages
    - Navigation, avaries & entretien
    - Prises & abordages
    - Rencontres en mer
    - Trésor, épaves & légendes
    - Équipage, discipline & crises du bord
    - Santé & maladies
    - Autorité, guerre & infamie
    - Au port : rumeurs & négoce
    - Recrutement de compagnons

POUR AJOUTER UN ÉVÉNEMENT
    1. Écrire `_resolve_xxx(state, ui)` dans la section de sa famille.
    2. Ajouter son entrée dans EVENTS, sous la même famille.
    3. Fournir `assets/images/events/xxx.png` (sauf événement de port).
"""

import random

# =================================================================
# Helpers communs
# =================================================================

_WAR_PERIODS = [
    (1521, 1559, "les guerres d'Italie entre Habsbourg et Valois"),
    (1585, 1604, "la guerre anglo-espagnole"),
    (1618, 1648, "la guerre de Trente Ans"),
    (1652, 1674, "les guerres anglo-hollandaises"),
    (1688, 1697, "la guerre de la Ligue d'Augsbourg"),
    (1701, 1714, "la guerre de Succession d'Espagne"),
    (1718, 1720, "la guerre de la Quadruple-Alliance"),
    (1739, 1748, "la guerre de l'Oreille de Jenkins puis de Succession d'Autriche"),
    (1756, 1763, "la guerre de Sept Ans"),
    (1775, 1783, "la guerre d'Indépendance américaine"),
    (1793, 1799, "les guerres de la Révolution française"),
]

def _maybe_yield_prisoners(state, ui, chance=0.35):
    """Sur un abordage gagné, certains passagers/officiers sont retenus.

    Les femmes sont historiquement plus rares à bord — environ 1 chance
    sur 4 quand un passager est tiré au sort."""
    if random.random() > chance:
        return
    from data.prisoners import make_prisoner, PRISONER_TYPES

    # Pool pondéré : matelots fréquents, passagers occasionnels.
    male_pool = ["sailor", "sailor", "sailor",
                 "merchant_captain", "noble_passenger", "clergy"]
    female_pool = ["merchant_lady", "noble_lady", "courtesan"]

    n = random.randint(1, 3)
    taken = []
    for _ in range(n):
        # 20% des prisonniers tirés sont des femmes
        if random.random() < 0.20:
            ptype = random.choice(female_pool)
        else:
            ptype = random.choice(male_pool)
        state.prisoners.append(make_prisoner(ptype, source="prise marchande"))
        taken.append(ptype)
    labels = ", ".join(f"1 {PRISONER_TYPES[t]['label']}" for t in taken)
    ui.info(f"Prisonniers retenus à bord : {labels}.")

def _war_name(state):
    """Renvoie le nom de la guerre en cours, ou None en temps de paix."""
    try:
        year = state.current_date().year
    except Exception:
        return None
    for a, b, name in _WAR_PERIODS:
        if a <= year <= b:
            return name
    return None

def _count_captives(state):
    """Compte les captifs africains encore détenus en cale."""
    n = 0
    for p in state.prisoners:
        t = p.get("type") if isinstance(p, dict) else getattr(p, "type", None)
        if t == "enslaved_african":
            n += 1
    return n

def _remove_captives(state, k):
    """Retire jusqu'à k captifs africains de la liste des prisonniers."""
    kept, removed = [], 0
    for p in state.prisoners:
        t = p.get("type") if isinstance(p, dict) else getattr(p, "type", None)
        if t == "enslaved_african" and removed < k:
            removed += 1
            continue
        kept.append(p)
    state.prisoners = kept
    return removed

# =================================================================
# Résolutions, regroupées par famille
# =================================================================

# -----------------------------------------------------------------
# >>> MER, MÉTÉO & PRÉSAGES
# Tempêtes, calmes, vents, phénomènes et superstitions de la mer.
# -----------------------------------------------------------------

def _resolve_storm(state, ui):
    ui.show_scene("events", "storm")
    severity = random.randint(1, 3)
    hull_loss = severity * 8
    supply_loss = severity * 5
    crew_loss = severity - 1
    ui.narrate(
        "Le ciel s'assombrit, les écoutes sifflent. Une bourrasque tropicale "
        "frappe le navire. La coque craque, les barils roulent dans la cale."
    )
    state.ship["hull_current"] = max(0, state.ship["hull_current"] - hull_loss)
    state.supplies = max(0, state.supplies - supply_loss)
    if crew_loss > 0 and state.crew > crew_loss:
        state.crew -= crew_loss
    ui.info(f"Coque : -{hull_loss}   Vivres : -{supply_loss}   Hommes perdus : {crew_loss}")

def _resolve_hurricane(state, ui):
    """Ouragan de la saison cyclonique (juin-novembre aux Antilles), bien
    plus violent que la simple bourrasque. Alléger le navire en sacrifiant
    de la cargaison pouvait sauver la coque — choix cornélien."""
    ui.show_scene("events", "hurricane")
    ui.narrate(
        "Le baromètre s'effondre, le ciel vire au plomb verdâtre. Ce n'est "
        "pas un grain : c'est un ouragan. La mer se creuse en montagnes, le "
        "vent hurle dans la mâture comme une meute."
    )
    choice = ui.choose(
        "Que commandez-vous ?",
        [
            ("Jeter de la cargaison par-dessus bord pour alléger", "jettison"),
            ("Tout affaler, à la cape sèche, et prier", "ride"),
        ],
    )
    if choice == "jettison":
        thrown = min(state.loot, random.randint(80, 200))
        state.loot -= thrown
        hull_loss = random.randint(8, 18)
        crew_lost = random.randint(0, 2)
        state.ship["hull_current"] = max(0, state.ship["hull_current"] - hull_loss)
        state.crew = max(0, state.crew - crew_lost)
        state.morale = max(0, state.morale - 6)
        ui.info(
            f"-{thrown} de cargaison à la mer, mais le navire se relève mieux. "
            f"Coque -{hull_loss}, {crew_lost} perdus. Moral -6."
        )
    else:
        nav = state.get_effective_bonus("navigation")
        hull_loss = random.randint(20, 40) - nav * 3
        hull_loss = max(8, hull_loss)
        crew_lost = random.randint(2, 7)
        supply_loss = random.randint(6, 14)
        state.ship["hull_current"] = max(0, state.ship["hull_current"] - hull_loss)
        state.crew = max(0, state.crew - crew_lost)
        state.supplies = max(0, state.supplies - supply_loss)
        state.morale = max(0, state.morale - 12)
        ui.fail(
            f"Trois jours d'enfer. La coque encaisse, le gréement souffre. "
            f"Coque -{hull_loss}, {crew_lost} morts, vivres -{supply_loss}, moral -12."
        )

def _resolve_monsoon(state, ui):
    """La mousson commande la navigation de l'océan Indien : se tromper de
    saison, c'est affronter des vents contraires et des grains violents."""
    ui.show_scene("events", "monsoon")
    ui.narrate(
        "La mousson a tourné. Vents contraires, grains lourds, mer hachée : "
        "naviguer à contre-saison dans l'océan Indien se paie cher."
    )
    nav = state.get_effective_bonus("navigation")
    if nav >= 2 and random.random() < 0.5:
        state.advance_turn()
        state.morale = max(0, state.morale - 4)
        ui.info("Votre pilote louvoie au mieux ; on perd des jours, sans casse. Moral -4.")
        return
    hull_loss = random.randint(10, 22)
    supply_loss = random.randint(6, 14)
    crew_lost = random.randint(1, 4)
    state.ship["hull_current"] = max(0, state.ship["hull_current"] - hull_loss)
    state.supplies = max(0, state.supplies - supply_loss)
    state.crew = max(0, state.crew - crew_lost)
    state.morale = max(0, state.morale - 8)
    for _ in range(random.randint(2, 4)):
        state.advance_turn()
    ui.fail(
        f"La mousson vous malmène des jours durant. Coque -{hull_loss}, "
        f"vivres -{supply_loss}, {crew_lost} morts, moral -8."
    )

def _resolve_doldrums(state, ui):
    """Calme plat — fléau de la marine à voile sous les tropiques."""
    ui.show_scene("events", "doldrums")
    ui.narrate(
        "Trois jours sans une ride sur l'eau. Les voiles pendent comme du "
        "linge mouillé. La cale chauffe, l'eau croupit, les hommes s'agacent."
    )
    state.supplies = max(0, state.supplies - 8)
    state.morale = max(0, state.morale - 10)
    ui.info("Vivres -8, moral -10.")

def _resolve_lucky_breeze(state, ui):
    ui.show_scene("events", "lucky_breeze")
    ui.narrate(
        "Vent portant, mer plate. La traversée se fait sans incident. "
        "Le cuisinier sort même un quartier de porc en saumure pour le souper."
    )
    state.morale = min(100, state.morale + 5)
    ui.success("Moral en hausse.")

def _resolve_rogue_wave(state, ui):
    """Lame scélérate — vague isolée, anormalement haute, surgie d'une mer
    déjà formée. Frappe sans prévenir ; un bon timonier limite la casse."""
    if state.in_port:
        return
    ui.show_scene("events", "rogue_wave")
    ui.narrate(
        "Sans crier gare, une lame deux fois plus haute que les autres se "
        "dresse par l'avant. Une muraille d'eau verte s'abat sur le pont."
    )
    nav = state.get_effective_bonus("navigation")
    if nav >= 2 and random.random() < 0.6:
        state.morale = max(0, state.morale - 3)
        ui.info("Le timonier lofe juste à temps ; le navire escalade la lame. Quelques contusions. Moral -3.")
        return
    hull_loss = random.randint(8, 20)
    crew_lost = random.randint(1, 4)
    supply_loss = random.randint(0, 8)
    state.ship["hull_current"] = max(0, state.ship["hull_current"] - hull_loss)
    state.crew = max(0, state.crew - crew_lost)
    state.supplies = max(0, state.supplies - supply_loss)
    state.morale = max(0, state.morale - 6)
    ui.fail(
        f"La lame balaie le pont : coque -{hull_loss}, {crew_lost} hommes "
        f"emportés, vivres -{supply_loss}. Moral -6."
    )

def _resolve_st_elmo_fire(state, ui):
    """Feu Saint-Elme : décharge lumineuse dans la mâture par gros temps
    électrique. Les marins y lisaient un présage — bon (Castor et Pollux)
    ou funeste — selon l'humeur du bord. Pur effet de moral et de
    superstition."""
    ui.show_scene("events", "st_elmo_fire")
    ui.narrate(
        "La nuit, des flammèches bleues dansent à la pointe des vergues et au "
        "bout des mâts : le feu Saint-Elme. L'équipage retient son souffle. "
        "Présage ? Et de quoi ?"
    )
    # Un aumônier sait retourner le présage en faveur de l'équipage.
    if state.has_companion("pere_etienne") or random.random() < 0.5:
        state.morale = min(100, state.morale + 7)
        ui.success(
            "« Saint Elme veille sur nous ! » Le présage est tenu pour heureux. "
            "Les hommes se signent, rassurés. Moral +7."
        )
    else:
        state.morale = max(0, state.morale - 6)
        ui.info(
            "Les anciens hochent la tête : feu de mauvais augure. Une rumeur "
            "sourde gagne l'entrepont. Moral -6."
        )

def _resolve_sea_monster(state, ui):
    """Superstition de marins : poulpe géant, serpent de mer, sirène... Les
    récits de monstres peuplaient journaux de bord et cartes anciennes. Pur
    effet de moral, selon que l'on cède ou non à la peur."""
    ui.show_scene("events", "sea_monster")
    ui.narrate(
        "Au crépuscule, une forme immense glisse sous la coque — dos luisant, "
        "tentacule, ou banc de marsouins grossi par la peur ? Les vigies "
        "jurent avoir vu un monstre. L'entrepont gronde de superstition."
    )
    if state.has_companion("pere_etienne") or random.random() < 0.5:
        state.morale = min(100, state.morale + 4)
        ui.success(
            "Vous riez du « monstre » et baptisez un baril de rhum en son "
            "honneur. La peur tourne en chanson. Moral +4."
        )
    else:
        state.morale = max(0, state.morale - 5)
        ui.info("La rumeur enfle : Léviathan rôde. Les quarts de nuit se font à voix basse. Moral -5.")

def _resolve_whale_carcass(state, ui):
    """Carcasse de baleine — opportunité d'huile et de graisse."""
    ui.show_scene("events", "whale")
    ui.narrate(
        "Une carcasse de baleine flotte ventre en l'air, à quelques milles. "
        "Les requins n'ont pas tout pris. Graisse pour le calfatage et huile."
    )
    choice = ui.choose(
        "Mettre les chaloupes à l'eau ?",
        [
            ("Oui — récupérer ce qui peut l'être", "yes"),
            ("Non — perte de temps", "no"),
        ],
    )
    if choice == "yes":
        state.advance_turn()
        gain = random.randint(60, 140)
        state.gold += gain
        state.ship["hull_current"] = min(state.ship["hull_max"], state.ship["hull_current"] + 5)
        ui.success(f"+{gain} P8 en huile et graisse ; coque calfatée (+5).")

def _resolve_turtle_hunt(state, ui):
    """Chasse à la tortue verte, abondante aux Caïmans et au large de Cuba :
    les boucaniers s'y ravitaillaient en viande fraîche, remède naturel
    contre le scorbut (cf. boucan / Brethren of the Coast au glossaire)."""
    ui.show_scene("events", "turtle_hunt")
    ui.narrate(
        "Des dizaines de tortues vertes affleurent près d'un îlot de sable. "
        "Viande fraîche à profusion : de quoi tenir le scorbut à distance et "
        "remplir les cambuses."
    )
    choice = ui.choose(
        "Mettre les chaloupes à l'eau ?",
        [
            ("Oui — capturer et caquer la tortue", "hunt"),
            ("Non — perte de temps", "no"),
        ],
    )
    if choice == "hunt":
        state.advance_turn()
        gain = random.randint(15, 30)
        state.supplies = min(100, state.supplies + gain)
        state.morale = min(100, state.morale + 5)
        ui.success(f"Une journée de chasse. Vivres frais +{gain}, anti-scorbut. Moral +5.")
    else:
        ui.info("Vous gardez le cap. Les tortues replongent.")

# -----------------------------------------------------------------
# >>> NAVIGATION, AVARIES & ENTRETIEN
# Échouages, erreurs de route, carène et sinistres du navire.
# -----------------------------------------------------------------

def _resolve_sandbar(state, ui):
    """Échouage sur un banc de sable ou un récif mal porté sur la carte —
    hantise des eaux antillaises. Un bon navigateur évite le pire ;
    alléger ou attendre la marée pour déséchouer."""
    ui.show_scene("events", "sandbar")
    nav = state.get_effective_bonus("navigation")
    if nav >= 2 and random.random() < 0.7:
        ui.narrate(
            "La sonde travaille ; au dernier moment, votre navigateur fait "
            "abattre. La quille frôle le banc, sans toucher. Échappé belle."
        )
        state.morale = min(100, state.morale + 2)
        return
    ui.narrate(
        "Un raclement sinistre court le long de la quille : le navire talonne "
        "sur un banc de sable. Il s'immobilise, gîté, la mer clapotant aux "
        "sabords. La marée descend."
    )
    choice = ui.choose(
        "Comment vous dégagez-vous ?",
        [
            ("Alléger : jeter cargaison et canons à la mer", "lighten"),
            ("Attendre la marée haute, kedge à l'ancre", "tide"),
        ],
    )
    if choice == "lighten":
        thrown = min(state.loot, random.randint(60, 150))
        state.loot -= thrown
        hull_loss = random.randint(5, 12)
        state.ship["hull_current"] = max(0, state.ship["hull_current"] - hull_loss)
        ui.info(f"Allégé, le navire se libère à la marée montante. -{thrown} de cargaison, coque -{hull_loss}.")
    else:
        state.advance_turn()
        if random.random() < 0.7:
            hull_loss = random.randint(8, 16)
            state.ship["hull_current"] = max(0, state.ship["hull_current"] - hull_loss)
            ui.info(f"La marée vous relève au bout d'une nuit d'angoisse. Coque -{hull_loss}.")
        else:
            hull_loss = random.randint(18, 30)
            crew_lost = random.randint(1, 4)
            state.ship["hull_current"] = max(0, state.ship["hull_current"] - hull_loss)
            state.crew = max(0, state.crew - crew_lost)
            state.morale = max(0, state.morale - 8)
            ui.fail(f"Un grain se lève sur le banc. Le navire cogne. Coque -{hull_loss}, {crew_lost} morts.")

def _resolve_off_course(state, ui):
    """Erreur de point : avant le chronomètre de marine (Harrison, 1761), la
    longitude se devine plus qu'elle ne se mesure. Une dérive, et l'on se
    retrouve loin de sa route."""
    ui.show_scene("events", "off_course")
    ui.narrate(
        "Le point du midi ne tombe pas juste. Faute de mesurer la longitude "
        "avec certitude, on a dérivé loin de la route prévue. La côte attendue "
        "n'est nulle part."
    )
    nav = state.get_effective_bonus("navigation")
    if nav >= 2 and random.random() < 0.7:
        ui.success("Votre pilote reprend une hauteur d'astre, recoupe, et rétablit la route. Aucune perte.")
        return
    supply_loss = random.randint(5, 12)
    state.supplies = max(0, state.supplies - supply_loss)
    state.morale = max(0, state.morale - 6)
    for _ in range(random.randint(1, 3)):
        state.advance_turn()
    ui.info(f"Des jours à chercher sa route. Vivres -{supply_loss}, moral -6.")

def _resolve_careening_needed(state, ui):
    """La coque se charge de tarets et de coquillages : le navire ralentit et
    pourrit sous la flottaison. Le carénage dans une crique isolée était un
    entretien vital — et un moment de grande vulnérabilité."""
    if state.ship["hull_current"] > state.ship["hull_max"] * 0.8:
        return
    ui.show_scene("events", "careening_needed")
    ui.narrate(
        "Le navire mollit, traînant une barbe d'algues et de bernacles. La "
        "carène est rongée de tarets. Une crique discrète permettrait de "
        "l'abattre en carène et de gratter la coque — mais à terre, désarmé."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Caréner maintenant dans une crique isolée", "careen"),
            ("Tenir la mer encore un temps", "wait"),
        ],
    )
    if choice == "careen":
        state.advance_turn()
        state.supplies = max(0, state.supplies - 5)
        repair = random.randint(15, 30)
        state.ship["hull_current"] = min(state.ship["hull_max"], state.ship["hull_current"] + repair)
        state.morale = min(100, state.morale + 5)
        if random.random() < 0.15:
            crew_lost = random.randint(1, 3)
            state.crew = max(0, state.crew - crew_lost)
            ui.info(
                f"Carène grattée, calfatée, suiffée : coque +{repair}, moral +5. "
                f"Mais une patrouille a surpris des hommes à terre : {crew_lost} perdus."
            )
        else:
            ui.success(f"Carène nettoyée et calfatée. Coque +{repair}, le navire reprend son allant. Moral +5.")
    else:
        state.ship["hull_current"] = max(0, state.ship["hull_current"] - random.randint(3, 8))
        ui.info("Vous tenez la mer. La coque continue de se dégrader lentement.")

def _resolve_ship_fire(state, ui):
    """Incendie à bord — la hantise absolue d'un navire de bois et de
    goudron, surtout près de la sainte-barbe (soute à poudre). Réaction
    rapide ou désastre."""
    ui.show_scene("events", "ship_fire")
    ui.narrate(
        "« Au feu ! » Une gargousse mal éteinte, et voilà des flammes qui "
        "lèchent les bordages près de la sainte-barbe. À deux pas, la poudre. "
        "Quelques secondes décident de tout."
    )
    choice = ui.choose(
        "Que commandez-vous ?",
        [
            ("Chaîne de seaux et couvertures mouillées sur le foyer", "fight"),
            ("Noyer la sainte-barbe — sacrifier la poudre pour sauver le navire", "flood"),
        ],
    )
    if choice == "flood":
        state.flags["powder_low"] = True
        state.morale = max(0, state.morale - 5)
        ui.info(
            "L'eau de mer noie la soute : le feu meurt, mais la poudre est "
            "perdue. Vous voilà désarmés jusqu'au prochain ravitaillement. Moral -5."
        )
        return
    leadership = state.get_effective_bonus("leadership")
    if leadership >= 1 or random.random() < 0.6:
        crew_lost = random.randint(0, 3)
        hull_loss = random.randint(5, 15)
        state.crew = max(0, state.crew - crew_lost)
        state.ship["hull_current"] = max(0, state.ship["hull_current"] - hull_loss)
        ui.success(f"La chaîne tient bon, le feu est maîtrisé. Coque -{hull_loss}, {crew_lost} brûlé(s).")
    else:
        crew_lost = random.randint(4, 10)
        hull_loss = random.randint(20, 40)
        state.crew = max(0, state.crew - crew_lost)
        state.ship["hull_current"] = max(0, state.ship["hull_current"] - hull_loss)
        state.morale = max(0, state.morale - 15)
        ui.fail(
            f"Le feu court plus vite que les seaux. On l'éteint enfin, mais à "
            f"quel prix : coque -{hull_loss}, {crew_lost} morts, moral -15."
        )

def _resolve_powder_low(state, ui):
    """Pénurie de poudre et de boulets : sans munitions, l'intimidation
    s'effondre. Il faut se ravitailler — auprès d'un fort complaisant, d'un
    autre pirate, ou en grattant les fonds de barils."""
    if state.flags.get("powder_low") is False:
        return
    ui.show_scene("events", "powder_low")
    ui.narrate(
        "Le maître canonnier fait grise mine : il reste à peine de quoi tirer "
        "trois bordées. Sans poudre, le pavillon noir n'effraie plus personne."
    )
    choice = ui.choose(
        "Où trouver de la poudre ?",
        [
            ("Acheter cher à un fort complaisant (120 P8)", "buy"),
            ("Rationner et tenter la chance jusqu'à une prise", "ration"),
        ],
    )
    if choice == "buy" and state.gold >= 120:
        state.gold -= 120
        state.flags["powder_low"] = False
        state.morale = min(100, state.morale + 4)
        ui.success("Barils de poudre et boulets embarqués sous le manteau. -120 P8. Prêts à mordre.")
    elif choice == "buy":
        ui.fail("Pas les 120 P8. Le marchand referme sa porte. Toujours à sec de poudre.")
    else:
        state.flags["powder_low"] = True
        state.morale = max(0, state.morale - 4)
        ui.info("Rationnement strict des munitions. L'équipage serre les dents. Moral -4.")

# -----------------------------------------------------------------
# >>> PRISES & ABORDAGES
# Navires marchands et de transport à arraisonner.
# -----------------------------------------------------------------

def _resolve_merchant_sail(state, ui):
    ui.show_scene("events", "merchant_sail")
    ui.narrate(
        "« Voile à l'horizon ! » Un trois-mâts marchand louvoie sous le vent. "
        "Pavillon hollandais, semble peu armé."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Donner la chasse et arraisonner", "attack"),
            ("Hisser pavillon noir pour intimider", "intimidate"),
            ("Le laisser passer", "ignore"),
        ],
    )
    if choice == "ignore":
        ui.info("Le marchand s'éloigne, soulagé. Aucune perte, aucun gain.")
        return

    merchant_strength = random.randint(15, 35)
    intimid_bonus = state.get_effective_bonus("intimidation") * 5
    combat_bonus = state.get_effective_bonus("combat") * 4
    crew_factor = state.crew * (0.6 if choice == "intimidate" else 1.0)
    player_strength = crew_factor + intimid_bonus + combat_bonus + random.randint(0, 20)

    if player_strength > merchant_strength * 1.5:
        coin = random.randint(80, 180)
        cargo = random.randint(150, 350)
        ui.success(
            f"L'équipage marchand se rend sans combat. {coin} pièces en caisse, "
            f"et {cargo} de cargaison à revendre."
        )
        state.gold += coin
        state.loot += cargo
        state.morale = min(100, state.morale + 5)
        state.reputation += 1
        _maybe_yield_prisoners(state, ui, chance=0.45)
    elif player_strength > merchant_strength:
        coin = random.randint(60, 140)
        cargo = random.randint(80, 220)
        crew_lost = random.randint(1, 4)
        ui.success(
            f"Bref échange de mousqueterie, puis abordage victorieux. "
            f"{coin} pièces, {cargo} de cargaison. Pertes : {crew_lost} hommes."
        )
        state.gold += coin
        state.loot += cargo
        state.crew = max(0, state.crew - crew_lost)
        state.morale = min(100, state.morale + 3)
        state.reputation += 1
        _maybe_yield_prisoners(state, ui, chance=0.30)
    else:
        crew_lost = random.randint(5, 12)
        hull_loss = random.randint(10, 25)
        ui.fail(
            f"Le marchand portait des soldats embarqués ! L'abordage tourne mal. "
            f"Pertes : {crew_lost} hommes, coque : -{hull_loss}."
        )
        state.crew = max(0, state.crew - crew_lost)
        state.ship["hull_current"] = max(0, state.ship["hull_current"] - hull_loss)
        state.morale = max(0, state.morale - 15)

def _resolve_fishing_boat(state, ui):
    """Barque de pêche côtière. Petite prise, mais les pirates y
    trouvaient des vivres frais, des nouvelles, et parfois des hommes
    qu'ils enrôlaient de gré ou de force (pratique courante du « pressing »
    de pêcheurs et caboteurs)."""
    ui.show_scene("events", "fishing_boat")
    ui.narrate(
        "Une barque de pêche tire ses lignes sous le vent. Quatre hommes "
        "à bord, des paniers de poisson, pas une arme en vue."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Arraisonner — vivres et nouvelles", "take"),
            ("Proposer aux pêcheurs de signer les Articles", "press"),
            ("Les laisser à leurs filets", "ignore"),
        ],
    )
    if choice == "ignore":
        ui.info("Vous passez au large. Un pêcheur ôte son bonnet, soulagé.")
        return
    if choice == "take":
        gain = random.randint(15, 40)
        state.supplies = min(100, state.supplies + 12)
        state.gold += gain
        rumor = random.choice([
            "Ils disent qu'un convoi sucrier appareille sous peu de la Jamaïque.",
            "Une frégate de guerre aurait mouillé hier dans la rade voisine.",
            "Un navire désemparé dérive, dit-on, à deux jours de cap au sud.",
        ])
        ui.success(f"Vivres +12, +{gain} P8. Et un mot glané : « {rumor} »")
        return
    # press : enrôler un ou deux pêcheurs
    joiners = min(state.ship["crew_max"] - state.crew, random.randint(1, 3))
    if joiners <= 0:
        ui.info("Le rôle est plein. Vous prenez seulement leur poisson (+8 vivres).")
        state.supplies = min(100, state.supplies + 8)
        return
    state.crew += joiners
    state.supplies = min(100, state.supplies + 6)
    if random.random() < 0.5:
        ui.success(f"{joiners} pêcheur(s) signent volontiers — la mer libre vaut mieux que la misère côtière.")
    else:
        state.morale = max(0, state.morale - 3)
        ui.info(f"{joiners} pêcheur(s) embarqués de force. L'équipage hausse les épaules.")

def _resolve_bermuda_sloop(state, ui):
    """Sloop bermudien — voilier en cèdre réputé pour sa vitesse, très
    convoité des pirates qui aimaient s'en emparer pour leurs propres
    courses. Prise rapide à faible équipage."""
    ui.show_scene("events", "bermuda_sloop")
    ui.narrate(
        "Une voile basse et fine taille la mer : un sloop bermudien, coque "
        "de cèdre, fait pour courir. Léger en hommes, lourd en marchandise."
    )
    speed = state.ship["speed"] + state.get_effective_bonus("speed_bonus")
    if speed + random.randint(0, 6) < 8:
        ui.info("Le sloop est trop fin pour vous : il vous distance et s'efface à l'horizon.")
        state.morale = max(0, state.morale - 2)
        return
    coin = random.randint(60, 140)
    cargo = random.randint(90, 200)
    crew_lost = random.randint(0, 3)
    state.gold += coin
    state.loot += cargo
    state.crew = max(0, state.crew - crew_lost)
    state.reputation += 1
    state.morale = min(100, state.morale + 4)
    ui.success(
        f"Vous le rattrapez avant midi. {coin} P8, {cargo} de cargaison. "
        f"Pertes : {crew_lost}. Un beau coursier, ce sloop."
    )
    _maybe_yield_prisoners(state, ui, chance=0.30)

def _resolve_dutch_fluyt(state, ui):
    """Fluyt (flûte) hollandais — cargo bon marché à équipage réduit, épine
    dorsale du commerce néerlandais. Gros volume, peu de défenseurs."""
    ui.show_scene("events", "dutch_fluyt")
    ui.narrate(
        "Une flûte hollandaise, ventrue, peu de canons, à peine vingt hommes "
        "pour la manœuvre. Tout son prix est dans la cale."
    )
    intimid = state.get_effective_bonus("intimidation")
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Tirer un coup de semonce et sommer de se rendre", "intimidate"),
            ("Aborder franchement", "board"),
            ("Laisser filer", "ignore"),
        ],
    )
    if choice == "ignore":
        ui.info("Vous laissez la flûte poursuivre sa route placide.")
        return
    if choice == "intimidate" and (intimid >= 1 or random.random() < 0.6):
        cargo = random.randint(200, 420)
        coin = random.randint(40, 110)
        state.loot += cargo
        state.gold += coin
        state.reputation += 1
        ui.success(f"Le pavillon noir suffit. {cargo} de cargaison, {coin} P8, sans un mort.")
        _maybe_yield_prisoners(state, ui, chance=0.25)
        return
    cargo = random.randint(160, 360)
    coin = random.randint(30, 90)
    crew_lost = random.randint(1, 4)
    state.loot += cargo
    state.gold += coin
    state.crew = max(0, state.crew - crew_lost)
    ui.success(f"Abordage court. {cargo} de cargaison, {coin} P8. Pertes : {crew_lost}.")
    _maybe_yield_prisoners(state, ui, chance=0.30)

def _resolve_sugar_drogher(state, ui):
    """Caboteur antillais chargé de sucre, de mélasse et de rhum, entre les
    îles (commerce triangulaire, cf. carte du repository). Le rhum remonte
    le moral — mais peut aussi le défaire."""
    ui.show_scene("events", "sugar_drogher")
    ui.narrate(
        "Un caboteur ras de l'eau, gréé à l'antillaise, sent le sucre brûlé "
        "à une encablure. Des barriques de mélasse, et — la vigie jubile — "
        "des futailles de rhum."
    )
    choice = ui.choose(
        "Que prenez-vous ?",
        [
            ("Tout — y compris le rhum", "all"),
            ("La cargaison, mais consigner le rhum sous clé", "ration"),
            ("Passer au large", "ignore"),
        ],
    )
    if choice == "ignore":
        ui.info("Vous dédaignez la mélasse. L'équipage grogne un peu.")
        state.morale = max(0, state.morale - 2)
        return
    cargo = random.randint(120, 260)
    state.loot += cargo
    state.reputation += 1
    if choice == "all":
        if random.random() < 0.55:
            state.morale = min(100, state.morale + 12)
            ui.success(f"+{cargo} de cargaison. La nuit tourne à la beuverie : moral +12.")
        else:
            crew_lost = random.randint(0, 2)
            state.crew = max(0, state.crew - crew_lost)
            state.morale = max(0, state.morale - 4)
            ui.info(
                f"+{cargo} de cargaison. Mais l'ivresse vire à la rixe ; "
                f"{crew_lost} homme(s) hors d'état, moral -4."
            )
    else:  # ration
        state.morale = min(100, state.morale + 5)
        ui.success(f"+{cargo} de cargaison, rhum consigné. Discipline tenue, moral +5.")

def _resolve_careened_ship(state, ui):
    """Trouve un navire en train de caréner sur une plage — prise facile."""
    ui.show_scene("events", "careened")
    ui.narrate(
        "Dans une crique, un brigantin marchand est tiré au sec, coque "
        "exposée, voiles à terre. L'équipage occupé à gratter les "
        "coquillages ne vous a pas vu."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Attaquer immédiatement", "attack"),
            ("Passer au large — trop voyant", "ignore"),
        ],
    )
    if choice == "attack":
        booty = random.randint(150, 350)
        cargo = random.randint(100, 250)
        state.gold += booty
        state.loot += cargo
        state.reputation += 1
        state.morale = min(100, state.morale + 6)
        # 30% chance de prisonniers utiles
        if random.random() < 0.3:
            from data.prisoners import make_prisoner
            n = random.randint(1, 3)
            for _ in range(n):
                ptype = random.choice(["sailor", "merchant_captain", "noble_passenger"])
                state.prisoners.append(make_prisoner(ptype, source="brigantin caréné"))
            ui.success(f"Prise rapide. +{booty} P8, +{cargo} cargaison, et {n} prisonnier(s) sur la plage.")
        else:
            ui.success(f"Prise nette. +{booty} P8 et +{cargo} de cargaison.")
        # Matières premières échouées : à rapporter au repaire si on en a un.
        hold = getattr(state, "cargo_hold", None)
        if hold is not None:
            import random as _r
            from data.resources import RESOURCES as _RES
            # 1 à 3 types différents, petites quantités
            for rid in _r.sample(list(_RES.keys()), k=_r.randint(1, 3)):
                qty = _r.randint(2, 6)
                room = max(0, state.ship.get("cargo", 0) * 15 - sum(hold.values()))
                added = min(qty, room)
                if added > 0:
                    hold[rid] = hold.get(rid, 0) + added
                    ui.info(f"  +{added} {_RES[rid]['label']} (cale).")
                if room <= 0:
                    ui.info("  La cale déborde : le reste est laissé à la mer.")
                    break
    else:
        ui.info("Vous gardez le large. Discret, mais sans gain.")

def _resolve_packet_boat(state, ui):
    """Aviso / paquebot postal — petit, rapide, chargé de courrier et de
    dépêches plus que d'or. Sa vraie valeur est le renseignement (et,
    parfois, un passager monnayable)."""
    from data.prisoners import make_prisoner
    ui.show_scene("events", "packet_boat")
    ui.narrate(
        "Un fin voilier force de toile pour vous échapper : un paquebot "
        "postal, ses sacs de courrier scellés et ses dépêches d'amirauté. "
        "Peu d'or, mais ce qu'il sait vaut peut-être davantage."
    )
    speed = state.ship["speed"] + state.get_effective_bonus("speed_bonus")
    if speed + random.randint(0, 6) < 9:
        ui.info("Le paquebot file plus vite que vous. Ses dépêches vous échappent.")
        return
    coin = random.randint(20, 70)
    state.gold += coin
    state.flags["dispatch_intel"] = True
    rumor = random.choice([
        "Une dépêche évoque un convoi marchand attendu sous escorte légère.",
        "Un ordre d'amirauté détourne une frégate loin de ces eaux pour un mois.",
        "Une lettre annonce le départ d'un riche navire de la Compagnie.",
    ])
    ui.success(f"Le paquebot pris. +{coin} P8, et des dépêches : « {rumor} »")
    # Parfois un courrier de qualité parmi les passagers
    if random.random() < 0.4:
        ptype = random.choice(["noble_passenger", "clergy", "navy_officer"])
        state.prisoners.append(make_prisoner(ptype, source="paquebot postal"))
        ui.info("Un passager de qualité est retenu — il pourra valoir rançon.")

def _resolve_treasure_straggler(state, ui):
    """Galion retardataire de la flotte de l'argent espagnole (« flota »).
    Séparé de son escorte, il porte argent et doublons mais reste un
    adversaire redoutable. Repère : Drake et « The Cacafuego » (cf.
    biographies du repository)."""
    ui.show_scene("events", "treasure_straggler")
    ui.narrate(
        "Une haute poupe sculptée, dorée, isolée à l'horizon : un galion de "
        "la flotte de l'argent, désemparé d'un grain et séparé de son "
        "escorte. Sa cale vaut une fortune — sa batterie, votre peau."
    )
    combat = state.get_effective_bonus("combat") * 5
    nav = state.get_effective_bonus("navigation") * 2
    strength = state.crew + combat + nav + random.randint(-15, 20)
    choice = ui.choose(
        "Tenter le galion isolé ?",
        [
            ("Donner l'assaut tant qu'il est seul", "attack"),
            ("Le filer en attendant la nuit", "stalk"),
            ("Renoncer — l'escorte peut revenir", "leave"),
        ],
    )
    if choice == "leave":
        ui.info("Vous virez de bord. Un galion vaut mieux vivant qu'une potence.")
        return
    if choice == "stalk":
        state.advance_turn()
        strength += 20
        ui.info("Vous le pistez jusqu'au crépuscule ; le vent faiblit, son escorte ne revient pas.")
    if strength < 95:
        damage = random.randint(25, 45)
        crew_lost = random.randint(8, 16)
        state.ship["hull_current"] = max(0, state.ship["hull_current"] - damage)
        state.crew = max(0, state.crew - crew_lost)
        state.morale = max(0, state.morale - 12)
        ui.fail(f"Sa bordée vous ouvre un sabord. Vous décrochez. Coque -{damage}, {crew_lost} morts.")
        return
    coin = random.randint(400, 900)      # argent et doublons
    cargo = random.randint(200, 500)
    crew_lost = random.randint(6, 14)
    state.gold += coin
    state.loot += cargo
    state.crew = max(0, state.crew - crew_lost)
    state.reputation += 3
    state.morale = min(100, state.morale + 10)
    ui.success(
        f"Le galion amène pavillon. {coin} P8 d'argent et de doublons, "
        f"{cargo} de cargaison. {crew_lost} hommes y restent. On en parlera dans les tavernes."
    )
    _maybe_yield_prisoners(state, ui, chance=0.55)

def _resolve_indiaman(state, ui):
    """East Indiaman / navire des Indes orientales — riche prise avec
    passagers de qualité, hommes et femmes. Très bien défendu."""
    from data.prisoners import make_prisoner
    ui.show_scene("events", "indiaman")
    ui.narrate(
        "Une silhouette imposante à l'horizon : trois ponts de batterie, "
        "long château arrière, pavillon de la Compagnie. Un Indiaman, "
        "lourd de soie, d'épices, et de notables embarqués."
    )
    combat = state.get_effective_bonus("combat") * 5
    intim = state.get_effective_bonus("intimidation") * 3
    nav = state.get_effective_bonus("navigation") * 2
    strength = state.crew + combat + intim + nav + random.randint(-10, 20)
    threshold = 130

    choice = ui.choose(
        "L'Indiaman est puissant. Que faites-vous ?",
        [
            ("L'arraisonner", "attack"),
            ("Le pister jusqu'à un coup plus favorable", "stalk"),
            ("Trop dangereux — laisser passer", "leave"),
        ],
    )
    if choice == "leave":
        ui.info("La voile disparaît dans la brume. Pas de honte.")
        return
    if choice == "stalk":
        state.advance_turn()
        ui.info("Vous le pistez un jour. Au crépuscule, le vent tombe — ouverture.")
        strength += 25

    if strength < threshold:
        damage = random.randint(25, 45)
        crew_lost = random.randint(8, 18)
        state.ship["hull_current"] = max(0, state.ship["hull_current"] - damage)
        state.crew = max(0, state.crew - crew_lost)
        state.morale = max(0, state.morale - 12)
        ui.fail(
            f"Les pièces de l'Indiaman ouvrent un bordage. Vous décrochez. "
            f"Coque -{damage}, {crew_lost} morts."
        )
        return

    # Victoire — gros butin et plusieurs notables
    coin = random.randint(300, 600)
    cargo = random.randint(400, 900)
    state.gold += coin
    state.loot += cargo
    state.reputation += 3
    crew_lost = random.randint(5, 12)
    state.crew = max(0, state.crew - crew_lost)
    ui.success(
        f"L'Indiaman se rend. {coin} pièces, {cargo} de cargaison de luxe. "
        f"{crew_lost} hommes perdus à l'abordage."
    )
    # Notables : 3-6 prisonniers, mix M/F avec proportion notable F élevée
    n = random.randint(3, 6)
    pool_M = ["noble_passenger", "merchant_captain", "navy_officer", "clergy"]
    pool_F = ["noble_lady", "merchant_lady", "courtesan"]
    taken = []
    for _ in range(n):
        if random.random() < 0.45:    # plus de femmes sur un Indiaman (familles)
            ptype = random.choice(pool_F)
        else:
            ptype = random.choice(pool_M)
        state.prisoners.append(make_prisoner(ptype, source="East Indiaman capturé"))
        taken.append(ptype)
    from data.prisoners import PRISONER_TYPES
    labels = ", ".join(f"1 × {PRISONER_TYPES[t]['label']}" for t in taken)
    ui.info(f"Notables retenus à bord : {labels}.")

def _resolve_slave_ship(state, ui):
    """Capture d'un négrier — choix moral immédiat.

    Repères historiques : Bartholomew Roberts attaquait régulièrement les
    négriers sur la côte africaine ; les équipages de Sam Bellamy et
    Olivier Levasseur comptaient des hommes d'origine africaine ayant
    rejoint après capture. Le sort des captifs dépendait du capitaine
    et du vote de l'équipage."""
    from data.prisoners import make_prisoner
    ui.show_scene("events", "slave_ship")
    ui.narrate(
        "Trois mâts à l'horizon, ponts surélevés, ouvertures bardées de "
        "grilles sur le faux-pont. Un négrier — l'odeur, perceptible "
        "depuis trois encablures, ne ment pas."
    )
    combat_bonus = state.get_effective_bonus("combat") * 4
    crew_factor = state.crew
    player_strength = crew_factor + combat_bonus + random.randint(0, 30)
    if player_strength < 30:
        ui.fail("Vous n'avez ni les hommes ni les pièces pour l'arraisonner. Laissé filer.")
        return

    crew_lost = random.randint(2, 6)
    state.crew = max(0, state.crew - crew_lost)
    captives_count = random.randint(20, 60)
    ui.narrate(
        f"L'abordage prend deux heures. {crew_lost} de vos hommes restent à terre. "
        f"Dans la cale : {captives_count} Africains enchaînés. La cargaison comprend "
        "aussi du sucre brut et de la poudre d'or de la côte."
    )
    state.loot += random.randint(80, 200)

    choice = ui.choose(
        f"Que décidez-vous pour ces {captives_count} captifs ?",
        [
            ("Briser les fers — proposer les Articles à ceux qui voudront", "liberate"),
            ("Garder en cale pour vente au prochain marché", "hold"),
            ("Les déposer à terre, sans gain (libération sans incorporation)", "release"),
        ],
    )

    if choice == "liberate":
        max_joiners = state.ship["crew_max"] - state.crew
        joiners = min(max_joiners, int(captives_count * random.uniform(0.45, 0.70)))
        state.crew += joiners
        state.morale = min(100, state.morale + 15)
        state.reputation += 2
        state.flags["liberated_slaves"] = state.flags.get("liberated_slaves", 0) + captives_count
        ui.success(
            f"{joiners} signent les Articles sur-le-champ. Les autres demandent "
            "à descendre à la première terre. Le moral grimpe à bord."
        )

    elif choice == "hold":
        for _ in range(captives_count):
            state.prisoners.append(make_prisoner("enslaved_african", source="négrier capturé"))
        state.morale = max(0, state.morale - 6)
        ui.info(
            f"{captives_count} captifs sont entassés dans l'entrepont. "
            "L'air devient irrespirable. Plusieurs hommes de votre équipage "
            "détournent la tête."
        )

    else:  # release
        state.morale = min(100, state.morale + 8)
        state.reputation += 1
        state.flags["liberated_slaves"] = state.flags.get("liberated_slaves", 0) + captives_count
        ui.success(
            "Vous mettez le cap sur la côte la plus proche. Aucun gain en pièces, "
            "mais l'équipage approuve à voix haute."
        )

def _resolve_mughal_treasure_ship(state, ui):
    """Grand navire du Grand Moghol revenant de Moka et de La Mecque, lourd
    d'or, de pierreries et de pèlerins. Repère : Henry Avery captura le
    « Ganj-i-Sawai » en 1695 — le plus riche coup de l'âge d'or, qui déclencha
    une chasse internationale. Adversaire colossal."""
    from data.prisoners import make_prisoner
    ui.show_scene("events", "mughal_treasure_ship")
    ui.narrate(
        "Une montagne de bois doré barre l'horizon de la mer Rouge : un grand "
        "navire du Grand Moghol, de retour de Moka, chargé d'or, d'argent et "
        "de pèlerins. Sa batterie est redoutable — mais sa cale, fabuleuse."
    )
    combat = state.get_effective_bonus("combat") * 6
    nav = state.get_effective_bonus("navigation") * 2
    strength = state.crew + combat + nav + random.randint(-20, 25)
    choice = ui.choose(
        "Tenter le navire moghol ?",
        [
            ("Donner l'assaut, coûte que coûte", "attack"),
            ("Le canonner de loin pour le démâter d'abord", "gunnery"),
            ("Trop gros — renoncer", "leave"),
        ],
    )
    if choice == "leave":
        ui.info("La sagesse l'emporte : un tel mastodonte se paie en sang.")
        return
    if choice == "gunnery":
        if nav >= 4 or random.random() < 0.5:
            strength += 30
            ui.info("Vos bordées hachent son gréement avant l'abordage. Avantage pris.")
        else:
            damage = random.randint(15, 30)
            state.ship["hull_current"] = max(0, state.ship["hull_current"] - damage)
            ui.info(f"Échange de bordées coûteux. Coque -{damage}.")
    if strength < 110:
        damage = random.randint(30, 55)
        crew_lost = random.randint(12, 25)
        state.ship["hull_current"] = max(0, state.ship["hull_current"] - damage)
        state.crew = max(0, state.crew - crew_lost)
        state.morale = max(0, state.morale - 15)
        ui.fail(
            f"Le moghol vous écrase de sa hauteur. Vous rompez. "
            f"Coque -{damage}, {crew_lost} morts, moral -15."
        )
        return
    coin = random.randint(800, 1800)
    cargo = random.randint(400, 900)
    crew_lost = random.randint(10, 22)
    state.gold += coin
    state.loot += cargo
    state.crew = max(0, state.crew - crew_lost)
    state.reputation += 5
    state.morale = min(100, state.morale + 12)
    state.flags["took_mughal_prize"] = True
    ui.success(
        f"Le pavillon moghol s'abaisse. Or, perles, soie : +{coin} P8, "
        f"+{cargo} de cargaison ! {crew_lost} hommes y restent. Votre nom "
        "enfle d'un océan à l'autre — et la chasse contre vous avec lui."
    )
    n = random.randint(2, 5)
    for _ in range(n):
        ptype = random.choice(["noble_passenger", "noble_lady", "merchant_captain", "clergy"])
        state.prisoners.append(make_prisoner(ptype, source="navire moghol"))
    ui.info(f"{n} notables retenus — leur rançon vaudra des fortunes.")

def _resolve_red_sea_convoy(state, ui):
    """La flotte annuelle de Moka — convoi marchand indien et arabe franchissant
    le détroit de Bab-el-Mandeb, que les « Red Sea Men » (Tew, Avery)
    guettaient. Riche, mais souvent escorté."""
    ui.show_scene("events", "red_sea_convoy")
    ui.narrate(
        "À l'entrée de la mer Rouge, une forêt de voiles : la flotte de Moka, "
        "navires indiens et arabes en convoi. Le butin d'une saison entière — "
        "pour qui ose se jeter dans le tas."
    )
    combat = state.get_effective_bonus("combat") * 5
    strength = state.crew + combat + random.randint(-10, 25)
    choice = ui.choose(
        "Comment attaquez-vous le convoi de Moka ?",
        [
            ("Fondre sur un traînard mal escorté", "pick"),
            ("Attendre la nuit pour couper un isolé", "night"),
            ("Laisser passer — trop de voiles", "leave"),
        ],
    )
    if choice == "leave":
        ui.info("Vous laissez le convoi cingler vers Surat. Tant de richesses, tant de risques.")
        return
    if choice == "night":
        state.advance_turn()
        strength += 20
        ui.info("À la faveur de la nuit, vous isolez un gros marchand du convoi.")
    if strength < 70:
        damage = random.randint(15, 30)
        crew_lost = random.randint(5, 12)
        state.ship["hull_current"] = max(0, state.ship["hull_current"] - damage)
        state.crew = max(0, state.crew - crew_lost)
        state.morale = max(0, state.morale - 8)
        ui.fail(f"L'escorte du convoi vous repousse. Coque -{damage}, {crew_lost} morts, moral -8.")
        return
    coin = random.randint(300, 700)
    cargo = random.randint(300, 650)
    crew_lost = random.randint(4, 12)
    state.gold += coin
    state.loot += cargo
    state.crew = max(0, state.crew - crew_lost)
    state.reputation += 3
    state.morale = min(100, state.morale + 8)
    ui.success(
        f"Un marchand de Moka est à vous : café, épices, étoffes. "
        f"+{coin} P8, +{cargo} de cargaison. {crew_lost} morts."
    )
    _maybe_yield_prisoners(state, ui, chance=0.40)

def _resolve_dhow_trader(state, ui):
    """Boutre (dhow) arabe ou swahili, caboteur de l'océan Indien : petite
    prise — épices, ivoire — mais surtout des renseignements sur les grosses
    flottes de Surat et de Moka."""
    ui.show_scene("events", "dhow_trader")
    ui.narrate(
        "Un boutre à voile latine longe la côte, chargé de sacs d'épices, de "
        "défenses d'ivoire et de nattes. Quelques marins swahilis, pas un canon."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Arraisonner — épices et ivoire", "take"),
            ("Troquer pacifiquement contre des nouvelles", "trade"),
            ("Le laisser à son cabotage", "ignore"),
        ],
    )
    if choice == "ignore":
        ui.info("Vous le laissez filer entre les hauts-fonds.")
        return
    if choice == "trade":
        state.flags["surat_intel"] = True
        if state.gold >= 20:
            state.gold -= 20
            state.supplies = min(100, state.supplies + 12)
            ui.success("Troc honnête : vivres +12, et l'on vous indique la route des gros marchands.")
        else:
            ui.info("Peu à troquer, mais les marins parlent : une flotte attendue à Surat.")
        return
    cargo = random.randint(60, 160)
    coin = random.randint(20, 60)
    state.loot += cargo
    state.gold += coin
    state.flags["surat_intel"] = True
    ui.success(f"Petite mais nette : +{cargo} de cargaison, +{coin} P8, et un tuyau sur Surat.")

# -----------------------------------------------------------------
# >>> RENCONTRES EN MER
# Autres équipages, communautés côtières, gens à recueillir.
# -----------------------------------------------------------------

def _resolve_consort_proposal(state, ui):
    """Rencontre d'un autre capitaine pirate qui propose une consort.

    Pratique attestée : Roberts a navigué en consort avec plusieurs sloops ;
    Vane et Yeats ont opéré ensemble en 1718."""
    ui.show_scene("events", "consort")
    ui.narrate(
        "Un sloop hisse le pavillon rouge en signe de reconnaissance. "
        "Son capitaine — un certain Cornelius — propose une consort : "
        "moitié-moitié sur les prises pendant deux mois."
    )
    choice = ui.choose(
        "Accepter la consort ?",
        [
            ("Oui — partage moitié-moitié, deux mois", "yes"),
            ("Non — chacun pour soi", "no"),
        ],
    )
    if choice == "yes":
        for _ in range(2):
            state.advance_turn()
        roll = random.random()
        if roll < 0.55:
            gain = random.randint(300, 700)
            cargo = random.randint(200, 500)
            state.gold += gain
            state.loot += cargo
            state.reputation += 1
            ui.success(f"La consort prospère. Part : {gain} P8 + {cargo} de cargaison.")
        elif roll < 0.85:
            ui.info("Quelques petites prises. Vos parts se valent. Vous repartez.")
            state.gold += 80
        else:
            crew_lost = random.randint(4, 10)
            state.crew = max(0, state.crew - crew_lost)
            state.morale = max(0, state.morale - 10)
            ui.fail(
                f"Cornelius vous trahit en pleine prise. {crew_lost} hommes perdus, "
                "et lui s'enfuit avec la part. Réputation à reconquérir."
            )

def _resolve_rival_careening(state, ui):
    """Surprendre un équipage pirate rival abattu en carène sur une plage,
    navire désarmé. Parlementer, frapper, ou unir les forces. Les Frères de
    la côte alternaient solidarité et rivalité (cf. glossaire)."""
    if state.in_port:
        return
    ui.show_scene("events", "rival_careening")
    ui.narrate(
        "Dans une anse, un sloop est couché en carène, sa coque exposée, ses "
        "canons à terre. Un pavillon noir pend, mou, à un arbre. Un autre "
        "équipage de la côte, pris à découvert."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Les saluer en frères et faire de l'eau ensemble", "parley"),
            ("Profiter de leur faiblesse pour les dépouiller", "strike"),
            ("Leur proposer de se joindre à vous", "recruit"),
        ],
    )
    if choice == "parley":
        state.morale = min(100, state.morale + 4)
        if random.random() < 0.5:
            state.flags["dispatch_intel"] = True
            ui.success("Rhum partagé, nouvelles échangées. Leur capitaine vous tuyaute sur une prise. Moral +4.")
        else:
            ui.success("Salut entre gens de la côte. Aiguade paisible, et l'on se sépare bons amis. Moral +4.")
    elif choice == "strike":
        if state.get_effective_bonus("combat") >= 1 or random.random() < 0.6:
            gain = random.randint(120, 300)
            crew_lost = random.randint(2, 6)
            state.gold += gain
            state.crew = max(0, state.crew - crew_lost)
            state.reputation += 1
            state.morale = max(0, state.morale - 5)
            ui.info(
                f"Vous tombez sur eux désarmés. +{gain} P8, {crew_lost} morts. "
                "Frapper un frère de la côte laisse un goût amer. Moral -5."
            )
        else:
            crew_lost = random.randint(6, 12)
            state.crew = max(0, state.crew - crew_lost)
            state.morale = max(0, state.morale - 8)
            ui.fail(f"Ils s'étaient gardés une embuscade dans les arbres. {crew_lost} morts. Moral -8.")
    else:  # recruit
        joiners = min(state.ship["crew_max"] - state.crew, random.randint(3, 10))
        if joiners <= 0:
            ui.info("Le rôle est plein. Vous vous quittez avec un salut.")
            return
        state.crew += joiners
        state.morale = min(100, state.morale + 3)
        ui.success(f"Leur capitaine las cède : {joiners} hommes passent sous votre pavillon. Moral +3.")

def _resolve_native_canoes(state, ui):
    """Rencontre de pirogues kalinago ou caraïbes."""
    ui.show_scene("events", "native_canoes")
    ui.narrate(
        "Trois pirogues à balancier vous approchent. Hommes peints, lances. "
        "L'un d'eux brandit un éventail de plumes : signe d'échange pacifique."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Troquer (poudre + tissu → vivres frais et fruits)", "trade"),
            ("Les chasser au canon", "shoot"),
        ],
    )
    if choice == "trade":
        if state.gold >= 20:
            state.gold -= 20
            state.supplies = min(100, state.supplies + 20)
            ui.success("Échange honnête. +20 vivres frais, anti-scorbut naturel.")
        else:
            ui.info("Vous n'avez rien à troquer. Ils repartent, déçus.")
    else:
        state.morale = max(0, state.morale - 8)
        state.reputation += 1   # cruauté = réputation pirate, mais moral en chute
        ui.fail(
            "Une décharge. Les pirogues coulent. Vos hommes ne disent rien — "
            "mais le souper se prend en silence."
        )

def _resolve_maroon_camp(state, ui):
    """Communauté de marrons (cimarrones) réfugiée sur la côte. Repère :
    Drake s'allia aux cimarrones près de Panama en 1572-73 ; les Marrons de
    la Jamaïque tinrent tête aux Anglais. Alliance, troc, ou indifférence."""
    ui.show_scene("events", "maroon_camp")
    ui.narrate(
        "Sur une côte abrupte, des feux et des cultures en terrasses : un "
        "village de marrons, esclaves fugitifs organisés en communauté libre. "
        "Des guetteurs armés observent votre mouillage."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Parlementer et proposer une alliance de troc", "ally"),
            ("Troquer poudre et fer contre vivres frais", "trade"),
            ("Lever l'eau au large et ne pas les déranger", "leave"),
        ],
    )
    if choice == "leave":
        state.supplies = min(100, state.supplies + 5)
        ui.info("Aiguade discrète à l'écart. Vivres +5.")
        return
    if choice == "trade":
        if state.gold >= 25:
            state.gold -= 25
            state.supplies = min(100, state.supplies + 22)
            ui.success("Manioc, fruits, gibier fumé contre votre fer. Vivres +22, anti-scorbut.")
        else:
            ui.info("Vous n'avez rien qui les intéresse. Échange courtois mais maigre.")
        return
    # ally
    if state.flags.get("liberated_slaves", 0) > 0 or random.random() < 0.5:
        state.flags["maroon_allies"] = True
        state.supplies = min(100, state.supplies + 15)
        state.morale = min(100, state.morale + 6)
        joiners = min(state.ship["crew_max"] - state.crew, random.randint(0, 4))
        state.crew += joiners
        extra = f" et {joiners} hommes s'engagent" if joiners else ""
        ui.success(f"Pacte conclu : refuge et vivres assurés sur cette côte{extra}. Moral +6.")
    else:
        state.morale = max(0, state.morale - 2)
        ui.info("Méfiants, ils refusent l'alliance mais vous laissent faire de l'eau. Moral -2.")

def _resolve_malagasy_clan(state, ui):
    """Clan betsimisaraka de la côte est de Madagascar. Bien des pirates de la
    Round s'y établirent, prirent femme et alliés locaux (cf. voyages.py).
    Hospitalité au capitaine connu, défiance à l'étranger."""
    ui.show_scene("events", "malagasy_clan")
    ui.narrate(
        "Sur la côte malgache, un village betsimisaraka. Des piroguiers "
        "viennent au-devant de vous : selon votre renom, ce sera l'hospitalité "
        "ou la défiance."
    )
    if state.reputation >= 3 or state.flags.get("maroon_allies"):
        state.supplies = min(100, state.supplies + 18)
        state.morale = min(100, state.morale + 6)
        state.flags["malagasy_allies"] = True
        ui.success("Votre nom les rassure : bœufs, riz, fruits, un mouillage sûr. Vivres +18, moral +6.")
    else:
        choice = ui.choose(
            "Le clan se méfie. Que faites-vous ?",
            [
                ("Offrir des présents pour gagner sa confiance (40 P8)", "gift"),
                ("Faire de l'eau à la hâte et repartir", "leave"),
            ],
        )
        if choice == "gift" and state.gold >= 40:
            state.gold -= 40
            state.supplies = min(100, state.supplies + 15)
            state.reputation += 1
            state.flags["malagasy_allies"] = True
            ui.success("Les présents ouvrent les cœurs. Vivres +15, alliance nouée.")
        else:
            state.supplies = min(100, state.supplies + 5)
            ui.info("Aiguade prudente sous l'œil des guetteurs. Vivres +5.")

def _resolve_logwood_cutters(state, ui):
    """Coupeurs de bois de campêche (« Baymen ») de la baie de Campêche /
    Honduras : population rude, vivier de recrues pour la flibuste. Le bois
    de teinture se vendait cher en Europe."""
    ui.show_scene("events", "logwood_cutters")
    ui.narrate(
        "Dans une lagune bordée de palétuviers, un campement de coupeurs de "
        "bois de campêche : cabanes de feuilles, piles de bûches rouges, "
        "des hommes maigres rongés par les moustiques."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Troquer poudre et rhum contre du bois de teinture", "trade"),
            ("Recruter parmi ces hommes sans attache", "recruit"),
            ("Lever l'eau et repartir", "leave"),
        ],
    )
    if choice == "leave":
        state.supplies = min(100, state.supplies + 8)
        ui.info("Aiguade rapide. Vivres +8.")
        return
    if choice == "trade":
        if state.gold >= 30:
            state.gold -= 30
            state.loot += random.randint(120, 240)
            ui.success("Échange honnête. Du bois de campêche plein la cale, revendable au prix fort.")
        else:
            ui.info("Vous n'avez rien à troquer qui les tente. Ils retournent à leurs bûches.")
        return
    joiners = min(state.ship["crew_max"] - state.crew, random.randint(2, 6))
    if joiners <= 0:
        ui.info("Le rôle est plein. Vous repartez avec un baril d'eau de plus.")
        return
    state.crew += joiners
    state.morale = min(100, state.morale + 3)
    ui.success(f"{joiners} coupeurs lâchent la hache pour le pavillon noir. La vie y est moins dure.")

def _resolve_marooned_sailor(state, ui):
    """Un homme marronné par un autre équipage, retrouvé sur un îlot.
    Le marronnage était la peine pirate par excellence ; en recueillir la
    victime peut rapporter un homme reconnaissant — ou des ennuis."""
    ui.show_scene("events", "marooned_sailor")
    ui.narrate(
        "Sur un banc de sable nu, une silhouette agite une chemise au bout "
        "d'un bâton. Un homme marronné, brûlé de soleil, à demi fou de soif. "
        "Un pistolet vide pend à sa ceinture — la coutume du Code."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Le recueillir à bord", "rescue"),
            ("Lui jeter une outre d'eau et reprendre la route", "water"),
            ("Passer sans s'arrêter", "ignore"),
        ],
    )
    if choice == "ignore":
        state.morale = max(0, state.morale - 4)
        ui.info("Vous laissez l'îlot derrière vous. Vos hommes y songent : ce pourrait être eux. Moral -4.")
        return
    if choice == "water":
        state.morale = min(100, state.morale + 2)
        ui.info("Une outre lui tombe sur le sable. Geste de mer. Vous reprenez la route.")
        return
    if state.crew >= state.ship["crew_max"]:
        ui.info("Le rôle est plein ; vous le débarquerez au prochain port. Au moins est-il vivant.")
        state.morale = min(100, state.morale + 3)
        return
    state.crew += 1
    state.morale = min(100, state.morale + 5)
    if random.random() < 0.3:
        rumor = random.choice([
            "Il connaît la cache où son ancien capitaine a enterré son or.",
            "Il jure savoir la route d'un riche caboteur attendu sous peu.",
        ])
        ui.success(f"Repêché et reconnaissant : « {rumor} » Moral +5.")
    else:
        ui.success("Un bras de plus, et un homme qui vous doit la vie. Moral +5.")

def _resolve_man_overboard(state, ui):
    """Homme à la mer en pleine manœuvre — drame quotidien de la marine à
    voile. Le repêcher coûte du temps et un risque ; l'abandonner, du moral."""
    if state.crew < 8:
        return
    ui.show_scene("events", "man_overboard")
    ui.narrate(
        "« Un homme à la mer ! » Un gabier a lâché la vergue dans un coup de "
        "roulis. Sa tête paraît et disparaît dans le sillage."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Virer de bord et mettre la chaloupe à l'eau", "rescue"),
            ("Continuer — on ne risque pas le navire pour un homme", "abandon"),
        ],
    )
    if choice == "abandon":
        state.crew = max(0, state.crew - 1)
        state.morale = max(0, state.morale - 6)
        ui.fail("Le navire poursuit sa route. Le silence à bord est lourd. Moral -6.")
        return
    nav = state.get_effective_bonus("navigation")
    if nav >= 1 or random.random() < 0.6:
        state.morale = min(100, state.morale + 6)
        ui.success("Belle manœuvre : la chaloupe le récupère, recraché mais vivant. Moral +6.")
    else:
        state.crew = max(0, state.crew - 1)
        ui.info("La mer est plus rapide que vous. Vous le perdez — mais l'équipage a vu que vous avez tenté.")

def _resolve_castaways(state, ui):
    """Survivants d'un naufrage dérivant sur un radeau ou une embarcation —
    distincts de l'épave vide. Recueillir peut donner des bras, des notables
    monnayables, ou simplement la satisfaction d'un geste de mer."""
    from data.prisoners import make_prisoner
    ui.show_scene("events", "castaways")
    ui.narrate(
        "Un radeau de fortune, gréé d'une chemise en guise de voile. Cinq "
        "ou six naufragés, lèvres craquelées, agitent les bras. Les rescapés "
        "d'un navire perdu corps et biens."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Les recueillir tous à bord", "rescue"),
            ("Donner de l'eau et un cap, sans embarquer", "water"),
            ("Détourner la lunette et poursuivre", "ignore"),
        ],
    )
    if choice == "ignore":
        state.morale = max(0, state.morale - 5)
        ui.info("Vous les laissez à leur radeau. Le malaise plane sur le bord. Moral -5.")
        return
    if choice == "water":
        state.morale = min(100, state.morale + 2)
        ui.info("Eau et biscuits passés bord à bord, un cap donné. Geste de mer.")
        return
    state.morale = min(100, state.morale + 5)
    n = random.randint(2, 5)
    sailors = 0
    for _ in range(n):
        r = random.random()
        if r < 0.6 and state.crew < state.ship["crew_max"]:
            state.crew += 1
            sailors += 1
        elif r < 0.8:
            state.prisoners.append(make_prisoner("merchant_captain", source="naufragés recueillis"))
        else:
            state.prisoners.append(make_prisoner("noble_passenger", source="naufragés recueillis"))
    note = f"{sailors} matelot(s) s'engagent" if sailors else "aucun marin parmi eux"
    ui.success(f"Les naufragés montent à bord, reconnaissants : {note}. Moral +5.")

def _resolve_navy_deserter(state, ui):
    """Un déserteur de la Navy nage jusqu'à votre bord : artilleur ou gabier
    aguerri, fuyant le fouet et la solde volée. Les équipages pirates en
    regorgeaient."""
    ui.show_scene("events", "navy_deserter")
    ui.narrate(
        "Une tête émerge dans votre sillage : un homme a sauté d'un vaisseau "
        "du roi mouillé à l'écart et nage vers vous. Artilleur, dit-il, las du "
        "fouet et de la solde volée."
    )
    if state.crew >= state.ship["crew_max"]:
        state.morale = min(100, state.morale + 2)
        ui.info("Le rôle est plein ; vous le hissez tout de même à bord, surnuméraire reconnaissant.")
        return
    choice = ui.choose(
        "Le prenez-vous ?",
        [
            ("L'inscrire au rôle — un bon canonnier vaut de l'or", "take"),
            ("Le refuser — un déserteur peut être un mouchard", "refuse"),
        ],
    )
    if choice == "refuse":
        ui.info("Vous lui jetez une planche et reprenez la route. Il regagne la côte, dépité.")
        return
    state.crew += 1
    if random.random() < 0.85:
        state.morale = min(100, state.morale + 4)
        ui.success("Un artilleur aguerri de plus, qui connaît les manies de la Navy. Moral +4.")
    else:
        state.morale = max(0, state.morale - 3)
        ui.info("L'homme se révèle vantard et chicanier — un bras de plus, mais des grognes aussi. Moral -3.")

def _resolve_lady_in_peril(state, ui):
    """Dame en péril — rescousse d'une captive d'un autre pirate.

    Repère historique : la rumeur de viol et de mauvais traitements des
    prisonnières par les pirates apparaît dans plusieurs procès (Vane,
    Low), mais d'autres équipages (Roberts) avaient des Articles
    explicitement protecteurs. Les rescousses par des capitaines
    « gentilshommes » sont attestées."""
    from data.prisoners import make_prisoner
    ui.show_scene("events", "lady_in_peril")
    ui.narrate(
        "Vous croisez un sloop battant pavillon noir mal tenu. Un canot "
        "vous accoste depuis le large : un mousse, terrorisé. Il décrit "
        "le capitaine — un certain Sykes — et une jeune dame française "
        "retenue à bord depuis trois semaines."
    )
    speed = state.ship["speed"] + state.get_effective_bonus("speed_bonus")
    combat = state.get_effective_bonus("combat")
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Aborder Sykes pour libérer la dame", "rescue"),
            ("Lui proposer un rachat de la captive (200 P8)", "buy"),
            ("Passer son chemin", "ignore"),
        ],
    )
    if choice == "ignore":
        state.morale = max(0, state.morale - 3)
        ui.info("Vous reprenez votre route. Le mousse retourne à son sort.")
        return

    if choice == "buy":
        if state.gold < 200:
            ui.fail("Pas les 200 pièces. Sykes ne marchande pas.")
            return
        state.gold -= 200
        # La dame devient votre prisonnière
        p = make_prisoner("noble_lady", source="rachetée à Sykes")
        state.prisoners.append(p)
        ui.success(
            "Sykes empoche les 200 pièces. La dame — Mademoiselle de Sainte-Aulaire — "
            "est transbordée. Elle vous remercie d'un signe de tête sec."
        )
        return

    # Rescue
    if combat + (speed >= 7) >= 2 or random.random() > 0.4:
        crew_lost = random.randint(2, 6)
        state.crew = max(0, state.crew - crew_lost)
        ui.success(
            f"Sykes mort, son sloop pris. {crew_lost} hommes perdus à l'abordage."
        )
        gain = random.randint(80, 200)
        state.gold += gain
        ui.info(f"+{gain} P8 récupérés sur Sykes.")
        # Choix : rendre la dame à sa famille (réputation) ou la garder pour rançon
        sub = ui.choose(
            "Que faites-vous de Mlle de Sainte-Aulaire ?",
            [
                ("La conduire à la famille — sans réclamer la rançon", "return"),
                ("La garder à bord et envoyer notre propre demande de rançon", "ransom"),
            ],
        )
        if sub == "return":
            state.morale = min(100, state.morale + 12)
            state.reputation += 2
            state.flags["sainte_aulaire_saved"] = True
            ui.success(
                "Vous la déposez en Martinique. Sa famille en garde mémoire ; "
                "l'équipage approuve."
            )
        else:
            p = make_prisoner("noble_lady", source="sauvée de Sykes")
            state.prisoners.append(p)
            ui.info("Mlle de Sainte-Aulaire est ajoutée à votre liste de notables.")
    else:
        damage = random.randint(15, 30)
        crew_lost = random.randint(6, 12)
        state.ship["hull_current"] = max(0, state.ship["hull_current"] - damage)
        state.crew = max(0, state.crew - crew_lost)
        ui.fail(
            f"L'abordage tourne mal. Sykes s'enfuit avec la dame. "
            f"Coque -{damage}, {crew_lost} morts."
        )

# -----------------------------------------------------------------
# >>> TRÉSOR, ÉPAVES & LÉGENDES
# Épaves, caches, bouteilles à la mer et navires fantômes.
# -----------------------------------------------------------------

def _resolve_wreck(state, ui):
    ui.show_scene("events", "wreck")
    ui.narrate(
        "La vigie hèle : une carcasse de navire échouée sur un récif. "
        "Le pavillon est en lambeaux. Personne en vue."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Envoyer la chaloupe fouiller l'épave", "search"),
            ("Continuer la route", "ignore"),
        ],
    )
    if choice == "ignore":
        ui.info("Vous passez au large. Peut-être un piège évité.")
        return
    roll = random.random()
    if roll < 0.6:
        booty = random.randint(50, 200)
        ui.success(f"Vivres, poudre et un coffre. {booty} pièces de huit récupérées.")
        state.gold += booty
        state.supplies = min(100, state.supplies + 10)
        # Matières premières échouées : à rapporter au repaire si on en a un.
        hold = getattr(state, "cargo_hold", None)
        if hold is not None:
            import random as _r
            from data.resources import RESOURCES as _RES
            # 1 à 3 types différents, petites quantités
            for rid in _r.sample(list(_RES.keys()), k=_r.randint(1, 3)):
                qty = _r.randint(2, 6)
                room = max(0, state.ship.get("cargo", 0) * 15 - sum(hold.values()))
                added = min(qty, room)
                if added > 0:
                    hold[rid] = hold.get(rid, 0) + added
                    ui.info(f"  +{added} {_RES[rid]['label']} (cale).")
                if room <= 0:
                    ui.info("  La cale déborde : le reste est laissé à la mer.")
                    break
    elif roll < 0.85:
        ui.info("L'épave est nettoyée. Rien à prendre.")
    else:
        crew_lost = random.randint(2, 6)
        ui.fail(
            "Embuscade ! Des survivants armés se cachaient dans l'entrepont. "
            f"Vous perdez {crew_lost} hommes avant de reprendre le dessus."
        )
        state.crew = max(0, state.crew - crew_lost)

def _resolve_buried_treasure(state, ui):
    """Cache enterrée, retrouvée grâce à un renseignement accumulé (rumeur
    de taverne, dépêche, tuyau de Sainte-Marie). L'or enterré relevait plus
    de la légende que de la pratique — mais Kidd a bel et bien enfoui une
    partie de son butin à Gardiners Island en 1699, repère que le jeu
    exploite ici."""
    has_intel = any(state.flags.get(f) for f in
                    ("dispatch_intel", "surat_intel", "war_intel"))
    ui.show_scene("events", "buried_treasure")
    if not has_intel:
        ui.narrate(
            "Un vieux plan griffonné, acheté trois sols à un mourant, vous a "
            "mené à cet îlot. Trois palmiers, un rocher fendu — et rien qui "
            "ressemble aux repères tracés. La piste est froide."
        )
        if random.random() < 0.35:
            gain = random.randint(40, 120)
            state.gold += gain
            ui.success(f"Sous une dalle, un petit coffre tout de même : +{gain} P8.")
        else:
            state.advance_turn()
            state.morale = max(0, state.morale - 4)
            ui.info("Une journée à creuser le sable pour rien. Les hommes maugréent. Moral -4.")
        return
    ui.narrate(
        "Recoupant vos renseignements, vous gagnez un mouillage discret. Au "
        "pied d'un manguier marqué d'une croix gravée, la pelle sonne creux : "
        "un coffre cerclé de fer."
    )
    # Consomme un renseignement
    for f in ("dispatch_intel", "surat_intel", "war_intel"):
        if state.flags.get(f):
            state.flags[f] = False
            break
    if random.random() < 0.8:
        gain = random.randint(250, 600)
        state.gold += gain
        state.morale = min(100, state.morale + 10)
        state.reputation += 1
        ui.success(f"Pièces de huit, doublons, un peu d'argenterie : +{gain} P8 ! Moral +10.")
    else:
        crew_lost = random.randint(2, 5)
        state.crew = max(0, state.crew - crew_lost)
        state.morale = max(0, state.morale - 8)
        ui.fail(
            "Le coffre était un appât : ceux qui l'ont enterré attendaient en "
            f"embuscade dans les palétuviers. {crew_lost} morts. Moral -8."
        )

def _resolve_salvage_wreck(state, ui):
    """Renflouage d'une épave engloutie sur un récif. Repère historique :
    William Phips, en 1687, repêcha une fortune sur la « Concepción »
    coulée au large d'Hispaniola. Plongée en apnée, dangereuse."""
    ui.show_scene("events", "salvage_wreck")
    ui.narrate(
        "Par eau claire, sur un haut-fond, la membrure d'un navire coulé se "
        "devine à quatre brasses. Espagnol, à voir ses canons couverts de "
        "corail. Sa cale n'a peut-être pas tout rendu à la mer."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Faire plonger les hommes en apnée pour fouiller", "dive"),
            ("Marquer l'endroit et passer — trop risqué", "mark"),
        ],
    )
    if choice == "mark":
        state.flags["dispatch_intel"] = True
        ui.info("Vous relevez la position. On y reviendra avec le matériel qu'il faut.")
        return
    state.advance_turn()
    roll = random.random()
    if roll < 0.6:
        gain = random.randint(150, 400)
        state.gold += gain
        state.morale = min(100, state.morale + 6)
        ui.success(f"Les plongeurs remontent argenterie et pièces : +{gain} P8. Moral +6.")
    elif roll < 0.85:
        ui.info("La mer a déjà tout pris ou tout dispersé. Beaucoup d'efforts, peu de prise.")
    else:
        crew_lost = random.randint(1, 3)
        state.crew = max(0, state.crew - crew_lost)
        state.morale = max(0, state.morale - 6)
        ui.fail(
            f"Les requins rôdaient sous la coque. {crew_lost} plongeur(s) ne "
            "remontent pas. Moral -6."
        )

def _resolve_message_in_bottle(state, ui):
    """Bouteille à la mer — appel de détresse, fragment de carte, ou
    plaisanterie de gabier. Petit événement d'atmosphère et d'amorce."""
    ui.show_scene("events", "message_in_bottle")
    ui.narrate(
        "Une bouteille cachetée à la cire flotte contre la coque. Dedans, un "
        "papier jauni d'eau de mer."
    )
    roll = random.random()
    if roll < 0.4:
        state.flags["dispatch_intel"] = True
        ui.success("Un fragment de carte avec une croix et des relèvements. Soigneusement rangé.")
    elif roll < 0.7:
        rumor = random.choice([
            "Un appel de naufragés sur un îlot sans nom, daté de l'an passé.",
            "La confession d'un mourant : un magot caché « sous le troisième palmier ».",
            "Un billet d'amour jamais parvenu. Les hommes en rient toute la soirée.",
        ])
        state.morale = min(100, state.morale + 3)
        ui.info(f"« {rumor} » Moral +3.")
    else:
        ui.info("De l'eau de mer et de l'encre délavée. Illisible. À la mer.")

def _resolve_ghost_ship(state, ui):
    """Navire intact dérivant toutes voiles dehors, sans âme à bord — peste,
    mutinerie ou abandon dans la panique. Les marins y voyaient un présage
    funeste. Fouiller, c'est risquer la contagion."""
    ui.show_scene("events", "ghost_ship")
    ui.narrate(
        "Toutes voiles dehors, un navire dérive en travers du vent. Vous le "
        "hélez : nul ne répond. Pont désert, écoutilles béantes, table encore "
        "mise. Pas un cadavre, pas une explication."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Fouiller le navire abandonné", "board"),
            ("Le prendre en remorque comme prise", "tow"),
            ("Fuir ce mauvais présage", "flee"),
        ],
    )
    if choice == "flee":
        state.morale = max(0, state.morale - 3)
        ui.info("Les hommes se signent. On laisse le navire à ses fantômes. Moral -3.")
        return
    if choice == "board":
        roll = random.random()
        if roll < 0.5:
            gain = random.randint(80, 220)
            cargo = random.randint(50, 150)
            state.gold += gain
            state.loot += cargo
            ui.success(f"Cale pleine, abandonnée dans la panique : +{gain} P8 et +{cargo} de cargaison.")
        elif roll < 0.8:
            ui.info("Rien que des effets personnels et un journal s'arrêtant net. Glaçant.")
        else:
            losses = max(1, state.crew // 12)
            state.crew = max(0, state.crew - losses)
            state.morale = max(0, state.morale - 10)
            ui.fail(
                f"L'équipage avait fui une fièvre — qui rôde encore à bord. "
                f"{losses} des vôtres tombent malades. Moral -10."
            )
        return
    state.advance_turn()
    if random.random() < 0.6:
        gain = random.randint(120, 300)
        state.gold += gain
        ui.success(f"Remorqué jusqu'à un mouillage et dépecé : +{gain} P8 de coque et de gréement.")
    else:
        state.morale = max(0, state.morale - 5)
        ui.info("La remorque casse dans la nuit ; le navire fantôme disparaît. Temps perdu, moral -5.")

# -----------------------------------------------------------------
# >>> ÉQUIPAGE, DISCIPLINE & CRISES DU BORD
# Le Code, le partage, les querelles et les soulèvements.
# -----------------------------------------------------------------

def _resolve_mutiny_threat(state, ui):
    if state.morale > 35:
        return
    ui.show_scene("events", "mutiny")
    ui.narrate(
        "Le quartier-maître vous demande audience. Les hommes murmurent. "
        "Trop de mois sans prise, les parts s'amenuisent."
    )
    choice = ui.choose(
        "Comment réagissez-vous ?",
        [
            ("Distribuer une avance sur le trésor (100 pièces)", "pay"),
            ("Promettre une nouvelle expédition", "promise"),
            ("Faire fouetter le meneur", "punish"),
        ],
    )
    if choice == "pay" and state.gold >= 100:
        state.gold -= 100
        state.morale = min(100, state.morale + 20)
        ui.success("L'or apaise les esprits. Le code est respecté.")
    elif choice == "pay":
        ui.fail("Vous n'avez pas 100 pièces. Les hommes en concluent que le capitaine ment.")
        state.morale = max(0, state.morale - 15)
    elif choice == "promise":
        state.morale = min(100, state.morale + 5)
        ui.info("Les hommes grognent mais retournent à leurs postes.")
    else:
        leadership = state.get_effective_bonus("leadership")
        intimidation = state.get_effective_bonus("intimidation")
        if leadership + intimidation >= 2:
            state.morale = max(0, state.morale - 5)
            ui.info("L'exemple porte. Le silence retombe, mais lourd.")
        else:
            state.morale = max(0, state.morale - 20)
            ui.fail("Sept hommes désertent à la prochaine escale.")
            state.crew = max(0, state.crew - 7)

def _resolve_division_of_spoils(state, ui):
    """Partage du butin selon les Articles (Roberts, art. 10 : capitaine et
    quartier-maître deux parts, etc. — cf. appendice du repository). Tenir
    le partage équitable cimente l'équipage ; se servir d'abord le défait."""
    if state.loot < 80:
        return
    ui.show_scene("events", "division_of_spoils")
    ui.narrate(
        "La prise vendue, le quartier-maître étale les parts sur le grand "
        "panneau. Tous les yeux sont sur vos mains. Les Articles sont clairs : "
        "deux parts au capitaine, deux au quartier-maître, une à chaque homme."
    )
    choice = ui.choose(
        "Comment partagez-vous ?",
        [
            ("Au plus juste, selon les Articles", "fair"),
            ("Vous réserver discrètement une part de plus", "skim"),
        ],
    )
    if choice == "fair":
        state.morale = min(100, state.morale + 10)
        ui.success("Partage net, à la part. L'équipage vous tient pour un capitaine d'honneur. Moral +10.")
    else:
        bonus = int(state.loot * 0.12)
        state.gold += bonus
        leadership = state.get_effective_bonus("leadership")
        if leadership >= 2 or random.random() < 0.4:
            state.morale = max(0, state.morale - 6)
            ui.info(f"+{bonus} P8 détournés. Quelques regards lourds, mais nul n'ose parler. Moral -6.")
        else:
            state.morale = max(0, state.morale - 16)
            ui.fail(
                f"+{bonus} P8 détournés — mais le quartier-maître a compté. "
                "« Un capitaine n'est qu'un homme à qui l'on a confié deux parts. » Moral -16."
            )

def _resolve_duel_ashore(state, ui):
    """Querelle entre deux hommes. Les Articles interdisent de se battre à
    bord (Roberts, art. 8) : le différend se vide à terre, au pistolet puis
    au coutelas, sous l'arbitrage du quartier-maître."""
    if state.crew < 12:
        return
    ui.show_scene("events", "duel_ashore")
    ui.narrate(
        "Deux hommes en sont venus aux mains pour une part de butin. Le Code "
        "défend de frapper à bord : la querelle doit se vider à terre, "
        "dos à dos, au commandement du quartier-maître."
    )
    choice = ui.choose(
        "Que décidez-vous ?",
        [
            ("Laisser le quartier-maître arbitrer le duel à terre", "duel"),
            ("Imposer une réconciliation forcée", "reconcile"),
        ],
    )
    if choice == "duel":
        if random.random() < 0.5:
            ui.info("Premier sang au coutelas, sans mort. L'affaire est close, la discipline tient.")
            state.morale = min(100, state.morale + 3)
        else:
            state.crew = max(0, state.crew - 1)
            ui.info("Une balle de pistolet règle tout. Un homme en terre, mais le Code respecté.")
    else:
        leadership = state.get_effective_bonus("leadership")
        if leadership >= 1 or random.random() < 0.5:
            state.morale = min(100, state.morale + 2)
            ui.info("Votre autorité suffit : les deux hommes se serrent la main, à contrecœur.")
        else:
            state.morale = max(0, state.morale - 8)
            ui.fail("Bafouer le Code déplaît. « Le capitaine se croit roi. » Moral -8.")

def _resolve_thief_among_us(state, ui):
    """Un homme a volé sur la part commune. Les Articles (Roberts, art. 2)
    prévoient le marronnage, ou le nez et les oreilles fendus. L'équipage
    attend justice."""
    if state.crew < 10:
        return
    ui.show_scene("events", "thief_among_us")
    ui.narrate(
        "Le quartier-maître traîne un homme devant vous : il a soustrait des "
        "pièces à la part commune. Les Articles ne laissent guère de choix — "
        "et l'équipage, rassemblé, attend votre sentence."
    )
    choice = ui.choose(
        "Quelle sentence ?",
        [
            ("Le marronner sur un îlot, selon le Code", "maroon"),
            ("Le faire fouetter et le garder au rôle", "flog"),
            ("Lui pardonner — la clémence du capitaine", "pardon"),
        ],
    )
    if choice == "maroon":
        state.crew = max(0, state.crew - 1)
        state.morale = min(100, state.morale + 6)
        ui.info("Un mousquet, une bouteille d'eau, un îlot. Le Code est appliqué. L'équipage approuve.")
    elif choice == "flog":
        state.morale = min(100, state.morale + 2)
        ui.info("Le fouet siffle au cabestan. Brutal, mais l'homme reste un bras de plus.")
    else:
        if random.random() < 0.5:
            state.morale = max(0, state.morale - 10)
            ui.fail("Pardonner un voleur ? L'équipage y voit faiblesse. Moral -10.")
        else:
            state.morale = min(100, state.morale + 4)
            ui.info("Votre clémence étonne ; le gracié vous sera dévoué. Moral +4.")

def _resolve_gambling_dispute(state, ui):
    """Jeu d'argent à bord — formellement interdit par les Articles (Roberts,
    art. 3 : « None shall game for money »), justement parce qu'il engendrait
    rixes et dettes. Une partie de dés a mal tourné."""
    if state.crew < 12:
        return
    ui.show_scene("events", "gambling_dispute")
    ui.narrate(
        "Des dés roulent dans l'entrepont malgré l'interdit du Code. Une "
        "dette de jeu a dégénéré : deux clans se forment, couteaux sortis."
    )
    choice = ui.choose(
        "Comment tranchez-vous ?",
        [
            ("Confisquer les dés et rappeler l'Article du Code", "enforce"),
            ("Fermer les yeux — ce ne sont que des dés", "ignore"),
        ],
    )
    if choice == "enforce":
        leadership = state.get_effective_bonus("leadership")
        if leadership >= 1 or random.random() < 0.6:
            state.morale = min(100, state.morale + 4)
            ui.success("Dés par-dessus bord, Article relu à voix haute. La paix revient. Moral +4.")
        else:
            state.morale = max(0, state.morale - 4)
            ui.info("Les joueurs grognent contre la rigueur, mais rangent leurs couteaux. Moral -4.")
    else:
        if random.random() < 0.5:
            state.crew = max(0, state.crew - 1)
            state.morale = max(0, state.morale - 8)
            ui.fail("La rixe éclate à la nuit. Un homme reçoit un coup de couteau. Moral -8.")
        else:
            state.morale = max(0, state.morale - 3)
            ui.info("La dispute couve sans éclater. L'entrepont reste tendu. Moral -3.")

def _resolve_musicians(state, ui):
    """Une prise comptait des musiciens. Les Articles de Roberts (art. 11)
    réglaient leur sort : repos le seul jour du Sabbat. La musique tenait
    le moral et rythmait l'abordage."""
    if state.crew < 15 or state.flags.get("has_musicians"):
        return
    from data.prisoners import make_prisoner
    ui.show_scene("events", "musicians")
    ui.narrate(
        "Parmi les prisonniers du dernier abordage, deux ménétriers : un "
        "violoneux et un joueur de fifre. Ils tremblent — on sait que les "
        "pirates gardent volontiers leurs musiciens."
    )
    choice = ui.choose(
        "Que faites-vous d'eux ?",
        [
            ("Les enrôler — musique tous les jours, sauf le Sabbat", "keep"),
            ("Les débarquer au prochain port", "release"),
        ],
    )
    if choice == "keep":
        state.flags["has_musicians"] = True
        state.morale = min(100, state.morale + 8)
        ui.success("Le violon grince, le fifre s'égosille. Le bord retrouve de l'allant. Moral +8.")
    else:
        state.morale = min(100, state.morale + 2)
        ui.info("Vous les rendez à terre. L'équipage le regrette un peu.")

def _resolve_stowaway(state, ui):
    """Passager clandestin découvert dans la cale — souvent un engagé en
    fuite (« indentured servant ») ou un débiteur échappant à sa servitude,
    deux profils qui grossissaient bel et bien les rangs de la flibuste."""
    if state.flags.get("stowaway_done"):
        return
    ui.show_scene("events", "stowaway")
    ui.narrate(
        "En roulant un baril, on déloge un clandestin tapi dans la cale : un "
        "engagé en fuite, échappé d'une plantation où on le tenait quasi "
        "esclave. Il supplie qu'on le garde plutôt que de le rendre."
    )
    choice = ui.choose(
        "Que faites-vous de lui ?",
        [
            ("Lui offrir une place aux Articles", "keep"),
            ("Le faire travailler à fond de cale, sans part", "labor"),
            ("Le débarquer au prochain port", "drop"),
        ],
    )
    state.flags["stowaway_done"] = True
    if choice == "keep":
        if state.crew < state.ship["crew_max"]:
            state.crew += 1
            state.morale = min(100, state.morale + 4)
            ui.success("Il signe d'une croix, les larmes aux yeux. Un homme libre de plus au rôle. Moral +4.")
        else:
            ui.info("Le rôle est plein ; il servira comme surnuméraire jusqu'à une place libre.")
    elif choice == "labor":
        state.morale = max(0, state.morale - 3)
        ui.info("Pompes et corvées, sans part. L'équipage juge le procédé peu fraternel. Moral -3.")
    else:
        ui.info("Vous le débarquerez discrètement. Il vous maudit à voix basse.")

def _resolve_prize_crew(state, ui):
    """Conserver une prise impose d'y détacher un équipage de prise — autant
    de bras en moins, et le risque qu'ils s'évaporent avec le navire."""
    if state.crew < 25 or state.loot < 100:
        return
    ui.show_scene("events", "prize_crew")
    ui.narrate(
        "La dernière prise vaut mieux qu'on la mène au marché que de la "
        "dépouiller en hâte. Mais l'armer d'un équipage de prise, c'est se "
        "priver de bras — et parier sur leur fidélité."
    )
    choice = ui.choose(
        "Que faites-vous de la prise ?",
        [
            ("Détacher un équipage de prise pour la vendre au port", "man"),
            ("La dépouiller et la saborder sur-le-champ", "strip"),
        ],
    )
    if choice == "strip":
        bump = min(state.loot, random.randint(60, 140))
        state.gold += int(bump * 0.5)
        ui.success(f"Dépouillée jusqu'à l'os, puis sabordée. +{int(bump * 0.5)} P8 du plus portable.")
        return
    detached = min(state.crew // 5, random.randint(4, 10))
    state.crew = max(0, state.crew - detached)
    state.advance_turn()
    if random.random() < 0.75:
        gain = random.randint(200, 450)
        state.gold += gain
        state.crew += detached
        state.reputation += 1
        ui.success(
            f"La prise vendue au port, l'équipage de prise vous rejoint : "
            f"+{gain} P8, {detached} hommes de retour."
        )
    else:
        state.morale = max(0, state.morale - 6)
        ui.fail(
            f"L'équipage de prise a filé avec le navire et son chargement. "
            f"{detached} hommes et la prise envolés. Moral -6."
        )

def _resolve_design_colours(state, ui):
    """Concevoir ses propres couleurs : chaque grand capitaine avait son
    pavillon (Roberts, Teach, Rackham). Un emblème qui terrifie vaut une
    bordée. Événement unique."""
    if state.flags.get("colours_chosen"):
        return
    ui.show_scene("events", "design_colours")
    ui.narrate(
        "L'équipage veut ses propres couleurs — un pavillon qui glace le sang "
        "avant la première bordée. Le voilier déroule sa toile noire, "
        "aiguille en main."
    )
    choice = ui.choose(
        "Quel emblème pour votre pavillon ?",
        [
            ("Tête de mort sur tibias croisés", "skull"),
            ("Squelette tenant un sablier — l'heure est comptée", "hourglass"),
            ("Cœur transpercé saignant — quartier ou mort", "heart"),
        ],
    )
    state.flags["colours_chosen"] = choice
    state.morale = min(100, state.morale + 6)
    state.reputation += 1
    motifs = {
        "skull": "la tête de mort classique, lisible de loin",
        "hourglass": "le squelette au sablier, promesse que le temps presse",
        "heart": "le cœur saignant, qui ne laisse guère espérer quartier",
    }
    ui.success(f"Vos couleurs sont hissées : {motifs[choice]}. L'équipage gronde de fierté. Moral +6, réputation +1.")

def _resolve_slave_revolt(state, ui):
    """Révolte des captifs entassés en cale — conséquence directe de les y
    garder enchaînés (suite possible du choix « garder » lors d'une prise de
    négrier). Le capitaine tranche : libérer, mater, ou débarquer."""
    captives = _count_captives(state)
    if captives <= 0:
        return
    ui.show_scene("events", "slave_revolt")
    ui.narrate(
        "Dans l'entrepont, les captifs enchaînés depuis le négrier ont brisé "
        "un fer. La révolte gronde, sourde, prête à éclater dans le noir."
    )
    choice = ui.choose(
        "Comment réagissez-vous ?",
        [
            ("Briser les fers et leur proposer les Articles", "free"),
            ("Mater la révolte par la force", "crush"),
            ("Négocier : les débarquer à la prochaine terre", "release"),
        ],
    )
    if choice == "free":
        joiners = min(state.ship["crew_max"] - state.crew, int(captives * random.uniform(0.4, 0.7)))
        joiners = max(0, joiners)
        state.crew += joiners
        _remove_captives(state, captives)
        state.morale = min(100, state.morale + 12)
        state.reputation += 2
        state.flags["liberated_slaves"] = state.flags.get("liberated_slaves", 0) + captives
        ui.success(f"Vous libérez les captifs ; {joiners} signent les Articles. L'entrepont respire. Moral +12.")
    elif choice == "crush":
        crew_lost = random.randint(1, 5)
        killed = max(1, captives // 3)
        state.crew = max(0, state.crew - crew_lost)
        _remove_captives(state, killed)
        state.morale = max(0, state.morale - 12)
        state.reputation += 1
        ui.fail(
            f"La révolte est noyée dans le sang. {crew_lost} des vôtres "
            "blessés, et l'horreur pèse sur le bord. Moral -12."
        )
    else:
        _remove_captives(state, captives)
        state.morale = min(100, state.morale + 5)
        state.flags["liberated_slaves"] = state.flags.get("liberated_slaves", 0) + captives
        ui.info("Vous mettez le cap sur la côte et débarquez les captifs. Sans gain, mais le calme revient. Moral +5.")

# -----------------------------------------------------------------
# >>> SANTÉ & MALADIES
# Scorbut, fièvres, blessures et vermine.
# -----------------------------------------------------------------

def _resolve_scurvy(state, ui):
    # Mahalia et le chirurgien immunisent du scorbut
    if state.has_trait("scurvy_resist"):
        ui.narrate(
            "Quelques bouches saignent, mais les tisanes d'herbes et de "
            "citron tiennent le scorbut à distance. L'équipage tient."
        )
        return
    ui.show_scene("events", "scurvy")
    ui.narrate(
        "Les gencives saignent, les dents bougent, les jambes enflent. "
        "Le scorbut s'installe à bord. Faute de vivres frais, les hommes "
        "tombent les uns après les autres."
    )
    losses = max(1, state.crew // 12)
    # Chirurgien / Margot peuvent sauver une partie
    save_chance = state.get_modifier("crew_save_chance", 0.0)
    if save_chance > 0 and random.random() < save_chance:
        saved = losses // 2
        losses -= saved
        ui.info(f"Le chirurgien en sauve {saved}.")
    state.crew = max(0, state.crew - losses)
    state.morale = max(0, state.morale - 10)
    ui.info(f"{losses} hommes hors de combat. Moral en baisse.")

def _resolve_disease_outbreak(state, ui):
    ui.show_scene("events", "disease")
    ui.narrate(
        "Une fièvre malsaine se propage dans l'entrepont. Trois hommes "
        "sont déjà morts ce matin. Le chirurgien hoche la tête en silence."
    )
    losses = max(2, state.crew // 8)
    state.crew = max(0, state.crew - losses)
    state.morale = max(0, state.morale - 15)
    ui.info(f"{losses} hommes succombent à la fièvre. Moral entamé.")

def _resolve_yellow_fever(state, ui):
    """Fièvre jaune (vomito negro) : épidémie attestée Caraïbes 1690s+."""
    if state.has_trait("scurvy_resist"):
        ui.narrate(
            "Une fièvre jaune balaie l'entrepont. Le chirurgien tient bon "
            "à coups de quinquina ; pas un mort, mais l'équipage tremble."
        )
        state.morale = max(0, state.morale - 5)
        return
    ui.show_scene("events", "yellow_fever")
    ui.narrate(
        "Fièvre brûlante, urine noire, vomi de sang. Le vomito negro "
        "frappe sans prévenir. En trois jours, le quart de l'équipage "
        "est sur le dos."
    )
    losses = max(3, state.crew // 5)
    save = state.get_modifier("crew_save_chance", 0.0)
    if save > 0 and random.random() < save:
        losses = losses // 2
        ui.info("Le chirurgien en sauve la moitié.")
    state.crew = max(0, state.crew - losses)
    state.morale = max(0, state.morale - 20)
    ui.info(f"{losses} hommes morts. Moral -20.")

def _resolve_amputation(state, ui):
    """Blessé grave après un combat. Sans antiseptique, l'amputation était
    le seul recours ; les Articles (Roberts, art. 9) prévoyaient 800 P8
    d'indemnité pour un membre perdu, prélevés sur la caisse commune."""
    if state.crew < 12:
        return
    ui.show_scene("events", "amputation")
    has_surgeon = state.get_modifier("crew_save_chance", 0.0) > 0
    ui.narrate(
        "Un homme délire, la jambe noircie depuis l'abordage. La gangrène "
        "gagne. Il faut couper, et vite."
    )
    if has_surgeon:
        ui.narrate("Le chirurgien affûte sa scie, prépare la poix et le garrot.")
        survives = random.random() < 0.8
    else:
        ui.narrate("Faute de chirurgien, c'est le charpentier et sa scie à bois qui s'y collent.")
        survives = random.random() < 0.45
    # Indemnité du Code si caisse suffisante
    indemnite = 0
    if state.gold >= 200:
        indemnite = min(800, state.gold // 4)
    choice = ui.choose(
        "Comment réglez-vous la chose ?",
        [
            (f"Verser l'indemnité du Code ({indemnite} P8 si possible)", "pay"),
            ("Promettre le versement à la prochaine prise", "promise"),
        ],
    )
    if not survives:
        state.crew = max(0, state.crew - 1)
        state.morale = max(0, state.morale - 6)
        ui.fail("L'homme ne survit pas au choc. On le coud dans son hamac. Moral -6.")
        return
    if choice == "pay" and indemnite > 0:
        state.gold -= indemnite
        state.morale = min(100, state.morale + 8)
        ui.success(f"L'homme vit, manchot mais payé : -{indemnite} P8 de la caisse commune. Le Code tient. Moral +8.")
    else:
        state.morale = max(0, state.morale - 3)
        ui.info("L'homme vit. L'indemnité attendra la prochaine prise — l'équipage note la dette. Moral -3.")

def _resolve_dysentery(state, ui):
    """Le « flux de sang » (dysenterie) : eau croupie et entrepont insalubre
    en faisaient l'un des plus grands tueurs du bord, plus encore que le
    combat."""
    if state.crew < 18:
        return
    if state.has_trait("scurvy_resist"):
        ui.narrate(
            "Le flux de sang menace, mais l'eau est tenue propre et les "
            "tisanes font effet. Quelques jours d'alitement, pas de mort."
        )
        state.morale = max(0, state.morale - 4)
        return
    ui.show_scene("events", "dysentery")
    ui.narrate(
        "L'eau des barriques a tourné. Le flux de sang court d'un hamac à "
        "l'autre ; l'entrepont empeste. Les hommes faiblissent à vue d'œil."
    )
    losses = max(1, state.crew // 14)
    save = state.get_modifier("crew_save_chance", 0.0)
    if save > 0 and random.random() < save:
        losses = max(1, losses // 2)
        ui.info("Le chirurgien isole les malades et rationne l'eau propre — moitié sauvée.")
    state.crew = max(0, state.crew - losses)
    state.supplies = max(0, state.supplies - 6)
    state.morale = max(0, state.morale - 10)
    ui.info(f"{losses} hommes emportés par le flux. Vivres -6, moral -10.")

def _resolve_pox(state, ui):
    """La vérole et autres maux gagnés à terre, après une bordée dans les
    tavernes et bordels d'un port (Port Royal était fameuse pour cela).
    Affaiblit l'équipage plus qu'elle ne tue."""
    if not state.flags.get("recent_shore_leave") and state.morale > 60:
        # Survient surtout après une bonne escale.
        if random.random() > 0.5:
            return
    ui.show_scene("events", "pox")
    ui.narrate(
        "Quinze jours après l'escale, les conséquences se déclarent. La "
        "vérole et ses cousines parcourent le bord. Le chirurgien sort le "
        "mercure ; les hommes rasent les murs de la coursive."
    )
    state.morale = max(0, state.morale - 8)
    afflicted = max(1, state.crew // 16)
    if random.random() < 0.3:
        state.crew = max(0, state.crew - 1)
        ui.info(f"{afflicted} hommes diminués, un cas emporté par le mercure autant que par le mal. Moral -8.")
    else:
        ui.info(f"{afflicted} hommes diminués pour quelque temps. Moral -8.")

def _resolve_rat_infestation(state, ui):
    """Les rats pullulaient dans les cales, dévorant les vivres et propageant
    la maladie par leurs puces. Un chat de bord valait son pesant d'or."""
    ui.show_scene("events", "rat_infestation")
    ui.narrate(
        "Les rats ont pris la cale d'assaut. Biscuit éventré, fromage rongé, "
        "cordages mâchés — et leurs puces propagent la fièvre. Le chat du bord "
        "ne suffit plus."
    )
    supply_loss = random.randint(6, 14)
    state.supplies = max(0, state.supplies - supply_loss)
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Vider la cale et enfumer au soufre (une journée)", "fumigate"),
            ("Lâcher furets et chats, et serrer les dents", "tolerate"),
        ],
    )
    if choice == "fumigate":
        state.advance_turn()
        state.morale = min(100, state.morale + 2)
        ui.success(f"Cale enfumée, rats noyés et chassés. Vivres -{supply_loss}, mais le mal est jugulé.")
    else:
        if random.random() < 0.4:
            losses = max(1, state.crew // 16)
            state.crew = max(0, state.crew - losses)
            state.morale = max(0, state.morale - 6)
            ui.fail(f"Les puces des rats apportent la fièvre : {losses} hommes alités. Vivres -{supply_loss}, moral -6.")
        else:
            state.morale = max(0, state.morale - 3)
            ui.info(f"On vit avec la vermine. Vivres -{supply_loss}, moral -3.")

# -----------------------------------------------------------------
# >>> AUTORITÉ, GUERRE & INFAMIE
# Marines de guerre, garde-côtes, pardons, raids et répression.
# -----------------------------------------------------------------

def _resolve_navy_patrol(state, ui):
    ui.show_scene("events", "navy_patrol")
    ui.narrate(
        "À l'aube, deux silhouettes carrées émergent de la brume : "
        "une frégate de la Royal Navy escortée d'un sloop de guerre. "
        "Ils ont vu votre pavillon."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Fuir toutes voiles dehors", "flee"),
            ("Engager le combat", "fight"),
            ("Hisser pavillon de complaisance", "bluff"),
        ],
    )
    speed = state.ship["speed"] + state.get_effective_bonus("speed_bonus")
    if choice == "flee":
        if speed + random.randint(1, 6) >= 10:
            ui.success("Votre navire file mieux que les leurs. Vous les semez avant la nuit.")
            state.morale = min(100, state.morale + 2)
        else:
            hull_loss = random.randint(15, 35)
            crew_lost = random.randint(3, 10)
            ui.fail(f"Leurs canons trouvent leur portée. Coque -{hull_loss}, {crew_lost} morts.")
            state.ship["hull_current"] = max(0, state.ship["hull_current"] - hull_loss)
            state.crew = max(0, state.crew - crew_lost)
    elif choice == "fight":
        ui.fail(
            "Affronter deux navires de guerre est de la folie. La frégate "
            "vous démâte, le sloop fait l'abordage."
        )
        hull_loss = 40
        crew_lost = random.randint(15, 30)
        state.ship["hull_current"] = max(0, state.ship["hull_current"] - hull_loss)
        state.crew = max(0, state.crew - crew_lost)
        state.morale = max(0, state.morale - 25)
    else:
        bluff_diff = state.reputation
        if random.randint(1, 10) > bluff_diff + 3:
            ui.success("Pavillon hollandais hissé, papiers falsifiés exhibés. Ils passent leur route.")
        else:
            ui.fail("Le capitaine de la frégate reconnaît votre navire à sa silhouette !")
            hull_loss = 25
            crew_lost = random.randint(5, 15)
            state.ship["hull_current"] = max(0, state.ship["hull_current"] - hull_loss)
            state.crew = max(0, state.crew - crew_lost)

def _resolve_coastal_ambush(state, ui):
    """Embuscade de chasseurs de pirates dans un mouillage côtier."""
    if state.reputation < 3:
        return
    ui.show_scene("events", "ambush")
    ui.narrate(
        "Vous mouillez dans une crique pour faire de l'eau. À l'aube, "
        "quatre pinasses surgissent — chasseurs de primes, milice "
        "coloniale, et un sloop de la Navy au large."
    )
    speed = state.ship["speed"] + state.get_effective_bonus("speed_bonus")
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Couper les amarres et fuir", "flee"),
            ("Engager les pinasses au mousquet", "fight"),
        ],
    )
    if choice == "flee":
        if speed >= 8:
            ui.success("Vos hommes coupent l'amarre, la voile prend. Vous filez.")
        else:
            damage = random.randint(15, 30)
            crew_lost = random.randint(3, 8)
            state.ship["hull_current"] = max(0, state.ship["hull_current"] - damage)
            state.crew = max(0, state.crew - crew_lost)
            ui.fail(f"Le sloop vous rattrape un moment. Coque -{damage}, {crew_lost} morts.")
    else:
        combat = state.get_effective_bonus("combat")
        if combat >= 2 or random.random() > 0.4:
            crew_lost = random.randint(2, 6)
            state.crew = max(0, state.crew - crew_lost)
            state.reputation += 2
            ui.success(f"Les pinasses sont coulées. {crew_lost} de vos hommes y restent.")
        else:
            damage = random.randint(20, 35)
            crew_lost = random.randint(8, 15)
            state.ship["hull_current"] = max(0, state.ship["hull_current"] - damage)
            state.crew = max(0, state.crew - crew_lost)
            ui.fail(f"Sortie héroïque mais coûteuse. Coque -{damage}, {crew_lost} hommes perdus.")

def _resolve_guarda_costa(state, ui):
    """Garde-côtes espagnols (« guardas costas ») : corsaires de Sa Majesté
    Catholique lancés contre toute voile suspecte dans les Caraïbes, et dont
    les abus envers les marins anglais menèrent à la guerre de l'Oreille de
    Jenkins (1739)."""
    ui.show_scene("events", "guarda_costa")
    ui.narrate(
        "Une voile espagnole force vers vous, pavillon de guerre : un "
        "garde-côte, de ces corsaires qui arraisonnent toute voile suspecte — "
        "et dont les abus nourrissent bien des rancunes."
    )
    speed = state.ship["speed"] + state.get_effective_bonus("speed_bonus")
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Fuir vers le large", "flee"),
            ("Lui tenir tête au canon", "fight"),
            ("Hisser des papiers de complaisance", "bluff"),
        ],
    )
    if choice == "flee":
        if speed + random.randint(1, 6) >= 9:
            ui.success("Plus fin que le garde-côte, vous le distancez avant la nuit.")
        else:
            damage = random.randint(12, 28)
            crew_lost = random.randint(2, 8)
            state.ship["hull_current"] = max(0, state.ship["hull_current"] - damage)
            state.crew = max(0, state.crew - crew_lost)
            ui.fail(f"Ses pièces vous accrochent. Coque -{damage}, {crew_lost} morts.")
    elif choice == "fight":
        combat = state.get_effective_bonus("combat")
        if combat >= 1 or random.random() > 0.45:
            gain = random.randint(120, 280)
            crew_lost = random.randint(3, 9)
            state.gold += gain
            state.crew = max(0, state.crew - crew_lost)
            state.reputation += 2
            ui.success(f"Le garde-côte amène pavillon. +{gain} P8, {crew_lost} morts.")
        else:
            damage = random.randint(20, 38)
            crew_lost = random.randint(8, 16)
            state.ship["hull_current"] = max(0, state.ship["hull_current"] - damage)
            state.crew = max(0, state.crew - crew_lost)
            state.morale = max(0, state.morale - 10)
            ui.fail(f"Le garde-côte mord dur. Coque -{damage}, {crew_lost} morts, moral -10.")
    else:
        if random.randint(1, 10) > state.reputation + 3:
            ui.success("Papiers exhibés, mine innocente : il vous laisse passer en maugréant.")
        else:
            damage = random.randint(15, 30)
            crew_lost = random.randint(4, 10)
            state.ship["hull_current"] = max(0, state.ship["hull_current"] - damage)
            state.crew = max(0, state.crew - crew_lost)
            ui.fail(f"Il ne croit pas vos papiers. Coque -{damage}, {crew_lost} morts.")

def _resolve_kings_pardon(state, ui):
    ui.show_scene("events", "kings_pardon")
    ui.narrate(
        "Une chaloupe sous pavillon parlementaire vous accoste. Un émissaire "
        "remet un placard : Sa Majesté offre un pardon royal à tout pirate "
        "qui se soumettra avant un an. C'est l'« Act of Grace »."
    )
    choice = ui.choose(
        "Acceptez-vous le pardon ?",
        [
            ("Accepter et abandonner la course", "accept"),
            ("Brûler le placard et continuer", "refuse"),
        ],
    )
    if choice == "accept":
        ui.success(
            "Vous gardez vos biens, votre liberté, et peut-être votre tête. "
            "La partie s'achève sur une retraite honorable."
        )
        state.flags["pardoned"] = True
        state.game_over = True
        state.victory = True
    else:
        state.reputation += 2
        state.morale = min(100, state.morale + 10)
        ui.info(
            "L'équipage acclame votre refus. Mais les autorités, désormais, "
            "ne feront plus grâce."
        )
        state.flags["pardon_refused"] = True

def _resolve_letter_of_marque(state, ui):
    """Lettre de marque : en temps de guerre, un gouverneur peut légaliser
    la course (cf. glossaire « Letter of Marque » ; BrianJacque.pdf : « des
    corsaires n'étaient rien d'autre que des pirates au service d'un État »).
    Disponible uniquement pendant une guerre attestée."""
    war = _war_name(state)
    if not war or state.flags.get("privateer_commission") or state.flags.get("pardoned"):
        return
    ui.show_scene("events", "letter_of_marque")
    ui.narrate(
        f"Une chaloupe sous pavillon parlementaire vous accoste. Avec "
        f"{war}, un gouverneur des îles offre une lettre de marque : votre "
        "course devient légale contre les navires ennemis, et vos prises se "
        "vendront au grand jour dans ses ports."
    )
    choice = ui.choose(
        "Acceptez-vous la commission ?",
        [
            ("Accepter — devenir corsaire sous lettre de marque", "accept"),
            ("Refuser — nul maître au-dessus du pavillon noir", "refuse"),
        ],
    )
    if choice == "accept":
        state.flags["privateer_commission"] = True
        state.morale = min(100, state.morale + 6)
        ui.success(
            "Papiers en règle, dixième au gouverneur. Vous pillez sous "
            "couleur de loi : les ports amis s'ouvrent, la corde s'éloigne. Moral +6."
        )
    else:
        state.reputation += 1
        state.morale = min(100, state.morale + 4)
        ui.info("Vous brûlez la commission. « Frères de la côte, et de personne d'autre. » Moral +4.")

def _resolve_war_news(state, ui):
    """Nouvelle d'une guerre apportée par une prise ou un navire neutre.
    La déclaration de guerre redistribuait les cartes : nouveaux ennemis
    licites, nouvelles routes de convois, demande de corsaires."""
    war = _war_name(state)
    ui.show_scene("events", "war_news")
    if war:
        ui.narrate(
            f"Un navire neutre vous hèle et vous jette des gazettes par-dessus "
            f"l'eau : {war} embrase l'Europe et ses colonies. Les convois "
            "ennemis prennent la mer, mal escortés ; les gouverneurs cherchent "
            "des corsaires."
        )
        state.morale = min(100, state.morale + 5)
        state.flags["war_intel"] = True
        ui.success("Renseignement noté : les prises ennemies seront nombreuses. Moral +5.")
    else:
        ui.narrate(
            "Les gazettes d'un navire neutre annoncent la paix signée en "
            "Europe. Fini les prises faciles sous couleur de guerre : "
            "désormais, tout pillage est piraterie pure et simple."
        )
        state.morale = max(0, state.morale - 3)
        ui.info("La paix resserre l'étau sur les pavillons noirs. Moral -3.")

def _resolve_pirate_hunter(state, ui):
    """Nomination d'un chasseur de pirates résolu — repère historique :
    Woodes Rogers, gouverneur des Bahamas en 1718, qui apporta le pardon
    royal et la répression à Nassau. Atmosphère de fin d'âge d'or."""
    try:
        year = state.current_date().year
    except Exception:
        year = 1718
    if year < 1718:
        return
    if state.reputation < 4 or state.flags.get("pardoned"):
        return
    ui.show_scene("events", "pirate_hunter")
    ui.narrate(
        "Les nouvelles courent de port en port : un gouverneur résolu — un "
        "certain Woodes Rogers — s'est installé à Nassau avec pardon dans une "
        "main et corde dans l'autre. La Couronne a juré la fin des pavillons "
        "noirs ; les frégates se multiplient sur les routes."
    )
    choice = ui.choose(
        "Comment réagissez-vous ?",
        [
            ("Faire profil bas, changer de chasse pour un temps", "lielow"),
            ("Redoubler d'audace pendant qu'il en est temps", "defy"),
        ],
    )
    if choice == "lielow":
        state.advance_turn()
        state.flags["lying_low"] = True
        state.morale = max(0, state.morale - 4)
        ui.info("Vous gagnez des eaux discrètes et laissez retomber la traque. Un mois perdu, moral -4.")
    else:
        state.reputation += 2
        state.morale = min(100, state.morale + 8)
        state.flags["pirate_hunter_active"] = True
        ui.success(
            "« Une vie courte mais joyeuse ! » L'équipage gronde son approbation. "
            "Votre nom enfle — mais la cible sur votre dos aussi. Moral +8."
        )

def _resolve_raid_town(state, ui):
    """Sac d'une bourgade côtière mal défendue — pratique des grands
    boucaniers (Morgan à Portobello en 1668 et Panama en 1671 ; l'Olonnais
    à Maracaibo en 1667). Gros gain, gros risque, et choix moral sur le
    sort de la population."""
    if state.crew < 50 or state.reputation < 3:
        return
    ui.show_scene("events", "raid_town")
    ui.narrate(
        "Une bourgade espagnole sommeille au fond d'une baie : entrepôts, une "
        "église, un petit fort aux canons mal servis. Mal défendue, riche de "
        "la dernière récolte de sucre et d'indigo."
    )
    combat = state.get_effective_bonus("combat") * 5
    intim = state.get_effective_bonus("intimidation") * 4
    strength = state.crew + combat + intim + random.randint(-15, 25)
    choice = ui.choose(
        "Comment menez-vous l'affaire ?",
        [
            ("Débarquer et donner l'assaut au fort", "assault"),
            ("Menacer de tout brûler et exiger une rançon", "ransom"),
            ("Renoncer — une descente à terre est hasardeuse", "leave"),
        ],
    )
    if choice == "leave":
        ui.info("Vous laissez la bourgade à son sommeil. Pas de gloire, pas de risque.")
        return
    if choice == "ransom":
        if intim >= 8 or strength > 90:
            tribute = random.randint(200, 500)
            state.gold += tribute
            state.reputation += 2
            ui.success(f"Les notables paient pour sauver leurs toits : +{tribute} P8, sans un coup de feu.")
        else:
            state.morale = max(0, state.morale - 6)
            ui.fail("Le fort tire le premier ; votre bluff ne prend pas. Vous décrochez, bredouilles. Moral -6.")
        return
    # assault
    if strength < 90:
        crew_lost = random.randint(8, 18)
        state.crew = max(0, state.crew - crew_lost)
        state.morale = max(0, state.morale - 12)
        ui.fail(f"La milice tient le fort mieux qu'attendu. Repoussés. {crew_lost} morts, moral -12.")
        return
    booty = random.randint(300, 700)
    cargo = random.randint(200, 500)
    crew_lost = random.randint(5, 14)
    state.gold += booty
    state.loot += cargo
    state.crew = max(0, state.crew - crew_lost)
    state.reputation += 3
    sub = ui.choose(
        "La bourgade est à vous. Que faites-vous des habitants ?",
        [
            ("Piller les entrepôts et rembarquer, sans plus", "discipline"),
            ("Tout livrer au pillage et à la flamme", "sack"),
        ],
    )
    if sub == "discipline":
        state.morale = min(100, state.morale + 6)
        ui.success(
            f"Entrepôts vidés, fort épargné. +{booty} P8, +{cargo} de cargaison. "
            f"{crew_lost} hommes perdus. L'équipage vous tient pour juste. Moral +6."
        )
    else:
        state.reputation += 2
        state.morale = max(0, state.morale - 8)
        ui.info(
            f"La fumée monte sur la baie. +{booty} P8, +{cargo} de cargaison. "
            f"{crew_lost} morts. La terreur grossit votre nom — le souper se prend en silence. Moral -8."
        )
        _maybe_yield_prisoners(state, ui, chance=0.5)

def _resolve_press_gang(state, ui):
    """Au port : une presse de la Royal Navy rafle les marins dans les
    tavernes. L'impressment était la terreur des gens de mer aux XVIIe-
    XVIIIe siècles et vidait les équipages d'un coup."""
    if not state.in_port or state.crew < 10:
        return
    ui.narrate(
        "Une presse de la Navy ratisse les quais et les tavernes, raflant "
        "tout ce qui a le pied marin. Vos hommes à terre sont en danger d'être "
        "enrôlés de force sur un vaisseau du roi."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Rappeler l'équipage à bord en hâte", "recall"),
            ("Graisser la patte de l'officier de presse (80 P8)", "bribe"),
            ("Laisser faire et appareiller au plus vite", "flee"),
        ],
    )
    if choice == "recall":
        if state.get_effective_bonus("leadership") >= 1 or random.random() < 0.6:
            ui.success("Le rappel court de taverne en taverne ; vos hommes regagnent le bord à temps.")
        else:
            lost = random.randint(2, 6)
            state.crew = max(0, state.crew - lost)
            state.morale = max(0, state.morale - 5)
            ui.fail(f"Trop tard pour {lost} traînards, raflés par la presse. Moral -5.")
    elif choice == "bribe":
        if state.gold >= 80:
            state.gold -= 80
            ui.success("Quelques pièces dans la bonne main : la presse passe son chemin. -80 P8.")
        else:
            lost = random.randint(2, 5)
            state.crew = max(0, state.crew - lost)
            ui.fail(f"Pas de quoi corrompre l'officier. {lost} hommes embarqués de force.")
    else:
        lost = random.randint(3, 8)
        state.crew = max(0, state.crew - lost)
        state.morale = max(0, state.morale - 6)
        ui.fail(f"Vous larguez les amarres en abandonnant {lost} hommes aux griffes de la presse. Moral -6.")

def _resolve_wanted_poster(state, ui):
    """Au port : le capitaine découvre sa propre tête mise à prix. La
    notoriété flatte l'équipage mais resserre l'étau. Les proclamations et
    primes contre les pirates étaient placardées dans tous les ports."""
    if not state.in_port or state.reputation < 4:
        return
    bounty = state.reputation * random.randint(40, 80)
    ui.narrate(
        f"Sur la porte de la capitainerie, un placard fraîchement collé : "
        f"votre nom, votre signalement, et une prime de {bounty} livres pour "
        "qui vous livrera, mort ou vif."
    )
    choice = ui.choose(
        "Que faites-vous ?",
        [
            ("Arracher le placard et le clouer à votre grand mât", "defy"),
            ("Filer discrètement avant qu'on vous reconnaisse", "lielow"),
        ],
    )
    if choice == "defy":
        state.reputation += 1
        state.morale = min(100, state.morale + 6)
        ui.success("Le placard finit cloué au mât, trophée d'infamie. L'équipage exulte. Moral +6.")
    else:
        state.morale = max(0, state.morale - 2)
        ui.info("Capuchon rabattu, vous regagnez le bord sans bruit. Mieux vaut un nom discret. Moral -2.")

def _resolve_execution_dock(state, ui):
    """Au port : pendaison publique d'un pirate, corps gibeté pour l'exemple
    (Execution Dock à Wapping ; Kidd gibeté en 1701, Calico Jack en 1720).
    Spectacle destiné à terrifier les gens de mer."""
    if not state.in_port:
        return
    ui.narrate(
        "La foule se presse sur le quai : on pend un pirate à la marée basse. "
        "Son corps sera ensuite enduit de goudron et gibeté à l'entrée du "
        "port, pour que tout marin le voie en passant."
    )
    if state.has_companion("pere_etienne"):
        ui.narrate("Le père Étienne murmure une prière pour le supplicié.")
    choice = ui.choose(
        "Quel effet sur l'équipage ?",
        [
            ("Y voir un avertissement — la corde nous attend tous", "fear"),
            ("Y puiser un défi — vivre libre ou mourir ainsi", "defiance"),
        ],
    )
    if choice == "fear":
        state.morale = max(0, state.morale - 6)
        ui.info("Le gibet jette un froid. Certains songent au pardon royal. Moral -6.")
    else:
        state.morale = min(100, state.morale + 5)
        state.reputation += 1
        ui.success(
            "« Une vie courte mais joyeuse ! » Le défi soude l'équipage face à "
            "la potence. Moral +5."
        )

# -----------------------------------------------------------------
# >>> AU PORT : RUMEURS & NÉGOCE
# Tavernes, comptoirs, receleurs et courtiers (événements à quai).
# -----------------------------------------------------------------

def _resolve_tavern_rumor(state, ui):
    # Cet événement n'est tiré qu'au port → la scène est gérée par le port
    ui.narrate(
        "À l'arrière-salle d'une taverne, un vieux gabier ivre vous glisse "
        "un renseignement contre une rasade de rhum."
    )
    rumor = random.choice([
        "Un convoi espagnol partira de Carthagène dans deux mois.",
        "La frégate HMS Swallow patrouille au large des Bermudes.",
        "On dit qu'un capitaine cache son or sur l'Île de la Vache.",
        "Le gouverneur de Saint-Domingue cherche à délivrer des lettres de marque.",
    ])
    ui.info(f"Rumeur : « {rumor} »")

def _resolve_ransom_brokers(state, ui):
    """Rachat de captifs : des intermédiaires — parfois des religieux, à la
    manière des Trinitaires et Mercédaires qui rachetaient les captifs des
    Barbaresques — proposent de racheter vos prisonniers de qualité. Au
    port uniquement, et s'il y a des prisonniers."""
    if not state.in_port or not state.prisoners:
        return
    ui.narrate(
        "Un homme en habit sobre demande à vous voir : un courtier, mandaté "
        "par des familles et une confrérie de rachat. Il propose de racheter "
        "vos prisonniers de qualité — affaire discrète, paiement comptant."
    )
    n = min(len(state.prisoners), random.randint(1, 3))
    offer = n * random.randint(60, 160)
    choice = ui.choose(
        f"Céder {n} prisonnier(s) contre {offer} P8 de rançon ?",
        [
            ("Accepter le rachat", "sell"),
            ("Garder les prisonniers — réclamer mieux plus tard", "keep"),
        ],
    )
    if choice == "sell":
        for _ in range(n):
            if state.prisoners:
                state.prisoners.pop()
        state.gold += offer
        ui.success(f"Rançon réglée : +{offer} P8. {n} prisonnier(s) rendus à leurs proches.")
    else:
        ui.info("Vous refusez l'offre. Le courtier salue et s'en va — il reviendra.")

def _resolve_fence_the_loot(state, ui):
    """Écoulement du butin chez un receleur : il fallait un « marché
    conciliant et pas trop regardant pour blanchir le butin » (cf.
    ArnaudPirates2016.pdf). Convertit de la cargaison en pièces, avec la
    décote du receleur. Au port uniquement."""
    if not state.in_port or state.loot < 100:
        return
    ui.narrate(
        "Dans une arrière-cour du port, un marchand peu curieux examine votre "
        "cargaison. Pas de questions sur sa provenance — mais sa bourse paie "
        "au rabais ce qu'on ne peut vendre au grand jour."
    )
    portion = min(state.loot, random.randint(150, 400))
    rate = random.uniform(0.45, 0.65)   # décote du recel
    payout = int(portion * rate)
    choice = ui.choose(
        f"Écouler {portion} de cargaison contre {payout} P8 ({int(rate*100)} % de sa valeur) ?",
        [
            ("Vendre au receleur", "sell"),
            ("Garder pour un meilleur marché", "keep"),
        ],
    )
    if choice == "sell":
        state.loot -= portion
        state.gold += payout
        ui.success(f"Marché conclu dans l'ombre : -{portion} de cargaison, +{payout} P8 sonnants.")
    else:
        ui.info("Vous gardez la cargaison ; un port mieux disposé la paiera plus cher.")

def _resolve_baldridge_post(state, ui):
    """Le comptoir d'Adam Baldridge à l'île Sainte-Marie (c. 1690-1697) : base
    de ravitaillement de la Pirate Round, reliée au marchand new-yorkais
    Frederick Philipse. On y troque le butin contre tout le nécessaire — au
    prix fort. Événement de port (pas de scène dédiée)."""
    ui.narrate(
        "À l'île Sainte-Marie, le comptoir d'Adam Baldridge : entrepôts de "
        "palissade, rhum, poudre, étoffes. L'homme rachète le butin et "
        "fournit tout — contre bon or, et au prix de la Round."
    )
    choice = ui.choose(
        "Que faites-vous au comptoir ?",
        [
            ("Échanger de la cargaison contre vivres et poudre", "resupply"),
            ("Vendre du butin contre de l'or comptant", "sell"),
            ("Boire un coup et écouter les nouvelles", "rumor"),
        ],
    )
    if choice == "resupply":
        if state.loot >= 80:
            state.loot -= 80
            state.supplies = min(100, state.supplies + 25)
            state.flags["powder_low"] = False
            state.morale = min(100, state.morale + 4)
            ui.success("Cargaison troquée : vivres +25, soutes regarnies en poudre. Moral +4.")
        else:
            ui.info("Pas assez de cargaison à échanger. Baldridge ne fait pas crédit.")
    elif choice == "sell":
        if state.loot >= 100:
            portion = min(state.loot, random.randint(150, 350))
            payout = int(portion * 0.6)
            state.loot -= portion
            state.gold += payout
            ui.success(f"Baldridge paie comptant : -{portion} de cargaison, +{payout} P8.")
        else:
            ui.info("Trop peu à vendre pour intéresser le marchand.")
    else:
        state.flags["surat_intel"] = True
        state.morale = min(100, state.morale + 3)
        ui.info("Au goulot d'une bouteille, on apprend qu'une flotte indienne se prépare à Surat. Moral +3.")

# -----------------------------------------------------------------
# >>> RECRUTEMENT DE COMPAGNONS
# Officiers d'exception recrutés au fil des rencontres.
# -----------------------------------------------------------------

def _resolve_meet_pilot(state, ui):
    """Yusuf le Maure — recueilli d'une barque dérivante."""
    if state.has_companion("yusuf_le_maure"):
        return
    from data.companions import get_companion
    yusuf = get_companion("yusuf_le_maure")
    ui.show_scene("companions", "yusuf_le_maure")
    ui.narrate(
        "La vigie hèle : une chaloupe à la dérive. Un seul homme à bord, "
        "à demi mort de soif, des cartes roulées dans une vessie graissée."
    )
    ui.narrate(yusuf["recruitment"]["intro"])
    choice = ui.choose(
        "Embarquer cet homme ?",
        [
            ("Lui offrir une place aux Articles", "yes"),
            ("Donner de l'eau, puis le laisser à la dérive", "no"),
        ],
    )
    if choice == "yes":
        state.add_companion(yusuf)
        ui.success(f"{yusuf['name']} rejoint l'équipage. {yusuf['bonus_label']}")

def _resolve_meet_surgeon(state, ui):
    """John Cole, fuyant la justice de Boston."""
    if state.has_companion("john_cole_surgeon"):
        return
    from data.companions import get_companion
    cole = get_companion("john_cole_surgeon")
    ui.show_scene("companions", "john_cole_surgeon")
    ui.narrate(
        "Le navire que vous venez d'arraisonner transportait un passager "
        "discret en redingote tachée. Il ne demande qu'à embarquer."
    )
    ui.narrate(cole["recruitment"]["intro"])
    choice = ui.choose(
        "Le prendre à bord ?",
        [
            ("L'inscrire au rôle d'équipage", "yes"),
            ("Refuser — un fugitif amène des ennuis", "no"),
        ],
    )
    if choice == "yes":
        state.add_companion(cole)
        ui.success(f"{cole['name']} rejoint l'équipage. {cole['bonus_label']}")

def _resolve_meet_carpenter(state, ui):
    """Mary Lacy — révélation à l'occasion d'une réparation."""
    if state.has_companion("mary_lacy_carpenter"):
        return
    from data.companions import get_companion
    mary = get_companion("mary_lacy_carpenter")
    ui.show_scene("companions", "mary_lacy_carpenter")
    ui.narrate(
        "Le jeune charpentier que vous avez engagé au dernier port révèle, "
        "lors d'un combat où sa chemise se déchire, qu'il est une femme. "
        "L'équipage murmure. Vous tranchez."
    )
    choice = ui.choose(
        "Que décidez-vous ?",
        [
            ("La garder comme maître charpentier — son travail parle pour elle", "keep"),
            ("La débarquer au prochain port", "drop"),
        ],
    )
    if choice == "keep":
        state.add_companion(mary)
        state.morale = min(100, state.morale + 5)
        ui.success(f"{mary['name']} garde sa place officiellement. {mary['bonus_label']}")
    else:
        state.morale = max(0, state.morale - 10)
        ui.info("Vous la débarquez. L'équipage juge la décision sévère.")

def _resolve_priest_wreck(state, ui):
    """Père Étienne — seul survivant d'une épave."""
    if state.has_companion("pere_etienne"):
        return
    from data.companions import get_companion
    pere = get_companion("pere_etienne")
    ui.show_scene("companions", "pere_etienne")
    ui.narrate(
        "Sur les débris d'une barque éventrée, un homme en bure tachée. "
        "Vivant. Seul."
    )
    ui.narrate(pere["recruitment"]["intro"])
    choice = ui.choose(
        "L'accueillir ?",
        [
            ("Oui — un homme de lettres est utile", "yes"),
            ("Non — un défroqué porte malheur", "no"),
        ],
    )
    if choice == "yes":
        state.add_companion(pere)
        ui.success(f"{pere['name']} rejoint le bord. {pere['bonus_label']}")

# =================================================================
# Catalogue
# =================================================================

EVENTS = [
    # --- Mer, météo & présages ---
    {"id": "storm", "title": "Tempête", "weight": 12,
     "conditions": lambda s: True, "resolve": _resolve_storm},
    {"id": "hurricane", "title": "Ouragan", "weight": 5,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_hurricane},
    {"id": "monsoon", "title": "Mousson contraire", "weight": 6,
     "conditions": lambda s: s.flags.get("last_region") == "overseas" and not s.in_port,
     "resolve": _resolve_monsoon},
    {"id": "doldrums", "title": "Calme plat", "weight": 8,
     "conditions": lambda s: True, "resolve": _resolve_doldrums},
    {"id": "lucky_breeze", "title": "Vent favorable", "weight": 10,
     "conditions": lambda s: True, "resolve": _resolve_lucky_breeze},
    {"id": "rogue_wave", "title": "Lame scélérate", "weight": 5,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_rogue_wave},
    {"id": "st_elmo_fire", "title": "Feu Saint-Elme", "weight": 4,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_st_elmo_fire},
    {"id": "sea_monster", "title": "Monstre marin", "weight": 4,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_sea_monster},
    {"id": "whale", "title": "Carcasse de baleine", "weight": 3,
     "conditions": lambda s: True, "resolve": _resolve_whale_carcass},
    {"id": "turtle_hunt", "title": "Chasse à la tortue", "weight": 6,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_turtle_hunt},

    # --- Navigation, avaries & entretien ---
    {"id": "sandbar", "title": "Banc de sable", "weight": 5,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_sandbar},
    {"id": "off_course", "title": "Hors de route", "weight": 5,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_off_course},
    {"id": "careening_needed", "title": "Carène à gratter", "weight": 5,
     "conditions": lambda s: s.ship["hull_current"] <= s.ship["hull_max"] * 0.8 and not s.in_port,
     "resolve": _resolve_careening_needed},
    {"id": "ship_fire", "title": "Feu à bord", "weight": 4,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_ship_fire},
    {"id": "powder_low", "title": "Pénurie de poudre", "weight": 4,
     "conditions": lambda s: s.flags.get("powder_low") and not s.in_port,
     "resolve": _resolve_powder_low},

    # --- Prises & abordages ---
    {"id": "merchant_sail", "title": "Voile marchande", "weight": 25,
     "conditions": lambda s: True, "resolve": _resolve_merchant_sail},
    {"id": "fishing_boat", "title": "Barque de pêche", "weight": 9,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_fishing_boat},
    {"id": "bermuda_sloop", "title": "Sloop bermudien", "weight": 7,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_bermuda_sloop},
    {"id": "dutch_fluyt", "title": "Flûte hollandaise", "weight": 8,
     "conditions": lambda s: s.crew >= 20 and not s.in_port,
     "resolve": _resolve_dutch_fluyt},
    {"id": "sugar_drogher", "title": "Caboteur sucrier", "weight": 8,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_sugar_drogher},
    {"id": "careened", "title": "Navire en carène", "weight": 5,
     "conditions": lambda s: True, "resolve": _resolve_careened_ship},
    {"id": "packet_boat", "title": "Paquebot postal", "weight": 5,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_packet_boat},
    {"id": "treasure_straggler", "title": "Galion isolé", "weight": 3,
     "conditions": lambda s: s.crew >= 45 and not s.in_port,
     "resolve": _resolve_treasure_straggler},
    {"id": "indiaman", "title": "Indiaman à l'horizon", "weight": 3,
     "conditions": lambda s: s.crew >= 60 and s.reputation >= 2, "resolve": _resolve_indiaman},
    {"id": "slave_ship", "title": "Négrier à l'horizon", "weight": 5,
     "conditions": lambda s: s.crew >= 30, "resolve": _resolve_slave_ship},
    {"id": "mughal_treasure_ship", "title": "Navire moghol", "weight": 3,
     "conditions": lambda s: s.flags.get("last_region") == "overseas"
                   and s.crew >= 70 and s.reputation >= 3,
     "resolve": _resolve_mughal_treasure_ship},
    {"id": "red_sea_convoy", "title": "Convoi de Moka", "weight": 5,
     "conditions": lambda s: s.flags.get("last_region") == "overseas" and s.crew >= 40,
     "resolve": _resolve_red_sea_convoy},
    {"id": "dhow_trader", "title": "Boutre marchand", "weight": 7,
     "conditions": lambda s: s.flags.get("last_region") == "overseas" and not s.in_port,
     "resolve": _resolve_dhow_trader},

    # --- Rencontres en mer ---
    {"id": "consort", "title": "Proposition de consort", "weight": 4,
     "conditions": lambda s: s.reputation >= 2 and not s.in_port,
     "resolve": _resolve_consort_proposal},
    {"id": "rival_careening", "title": "Rival en carène", "weight": 4,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_rival_careening},
    {"id": "native_canoes", "title": "Pirogues kalinago", "weight": 5,
     "conditions": lambda s: True, "resolve": _resolve_native_canoes},
    {"id": "maroon_camp", "title": "Village marron", "weight": 4,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_maroon_camp},
    {"id": "malagasy_clan", "title": "Clan betsimisaraka", "weight": 6,
     "conditions": lambda s: s.flags.get("last_region") == "overseas" and not s.in_port,
     "resolve": _resolve_malagasy_clan},
    {"id": "logwood_cutters", "title": "Coupeurs de campêche", "weight": 4,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_logwood_cutters},
    {"id": "marooned_sailor", "title": "Marronné sur un îlot", "weight": 5,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_marooned_sailor},
    {"id": "man_overboard", "title": "Un homme à la mer", "weight": 6,
     "conditions": lambda s: s.crew >= 8 and not s.in_port,
     "resolve": _resolve_man_overboard},
    {"id": "castaways", "title": "Naufragés à la dérive", "weight": 5,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_castaways},
    {"id": "navy_deserter", "title": "Déserteur de la Navy", "weight": 4,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_navy_deserter},
    {"id": "lady_in_peril", "title": "Dame en péril", "weight": 3,
     "conditions": lambda s: s.crew >= 30, "resolve": _resolve_lady_in_peril},

    # --- Trésor, épaves & légendes ---
    {"id": "wreck", "title": "Épave à la dérive", "weight": 8,
     "conditions": lambda s: True, "resolve": _resolve_wreck},
    {"id": "buried_treasure", "title": "Cache enterrée", "weight": 4,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_buried_treasure},
    {"id": "salvage_wreck", "title": "Épave engloutie", "weight": 4,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_salvage_wreck},
    {"id": "message_in_bottle", "title": "Bouteille à la mer", "weight": 4,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_message_in_bottle},
    {"id": "ghost_ship", "title": "Navire fantôme", "weight": 3,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_ghost_ship},

    # --- Équipage, discipline & crises du bord ---
    {"id": "mutiny", "title": "Risque de mutinerie", "weight": 10,
     "conditions": lambda s: s.morale <= 35, "resolve": _resolve_mutiny_threat},
    {"id": "division_of_spoils", "title": "Partage du butin", "weight": 6,
     "conditions": lambda s: s.loot >= 80, "resolve": _resolve_division_of_spoils},
    {"id": "duel_ashore", "title": "Querelle à terre", "weight": 5,
     "conditions": lambda s: s.crew >= 12, "resolve": _resolve_duel_ashore},
    {"id": "thief_among_us", "title": "Un voleur à bord", "weight": 5,
     "conditions": lambda s: s.crew >= 10, "resolve": _resolve_thief_among_us},
    {"id": "gambling_dispute", "title": "Jeu interdit", "weight": 5,
     "conditions": lambda s: s.crew >= 12, "resolve": _resolve_gambling_dispute},
    {"id": "musicians", "title": "Ménétriers captifs", "weight": 4,
     "conditions": lambda s: s.crew >= 15 and not s.flags.get("has_musicians"),
     "resolve": _resolve_musicians},
    {"id": "stowaway", "title": "Passager clandestin", "weight": 4,
     "conditions": lambda s: not s.flags.get("stowaway_done"),
     "resolve": _resolve_stowaway},
    {"id": "prize_crew", "title": "Équipage de prise", "weight": 4,
     "conditions": lambda s: s.crew >= 25 and s.loot >= 100 and not s.in_port,
     "resolve": _resolve_prize_crew},
    {"id": "design_colours", "title": "Nos couleurs", "weight": 4,
     "conditions": lambda s: s.crew >= 15 and not s.flags.get("colours_chosen"),
     "resolve": _resolve_design_colours},
    {"id": "slave_revolt", "title": "Révolte en cale", "weight": 6,
     "conditions": lambda s: _count_captives(s) > 0, "resolve": _resolve_slave_revolt},

    # --- Santé & maladies ---
    {"id": "scurvy", "title": "Scorbut", "weight": 6,
     "conditions": lambda s: s.supplies < 20, "resolve": _resolve_scurvy},
    {"id": "disease", "title": "Fièvre à bord", "weight": 5,
     "conditions": lambda s: s.crew > 20, "resolve": _resolve_disease_outbreak},
    {"id": "yellow_fever", "title": "Vomito negro", "weight": 4,
     "conditions": lambda s: s.crew > 30 and s.current_date().year >= 1690,
     "resolve": _resolve_yellow_fever},
    {"id": "amputation", "title": "L'amputation", "weight": 4,
     "conditions": lambda s: s.crew >= 12, "resolve": _resolve_amputation},
    {"id": "dysentery", "title": "Le flux de sang", "weight": 5,
     "conditions": lambda s: s.crew >= 18, "resolve": _resolve_dysentery},
    {"id": "pox", "title": "La vérole", "weight": 4,
     "conditions": lambda s: s.crew >= 16, "resolve": _resolve_pox},
    {"id": "rat_infestation", "title": "Les rats", "weight": 5,
     "conditions": lambda s: s.crew >= 12 and not s.in_port,
     "resolve": _resolve_rat_infestation},

    # --- Autorité, guerre & infamie ---
    {"id": "navy_patrol", "title": "Patrouille royale", "weight": 8,
     "conditions": lambda s: s.reputation >= 2, "resolve": _resolve_navy_patrol},
    {"id": "ambush", "title": "Embuscade côtière", "weight": 4,
     "conditions": lambda s: s.reputation >= 3, "resolve": _resolve_coastal_ambush},
    {"id": "guarda_costa", "title": "Garde-côte espagnol", "weight": 5,
     "conditions": lambda s: s.flags.get("last_region", "caribbean") != "overseas"
                   and not s.in_port and s.reputation >= 1,
     "resolve": _resolve_guarda_costa},
    {"id": "kings_pardon", "title": "Pardon royal", "weight": 3,
     "conditions": lambda s: s.reputation >= 6 and not s.flags.get("pardon_refused"),
     "resolve": _resolve_kings_pardon},
    {"id": "letter_of_marque", "title": "Lettre de marque", "weight": 4,
     "conditions": lambda s: bool(_war_name(s)) and s.reputation >= 2
                   and not s.flags.get("privateer_commission")
                   and not s.flags.get("pardoned"),
     "resolve": _resolve_letter_of_marque},
    {"id": "war_news", "title": "Nouvelle d'une guerre", "weight": 4,
     "conditions": lambda s: not s.in_port, "resolve": _resolve_war_news},
    {"id": "pirate_hunter", "title": "Chasseur de pirates", "weight": 3,
     "conditions": lambda s: s.current_date().year >= 1718 and s.reputation >= 4
                   and not s.flags.get("pardoned"),
     "resolve": _resolve_pirate_hunter},
    {"id": "raid_town", "title": "Sac d'une bourgade", "weight": 3,
     "conditions": lambda s: s.crew >= 50 and s.reputation >= 3 and not s.in_port,
     "resolve": _resolve_raid_town},
    {"id": "press_gang", "title": "La presse de la Navy", "weight": 5,
     "conditions": lambda s: s.in_port and s.crew >= 10,
     "resolve": _resolve_press_gang},
    {"id": "wanted_poster", "title": "Tête mise à prix", "weight": 4,
     "conditions": lambda s: s.in_port and s.reputation >= 4,
     "resolve": _resolve_wanted_poster},
    {"id": "execution_dock", "title": "Pendaison au quai", "weight": 4,
     "conditions": lambda s: s.in_port, "resolve": _resolve_execution_dock},

    # --- Au port : rumeurs & négoce ---
    {"id": "tavern_rumor", "title": "Rumeur de taverne", "weight": 5,
     "conditions": lambda s: s.in_port, "resolve": _resolve_tavern_rumor},
    {"id": "ransom_brokers", "title": "Courtier en rançons", "weight": 5,
     "conditions": lambda s: s.in_port and len(s.prisoners) > 0,
     "resolve": _resolve_ransom_brokers},
    {"id": "fence_the_loot", "title": "Receleur du port", "weight": 6,
     "conditions": lambda s: s.in_port and s.loot >= 100,
     "resolve": _resolve_fence_the_loot},
    {"id": "baldridge_post", "title": "Comptoir de Baldridge", "weight": 6,
     "conditions": lambda s: s.in_port and s.flags.get("last_region") == "overseas",
     "resolve": _resolve_baldridge_post},

    # --- Recrutement de compagnons ---
    {"id": "meet_pilot", "title": "Pilote à la dérive", "weight": 3,
     "conditions": lambda s: not s.has_companion("yusuf_le_maure"),
     "resolve": _resolve_meet_pilot},
    {"id": "meet_surgeon", "title": "Passager clandestin", "weight": 3,
     "conditions": lambda s: not s.has_companion("john_cole_surgeon") and s.reputation >= 2,
     "resolve": _resolve_meet_surgeon},
    {"id": "meet_carpenter", "title": "Une femme à bord", "weight": 2,
     "conditions": lambda s: not s.has_companion("mary_lacy_carpenter") and s.turn >= 6,
     "resolve": _resolve_meet_carpenter},
    {"id": "priest_wreck", "title": "Naufragé en soutane", "weight": 2,
     "conditions": lambda s: not s.has_companion("pere_etienne"),
     "resolve": _resolve_priest_wreck},
]

def pick_event(state):
    eligible = [e for e in EVENTS if e["conditions"](state)]
    if not eligible:
        return None
    weights = [e["weight"] for e in eligible]
    return random.choices(eligible, weights=weights, k=1)[0]
