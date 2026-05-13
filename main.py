"""
Point d'entrée du jeu « La Course des Indes ».

Lancement :
    python main.py            # interface texte (par défaut)
    python main.py --gui      # interface graphique (Tkinter)
    python main.py --check-images   # liste les images attendues / manquantes

Pour ajouter du contenu, voir data/*.py.
Pour la convention des images, voir core/images.py et assets/images/MANIFEST.md.
"""

import os
import sys
import argparse


# Ajoute le dossier du jeu au PYTHONPATH (quel que soit le cwd)
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# Auto-réparation : crée les __init__.py manquants (utile après téléchargement)
for _sub in ("core", "data"):
    _dir = os.path.join(HERE, _sub)
    if not os.path.isdir(_dir):
        sys.stderr.write(
            f"\nERREUR : le dossier '{_sub}/' est introuvable à côté de main.py.\n"
        )
        sys.exit(1)
    _init = os.path.join(_dir, "__init__.py")
    if not os.path.isfile(_init):
        try:
            open(_init, "w").close()
        except OSError:
            pass


def parse_args():
    p = argparse.ArgumentParser(description="La Course des Indes — jeu de gestion pirate.")
    p.add_argument("--gui", action="store_true",
                   help="Lance l'interface graphique (Tkinter).")
    p.add_argument("--check-images", action="store_true",
                   help="Liste toutes les images attendues et manquantes, puis quitte.")
    return p.parse_args()


def cmd_check_images():
    from core import images
    expected = images.list_expected_images()
    missing = images.check_missing_images()

    print()
    print(f"Racine des images : {images.IMAGE_ROOT}")
    print()
    total = sum(len(v) for v in expected.values())
    print(f"Images attendues : {total}")
    for cat, paths in expected.items():
        print(f"  - {cat:<14} : {len(paths)} fichier(s)")

    print()
    if missing:
        print(f"Images MANQUANTES : {len(missing)}")
        by_cat = {}
        for cat, p in missing:
            by_cat.setdefault(cat, []).append(p)
        for cat, paths in by_cat.items():
            print(f"\n  [{cat}]")
            for p in paths:
                rel = os.path.relpath(p, HERE)
                print(f"    {rel}")
    else:
        print("Toutes les images attendues sont présentes.")


def main():
    args = parse_args()

    if args.check_images:
        cmd_check_images()
        return

    from core.engine import run

    if args.gui:
        try:
            from core.ui_gui import GraphicalUI
        except ImportError as exc:
            sys.stderr.write(
                f"Impossible de charger l'interface graphique : {exc}\n"
                f"Tkinter est-il installé ?\n"
            )
            sys.exit(1)
        ui = GraphicalUI()
        try:
            run(ui)
        except KeyboardInterrupt:
            pass
        # Maintenir la fenêtre ouverte sur l'écran de fin
        ui.mainloop()
    else:
        try:
            run()
        except KeyboardInterrupt:
            print("\n\nPartie interrompue. À la prochaine, capitaine.")


if __name__ == "__main__":
    main()
