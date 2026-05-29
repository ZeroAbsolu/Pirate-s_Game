"""
Ressources brutes et biens manufacturés du repaire.

Deux familles d'objets stockables :

  * MATIÈRES PREMIÈRES (`RESOURCES`) : récupérées sur les épaves et les
    prises, ou achetées chez les fournisseurs (« chandler ») des ports.
    Elles servent à CONSTRUIRE les bâtiments du repaire et à les FAIRE
    TOURNER (la distillerie consomme de la mélasse, la fonderie du fer…).

  * BIENS MANUFACTURÉS (`GOODS`) : produits par les ateliers du repaire à
    partir des matières premières. Ils se revendent (marché noir, ports)
    ou s'emploient à bord (rhum → moral, boulets/armes → combat,
    viande boucanée → vivres).

Cohérence historique
====================
  - Le « boucan » (viande de bœuf ou de tortue fumée sur des grils, mot
    tupi via les boucaniers d'Hispaniola) constituait le ravitaillement
    de base des équipages de la Tortue et de Saint-Domingue.
  - Le rhum était distillé à partir de la mélasse, sous-produit du sucre,
    dès le milieu du XVIIᵉ siècle aux Antilles (« kill-devil », guildive).
  - La poudre, le fer en barre, le cordage, la toile à voile et les
    « bois d'œuvre » (madriers, espars) étaient des cargaisons courantes,
    donc des prises plausibles, et des denrées de réapprovisionnement.

Toutes les valeurs sont libellées en pièces de huit (P8). Les prix de
vente fluctuent (offre, discrétion du receleur, marchandage) : voir
`roll_market_factor` et `haggle`.
"""

import random


# ===================================================================
# Matières premières
# ===================================================================

RESOURCES = {
    "bois": {
        "id": "bois", "label": "Bois d'œuvre", "abbr": "bois",
        "base_price": 4,
        "desc": "Madriers, planches, espars. Construction et carénage.",
    },
    "fer": {
        "id": "fer", "label": "Fer & ferrures", "abbr": "fer",
        "base_price": 7,
        "desc": "Barres de fer, clous, ferrures. Forge, fonderie, armurerie.",
    },
    "toile": {
        "id": "toile", "label": "Toile à voile", "abbr": "toile",
        "base_price": 5,
        "desc": "Toile de Hollande pour les voiles et les pansements.",
    },
    "cordage": {
        "id": "cordage", "label": "Cordage & chanvre", "abbr": "cordage",
        "base_price": 4,
        "desc": "Filin, manœuvres, garcettes. Gréement et carénage.",
    },
    "poudre": {
        "id": "poudre", "label": "Poudre", "abbr": "poudre",
        "base_price": 11,
        "desc": "Poudre à canon. Défense du repaire, batteries, fonderie.",
    },
    "pierre": {
        "id": "pierre", "label": "Pierre de taille", "abbr": "pierre",
        "base_price": 3,
        "desc": "Moellons et pierre. Bâtiments durables et fortifications.",
    },
    "melasse": {
        "id": "melasse", "label": "Mélasse", "abbr": "mélasse",
        "base_price": 3,
        "desc": "Sous-produit du sucre. Matière première du rhum (guildive).",
    },
}


# ===================================================================
# Biens manufacturés
# ===================================================================

GOODS = {
    "rhum": {
        "id": "rhum", "label": "Rhum (guildive)", "abbr": "rhum",
        "base_price": 13,
        "desc": "Distillé de la mélasse. Se vend cher, et délie les hommes.",
    },
    "boulets": {
        "id": "boulets", "label": "Boulets & mitraille", "abbr": "boulets",
        "base_price": 9,
        "desc": "Coulés à la fonderie. Pour les pièces du bord, ou la vente.",
    },
    "armes": {
        "id": "armes", "label": "Armes & mousquets", "abbr": "armes",
        "base_price": 15,
        "desc": "Coutelas, piques, mousquets. Arment l'équipage à l'abordage.",
    },
    "boucan": {
        "id": "boucan", "label": "Viande boucanée", "abbr": "boucan",
        "base_price": 5,
        "desc": "Bœuf et tortue fumés. Ravitaillement de longue conservation.",
    },
}


# Index commun pour retrouver un objet quel que soit sa famille.
ALL_ITEMS = {}
ALL_ITEMS.update(RESOURCES)
ALL_ITEMS.update(GOODS)


def is_resource(item_id: str) -> bool:
    return item_id in RESOURCES


def is_good(item_id: str) -> bool:
    return item_id in GOODS


def label(item_id: str) -> str:
    return ALL_ITEMS[item_id]["label"]


def base_price(item_id: str) -> int:
    return ALL_ITEMS[item_id]["base_price"]


def list_resources() -> list:
    return list(RESOURCES.values())


def list_goods() -> list:
    return list(GOODS.values())


# ===================================================================
# Marché : prix variables et marchandage
# ===================================================================

def roll_market_factor(rng=random) -> float:
    """Coefficient de marché du jour (offre/demande, discrétion).

    Entre 0.7 (marché saturé, receleur méfiant) et 1.35 (forte demande).
    """
    return round(rng.uniform(0.70, 1.35), 2)


def sell_unit_price(item_id: str, factor: float = 1.0, trade_bonus: float = 0.0,
                    rng=random) -> int:
    """Prix de VENTE unitaire courant d'un objet (ce que paie l'acheteur).

    `trade_bonus` : avantage du lieu (proximité d'un grand marché,
    marché noir bien tenu, etc.), additif au coefficient.
    """
    price = base_price(item_id) * (factor + trade_bonus)
    return max(1, int(round(price)))


def buy_unit_price(item_id: str, factor: float = 1.0, surcharge: float = 0.0,
                   rng=random) -> int:
    """Prix d'ACHAT unitaire (ce que paie le joueur chez un fournisseur).

    Toujours un peu plus élevé que la revente : marge du marchand.
    `surcharge` : majoration de lieu (comptoir isolé, port hostile…).
    """
    price = base_price(item_id) * (factor * 1.25 + surcharge)
    return max(1, int(round(price)))


def haggle(amount: int, skill: int = 0, rng=random):
    """Marchandage sur une transaction.

    `skill` agrège l'autorité/ruse du capitaine (leadership + discipline
    + ce que l'on veut). Renvoie (montant_ajusté, issue) où issue ∈
    {"gagné", "neutre", "perdu"}.
    """
    roll = rng.random() + 0.06 * max(0, skill)
    if roll > 0.62:
        return int(round(amount * 1.15)), "gagné"
    if roll < 0.28:
        return int(round(amount * 0.90)), "perdu"
    return amount, "neutre"
