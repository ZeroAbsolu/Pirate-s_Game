"""
Capitaines jouables. Mélange de personnages historiques attestés
et d'options génériques pour permettre une partie "fictive".

Chaque capitaine apporte un bonus de départ. La période et la zone
sont indiquées pour cohérence historique.

Champs :
    id              : identifiant
    name            : nom complet
    nickname        : surnom éventuel
    period          : années d'activité historique
    region          : zone géographique principale
    biography       : courte biographie ou présentation
    starting_gold   : pièces de huit au départ
    starting_crew   : équipage de base
    bonus           : dictionnaire de bonus appliqués au départ
                      (clé = attribut joueur, valeur = modificateur)
    image           : illustration (pour usage UI futur)
"""

CAPTAINS = {
    "henry_morgan": {
        "id": "henry_morgan",
        "name": "Henry Morgan",
        "nickname": "L'Amiral des Boucaniers",
        "period": "1635-1688",
        "region": "Antilles, Caraïbes",
        "biography": (
            "Gallois devenu boucanier puis corsaire au service de la "
            "Jamaïque anglaise. Pilla Portobelo (1668), Maracaibo (1669) "
            "et Panama (1671). Son code de partage est l'un des plus anciens "
            "documentés. Sera anobli et nommé lieutenant-gouverneur."
        ),
        "starting_gold": 800,
        "starting_crew": 60,
        "bonus": {
            "leadership": 2,       # autorité reconnue
            "reputation": 3,       # nom déjà craint
        },
        "image": "assets/images/cap_morgan.png",
    },
    "barbe_noire": {
        "id": "barbe_noire",
        "name": "Edward Teach",
        "nickname": "Barbe-Noire",
        "period": "1716-1718",
        "region": "Antilles, côtes des Carolines",
        "biography": (
            "Probablement né à Bristol, ancien corsaire de la guerre de "
            "Succession d'Espagne. Mèches lentes nouées dans la barbe pour "
            "terrifier, il évitait souvent le combat par sa seule réputation. "
            "Bloqua le port de Charleston en 1718. Tué au combat la même année."
        ),
        "starting_gold": 500,
        "starting_crew": 70,
        "bonus": {
            "intimidation": 3,
            "reputation": 2,
        },
        "image": "assets/images/cap_barbe_noire.png",
    },
    "bartholomew_roberts": {
        "id": "bartholomew_roberts",
        "name": "Bartholomew Roberts",
        "nickname": "Black Bart",
        "period": "1719-1722",
        "region": "Atlantique, Afrique, Caraïbes",
        "biography": (
            "Gallois originellement marin sur un négrier, capturé par "
            "Howell Davis puis élu capitaine après la mort de ce dernier. "
            "Plus de 400 navires capturés en trois ans. Rédigea des Articles "
            "stricts. Tué d'une mitraille au cap Lopez en février 1722."
        ),
        "starting_gold": 600,
        "starting_crew": 80,
        "bonus": {
            "navigation": 2,
            "discipline": 2,
            "reputation": 1,
        },
        "image": "assets/images/cap_roberts.png",
    },
    "anne_bonny": {
        "id": "anne_bonny",
        "name": "Anne Bonny",
        "nickname": None,
        "period": "1718-1720",
        "region": "Bahamas, Caraïbes",
        "biography": (
            "Née Anne Cormac en Irlande. Compagne de Calico Jack Rackham, "
            "elle combattit aux côtés de Mary Read sur le sloop William. "
            "Capturée en 1720, elle évita la pendaison en plaidant la grossesse."
        ),
        "starting_gold": 400,
        "starting_crew": 45,
        "bonus": {
            "combat": 2,
            "intimidation": 1,
        },
        "image": "assets/images/cap_bonny.png",
    },
    "calico_jack": {
        "id": "calico_jack",
        "name": "John Rackham",
        "nickname": "Calico Jack",
        "period": "1718-1720",
        "region": "Bahamas, Cuba, Jamaïque",
        "biography": (
            "Surnommé pour ses vêtements en calicot indien. Élu capitaine "
            "après avoir destitué Charles Vane pour lâcheté. Spécialiste "
            "des petites prises côtières au sloop. Pendu à Port Royal en 1720."
        ),
        "starting_gold": 450,
        "starting_crew": 40,
        "bonus": {
            "stealth": 2,
            "navigation": 1,
        },
        "image": "assets/images/cap_calico.png",
    },
    "olivier_levasseur": {
        "id": "olivier_levasseur",
        "name": "Olivier Levasseur",
        "nickname": "La Buse",
        "period": "1716-1730",
        "region": "Caraïbes, océan Indien",
        "biography": (
            "Calaisien, ancien corsaire de Louis XIV. Passe à la piraterie "
            "après les traités d'Utrecht. Bascule vers l'océan Indien et "
            "y prend en 1721 le Nossa Senhora do Cabo, l'une des plus grosses "
            "prises de l'histoire. Pendu à Bourbon en 1730."
        ),
        "starting_gold": 550,
        "starting_crew": 65,
        "bonus": {
            "navigation": 3,
            "stealth": 1,
        },
        "image": "assets/images/cap_labuse.png",
    },
    "francois_lolonois": {
        "id": "francois_lolonois",
        "name": "Jean-David Nau",
        "nickname": "L'Olonnais",
        "period": "1660-1668",
        "region": "Caraïbes, golfe du Mexique",
        "biography": (
            "Engagé sablais devenu boucanier de Saint-Domingue, l'un des "
            "premiers grands chefs de la Tortue. Réputé pour sa cruauté envers "
            "les prisonniers espagnols. Saccagea Maracaibo en 1666."
        ),
        "starting_gold": 500,
        "starting_crew": 55,
        "bonus": {
            "intimidation": 3,
            "combat": 1,
        },
        "image": "assets/images/cap_lolonois.png",
    },
    "capitaine_libre": {
        "id": "capitaine_libre",
        "name": "Capitaine sans nom",
        "nickname": None,
        "period": "à définir",
        "region": "libre",
        "biography": (
            "Un capitaine de votre invention. Aucun bonus, mais aucune "
            "réputation préexistante : à vous d'écrire votre légende."
        ),
        "starting_gold": 700,
        "starting_crew": 50,
        "bonus": {},
        "image": "assets/images/cap_libre.png",
    },
}


def get_captain(captain_id: str) -> dict:
    return dict(CAPTAINS[captain_id])


def list_captains() -> list:
    return list(CAPTAINS.values())
