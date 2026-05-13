"""
Moteur de jeu : création de partie, boucle principale, écran de fin.

Le moteur reçoit son UI en paramètre — TextUI ou GraphicalUI.
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


def end_screen(state, ui):
    ui.title("Fin de la traversée")
    if state.victory:
        ui.success(
            f"Capitaine {state.captain['name']}, vous quittez la course "
            f"avec {state.gold} pièces de huit et une réputation de {state.reputation}."
        )
    else:
        ui.fail(
            f"Capitaine {state.captain['name']} a sombré. "
            f"Tours joués : {state.turn}. Or final : {state.gold}. "
            f"Réputation : {state.reputation}."
        )
    ui.divider()
    ui.info("Que la mer vous soit clémente — ou cruelle, c'est selon.")


# -------------------------------------------------------------------
# Point d'entrée
# -------------------------------------------------------------------

def run(ui=None):
    """Lance une partie. Si aucune UI n'est passée, on utilise TextUI."""
    if ui is None:
        ui = TextUI()
    intro(ui)
    captain = choose_captain(ui)
    ship = choose_ship(ui)
    state = GameState(captain, ship)
    main_loop(state, ui)
    end_screen(state, ui)
