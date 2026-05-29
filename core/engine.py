"""
Moteur de jeu : création de partie, boucle principale, écrans de fin.

Écrans de fin :
  - victory_screen   : pardon royal ou retrait honorable
  - game_over_screen : défaite (cause détaillée + bilan)
  - abandon_screen   : sortie volontaire du joueur
Chacun propose de recommencer une nouvelle partie.
"""

from core.game import GameState
from core.ui import TextUI
from data.captains import list_captains, get_captain
from data.ships import list_starting_ships, get_ship
from data.actions import list_actions


# -------------------------------------------------------------------
# Création de partie
# -------------------------------------------------------------------

def choose_captain(ui) -> dict:
    ui.title("Choix du capitaine")
    captains = list_captains()
    options = []
    for c in captains:
        nick = f" « {c['nickname']} »" if c.get("nickname") else ""
        options.append((f"{c['name']}{nick}  [{c['period']}]", c["id"]))
    cap_id = ui.choose("Sous quels traits prendrez-vous la mer ?", options)
    captain = get_captain(cap_id)
    ui.show_captain_card(captain)

    if cap_id == "capitaine_libre":
        new_name = ui.ask_text("Donnez un nom à votre capitaine :")
        if new_name:
            captain["name"] = new_name
        nick = ui.ask_text("Un surnom ? (laissez vide si aucun)")
        if nick:
            captain["nickname"] = nick

    return captain


def choose_ship(ui) -> dict:
    ui.title("Choix du premier navire")
    starts = list_starting_ships()
    for s in starts:
        ui.show_ship_card(s)
    options = [(s["name"], s["id"]) for s in starts]
    sid = ui.choose("Quel navire voulez-vous prendre ?", options)
    ship_data = get_ship(sid)
    ship_data["hull_max"] = ship_data["hull"] * 10
    ship_data["hull_current"] = ship_data["hull_max"]
    return ship_data


def intro(ui):
    ui.title("LA COURSE DES INDES")
    ui.narrate(
        "1716. Les traités d'Utrecht ont coupé court aux lettres de marque. "
        "Les anciens corsaires, sans solde et sans guerre, basculent dans la "
        "course illégale. Sur la mer des Antilles, on hisse le pavillon noir."
    )
    ui.info("Vous êtes l'un d'eux. À vous d'écrire la suite.")


# -------------------------------------------------------------------
# Boucle de jeu
# -------------------------------------------------------------------

def main_loop(state: GameState, ui):
    while not state.game_over:
        # Annonces des rançons fraîchement encaissées
        news = state.flags.pop("recent_ransom_news", [])
        for n in news:
            p = n["prisoner"]
            ui.success(
                f"Une rançon est arrivée pour {p['label']} ({n['amount']} P8 reçus)."
            )

        state.render_status(ui)
        actions = list_actions(state)
        options = [(a["label"], a["id"]) for a in actions]
        options.append(("Abandonner la partie", "quit"))
        choice = ui.choose("Que faites-vous ce tour ?", options)
        if choice == "quit":
            ui.info("Vous mettez vos hommes à terre et disparaissez avec votre or.")
            state.game_over = True
            state.victory = False
            break

        action = next(a for a in actions if a["id"] == choice)
        action["execute"](state, ui)
        state.check_defeat(ui)


# -------------------------------------------------------------------
# Écrans de fin
# -------------------------------------------------------------------

def _bilan(state, ui):
    """Bilan de carrière commun aux trois fins."""
    ui.divider()
    ui.info("BILAN DE LA CARRIÈRE")
    nick = f" « {state.captain['nickname']} »" if state.captain.get("nickname") else ""
    ui.info(f"  Capitaine     : {state.captain['name']}{nick}")
    ui.info(f"  Navire        : {state.ship['name']}")
    if state.base is not None:
        ui.divider()
    for line in state.base.summary_lines():
        ui.info(line)
    ui.info(f"  Tours tenus   : {state.turn}  (~{state.turn // 2} mois en mer)")
    ui.info(f"  Or final      : {state.gold} pièces de huit")
    ui.info(f"  Réputation    : {state.reputation}")
    if state.companions:
        names = ", ".join(c["name"] for c in state.companions)
        ui.info(f"  Compagnons    : {len(state.companions)} ({names})")
    if state.flags.get("liberated_slaves"):
        ui.info(f"  Captifs libérés : {state.flags['liberated_slaves']}")
    if state.flags.get("sold_enslaved"):
        ui.info(f"  Captifs vendus  : {state.flags['sold_enslaved']}")
    if state.flags.get("sold_to_brothel"):
        ui.info(f"  Captives vendues aux maisons : {state.flags['sold_to_brothel']}")
    ui.divider()


def game_over_screen(state, ui):
    """Affiché en cas de défaite (équipage décimé, naufrage, mutinerie)."""
    ui.show_scene("ui", "game_over")
    ui.game_over_banner("GAME OVER")
    ui.info(f"Cause de la défaite : {state.defeat_reason}")
    ui.narrate(state.defeat_narrative or "")
    _bilan(state, ui)


def victory_screen(state, ui):
    """Pardon royal ou retrait honorable."""
    ui.show_scene("ui", "victory")
    ui.title("Retraite honorable")
    if state.flags.get("pardoned"):
        ui.narrate(
            f"Capitaine {state.captain['name']} a accepté le pardon royal. "
            f"Vous quittez la course avec votre tête et {state.gold} pièces "
            f"de huit. Quelques-uns d'entre vous deviendront chasseurs "
            f"de pirates, comme Hornigold."
        )
    else:
        ui.narrate(
            f"Capitaine {state.captain['name']}, vous quittez la course "
            f"avec {state.gold} pièces de huit et une réputation de "
            f"{state.reputation}."
        )
    _bilan(state, ui)


def abandon_screen(state, ui):
    """Le joueur a choisi de tout abandonner."""
    ui.title("Carrière interrompue")
    ui.narrate(
        f"Capitaine {state.captain['name']} met ses hommes à terre et "
        f"disparaît avec sa part. Quelque part dans les Caraïbes, un "
        f"homme sans nom plante une enseigne de taverne."
    )
    _bilan(state, ui)


# -------------------------------------------------------------------
# Restart
# -------------------------------------------------------------------

def ask_restart(ui) -> bool:
    """Demande au joueur s'il veut recommencer. Renvoie True pour relancer."""
    choice = ui.choose(
        "Que souhaitez-vous faire ?",
        [
            ("Commencer une nouvelle partie", "restart"),
            ("Quitter le jeu", "quit"),
        ],
    )
    return choice == "restart"


# -------------------------------------------------------------------
# Point d'entrée
# -------------------------------------------------------------------

def run(ui=None):
    """Lance le cycle complet : partie → écran de fin → restart éventuel."""
    if ui is None:
        ui = TextUI()

    while True:
        intro(ui)
        captain = choose_captain(ui)
        ship = choose_ship(ui)
        state = GameState(captain, ship)
        main_loop(state, ui)

        # Aiguillage vers le bon écran de fin
        if state.victory:
            victory_screen(state, ui)
        elif state.defeat_reason:
            game_over_screen(state, ui)
        else:
            abandon_screen(state, ui)

        # Proposer de recommencer
        if not ask_restart(ui):
            ui.info("Que la mer vous soit clémente — ou cruelle, c'est selon.")
            return

        # Remise à zéro de l'interface
        ui.reset()
