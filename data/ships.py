"""
Navires historiques disponibles dans le jeu.
Période couverte : 1400-1799.

Chaque navire est défini par un dictionnaire avec ses caractéristiques.
Pour ajouter un nouveau navire, il suffit d'ajouter une entrée dans SHIPS.

Champs :
    id              : identifiant unique
    name            : nom francisé du type de navire
    period          : période d'usage approximative
    masts           : nombre de mâts
    crew_min/max    : équipage minimum / maximum
    guns            : nombre typique de canons
    speed           : vitesse relative (1-10)
    cargo           : capacité de cale (1-10)
    hull            : robustesse de coque (1-10)
    cost            : coût d'achat en pièces de huit
    description     : description historique
    image           : chemin relatif vers l'illustration (optionnel, pour usage futur)
"""

SHIPS = {
    "barque_longue": {
        "id": "barque_longue",
        "name": "Barque longue",
        "period": "1500-1700",
        "masts": 1,
        "crew_min": 20,
        "crew_max": 40,
        "guns": 4,
        "speed": 7,
        "cargo": 2,
        "hull": 3,
        "cost": 600,
        "description": (
            "Petit voilier ponté à un mât, utilisé pour le cabotage et "
            "la course côtière. Idéal pour débuter, peu armé mais agile."
        ),
        "image": "assets/images/barque_longue.png",
    },
    "sloop": {
        "id": "sloop",
        "name": "Sloop",
        "period": "1650-1800",
        "masts": 1,
        "crew_min": 40,
        "crew_max": 75,
        "guns": 10,
        "speed": 9,
        "cargo": 3,
        "hull": 4,
        "cost": 1500,
        "description": (
            "Voilier rapide et maniable à un mât, gréement aurique. "
            "Favori des flibustiers des Antilles (Calico Jack, Stede Bonnet). "
            "Faible tirant d'eau, parfait pour les criques."
        ),
        "image": "assets/images/sloop.png",
    },
    "goelette": {
        "id": "goelette",
        "name": "Goélette",
        "period": "1700-1800",
        "masts": 2,
        "crew_min": 50,
        "crew_max": 90,
        "guns": 12,
        "speed": 8,
        "cargo": 4,
        "hull": 4,
        "cost": 2200,
        "description": (
            "Voilier à deux mâts à voiles auriques, apparu au début du XVIIIe. "
            "Manœuvrable et rapide au près, prisée des contrebandiers."
        ),
        "image": "assets/images/goelette.png",
    },
    "brigantin": {
        "id": "brigantin",
        "name": "Brigantin",
        "period": "1650-1800",
        "masts": 2,
        "crew_min": 70,
        "crew_max": 130,
        "guns": 14,
        "speed": 7,
        "cargo": 5,
        "hull": 5,
        "cost": 3000,
        "description": (
            "Deux-mâts à voiles carrées et auriques. Polyvalent : "
            "assez rapide pour la chasse, assez solide pour le combat. "
            "Edward England et Howell Davis y avaient leurs préférences."
        ),
        "image": "assets/images/brigantin.png",
    },
    "fregate_legere": {
        "id": "fregate_legere",
        "name": "Frégate légère",
        "period": "1650-1800",
        "masts": 3,
        "crew_min": 120,
        "crew_max": 200,
        "guns": 28,
        "speed": 7,
        "cargo": 6,
        "hull": 7,
        "cost": 6500,
        "description": (
            "Trois-mâts de guerre rapide. Le Queen Anne's Revenge de "
            "Barbe-Noire en était une, prise sur les Français. "
            "Compromis idéal entre force de feu et vitesse."
        ),
        "image": "assets/images/fregate_legere.png",
    },
    "galion": {
        "id": "galion",
        "name": "Galion",
        "period": "1550-1700",
        "masts": 3,
        "crew_min": 150,
        "crew_max": 250,
        "guns": 36,
        "speed": 4,
        "cargo": 9,
        "hull": 8,
        "cost": 9000,
        "description": (
            "Lourd trois-mâts espagnol des flottes des Indes. "
            "Énorme cale, château arrière imposant, mais lent. "
            "Plus une proie qu'un navire de pirate, sauf prise rare."
        ),
        "image": "assets/images/galion.png",
    },
    "vaisseau_ligne": {
        "id": "vaisseau_ligne",
        "name": "Vaisseau de ligne",
        "period": "1670-1800",
        "masts": 3,
        "crew_min": 250,
        "crew_max": 500,
        "guns": 60,
        "speed": 5,
        "cargo": 7,
        "hull": 10,
        "cost": 18000,
        "description": (
            "Forteresse flottante à plusieurs ponts de batterie. "
            "Rarement entre mains pirates : Bartholomew Roberts y est "
            "parvenu en s'emparant du Royal Fortune. Coûte cher en équipage."
        ),
        "image": "assets/images/vaisseau_ligne.png",
    },
    # --- Période antérieure, plutôt 1400-1550 ---
    "caravelle": {
        "id": "caravelle",
        "name": "Caravelle",
        "period": "1400-1550",
        "masts": 3,
        "crew_min": 20,
        "crew_max": 40,
        "guns": 6,
        "speed": 7,
        "cargo": 4,
        "hull": 4,
        "cost": 1200,
        "description": (
            "Voilier portugais à voiles latines, capable de remonter "
            "au vent. Navire des grandes découvertes, utilisé par "
            "les corsaires barbaresques et atlantiques."
        ),
        "image": "assets/images/caravelle.png",
    },
    "caraque": {
        "id": "caraque",
        "name": "Caraque",
        "period": "1400-1570",
        "masts": 3,
        "crew_min": 60,
        "crew_max": 120,
        "guns": 20,
        "speed": 4,
        "cargo": 8,
        "hull": 7,
        "cost": 4500,
        "description": (
            "Grand navire océanique du XVe au XVIe siècle, ancêtre du galion. "
            "Lourde, ventrue, mais capable de longs voyages."
        ),
        "image": "assets/images/caraque.png",
    },
}


def get_ship(ship_id: str) -> dict:
    """Renvoie une COPIE des données du navire (pour ne pas altérer l'original)."""
    return dict(SHIPS[ship_id])


def list_starting_ships() -> list:
    """Navires raisonnablement accessibles en début de partie."""
    return [SHIPS["barque_longue"], SHIPS["sloop"], SHIPS["caravelle"]]


def list_all_ships() -> list:
    return list(SHIPS.values())
