"""
Ports historiques accessibles. Tous attestés sur la période 1400-1799.

Services disponibles dans un port :
    - recruit      : recruter de l'équipage
    - repair       : caréner / réparer le navire
    - supplies     : acheter des vivres
    - fence        : revendre du butin (recel)
    - tavern       : recueillir des rumeurs (événements)
    - shipyard     : changer de navire

Chaque port a aussi une « hostility » (1 = sûr pour pirates, 10 = forte garnison).
"""

PORTS = {
    "tortuga": {
        "id": "tortuga",
        "name": "L'île de la Tortue",
        "historical_name": "Tortuga",
        "region": "Hispaniola (Caraïbes)",
        "controlled_by": "France (officieusement les flibustiers)",
        "active_period": "1630-1700",
        "description": (
            "Repaire historique des flibustiers et boucaniers. "
            "Les gouverneurs français de Saint-Domingue toléraient leurs "
            "raids sur les Espagnols. Bertrand d'Ogeron y régularisa la "
            "flibuste dans les années 1660."
        ),
        "services": ["recruit", "repair", "supplies", "fence", "tavern"],
        "hostility": 1,
        "fence_rate": 0.7,        # rachète 70% de la valeur du butin
        "supply_price": 4,        # pièces de huit par unité de vivres
        "image": "assets/images/port_tortuga.png",
    },
    "port_royal": {
        "id": "port_royal",
        "name": "Port Royal",
        "historical_name": "Port Royal",
        "region": "Jamaïque",
        "controlled_by": "Angleterre",
        "active_period": "1655-1692",
        "description": (
            "Surnommée « la ville la plus dépravée du monde ». Base des "
            "corsaires anglais sous le gouverneur Thomas Modyford, qui "
            "commissionnait Henry Morgan. Engloutie aux trois quarts par "
            "le tremblement de terre du 7 juin 1692."
        ),
        "services": ["recruit", "repair", "supplies", "fence", "tavern", "shipyard"],
        "hostility": 3,
        "fence_rate": 0.8,
        "supply_price": 5,
        "image": "assets/images/port_royal.png",
    },
    "nassau": {
        "id": "nassau",
        "name": "Nassau",
        "historical_name": "Nassau, New Providence",
        "region": "Bahamas",
        "controlled_by": "Pirates puis Angleterre (1718)",
        "active_period": "1706-1718",
        "description": (
            "La « République des pirates ». Abandonnée par les Anglais en "
            "1703, occupée par Hornigold, Vane, Teach, Jennings et leurs "
            "compagnies. Woodes Rogers y rétablit l'autorité royale en 1718, "
            "armé du pardon du roi George Ier."
        ),
        "services": ["recruit", "repair", "supplies", "fence", "tavern"],
        "hostility": 1,
        "fence_rate": 0.75,
        "supply_price": 5,
        "image": "assets/images/port_nassau.png",
    },
    "ile_sainte_marie": {
        "id": "ile_sainte_marie",
        "name": "Île Sainte-Marie",
        "historical_name": "Nosy Boraha",
        "region": "Madagascar (océan Indien)",
        "controlled_by": "Communautés pirates",
        "active_period": "1690-1720",
        "description": (
            "Base de la « Pirate Round » : pillage des navires moghols et "
            "des Indiamen. Adam Baldridge y tenait un comptoir financé "
            "depuis New York par Frederick Philipse."
        ),
        "services": ["recruit", "repair", "supplies", "fence", "tavern"],
        "hostility": 2,
        "fence_rate": 0.65,
        "supply_price": 6,
        "image": "assets/images/port_sainte_marie.png",
    },
    "la_havane": {
        "id": "la_havane",
        "name": "La Havane",
        "historical_name": "La Habana",
        "region": "Cuba",
        "controlled_by": "Espagne",
        "active_period": "1519-1799",
        "description": (
            "Port d'attache de la Flotte des Indes. Fortifié par le "
            "Castillo del Morro. Les pirates n'y entrent pas — sauf pour "
            "le brûler comme le fit Jacques de Sores en 1555."
        ),
        "services": ["supplies", "fence"],
        "hostility": 9,
        "fence_rate": 0.4,
        "supply_price": 7,
        "image": "assets/images/port_havane.png",
    },
    "charleston": {
        "id": "charleston",
        "name": "Charles Town",
        "historical_name": "Charles Town",
        "region": "Caroline (Amérique du Nord)",
        "controlled_by": "Angleterre",
        "active_period": "1670-1799",
        "description": (
            "Port colonial complaisant à l'égard des pirates jusqu'aux "
            "années 1710. Bloqué par Barbe-Noire en mai 1718 contre rançon. "
            "Stede Bonnet y fut jugé et pendu la même année."
        ),
        "services": ["recruit", "repair", "supplies", "tavern", "shipyard"],
        "hostility": 5,
        "fence_rate": 0.6,
        "supply_price": 5,
        "image": "assets/images/port_charleston.png",
    },
    "saint_domingue": {
        "id": "saint_domingue",
        "name": "Petit-Goâve",
        "historical_name": "Petit-Goâve, Saint-Domingue",
        "region": "Hispaniola (côte ouest)",
        "controlled_by": "France",
        "active_period": "1660-1720",
        "description": (
            "Port français où s'organisaient les expéditions de flibuste "
            "vers la mer du Sud. Les gouverneurs (de Cussy, du Casse) "
            "y délivraient des commissions de course."
        ),
        "services": ["recruit", "repair", "supplies", "fence", "tavern"],
        "hostility": 3,
        "fence_rate": 0.75,
        "supply_price": 5,
        "image": "assets/images/port_petit_goave.png",
    },
}


def get_port(port_id: str) -> dict:
    return dict(PORTS[port_id])


def list_ports() -> list:
    return list(PORTS.values())
