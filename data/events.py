"""
Événements aléatoires en mer.

Chaque événement déclare une scène d'illustration via son `id` :
l'image attendue est `assets/images/events/<id>.png`.

Pour AJOUTER un événement : créer `_resolve_xxx(state, ui)` puis ajouter
l'entrée dans EVENTS plus bas.
"""

import random


# -------------------------------------------------------------------
# Helpers communs
# -------------------------------------------------------------------

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


# -------------------------------------------------------------------
# Résolutions
# -------------------------------------------------------------------

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
    elif roll < 0.85:
        ui.info("L'épave est nettoyée. Rien à prendre.")
    else:
        crew_lost = random.randint(2, 6)
        ui.fail(
            "Embuscade ! Des survivants armés se cachaient dans l'entrepont. "
            f"Vous perdez {crew_lost} hommes avant de reprendre le dessus."
        )
        state.crew = max(0, state.crew - crew_lost)


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


def _resolve_lucky_breeze(state, ui):
    ui.show_scene("events", "lucky_breeze")
    ui.narrate(
        "Vent portant, mer plate. La traversée se fait sans incident. "
        "Le cuisinier sort même un quartier de porc en saumure pour le souper."
    )
    state.morale = min(100, state.morale + 5)
    ui.success("Moral en hausse.")


# -------------------------------------------------------------------
# Recrutement de compagnons via événements en mer
# -------------------------------------------------------------------

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


# -------------------------------------------------------------------
# Nouveaux événements — diversification
# -------------------------------------------------------------------

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
    else:
        ui.info("Vous gardez le large. Discret, mais sans gain.")


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


# -------------------------------------------------------------------
# Catalogue
# -------------------------------------------------------------------

EVENTS = [
    {"id": "storm", "title": "Tempête", "weight": 12,
     "conditions": lambda s: True, "resolve": _resolve_storm},
    {"id": "merchant_sail", "title": "Voile marchande", "weight": 25,
     "conditions": lambda s: True, "resolve": _resolve_merchant_sail},
    {"id": "navy_patrol", "title": "Patrouille royale", "weight": 8,
     "conditions": lambda s: s.reputation >= 2, "resolve": _resolve_navy_patrol},
    {"id": "scurvy", "title": "Scorbut", "weight": 6,
     "conditions": lambda s: s.supplies < 20, "resolve": _resolve_scurvy},
    {"id": "mutiny", "title": "Risque de mutinerie", "weight": 10,
     "conditions": lambda s: s.morale <= 35, "resolve": _resolve_mutiny_threat},
    {"id": "kings_pardon", "title": "Pardon royal", "weight": 3,
     "conditions": lambda s: s.reputation >= 6 and not s.flags.get("pardon_refused"),
     "resolve": _resolve_kings_pardon},
    {"id": "wreck", "title": "Épave à la dérive", "weight": 8,
     "conditions": lambda s: True, "resolve": _resolve_wreck},
    {"id": "tavern_rumor", "title": "Rumeur de taverne", "weight": 5,
     "conditions": lambda s: s.in_port, "resolve": _resolve_tavern_rumor},
    {"id": "disease", "title": "Fièvre à bord", "weight": 5,
     "conditions": lambda s: s.crew > 20, "resolve": _resolve_disease_outbreak},
    {"id": "lucky_breeze", "title": "Vent favorable", "weight": 10,
     "conditions": lambda s: True, "resolve": _resolve_lucky_breeze},

    # Recrutements d'officiers (rares — réservés au compagnon manquant)
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

    # Diversification : prises et rencontres
    {"id": "slave_ship", "title": "Négrier à l'horizon", "weight": 5,
     "conditions": lambda s: s.crew >= 30, "resolve": _resolve_slave_ship},
    {"id": "doldrums", "title": "Calme plat", "weight": 8,
     "conditions": lambda s: True, "resolve": _resolve_doldrums},
    {"id": "consort", "title": "Proposition de consort", "weight": 4,
     "conditions": lambda s: s.reputation >= 2 and not s.in_port,
     "resolve": _resolve_consort_proposal},
    {"id": "careened", "title": "Navire en carène", "weight": 5,
     "conditions": lambda s: True, "resolve": _resolve_careened_ship},
    {"id": "yellow_fever", "title": "Vomito negro", "weight": 4,
     "conditions": lambda s: s.crew > 30 and s.current_date().year >= 1690,
     "resolve": _resolve_yellow_fever},
    {"id": "native_canoes", "title": "Pirogues kalinago", "weight": 5,
     "conditions": lambda s: True, "resolve": _resolve_native_canoes},
    {"id": "whale", "title": "Carcasse de baleine", "weight": 3,
     "conditions": lambda s: True, "resolve": _resolve_whale_carcass},
    {"id": "ambush", "title": "Embuscade côtière", "weight": 4,
     "conditions": lambda s: s.reputation >= 3, "resolve": _resolve_coastal_ambush},
    {"id": "indiaman", "title": "Indiaman à l'horizon", "weight": 3,
     "conditions": lambda s: s.crew >= 60 and s.reputation >= 2, "resolve": _resolve_indiaman},
    {"id": "lady_in_peril", "title": "Dame en péril", "weight": 3,
     "conditions": lambda s: s.crew >= 30, "resolve": _resolve_lady_in_peril},
]


def pick_event(state):
    eligible = [e for e in EVENTS if e["conditions"](state)]
    if not eligible:
        return None
    weights = [e["weight"] for e in eligible]
    return random.choices(eligible, weights=weights, k=1)[0]
