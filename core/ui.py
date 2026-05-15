"""
Couche d'interface utilisateur — version texte.

API publique (identique entre TextUI et GraphicalUI) :
    info / narrate / success / fail / event_banner / title / divider
    ask_text / ask_int / choose
    show_captain_card / show_ship_card
    render_status(state)
    show_image(path)                       # affichage direct d'un chemin
    show_scene(category, instance_id, variant=None)
                                            # affichage par catégorie + id

Voir core/ui_gui.py pour la version Tkinter.

Encodage :
  - Force UTF-8 sur la sortie standard (Python 3.7+) avec fallback,
  - Active les séquences ANSI (VT100) sur Windows 10+,
  - Bascule en symboles ASCII si le terminal ne supporte pas l'unicode,
  - Désactive les couleurs si la sortie n'est pas un terminal.
"""

import os
import sys

from core import images


# ---------------------------------------------------------------
# Setup encodage
# ---------------------------------------------------------------

def _setup_stdout():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if sys.platform == "win32":
        try:
            os.system("")   # active VT100 sur Win10+
        except Exception:
            pass


_setup_stdout()


def _supports_unicode() -> bool:
    enc = (getattr(sys.stdout, "encoding", "") or "").lower()
    if "utf" in enc:
        return True
    try:
        "✓◆—«»".encode(enc or "ascii")
        return True
    except (UnicodeEncodeError, LookupError):
        return False


def _supports_ansi() -> bool:
    if not sys.stdout.isatty():
        return False
    return True


_UNICODE = _supports_unicode()
_ANSI = _supports_ansi()


def _c(code: str) -> str:
    return code if _ANSI else ""


C_RESET   = _c("\033[0m")
C_BOLD    = _c("\033[1m")
C_DIM     = _c("\033[2m")
C_RED     = _c("\033[31m")
C_GREEN   = _c("\033[32m")
C_YELLOW  = _c("\033[33m")
C_BLUE    = _c("\033[34m")
C_MAGENTA = _c("\033[35m")
C_CYAN    = _c("\033[36m")


if _UNICODE:
    SYM_OK, SYM_FAIL, SYM_DIAMOND = "✓", "✗", "◆"
    SYM_EMDASH, SYM_LQUO, SYM_RQUO = "—", "«", "»"
else:
    SYM_OK, SYM_FAIL, SYM_DIAMOND = "[+]", "[-]", "##"
    SYM_EMDASH, SYM_LQUO, SYM_RQUO = "-", '"', '"'


def _ascii_safe(text: str) -> str:
    if _UNICODE:
        return text
    table = {
        "«": '"', "»": '"', "—": "-", "–": "-",
        "œ": "oe", "Œ": "OE", "æ": "ae",
        "✓": "[+]", "✗": "[-]", "◆": "##",
    }
    out = text
    for k, v in table.items():
        out = out.replace(k, v)
    return out


def _safe_print(text: str = ""):
    try:
        print(_ascii_safe(text))
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"))


# ---------------------------------------------------------------
# Date FR
# ---------------------------------------------------------------

_MONTHS_FR = ["janvier", "février", "mars", "avril", "mai", "juin",
              "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def format_date_fr(d) -> str:
    return f"{d.day} {_MONTHS_FR[d.month - 1]} {d.year}"


# ---------------------------------------------------------------
# Wrap
# ---------------------------------------------------------------

def _wrap(text: str, width: int):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------
# UI texte
# ---------------------------------------------------------------

class TextUI:
    """Interface textuelle pour console."""

    # ----- Sorties -----
    def title(self, text):
        _safe_print(); _safe_print(f"{C_BOLD}{C_YELLOW}=== {text} ==={C_RESET}")

    def divider(self):
        _safe_print(f"{C_DIM}" + "-" * 64 + f"{C_RESET}")

    def info(self, text):
        _safe_print(f"  {text}")

    def narrate(self, text):
        _safe_print(); _safe_print(f"{C_CYAN}  {text}{C_RESET}")

    def success(self, text):
        _safe_print(f"{C_GREEN}  {SYM_OK} {text}{C_RESET}")

    def fail(self, text):
        _safe_print(f"{C_RED}  {SYM_FAIL} {text}{C_RESET}")

    def event_banner(self, title):
        _safe_print()
        _safe_print(f"{C_BOLD}{C_MAGENTA}  {SYM_DIAMOND} ÉVÉNEMENT : {title} {SYM_DIAMOND}{C_RESET}")

    def game_over_banner(self, text):
        """Affichage dramatique de fin de partie."""
        bar = "=" * 56
        _safe_print()
        _safe_print(f"{C_BOLD}{C_RED}{bar}{C_RESET}")
        _safe_print(f"{C_BOLD}{C_RED}{text.center(56)}{C_RESET}")
        _safe_print(f"{C_BOLD}{C_RED}{bar}{C_RESET}")
        _safe_print()

    def reset(self):
        """Remise à zéro avant une nouvelle partie. En texte : rien à faire
        (la nouvelle partie s'enchaîne dans la même console)."""
        _safe_print()
        _safe_print(f"{C_BOLD}{C_YELLOW}~~~ NOUVELLE PARTIE ~~~{C_RESET}")
        _safe_print()

    # ----- Images (en texte, on signale juste leur présence) -----
    # En mode texte, un terminal ne peut pas afficher d'image : on se
    # contente de confirmer que l'illustration a bien été trouvée. Pour
    # la voir réellement, lancer le jeu avec : python main.py --gui
    _image_hint_shown = False   # astuce affichée une seule fois par session

    def show_image(self, path):
        if path and os.path.isfile(path):
            if not TextUI._image_hint_shown:
                _safe_print(
                    f"{C_DIM}  (Astuce : les illustrations s'affichent dans la "
                    f"fenêtre graphique. Lancez « python main.py --gui »){C_RESET}"
                )
                TextUI._image_hint_shown = True
            _safe_print(
                f"{C_DIM}  [illustration trouvée : {os.path.basename(path)}]{C_RESET}"
            )

    def show_scene(self, category, instance_id, variant=None):
        """
        Indique au joueur (visuellement, en mode graphique ; symboliquement
        en mode texte) la scène en cours.

        category : 'captains' | 'ships' | 'ports' | 'events' | 'actions' | 'ui'
        instance_id : id de l'entité (ou id du port pour les port_events)
        variant : pour les ports, sous-scène ('main', 'tavern', 'shipyard'…)
                  pour les port_events, l'id de l'événement de port (préfixé)
        """
        path = self._resolve_scene(category, instance_id, variant)
        self.show_image(path)

    def _resolve_scene(self, category, instance_id, variant=None):
        """Construit le chemin selon la convention, avec repli."""
        if category == "ports":
            primary = images.port_image_path(instance_id, variant or "main")
            fallback = images.port_image_path(instance_id, "main")
            return images.resolve_with_fallback(primary, fallback)
        if category == "port_events":
            # instance_id = port_id, variant = event_id
            primary = images.port_event_image_path(instance_id, variant)
            fallback = images.port_image_path(instance_id, "main")
            return images.resolve_with_fallback(primary, fallback)
        if category == "captains":
            return images.resolve(images.captain_image_path(instance_id))
        if category == "ships":
            return images.resolve(images.ship_image_path(instance_id))
        if category == "companions":
            return images.resolve(images.companion_image_path(instance_id))
        if category == "events":
            return images.resolve(images.event_image_path(instance_id))
        if category == "actions":
            return images.resolve(images.action_image_path(instance_id))
        if category == "ui":
            return images.resolve(images.ui_image_path(instance_id))
        return None

    # ----- Saisie -----
    def ask_text(self, prompt):
        try:
            return input(_ascii_safe(f"{C_BOLD}> {prompt} {C_RESET}")).strip()
        except EOFError:
            return ""

    def ask_int(self, prompt, min_val=0, max_val=9999):
        while True:
            raw = self.ask_text(prompt)
            if raw == "":
                return min_val
            try:
                val = int(raw)
                if min_val <= val <= max_val:
                    return val
                self.fail(f"Saisissez un nombre entre {min_val} et {max_val}.")
            except ValueError:
                self.fail("Nombre attendu.")

    def choose(self, prompt, options):
        _safe_print()
        _safe_print(f"  {C_BOLD}{prompt}{C_RESET}")
        for i, (label, _) in enumerate(options, 1):
            _safe_print(f"   {C_YELLOW}{i:>2}.{C_RESET} {label}")
        while True:
            raw = self.ask_text("Choix")
            try:
                idx = int(raw)
                if 1 <= idx <= len(options):
                    return options[idx - 1][1]
            except ValueError:
                pass
            self.fail(f"Entrez un numéro entre 1 et {len(options)}.")

    # ----- Fiches -----
    def show_captain_card(self, captain):
        self.divider()
        nick = f" {SYM_LQUO} {captain['nickname']} {SYM_RQUO}" if captain.get("nickname") else ""
        _safe_print(f"  {C_BOLD}{captain['name']}{nick}{C_RESET}")
        _safe_print(f"  {C_DIM}{captain['period']}  {SYM_EMDASH}  {captain['region']}{C_RESET}")
        self.show_scene("captains", captain["id"])
        _safe_print()
        for line in _wrap(captain["biography"], 60):
            _safe_print(f"  {line}")
        if captain["bonus"]:
            bonus_str = ", ".join(f"{k} +{v}" for k, v in captain["bonus"].items())
            _safe_print(f"  {C_GREEN}Bonus : {bonus_str}{C_RESET}")
        _safe_print(f"  Or : {captain['starting_gold']}   Équipage : {captain['starting_crew']}")

    def show_ship_card(self, ship):
        self.divider()
        _safe_print(f"  {C_BOLD}{ship['name']}{C_RESET}   {C_DIM}({ship['period']}){C_RESET}")
        self.show_scene("ships", ship["id"])
        _safe_print(f"  Mâts : {ship['masts']}   Canons : {ship['guns']}   "
                    f"Coque : {ship['hull']}/10   Vitesse : {ship['speed']}/10")
        _safe_print(f"  Équipage : {ship['crew_min']}-{ship['crew_max']}   "
                    f"Cale : {ship['cargo']}/10   Coût : {ship['cost']} pièces")
        for line in _wrap(ship["description"], 60):
            _safe_print(f"  {line}")

    # ----- Statut -----
    def render_status(self, state):
        self.divider()
        _safe_print(f"  Tour {state.turn}   {SYM_EMDASH}   {format_date_fr(state.current_date())}")
        nick = f" {SYM_LQUO} {state.captain['nickname']} {SYM_RQUO}" if state.captain.get("nickname") else ""
        _safe_print(f"  Capitaine : {state.captain['name']}{nick}")
        _safe_print(f"  Navire    : {state.ship['name']}  "
                    f"(coque {state.ship['hull_current']}/{state.ship['hull_max']}, "
                    f"{state.ship['guns']} canons)")
        _safe_print(f"  Équipage  : {state.crew} hommes")
        _safe_print(f"  Vivres    : {state.supplies}/100")
        _safe_print(f"  Moral     : {state.morale}/100")
        _safe_print(f"  Caisse    : {state.gold} pièces de huit")
        if state.loot:
            _safe_print(f"  Butin brut: {state.loot} (à recéler)")
        _safe_print(f"  Réputation: {state.reputation}")
        if state.companions:
            _safe_print(f"  {C_BOLD}Équipage nommé :{C_RESET}")
            for c in state.companions:
                nick = f" {SYM_LQUO} {c['nickname']} {SYM_RQUO}" if c.get("nickname") else ""
                _safe_print(f"    - {c['name']}{nick} ({c['role']})")
        if state.prisoners:
            from data.prisoners import count_by_type, PRISONER_TYPES
            counts = count_by_type(state.prisoners)
            parts = [f"{n} {PRISONER_TYPES[t]['label']}" for t, n in counts.items()]
            _safe_print(f"  Prisonniers: {', '.join(parts)}")
        if state.pending_ransoms:
            total = sum(r["amount"] for r in state.pending_ransoms)
            next_due = min(r["due_turn"] for r in state.pending_ransoms)
            _safe_print(f"  Rançons en attente: {len(state.pending_ransoms)} ({total} P8, "
                        f"prochaine ~tour {next_due})")
        if state.in_port and state.current_port:
            _safe_print(f"  Au mouillage : {state.current_port['name']}")
        self.divider()
