"""
Système de gestion des illustrations.

Convention de nommage et arborescence
=====================================

Toutes les images sont stockées sous `assets/images/`, organisées par catégorie.
Le nom du fichier correspond EXACTEMENT à l'identifiant (`id`) de l'élément.

    assets/images/
    ├── captains/              # un fichier par capitaine
    │   ├── henry_morgan.png
    │   ├── barbe_noire.png
    │   └── ...
    ├── ships/                 # un fichier par type de navire
    │   ├── sloop.png
    │   └── ...
    ├── ports/                 # un dossier par port
    │   ├── nassau/
    │   │   ├── main.png       # vue d'ensemble (obligatoire)
    │   │   ├── tavern.png     # fond de la taverne
    │   │   ├── shipyard.png   # fond du chantier
    │   │   ├── recruit.png    # fond de l'embauche
    │   │   ├── supplies.png   # fond du magasin
    │   │   ├── fence.png      # fond du receleur
    │   │   ├── repair.png     # fond du carénage
    │   │   ├── event_flying_gang.png   # fond d'événement de port
    │   │   └── event_rogers.png
    │   └── tortuga/ ...
    ├── events/                # événements génériques (en mer)
    │   ├── storm.png
    │   └── ...
    ├── actions/               # icônes/illustrations d'actions
    │   ├── sail.png
    │   └── ...
    └── ui/                    # éléments d'interface
        ├── background.png     # fond par défaut (mer + ciel)
        └── logo.png

Format recommandé
=================

  - PNG-24 (RGB, 8 bits/canal) ; PNG-32 (RGBA) si transparence souhaitée.
  - sRGB.
  - Tailles cibles (le jeu redimensionne automatiquement) :
      • Fonds de scène (ports, événements, actions) : 1024×768 (4:3) ou
        1280×720 (16:9). C'est ce qui sert de fond dans la fenêtre.
      • Portraits de capitaine : 600×800 (portrait, ratio 3:4).
      • Illustrations de navires : 800×500 (paysage).
      • Icônes UI : libre (recommandé 256×256 ou plus).

Convention de nommage
=====================

  - Lettres minuscules uniquement.
  - Pas d'espaces ni d'accents : utiliser les `id` techniques.
  - Séparateurs : underscore `_`.
  - Pour un événement de port, préfixer par `event_`.

API
===

Trois fonctions de construction de chemins (sans I/O) :

    captain_image_path(captain_id)
    ship_image_path(ship_id)
    port_image_path(port_id, scene="main")
    port_event_image_path(port_id, event_id)
    event_image_path(event_id)
    action_image_path(action_id)
    ui_image_path(asset_name)

Et trois helpers de résolution :

    resolve(path)                            -> path si présent, sinon None
    resolve_with_fallback(*paths)            -> premier présent, sinon None
    list_expected_images(catalog)            -> tous les chemins attendus
"""

import os


# Racine : <repo>/assets/images
IMAGE_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "assets", "images")
)

IMAGE_EXT = "png"   # extension par défaut


# ---------------------------------------------------------------
# Construction de chemins (jamais d'accès disque)
# ---------------------------------------------------------------

def captain_image_path(captain_id: str) -> str:
    return os.path.join(IMAGE_ROOT, "captains", f"{captain_id}.{IMAGE_EXT}")


def ship_image_path(ship_id: str) -> str:
    return os.path.join(IMAGE_ROOT, "ships", f"{ship_id}.{IMAGE_EXT}")


def port_image_path(port_id: str, scene: str = "main") -> str:
    """Scènes prévues : main, tavern, shipyard, recruit, supplies, fence, repair."""
    return os.path.join(IMAGE_ROOT, "ports", port_id, f"{scene}.{IMAGE_EXT}")


def port_event_image_path(port_id: str, event_id: str) -> str:
    return os.path.join(IMAGE_ROOT, "ports", port_id, f"event_{event_id}.{IMAGE_EXT}")


def event_image_path(event_id: str) -> str:
    return os.path.join(IMAGE_ROOT, "events", f"{event_id}.{IMAGE_EXT}")


def action_image_path(action_id: str) -> str:
    return os.path.join(IMAGE_ROOT, "actions", f"{action_id}.{IMAGE_EXT}")


def ui_image_path(asset: str) -> str:
    return os.path.join(IMAGE_ROOT, "ui", f"{asset}.{IMAGE_EXT}")


def companion_image_path(companion_id: str) -> str:
    return os.path.join(IMAGE_ROOT, "companions", f"{companion_id}.{IMAGE_EXT}")


# ---------------------------------------------------------------
# Résolution (avec vérification disque)
# ---------------------------------------------------------------

def resolve(path: str):
    """Renvoie le chemin si le fichier existe, sinon None."""
    if path and os.path.isfile(path):
        return path
    return None


def resolve_with_fallback(*candidates):
    """Renvoie le premier chemin existant parmi les candidats."""
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None


# ---------------------------------------------------------------
# Listing : utile pour générer un manifeste à jour
# ---------------------------------------------------------------

# Sous-scènes possibles d'un port (au sens des services).
PORT_SCENES = ("main", "tavern", "shipyard", "recruit",
               "supplies", "fence", "repair")


def list_expected_images():
    """
    Renvoie un dict { 'category' : [paths...] } de toutes les images
    attendues compte tenu du contenu actuel des fichiers data/.
    À utiliser pour générer ou vérifier le manifeste.
    """
    # Imports locaux pour ne pas créer de dépendance circulaire au chargement
    from data.captains import CAPTAINS
    from data.ships import SHIPS
    from data.ports import PORTS
    from data.events import EVENTS
    from data.actions import ACTIONS
    from data.port_events import PORT_EVENTS
    from data.companions import COMPANIONS
    from data.buildings import BUILDINGS
    from data.voyages import iter_voyage_event_ids

    out = {
        "captains": [captain_image_path(cid) for cid in CAPTAINS],
        "ships":    [ship_image_path(sid) for sid in SHIPS],
        "ports":    [],
        "port_events": [],
        "buildings": [],
        "events":   ([event_image_path(e["id"]) for e in EVENTS] +
                     [event_image_path(eid) for eid in iter_voyage_event_ids()]),
        "actions":  [action_image_path(a["id"]) for a in ACTIONS],
        "companions": [companion_image_path(cid) for cid in COMPANIONS],
        "ui":       [
            ui_image_path("background"),
            ui_image_path("logo"),
            ui_image_path("game_over"),
            ui_image_path("victory"),
        ],
    }

    for pid, port in PORTS.items():
        # Scène principale (obligatoire) + une scène par service
        out["ports"].append(port_image_path(pid, "main"))
        for service in port.get("services", []):
            out["ports"].append(port_image_path(pid, service))

    for pid, events in PORT_EVENTS.items():
        for e in events:
            out["port_events"].append(port_event_image_path(pid, e["id"]))

    # Bâtiments : leurs scènes vivent dans le dossier du port,
    # comme une sous-scène nommée par l'id du bâtiment.
    for pid, blist in BUILDINGS.items():
        for b in blist:
            out["buildings"].append(port_image_path(pid, b["id"]))

    return out


def check_missing_images():
    """Renvoie la liste des chemins attendus qui n'existent pas sur disque."""
    missing = []
    for category, paths in list_expected_images().items():
        for p in paths:
            if not os.path.isfile(p):
                missing.append((category, p))
    return missing
