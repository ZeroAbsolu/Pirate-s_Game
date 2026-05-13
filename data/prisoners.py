"""
Système de prisonniers.

Champs sur chaque instance de prisonnier :
    type        : id du type (cf. PRISONER_TYPES)
    label       : libellé affiché
    gender      : "M" ou "F"
    is_enslaved : bool
    source      : description du contexte de capture (texte libre)

Types féminins :
    Historiquement, les passagères de qualité étaient relativement rares mais
    pas exceptionnelles : épouses, filles ou veuves embarquées pour rejoindre
    un mari ou un père en colonie. Les pirates qui les capturaient gardaient
    presque toujours ces notables pour rançon : la valeur d'une rançon pour
    une dame de qualité était souvent supérieure à celle d'un homme du même
    rang — les familles préférant éviter à la fois le déshonneur public et
    une captivité prolongée.

Vente aux bordels :
    Pratique attestée à Port Royal, Tortuga, et dans une moindre mesure
    Nassau. Mécaniquement, le tarif est ici **forfaitaire et faible** :
    une notable rapporte beaucoup plus en rançon qu'en vente — ce qui
    correspond à la logique économique réelle d'un capitaine pirate
    (Roberts, Bonny, Bellamy) qui gardait ses captifs en vie pour le
    paiement attendu, et n'en disposait autrement qu'en cas d'urgence
    ou d'impossibilité de joindre la famille.
"""

import random


PRISONER_TYPES = {

    # --- Officiers, matelots, religieux (gender par défaut = M) ---
    "merchant_captain": {
        "id": "merchant_captain",
        "label": "Capitaine marchand",
        "default_gender": "M",
        "ransom_value": (150, 350),
        "engage_value": (40, 80),
        "is_enslaved": False,
        "description": "Le commandant d'une prise. Sa compagnie paiera peut-être.",
    },
    "navy_officer": {
        "id": "navy_officer",
        "label": "Officier de marine",
        "default_gender": "M",
        "ransom_value": (200, 500),
        "engage_value": (30, 60),
        "is_enslaved": False,
        "description": "Pris lors d'une escarmouche. Sa pendaison pour piraterie nous attend.",
    },
    "sailor": {
        "id": "sailor",
        "label": "Matelot",
        "default_gender": "M",
        "ransom_value": (5, 20),
        "engage_value": (10, 25),
        "is_enslaved": False,
        "description": "Un simple marin de la prise.",
        "can_join_crew": True,
        "join_chance": 0.4,
    },
    "clergy": {
        "id": "clergy",
        "label": "Religieux",
        "default_gender": "M",
        "ransom_value": (60, 180),
        "engage_value": (5, 15),
        "is_enslaved": False,
        "description": "Un prêtre ou un missionnaire en route pour les colonies.",
    },

    # --- Notables (M ou F selon instance) ---
    "noble_passenger": {
        "id": "noble_passenger",
        "label": "Notable",
        "default_gender": "M",
        "ransom_value": (300, 800),
        "engage_value": (50, 100),
        "is_enslaved": False,
        "description": "Un voyageur en linge de Hollande. Famille fortunée.",
    },

    # --- Types féminins (avec rançons supérieures aux hommes équivalents) ---
    "merchant_lady": {
        "id": "merchant_lady",
        "label": "Marchande / bourgeoise",
        "default_gender": "F",
        "ransom_value": (250, 600),     # > merchant_captain
        "engage_value": (30, 60),
        "is_enslaved": False,
        "description": (
            "Épouse ou fille de marchand, embarquée pour rejoindre la famille "
            "en colonie. Sa parenté paiera vite et bien."
        ),
    },
    "noble_lady": {
        "id": "noble_lady",
        "label": "Dame de qualité",
        "default_gender": "F",
        "ransom_value": (600, 1400),    # >> noble_passenger
        "engage_value": (60, 120),
        "is_enslaved": False,
        "description": (
            "Dame d'une grande maison. Sa famille paiera plus qu'elle ne le "
            "ferait pour un fils — l'honneur en jeu et la captivité prolongée "
            "intolérable."
        ),
    },
    "courtesan": {
        "id": "courtesan",
        "label": "Demoiselle de compagnie",
        "default_gender": "F",
        "ransom_value": (80, 220),
        "engage_value": (20, 40),
        "is_enslaved": False,
        "description": "Suivante d'une dame de qualité, ou voyageuse seule.",
    },

    # --- Captifs africains (esclavage de la traite) ---
    "enslaved_african": {
        "id": "enslaved_african",
        "label": "Captif africain",
        "default_gender": "M",   # genre stocké par instance
        "ransom_value": (0, 0),
        "engage_value": (0, 0),
        "is_enslaved": True,
        "description": (
            "Arraché à sa terre, transporté à fond de cale d'un négrier."
        ),
        "slave_price": (50, 100),
        "morale_cost_sell": 2,
        "join_chance_liberate": 0.55,
    },
}


# Tarif forfaitaire bas du bordel par captive vendue (femme uniquement).
# Indépendant du rang : ce sera toujours nettement inférieur à la rançon.
BROTHEL_PRICE = (60, 100)
BROTHEL_MORALE_COST = 6           # par captive — plus lourd que le marché aux esclaves
BROTHEL_REP_COST_PER_3 = 1


# ---------------------------------------------------------------
# Construction et helpers
# ---------------------------------------------------------------

def make_prisoner(type_id: str, source: str = "", gender: str = None) -> dict:
    """Crée une instance de prisonnier. Si gender non précisé, prend le
    gender par défaut du type."""
    proto = PRISONER_TYPES[type_id]
    return {
        "type": type_id,
        "label": proto["label"],
        "gender": gender or proto.get("default_gender", "M"),
        "source": source,
        "is_enslaved": proto["is_enslaved"],
    }


def count_by_type(prisoners: list) -> dict:
    out = {}
    for p in prisoners:
        out[p["type"]] = out.get(p["type"], 0) + 1
    return out


def filter_by_type(prisoners: list, type_id: str) -> list:
    return [p for p in prisoners if p["type"] == type_id]


def filter_enslaved(prisoners: list) -> list:
    return [p for p in prisoners if p["is_enslaved"]]


def filter_non_enslaved(prisoners: list) -> list:
    return [p for p in prisoners if not p["is_enslaved"]]


def filter_female(prisoners: list) -> list:
    return [p for p in prisoners if p.get("gender") == "F" and not p["is_enslaved"]]


def filter_ransomable(prisoners: list) -> list:
    """Notables, marchands et suivantes — ceux pour qui une lettre de
    rançon a du sens (les simples matelots sont vendus comme engagés)."""
    types = ("noble_passenger", "noble_lady",
             "merchant_captain", "merchant_lady",
             "navy_officer", "clergy", "courtesan")
    return [p for p in prisoners if p["type"] in types]


def value_for_engage(prisoner: dict) -> int:
    if prisoner["is_enslaved"]:
        return 0
    proto = PRISONER_TYPES[prisoner["type"]]
    lo, hi = proto["engage_value"]
    return random.randint(lo, hi)


def value_for_ransom(prisoner: dict) -> int:
    """Rançon envoyée par lettre. Notable F > notable M, historiquement."""
    if prisoner["is_enslaved"]:
        return 0
    proto = PRISONER_TYPES[prisoner["type"]]
    lo, hi = proto["ransom_value"]
    return random.randint(lo, hi)


def value_for_slave_market(prisoner: dict) -> int:
    if not prisoner["is_enslaved"]:
        return 0
    proto = PRISONER_TYPES["enslaved_african"]
    lo, hi = proto["slave_price"]
    return random.randint(lo, hi)


def value_for_brothel(prisoner: dict) -> int:
    """Tarif forfaitaire bas — ne paie que pour des captives non-enslaved."""
    if prisoner.get("gender") != "F" or prisoner["is_enslaved"]:
        return 0
    lo, hi = BROTHEL_PRICE
    return random.randint(lo, hi)


def ransom_delay_turns() -> int:
    """Délai d'acheminement de la rançon, en tours (~2-3 mois)."""
    return random.randint(3, 6)
