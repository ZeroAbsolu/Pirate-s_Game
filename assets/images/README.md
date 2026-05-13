# Illustrations du jeu

Ce dossier contient les images affichées par l'interface graphique
(`python main.py --gui`).

## Bref

- **Format** : PNG (recommandé), JPEG accepté avec Pillow installé.
- **Convention de nommage** : minuscules + snake_case + identique à l'`id`
  technique de l'élément (voir `data/*.py`).
- **Voir `MANIFEST.md`** pour la liste complète des fichiers attendus
  (92 au total), avec tailles et descriptions.
- **Vérifier ce qui manque** : depuis la racine du jeu, lancer
  `python main.py --check-images`.

## Comportement quand une image manque

Le moteur applique cette cascade de repli :

1. Le fichier demandé (par ex. `ports/nassau/tavern.png`)
2. Pour les sous-scènes de port : le `main.png` du port
3. Une plaque grise avec le nom de la scène et la mention
   « illustration à venir » (le jeu reste jouable).

## Ajouter une image

Il suffit de poser le fichier au bon emplacement, en respectant le nom prévu.
Aucune modification de code n'est nécessaire. Le prochain lancement la trouvera.

## Régénérer le manifeste

Le `MANIFEST.md` a été produit automatiquement à partir du contenu de `data/`.
Quand vous ajoutez un capitaine, un navire, un port ou un événement, la liste
vivante est accessible via :

```
python main.py --check-images
```
