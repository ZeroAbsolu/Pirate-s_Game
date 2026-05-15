# MANIFEST — Images d'illustration

Total : **142** fichiers attendus (138 obligatoires + 4 UI facultatifs).

Régénérer la liste vivante : `python main.py --check-images`

## Format

- **PNG** (RGB ou RGBA), sRGB, 8 bits/canal — JPEG accepté avec Pillow.

| Catégorie | Ratio | Pixels |
|-----------|-------|--------|
| Capitaines, compagnons | 3:4 | 600 × 800 |
| Navires | 16:10 | 800 × 500 |
| Scènes (ports, bâtiments, événements) | 4:3 | 1024 × 768 |

## Convention

Minuscules, snake_case, identique à l'`id` technique. Si une image manque,
repli automatique sur `main.png` du port, puis sur une plaque grise.

---

## Capitaines (8)

Affichés sur la fiche du capitaine au moment du choix initial.

- `assets/images/captains/henry_morgan.png` — **Henry Morgan** « L'Amiral des Boucaniers »
- `assets/images/captains/barbe_noire.png` — **Edward Teach** « Barbe-Noire »
- `assets/images/captains/bartholomew_roberts.png` — **Bartholomew Roberts** « Black Bart »
- `assets/images/captains/anne_bonny.png` — **Anne Bonny**
- `assets/images/captains/calico_jack.png` — **John Rackham** « Calico Jack »
- `assets/images/captains/olivier_levasseur.png` — **Olivier Levasseur** « La Buse »
- `assets/images/captains/francois_lolonois.png` — **Jean-David Nau** « L'Olonnais »
- `assets/images/captains/capitaine_libre.png` — **Capitaine sans nom**

## Compagnons (15)

Affichés dans **quatre contextes** :
1. Pendant l'événement de recrutement (officiers : rencontre en mer ou au port).
2. Pendant la **rencontre aléatoire à la taverne** pour les hôtesses
   (déclenchée après *Boire avec l'équipage* — cf. `data/actions.py`,
   `_tavern_hostess_encounter`). Le portrait reste visible pendant toute
   la rencontre, à chaque cadeau offert.
3. Au moment du recrutement effectif.
4. Via l'action **Inspecter** — le joueur peut consulter le portrait et la
   fiche détaillée de n'importe quel compagnon recruté.

- `assets/images/companions/marie_tessart.png` — **Marie Tessart** « L'Acadienne » (Hôtesse de la Cayonne, Tortuga)
- `assets/images/companions/bess_watson.png` — **Bess Watson** « Bess la Rousse » (Hôtesse du Cat and Fiddle, Port Royal)
- `assets/images/companions/hannah_mott.png` — **Hannah Mott** « La Veuve » (Hôtesse de Nassau)
- `assets/images/companions/mahalia.png` — **Mahalia** « La Sakalava » (Hôtesse du comptoir de Baldridge, Sainte-Marie)
- `assets/images/companions/beatriz_castano.png` — **Beatriz Castaño** « La Andaluza » (Hôtesse exilée à La Havane)
- `assets/images/companions/sarah_pemberton.png` — **Sarah Pemberton** (Hôtesse à Charles Town)
- `assets/images/companions/marguerite_lavigne.png` — **Marguerite Lavigne** « Margot la Manchotte » (Hôtesse de Petit-Goâve)
- `assets/images/companions/israel_hands.png` — **Israel Hands** (Maître canonnier)
- `assets/images/companions/walter_kennedy.png` — **Walter Kennedy** (Quartier-maître)
- `assets/images/companions/john_cole_surgeon.png` — **John Cole** « Le Chirurgien » (Chirurgien de bord)
- `assets/images/companions/yusuf_le_maure.png` — **Yusuf** « Le Maure » (Maître pilote)
- `assets/images/companions/pere_etienne.png` — **Étienne de Mortain** « Le père Étienne » (Aumônier déchu)
- `assets/images/companions/jean_boudin.png` — **Jean Boudin** « Le Cuistot » (Cuisinier de bord)
- `assets/images/companions/mary_lacy_carpenter.png` — **Mary Lacy** « Le maître charpentier en culottes » (Maître charpentier)
- `assets/images/companions/vieux_tom_buccaneer.png` — **Vieux Tom** « Le Boucanier » (Boucanier tireur d'élite)

## Navires (9)

Affichés sur la fiche de navire au moment du choix, à l'achat au chantier,
et lors du changement de bord.

- `assets/images/ships/barque_longue.png` — **Barque longue** *(1500-1700)*
- `assets/images/ships/sloop.png` — **Sloop** *(1650-1800)*
- `assets/images/ships/goelette.png` — **Goélette** *(1700-1800)*
- `assets/images/ships/brigantin.png` — **Brigantin** *(1650-1800)*
- `assets/images/ships/fregate_legere.png` — **Frégate légère** *(1650-1800)*
- `assets/images/ships/galion.png` — **Galion** *(1550-1700)*
- `assets/images/ships/vaisseau_ligne.png` — **Vaisseau de ligne** *(1670-1800)*
- `assets/images/ships/caravelle.png` — **Caravelle** *(1400-1550)*
- `assets/images/ships/caraque.png` — **Caraque** *(1400-1570)*

## Ports — scènes générales (40)

Fond de scène pour chaque service du port. Repli automatique sur `main.png`
si une sous-scène manque.

### L'île de la Tortue (`tortuga`) — 6

- `assets/images/ports/tortuga/main.png` — vue d'ensemble du mouillage
- `assets/images/ports/tortuga/recruit.png` — quai d'embauche
- `assets/images/ports/tortuga/repair.png` — carénage sur la plage
- `assets/images/ports/tortuga/supplies.png` — magasin de vivres
- `assets/images/ports/tortuga/fence.png` — comptoir du receleur
- `assets/images/ports/tortuga/tavern.png` — intérieur de taverne

### Port Royal (`port_royal`) — 7

- `assets/images/ports/port_royal/main.png` — vue d'ensemble du mouillage
- `assets/images/ports/port_royal/recruit.png` — quai d'embauche
- `assets/images/ports/port_royal/repair.png` — carénage sur la plage
- `assets/images/ports/port_royal/supplies.png` — magasin de vivres
- `assets/images/ports/port_royal/fence.png` — comptoir du receleur
- `assets/images/ports/port_royal/tavern.png` — intérieur de taverne
- `assets/images/ports/port_royal/shipyard.png` — chantier naval

### Nassau (`nassau`) — 6

- `assets/images/ports/nassau/main.png` — vue d'ensemble du mouillage
- `assets/images/ports/nassau/recruit.png` — quai d'embauche
- `assets/images/ports/nassau/repair.png` — carénage sur la plage
- `assets/images/ports/nassau/supplies.png` — magasin de vivres
- `assets/images/ports/nassau/fence.png` — comptoir du receleur
- `assets/images/ports/nassau/tavern.png` — intérieur de taverne

### Île Sainte-Marie (`ile_sainte_marie`) — 6

- `assets/images/ports/ile_sainte_marie/main.png` — vue d'ensemble du mouillage
- `assets/images/ports/ile_sainte_marie/recruit.png` — quai d'embauche
- `assets/images/ports/ile_sainte_marie/repair.png` — carénage sur la plage
- `assets/images/ports/ile_sainte_marie/supplies.png` — magasin de vivres
- `assets/images/ports/ile_sainte_marie/fence.png` — comptoir du receleur
- `assets/images/ports/ile_sainte_marie/tavern.png` — intérieur de taverne

### La Havane (`la_havane`) — 3

- `assets/images/ports/la_havane/main.png` — vue d'ensemble du mouillage
- `assets/images/ports/la_havane/supplies.png` — magasin de vivres
- `assets/images/ports/la_havane/fence.png` — comptoir du receleur

### Charles Town (`charleston`) — 6

- `assets/images/ports/charleston/main.png` — vue d'ensemble du mouillage
- `assets/images/ports/charleston/recruit.png` — quai d'embauche
- `assets/images/ports/charleston/repair.png` — carénage sur la plage
- `assets/images/ports/charleston/supplies.png` — magasin de vivres
- `assets/images/ports/charleston/tavern.png` — intérieur de taverne
- `assets/images/ports/charleston/shipyard.png` — chantier naval

### Petit-Goâve (`saint_domingue`) — 6

- `assets/images/ports/saint_domingue/main.png` — vue d'ensemble du mouillage
- `assets/images/ports/saint_domingue/recruit.png` — quai d'embauche
- `assets/images/ports/saint_domingue/repair.png` — carénage sur la plage
- `assets/images/ports/saint_domingue/supplies.png` — magasin de vivres
- `assets/images/ports/saint_domingue/fence.png` — comptoir du receleur
- `assets/images/ports/saint_domingue/tavern.png` — intérieur de taverne

## Bâtiments spécifiques (15)

Affichés à l'entrée du bâtiment dans le menu du port.

### L'île de la Tortue (`tortuga`)

- `assets/images/ports/tortuga/captif_market.png` — **Marché aux engagés et captifs**  
   _Tribune publique près du quai. Ouvert aux flibustiers._
- `assets/images/ports/tortuga/boucan_camp.png` — **Camp de boucanage**  
   _Grils fumants, viande de bœuf sauvage d'Hispaniola._
- `assets/images/ports/tortuga/brothel.png` — **Maison de la Cayonne**  
   _Bordel et tripot du port. Achète des captives à bas prix._

### Port Royal (`port_royal`)

- `assets/images/ports/port_royal/vendue.png` — **Vendue de Bridge Street**  
   _Marché public anglais (engagés et captifs)._
- `assets/images/ports/port_royal/governor_palace.png` — **Palais du gouverneur**  
   _Résidence officielle. Audience sur invitation._
- `assets/images/ports/port_royal/military_hospital.png` — **Hôpital militaire**  
   _Chirurgiens d'armée — soignent les blessés moyennant finance._
- `assets/images/ports/port_royal/brothel.png` — **Maison de Bear Garden Lane**  
   _« Sodom of the New World » — tripots, dés, filles publiques._

### Nassau (`nassau`)

- `assets/images/ports/nassau/articles_tree.png` — **Arbre des Articles**  
   _Lieu d'assemblée des capitaines pirates de Nassau._
- `assets/images/ports/nassau/weapon_cache.png` — **Cache d'armes**  
   _Canons et poudre détournés des navires marchands._

### Île Sainte-Marie (`ile_sainte_marie`)

- `assets/images/ports/ile_sainte_marie/village_sakalava.png` — **Village sakalava**  
   _Comptoir d'échanges avec le royaume sakalava du Boina._

### La Havane (`la_havane`)

- `assets/images/ports/la_havane/asiento.png` — **Asiento espagnol**  
   _Bureau du monopole. N'achète que des captifs africains._

### Charles Town (`charleston`)

- `assets/images/ports/charleston/vendue_charleston.png` — **Vendue de Charles Town**  
   _Marché public — esclaves, engagés, marchandises de prise._
- `assets/images/ports/charleston/huguenot_quarter.png` — **Quartier huguenot**  
   _Comptoir des Français réfugiés. Poudre fine, recrues._

### Petit-Goâve (`saint_domingue`)

- `assets/images/ports/saint_domingue/sugar_estate.png` — **Habitation sucrière**  
   _Plantation. Rachète le butin brut à bon prix._
- `assets/images/ports/saint_domingue/du_casse_residence.png` — **Résidence du gouverneur du Casse**  
   _Audience pour commissions de course (1691-1700)._

## Événements de port (21)

Affichés au moment de l'événement, en surimpression du port.

### L'île de la Tortue (`tortuga`)

- `assets/images/ports/tortuga/event_tortuga_ogeron.png` — **Audience chez d'Ogeron**
- `assets/images/ports/tortuga/event_tortuga_brawl.png` — **Querelle à la Cayonne**
- `assets/images/ports/tortuga/event_tortuga_boucaniers.png` — **Boucaniers descendus des hauteurs**
- `assets/images/ports/tortuga/event_tortuga_vieux_tom.png` — **Un vieux boucanier au comptoir**

### Port Royal (`port_royal`)

- `assets/images/ports/port_royal/event_portroyal_modyford.png` — **Réception chez Modyford**
- `assets/images/ports/port_royal/event_portroyal_quake.png` — **Secousses suspectes**
- `assets/images/ports/port_royal/event_portroyal_recruit.png` — **Marins disponibles**
- `assets/images/ports/port_royal/event_portroyal_kennedy.png` — **Un Londonien cherche un capitaine**

### Nassau (`nassau`)

- `assets/images/ports/nassau/event_nassau_flying_gang.png` — **Conseil du Flying Gang**
- `assets/images/ports/nassau/event_nassau_rogers.png` — **Arrivée de Woodes Rogers**
- `assets/images/ports/nassau/event_nassau_articles.png` — **Vote des Articles**
- `assets/images/ports/nassau/event_nassau_israel_hands.png` — **Israel Hands cherche un canon**

### Île Sainte-Marie (`ile_sainte_marie`)

- `assets/images/ports/ile_sainte_marie/event_saintemarie_baldridge.png` — **Comptoir d'Adam Baldridge**
- `assets/images/ports/ile_sainte_marie/event_saintemarie_round.png` — **Proposition de Pirate Round**

### La Havane (`la_havane`)

- `assets/images/ports/la_havane/event_havane_alert.png` — **Garnison en alerte**
- `assets/images/ports/la_havane/event_havane_corrupt.png` — **Fonctionnaire vénal**

### Charles Town (`charleston`)

- `assets/images/ports/charleston/event_charleston_siege.png` — **Blocus de Barbe-Noire**
- `assets/images/ports/charleston/event_charleston_convoy.png` — **Rumeur de convoi**

### Petit-Goâve (`saint_domingue`)

- `assets/images/ports/saint_domingue/event_petitgoave_ducasse.png` — **Expédition de du Casse**
- `assets/images/ports/saint_domingue/event_petitgoave_engages.png` — **Engagés en fuite**
- `assets/images/ports/saint_domingue/event_petitgoave_boudin.png` — **Cuisinier sur le carreau**

## Événements en mer (24)

- `assets/images/events/storm.png` — **Tempête**
- `assets/images/events/merchant_sail.png` — **Voile marchande**
- `assets/images/events/navy_patrol.png` — **Patrouille royale**
- `assets/images/events/scurvy.png` — **Scorbut**
- `assets/images/events/mutiny.png` — **Risque de mutinerie**
- `assets/images/events/kings_pardon.png` — **Pardon royal**
- `assets/images/events/wreck.png` — **Épave à la dérive**
- `assets/images/events/tavern_rumor.png` — **Rumeur de taverne**
- `assets/images/events/disease.png` — **Fièvre à bord**
- `assets/images/events/lucky_breeze.png` — **Vent favorable**
- `assets/images/events/meet_pilot.png` — **Pilote à la dérive**
- `assets/images/events/meet_surgeon.png` — **Passager clandestin**
- `assets/images/events/meet_carpenter.png` — **Une femme à bord**
- `assets/images/events/priest_wreck.png` — **Naufragé en soutane**
- `assets/images/events/slave_ship.png` — **Négrier à l'horizon**
- `assets/images/events/doldrums.png` — **Calme plat**
- `assets/images/events/consort.png` — **Proposition de consort**
- `assets/images/events/careened.png` — **Navire en carène**
- `assets/images/events/yellow_fever.png` — **Vomito negro**
- `assets/images/events/native_canoes.png` — **Pirogues kalinago**
- `assets/images/events/whale.png` — **Carcasse de baleine**
- `assets/images/events/ambush.png` — **Embuscade côtière**
- `assets/images/events/indiaman.png` — **Indiaman à l'horizon**
- `assets/images/events/lady_in_peril.png` — **Dame en péril**

## Actions (6)

Affichées au moment où l'action est choisie depuis le menu principal.

- `assets/images/actions/sail.png` — Naviguer (1 tour, événement aléatoire)
- `assets/images/actions/patrol.png` — Patrouiller une route commerciale
- `assets/images/actions/port.png` — Visiter un port
- `assets/images/actions/rest.png` — Hivernage / repos en crique
- `assets/images/actions/distribute.png` — Distribuer le butin (selon les Articles)
- `assets/images/actions/inspect.png` — Inspecter l'état du navire et de l'équipage  
   _Depuis cette action, le joueur peut consulter le portrait individuel de chaque compagnon recruté._

## UI (facultatif, 4)

- `assets/images/ui/background.png` — fond par défaut
- `assets/images/ui/logo.png` — logo d'intro
- `assets/images/ui/game_over.png` — fond de l'écran de défaite
- `assets/images/ui/victory.png` — fond de l'écran de retraite honorable

---

## Récapitulatif

| Catégorie | Nombre |
|---|---:|
| Capitaines | 8 |
| Compagnons | 15 |
| Navires | 9 |
| Ports — scènes | 40 |
| Bâtiments spécifiques | 15 |
| Événements de port | 21 |
| Événements en mer | 24 |
| Actions | 6 |
| **Sous-total obligatoire** | **138** |
| UI (facultatif) | 4 |
| **Total** | **142** |
