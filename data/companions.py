"""
Compagnons recrutables — officiers nommés et hôtesses de taverne.

Deux mécaniques de recrutement :

  1. **Hôtesses de taverne** (une par port) : se recrutent à force de
     cadeaux. Compteur d'affection par port dans state.affection[port_id].
     Au seuil atteint, la femme peut être embarquée lors d'une visite à
     la taverne.

  2. **Officiers / spécialistes** : se recrutent via des événements
     (de port ou en mer) avec conditions historiques. Cf. port_events.py.

Chaque compagnon apporte un dict `bonuses`. Deux types de bonus existent :

  * **Bonus de statistique** (additifs avec ceux du capitaine) :
      combat, intimidation, navigation, leadership, discipline, stealth

  * **Modificateurs de mécanique** (additifs, capés où nécessaire) :
      morale_floor          : plancher de moral (max parmi tous)
      morale_per_turn       : régénération automatique par tour
      supply_savings        : fraction de vivres économisée (0-0.7)
      repair_discount       : ristourne sur réparation (0-0.6)
      recruit_discount      : ristourne sur embauche (0-0.5)
      fence_bonus           : bonus sur taux de recel (0-0.2)
      desertion_reduction   : réduction des désertions (0-0.8)
      crew_save_chance      : chance d'annuler la moitié d'une perte d'équipage
      scurvy_resist         : 1 = annule scorbut
      hull_per_turn         : régénération de coque par tour
      speed_bonus           : ajout direct au score de vitesse
      spanish_intel         : 1 = révèle les convois espagnols
      event_intel           : 1 = annonce le titre d'un événement avant choix

Pour AJOUTER un compagnon : compléter COMPANIONS plus bas.
Pour qu'il soit recrutable, il faut soit qu'il soit déclaré « hôtesse »
(port défini), soit qu'un événement appelle `state.add_companion(...)`.

Convention d'image : assets/images/companions/<id>.png
"""

COMPANIONS = {

    # ===============================================================
    # HÔTESSES DE TAVERNE — une par port, recrutement par cadeaux
    # ===============================================================

    "marie_tessart": {
        "id": "marie_tessart",
        "name": "Marie Tessart",
        "nickname": "L'Acadienne",
        "type": "tavern_keeper",
        "role": "Hôtesse de la Cayonne",
        "port": "tortuga",
        "period": "Antilles, vers 1670-1685",
        "biography": (
            "Acadienne déportée par les Anglais après 1654, recasée à "
            "Tortuga avec son père bateleur. Tient la salle basse de la "
            "Cayonne. Connaît tous les capitaines de passage."
        ),
        "bonuses": {
            "fence_bonus": 0.05,
            "morale_floor": 30,
        },
        "bonus_label": "Receleuse aguerrie (+5% au recel, moral plancher 30)",
        "recruitment": {
            "method": "gifts",
            "gift_cost": 30,
            "gifts_needed": 3,
            "gift_flavor": "un coupon de toile d'Hollande",
            "intro": (
                "Marie remplit votre godet sans vous regarder. « Encore "
                "un capitaine qui croit qu'on l'attend. »"
            ),
            "accept": (
                "Marie pose son tablier. « Trois mois que j'attendais "
                "qu'un imbécile me propose enfin. » Elle prend son "
                "balluchon et suit vers la chaloupe."
            ),
        },
    },

    "bess_watson": {
        "id": "bess_watson",
        "name": "Bess Watson",
        "nickname": "Bess la Rousse",
        "type": "tavern_keeper",
        "role": "Hôtesse du Cat and Fiddle",
        "port": "port_royal",
        "period": "Jamaïque, 1680-1692",
        "biography": (
            "Fille d'un transporté écossais après la révolte de Monmouth "
            "(1685). Sert au Cat and Fiddle. Sait quels marchands "
            "désarment et quels capitaines paient en bons écus."
        ),
        "bonuses": {
            "desertion_reduction": 0.5,
            "morale_per_turn": 1,
        },
        "bonus_label": "Tient les hommes à carreau (-50% désertion, +1 moral/tour)",
        "recruitment": {
            "method": "gifts",
            "gift_cost": 40,
            "gifts_needed": 3,
            "gift_flavor": "une livre de tabac de Virginie",
            "intro": (
                "Bess vous toise. « Sir Henry Morgan venait ici aussi. "
                "Vous n'êtes pas Morgan. »"
            ),
            "accept": (
                "Bess plie son tablier. « Cette ville sombre, autant que "
                "ce soit en mer. »"
            ),
        },
    },

    "hannah_mott": {
        "id": "hannah_mott",
        "name": "Hannah Mott",
        "nickname": "La Veuve",
        "type": "tavern_keeper",
        "role": "Hôtesse de Nassau",
        "port": "nassau",
        "period": "Bahamas, 1710-1718",
        "biography": (
            "Veuve d'un capitaine corsaire pendu à La Havane en 1712. "
            "Tient la maison sur la pointe. Connaît les Articles par "
            "cœur — elle les a copiés trois fois pour des capitaines."
        ),
        "bonuses": {
            "discipline": 1,
            "event_intel": 1,
        },
        "bonus_label": "Femme avisée (discipline +1, devine les événements)",
        "recruitment": {
            "method": "gifts",
            "gift_cost": 35,
            "gifts_needed": 3,
            "gift_flavor": "un livre de prières relié",
            "intro": (
                "Hannah essuie un gobelet d'étain. « J'en ai vu défiler, "
                "des capitaines. Trois mois et plus de nouvelles. »"
            ),
            "accept": (
                "Hannah enroule les Articles dans un mouchoir. « Si je "
                "dois mourir en mer, autant que ce soit avec un nouveau. »"
            ),
        },
    },

    "mahalia": {
        "id": "mahalia",
        "name": "Mahalia",
        "nickname": "La Sakalava",
        "type": "tavern_keeper",
        "role": "Hôtesse du comptoir de Baldridge",
        "port": "ile_sainte_marie",
        "period": "Madagascar, 1693-1700",
        "biography": (
            "Née sur la côte sakalava de Madagascar, mariée puis libérée "
            "d'un négociant hollandais. Parle malgache, français et "
            "anglais portuaire. Connaît les plantes anti-fièvre."
        ),
        "bonuses": {
            "supply_savings": 0.20,
            "scurvy_resist": 1,
        },
        "bonus_label": "Connaît les herbes (vivres -20%, immunise du scorbut)",
        "recruitment": {
            "method": "gifts",
            "gift_cost": 40,
            "gifts_needed": 3,
            "gift_flavor": "un collier de perles de Bahreïn",
            "intro": (
                "Mahalia broie une racine dans un mortier. « Vous puez "
                "la mer, capitaine. Et le rhum. »"
            ),
            "accept": (
                "Mahalia rassemble ses sachets d'écorces. « Tes hommes "
                "tomberont moins si je viens. »"
            ),
        },
    },

    "beatriz_castano": {
        "id": "beatriz_castano",
        "name": "Beatriz Castaño",
        "nickname": "La Andaluza",
        "type": "tavern_keeper",
        "role": "Hôtesse exilée à La Havane",
        "port": "la_havane",
        "period": "Cuba, 1690-1710",
        "biography": (
            "Andalouse, ancienne danseuse expulsée pour scandale. Sert "
            "dans un bouge des bas-quartiers de La Havane. Hostile aux "
            "officiers du Roi catholique, qui l'ont chassée."
        ),
        "bonuses": {
            "spanish_intel": 1,
            "combat": 1,
        },
        "bonus_label": "Sait où passent les galions (combat +1)",
        "recruitment": {
            "method": "gifts",
            "gift_cost": 50,
            "gifts_needed": 2,    # plus difficile d'accès, mais moins de visites
            "gift_flavor": "une émeraude des mines de Muzo",
            "intro": (
                "Beatriz vous fixe entre deux notes de guitare. « Tu n'es "
                "pas espagnol. Bien. »"
            ),
            "accept": (
                "Beatriz cache un couteau dans sa basquine. « Vamos. "
                "Je connais leurs routes mieux qu'eux. »"
            ),
        },
    },

    "sarah_pemberton": {
        "id": "sarah_pemberton",
        "name": "Sarah Pemberton",
        "nickname": None,
        "type": "tavern_keeper",
        "role": "Hôtesse à Charles Town",
        "port": "charleston",
        "period": "Caroline, 1700-1718",
        "biography": (
            "Fille d'un planteur quaker ruiné par une mauvaise récolte "
            "d'indigo. Sait écrire, lire, tenir un livre de comptes. "
            "Sert au Pink House, taverne respectable du port."
        ),
        "bonuses": {
            "recruit_discount": 0.25,
            "morale_per_turn": 1,
        },
        "bonus_label": "Sait engager les hommes (-25% sur le recrutement)",
        "recruitment": {
            "method": "gifts",
            "gift_cost": 45,
            "gifts_needed": 3,
            "gift_flavor": "une rame de papier de Hollande et une plume",
            "intro": (
                "Sarah tient sa plume comme une dague. « Vous savez "
                "écrire, capitaine ? Pas tous. »"
            ),
            "accept": (
                "Sarah ferme son livre de comptes. « Si je dois sortir "
                "de cette ville, autant que ce soit en mer. »"
            ),
        },
    },

    "marguerite_lavigne": {
        "id": "marguerite_lavigne",
        "name": "Marguerite Lavigne",
        "nickname": "Margot la Manchotte",
        "type": "tavern_keeper",
        "role": "Hôtesse de Petit-Goâve",
        "port": "saint_domingue",
        "period": "Saint-Domingue, 1685-1700",
        "biography": (
            "Veuve d'un engagé picard, a perdu un bras dans la tempête "
            "de 1681 qui a balayé Léogâne. Tient le bouge des flibustiers. "
            "A appris à recoudre les plaies plus vite que personne."
        ),
        "bonuses": {
            "crew_save_chance": 0.30,
            "morale_per_turn": 1,
        },
        "bonus_label": "Sait recoudre (30% de chances de sauver des pertes)",
        "recruitment": {
            "method": "gifts",
            "gift_cost": 35,
            "gifts_needed": 3,
            "gift_flavor": "une trousse d'instruments en argent",
            "intro": (
                "Margot saisit son verre du bras qui lui reste. "
                "« On dit que tu paies bien, capitaine. On dit. »"
            ),
            "accept": (
                "Margot accroche une besace d'instruments. « Quelqu'un "
                "doit recoudre vos hommes. Ce sera moi. »"
            ),
        },
    },

    # ===============================================================
    # OFFICIERS / SPÉCIALISTES — recrutés via événements
    # ===============================================================

    "israel_hands": {
        "id": "israel_hands",
        "name": "Israel Hands",
        "nickname": None,
        "type": "officer",
        "role": "Maître canonnier",
        "port": None,
        "period": "Caraïbes, 1716-1718 (historique)",
        "biography": (
            "Servit comme second sur le Queen Anne's Revenge sous Edward "
            "Teach. Réputé pour son tir au canon. Survécut au combat "
            "d'Ocracoke en 1718, finit ses jours mendiant à Londres."
        ),
        "bonuses": {
            "combat": 2,
        },
        "bonus_label": "Tire au mille (combat +2)",
        "recruitment": {
            "method": "event",
            "intro": (
                "Un grand maigre au front balafré vous aborde sur le quai. "
                "« Israel Hands. J'ai servi sous Teach. Je tire au canon "
                "comme un autre signe son nom. »"
            ),
        },
    },

    "walter_kennedy": {
        "id": "walter_kennedy",
        "name": "Walter Kennedy",
        "nickname": None,
        "type": "officer",
        "role": "Quartier-maître",
        "port": None,
        "period": "Atlantique, 1719-1721 (historique)",
        "biography": (
            "Voleur des bas quartiers de Londres devenu pirate sur le "
            "Royal Rover de Howell Davis puis Bartholomew Roberts. Sait "
            "lire les hommes et tenir les Articles. Mauvaise fin : trahi "
            "et pendu à Wapping."
        ),
        "bonuses": {
            "leadership": 2,
            "desertion_reduction": 0.5,
        },
        "bonus_label": "Quartier-maître redouté (leadership +2, -50% désertion)",
        "recruitment": {
            "method": "event",
            "intro": (
                "Un Londonien au regard fuyant vous trouve à la taverne. "
                "« Walter Kennedy. Je sais conduire les hommes. Je sais "
                "aussi quand un capitaine devient un poids. »"
            ),
        },
    },

    "john_cole_surgeon": {
        "id": "john_cole_surgeon",
        "name": "John Cole",
        "nickname": "Le Chirurgien",
        "type": "officer",
        "role": "Chirurgien de bord",
        "port": None,
        "period": "Atlantique, 1700-1730",
        "biography": (
            "Médecin de Boston expulsé pour faux diplôme. N'a jamais "
            "tué un homme avec sa scie, ce qui est rare au XVIIIe siècle. "
            "Sur les navires pirates, on prenait souvent les chirurgiens "
            "de force, mais Cole, lui, signe les Articles."
        ),
        "bonuses": {
            "crew_save_chance": 0.40,
            "scurvy_resist": 1,
        },
        "bonus_label": "Chirurgien compétent (40% de saves, immunise du scorbut)",
        "recruitment": {
            "method": "event",
            "intro": (
                "Un homme en redingote tachée descend à pas pressés. "
                "« John Cole. La justice de Boston me veut. Embarquez-moi, "
                "je vous sers de chirurgien. »"
            ),
        },
    },

    "yusuf_le_maure": {
        "id": "yusuf_le_maure",
        "name": "Yusuf",
        "nickname": "Le Maure",
        "type": "officer",
        "role": "Maître pilote",
        "port": None,
        "period": "Atlantique, 1690-1720",
        "biography": (
            "Né dans une famille de pilotes barbaresques, capturé enfant "
            "lors d'une attaque maltaise, libéré à Marseille. A appris "
            "les cartes hollandaises, anglaises, françaises et arabes. "
            "Connaît les courants de l'Atlantique comme nul autre."
        ),
        "bonuses": {
            "navigation": 2,
            "speed_bonus": 1,
        },
        "bonus_label": "Maître pilote (navigation +2, vitesse +1)",
        "recruitment": {
            "method": "event",
            "intro": (
                "L'homme parle un français impeccable et trace des "
                "lignes sur le sable du doigt. « Yusuf. Je connais "
                "l'Atlantique mieux que mon nom. »"
            ),
        },
    },

    "pere_etienne": {
        "id": "pere_etienne",
        "name": "Étienne de Mortain",
        "nickname": "Le père Étienne",
        "type": "officer",
        "role": "Aumônier déchu",
        "port": None,
        "period": "1690-1720",
        "biography": (
            "Bénédictin de Cluny, écarté de l'ordre pour usure et "
            "fréquentations équivoques à Nantes. Lit le latin, tient "
            "les comptes, dit l'office quand on le lui demande."
        ),
        "bonuses": {
            "morale_per_turn": 2,
            "morale_floor": 30,
        },
        "bonus_label": "Discours bien sentis (+2 moral/tour, plancher 30)",
        "recruitment": {
            "method": "event",
            "intro": (
                "L'homme en bure tachée, seul survivant d'une épave, "
                "lève une main sale. « Étienne de Mortain, bénédictin "
                "déchu. Dieu et moi nous fâchons souvent. »"
            ),
        },
    },

    "jean_boudin": {
        "id": "jean_boudin",
        "name": "Jean Boudin",
        "nickname": "Le Cuistot",
        "type": "officer",
        "role": "Cuisinier de bord",
        "port": None,
        "period": "Saint-Domingue, 1685-1715",
        "biography": (
            "Ancien marmiton à la résidence du gouverneur de Saint-Domingue. "
            "Sait tirer trois soupes d'un baril de bœuf salé. Renvoyé "
            "pour avoir bu le bordeaux de Monsieur du Casse."
        ),
        "bonuses": {
            "supply_savings": 0.30,
            "morale_per_turn": 1,
        },
        "bonus_label": "Économise le baril (vivres -30%, +1 moral/tour)",
        "recruitment": {
            "method": "event",
            "intro": (
                "Un gros homme à tablier de cuir fait signe. « Jean "
                "Boudin. Je nourris cinquante hommes avec ce que d'autres "
                "donnent à trente. »"
            ),
        },
    },

    "mary_lacy_carpenter": {
        "id": "mary_lacy_carpenter",
        "name": "Mary Lacy",
        "nickname": "Le maître charpentier en culottes",
        "type": "officer",
        "role": "Maître charpentier",
        "port": None,
        "period": "Atlantique, 1700-1730",
        "biography": (
            "Embarquée à quinze ans déguisée en garçon sous le nom de "
            "William Chandler. Devenue maître charpentier à force. Inspirée "
            "des cas historiques de Hannah Snell et Mary Lacy."
        ),
        "bonuses": {
            "repair_discount": 0.30,
            "hull_per_turn": 1,
        },
        "bonus_label": "Charpentier hors pair (-30% réparation, +1 coque/tour)",
        "recruitment": {
            "method": "event",
            "intro": (
                "Un jeune charpentier au timbre étrangement aigu vous "
                "tend une plane. « Embauchez-moi à la place de votre "
                "ancien — j'ai vu ce qu'il a fait à votre bordage. »"
            ),
        },
    },

    "vieux_tom_buccaneer": {
        "id": "vieux_tom_buccaneer",
        "name": "Vieux Tom",
        "nickname": "Le Boucanier",
        "type": "officer",
        "role": "Boucanier tireur d'élite",
        "port": None,
        "period": "Hispaniola, 1670-1700",
        "biography": (
            "Trente ans à fumer le bœuf sauvage dans les collines de "
            "Saint-Domingue. Tire au long fusil à 200 pas. A connu "
            "l'Olonnais et n'aime pas en parler."
        ),
        "bonuses": {
            "combat": 1,
            "intimidation": 1,
        },
        "bonus_label": "Tireur des bois (combat +1, intimidation +1)",
        "recruitment": {
            "method": "event",
            "intro": (
                "Un vieil homme sec, fusil de boucanier sur l'épaule, "
                "vous dévisage. « Tom. J'ai fumé la viande trop "
                "longtemps. Je veux voir la mer avant de mourir. »"
            ),
        },
    },
}


# ---------------------------------------------------------------
# Helpers d'accès
# ---------------------------------------------------------------

def get_companion(companion_id: str) -> dict:
    return dict(COMPANIONS[companion_id])


def get_tavern_keeper(port_id: str):
    """Renvoie l'hôtesse associée à un port, ou None."""
    for c in COMPANIONS.values():
        if c.get("type") == "tavern_keeper" and c.get("port") == port_id:
            return dict(c)
    return None


def list_companions() -> list:
    return list(COMPANIONS.values())


# ---------------------------------------------------------------
# Application des bonus
# ---------------------------------------------------------------

# Bonus de statistique (additifs, pas de cap)
STAT_BONUSES = {"combat", "intimidation", "navigation",
                "leadership", "discipline", "stealth"}

# Modificateurs « pourcentage » avec un plafond pour éviter les abus
CAPPED_MODIFIERS = {
    "supply_savings":      0.70,
    "repair_discount":     0.60,
    "recruit_discount":    0.50,
    "fence_bonus":         0.20,
    "desertion_reduction": 0.80,
    "crew_save_chance":    0.70,
}

# Modificateurs additifs sans plafond
ADDITIVE_MODIFIERS = {"morale_per_turn", "hull_per_turn", "speed_bonus"}

# Modificateurs « max » (on prend la valeur la plus forte)
MAX_MODIFIERS = {"morale_floor"}

# Modificateurs binaires
BINARY_MODIFIERS = {"scurvy_resist", "spanish_intel", "event_intel"}


def aggregate_bonuses(captain_bonuses: dict, companions: list) -> dict:
    """
    Combine les bonus du capitaine + ceux des compagnons, en appliquant
    les règles de chaque catégorie (somme, somme avec cap, max, ou OU logique).
    """
    out = {}

    def _collect(name):
        vals = []
        if name in captain_bonuses:
            vals.append(captain_bonuses[name])
        for c in companions:
            if name in c.get("bonuses", {}):
                vals.append(c["bonuses"][name])
        return vals

    for name in STAT_BONUSES | ADDITIVE_MODIFIERS:
        vals = _collect(name)
        if vals:
            out[name] = sum(vals)

    for name, cap in CAPPED_MODIFIERS.items():
        vals = _collect(name)
        if vals:
            out[name] = min(cap, sum(vals))

    for name in MAX_MODIFIERS:
        vals = _collect(name)
        if vals:
            out[name] = max(vals)

    for name in BINARY_MODIFIERS:
        vals = _collect(name)
        if vals:
            out[name] = 1 if any(v for v in vals) else 0

    return out
