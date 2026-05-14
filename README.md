# La Course des Indes

Jeu de gestion de flotte pirate. Période historique : **1400-1799**, focus
sur l'âge d'or de la piraterie atlantique (1650-1730).

## Lancement

```bash
python main.py             # mode texte
python main.py --gui       # mode graphique (Tkinter)
python main.py --check-images   # liste les illustrations attendues
```

Pillow (`pip install Pillow`) est recommandé pour le mode GUI.

## Structure

```
pirate_game/
├── main.py
├── core/
│   ├── engine.py
│   ├── game.py            # GameState (compagnons, prisonniers, flags)
│   ├── ui.py              # UI texte (UTF-8, ANSI, fallback ASCII)
│   ├── ui_gui.py          # UI graphique Tkinter
│   └── images.py          # conventions de chemins
├── data/
│   ├── captains.py        # 8 capitaines (Morgan, Roberts, Bonny…)
│   ├── ships.py           # 9 types de navires
│   ├── ports.py           # 7 ports historiques
│   ├── buildings.py       # 13 bâtiments spécifiques aux ports
│   ├── companions.py      # 15 compagnons (7 hôtesses + 8 officiers)
│   ├── prisoners.py       # 6 types de captifs
│   ├── events.py          # 22 événements en mer
│   ├── port_events.py     # 21 événements à l'arrivée au port
│   └── actions.py         # 6 actions principales
└── assets/images/         # voir MANIFEST.md (136 fichiers attendus)
```

## Contenu

### 7 ports, 13 bâtiments spécifiques

| Port | Bâtiments distinctifs |
|---|---|
| Tortuga | Marché aux engagés et captifs · Camp de boucanage |
| Port Royal | Vendue de Bridge Street · Palais du gouverneur · Hôpital militaire |
| Nassau | Arbre des Articles · Cache d'armes |
| Île Sainte-Marie | Village sakalava |
| La Havane | Asiento espagnol (hostile) |
| Charleston | Vendue · Quartier huguenot |
| Petit-Goâve | Habitation sucrière · Résidence du gouverneur du Casse (1691-1700) |

Chaque bâtiment a sa propre scène/fond et ses interactions thématiques.

### 15 compagnons recrutables

- **7 hôtesses de taverne** (une par port) : recrutées en offrant
  3 cadeaux successifs. Bonus variés (recel, moral, discipline,
  économie de vivres, anti-scorbut, etc.).
- **8 officiers spécialistes** : recrutés via événements à condition
  historique. Mêlent figures attestées (Israel Hands, Walter Kennedy)
  et fictives (Mary Lacy le charpentier en culottes, Yusuf le Maure pilote,
  John Cole chirurgien, Père Étienne, Jean Boudin cuisinier, Vieux Tom
  boucanier).

Les bonus se cumulent avec ceux du capitaine (combat, intimidation,
leadership…) ou s'appliquent comme modificateurs (`repair_discount`,
`supply_savings`, `crew_save_chance`, etc.).

### Système de prisonniers

Six types de captifs (capitaine marchand, passager de haut rang, officier
de marine, matelot, religieux, **captif africain**).

Acquisition :
- Sur abordage marchand : 30-45 % de chances de retenir 1-3 prisonniers.
- Sur prise d'un négrier : événement dédié avec choix moral immédiat.
- Sur prise d'un navire en carène : possibles otages.

Sort des prisonniers (à terre, au bâtiment approprié) :

| Bâtiment | Captifs africains | Engagés / Notables |
|---|---|---|
| Marché aux engagés et captifs (Tortuga) | vente, **moral & réputation -** | vente comme engagés |
| Vendue (Port Royal, Charleston) | vente | vente / rançon |
| Asiento (La Havane) | vente à haut prix, **forte chute de réputation** | refusé |
| Au sein du marché : option « lettre de rançon » | (refusé) | gain élevé, +1 tour d'attente |

Pour les captifs africains spécifiquement, l'événement « Négrier à
l'horizon » propose trois choix au moment de la capture :

- **Libérer** : ~55 % rejoignent l'équipage (rapide montée de moral et
  réputation, dans la veine de Sam Bellamy et certains Articles de Roberts) ;
- **Garder en cale** : transport et vente différée — moral -, mais valeur ;
- **Déposer à terre** : aucun gain, mais reconnaissance morale.

### 22 événements en mer

Tempête, voile marchande, patrouille royale, scorbut, mutinerie, pardon
royal (Act of Grace 1717-1718), épave, fièvre tropicale, vent favorable,
**négrier à l'horizon**, **calme plat**, **proposition de consort**,
**navire en carène**, **vomito negro**, **pirogues kalinago**, **carcasse
de baleine**, **embuscade côtière**, plus les rencontres de recrutement
de compagnons (4).

### Écrans de fin et reprise

Trois fins possibles, chacune avec un écran dédié et un bilan de carrière :

- **Victoire** (`victory_screen`) — pardon royal accepté ou retraite honorable.
- **Game Over** (`game_over_screen`) — défaite avec **cause explicite** (Naufrage, Mutinerie générale, Équipage décimé) et narration.
- **Abandon** (`abandon_screen`) — sortie volontaire du joueur.

À l'issue de chaque partie, l'option **« Commencer une nouvelle partie »** est
proposée. L'interface se réinitialise (journal effacé, panneau de bord remis
à zéro, scène par défaut) sans avoir à relancer le programme.

### 21 événements de port

Audience chez d'Ogeron à Tortuga (1665-75), réception chez Modyford à
Port Royal (1664-71), conseil du Flying Gang à Nassau, arrivée de Woodes
Rogers (juillet 1718), comptoir d'Adam Baldridge à Sainte-Marie (≤1697),
blocus de Charleston par Barbe-Noire (mai 1718), expédition de du Casse
contre Carthagène (1697), rencontres avec Israel Hands, Walter Kennedy,
Jean Boudin, Vieux Tom, etc.

## Convention d'images

| Type | Chemin |
|---|---|
| Capitaine | `assets/images/captains/<id>.png` |
| Compagnon | `assets/images/companions/<id>.png` |
| Navire | `assets/images/ships/<id>.png` |
| Port (vue d'ensemble) | `assets/images/ports/<port_id>/main.png` |
| Sous-scène de port | `assets/images/ports/<port_id>/<scene>.png` |
| Bâtiment | `assets/images/ports/<port_id>/<building_id>.png` |
| Événement de port | `assets/images/ports/<port_id>/event_<event_id>.png` |
| Événement en mer | `assets/images/events/<event_id>.png` |
| Action | `assets/images/actions/<action_id>.png` |

136 fichiers au total (voir `assets/images/MANIFEST.md`). En l'absence
d'une image précise, le moteur retombe sur le `main.png` du port, puis
sur une plaque grise nommée — le jeu reste jouable même sans aucune
illustration.

## Ajouter du contenu

- **Nouveau bâtiment** : compléter `BUILDINGS[<port_id>]` dans
  `data/buildings.py`. Le menu de port l'intègre automatiquement, et
  son image attendue est `ports/<port_id>/<bldg_id>.png`.
- **Nouvel événement** : ajouter à `EVENTS` dans `data/events.py` (en mer)
  ou à `PORT_EVENTS[<port_id>]` (à l'arrivée).
- **Nouveau compagnon** : ajouter à `COMPANIONS` dans `data/companions.py`
  (champ `recruitment.method` = `"gifts"` pour une hôtesse, `"event"` pour
  un officier — dans ce dernier cas, écrire l'événement qui appelle
  `state.add_companion(...)`).
- **Nouveau type de prisonnier** : compléter `PRISONER_TYPES` dans
  `data/prisoners.py`.

## Sources

- Buti, G. & Hroděj, P. (dir.), *Histoire des pirates et des corsaires*,
  CNRS Éditions.
- Rediker, M., *Villains of All Nations: Atlantic Pirates in the Golden Age*.
- Cordingly, D., *Under the Black Flag*.
- Johnson, C., *A General History of the Pyrates* (1724).
- Woodard, C., *The Republic of Pirates*.
