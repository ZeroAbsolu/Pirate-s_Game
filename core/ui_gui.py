"""
Interface graphique Tkinter.

Hérite de TextUI : conserve les helpers (format de date, wrap, etc.).
Surcharge les méthodes interactives pour utiliser la fenêtre.

Caractéristiques :
  - Fenêtre unique avec : panneau de gauche (journal + boutons d'action),
    panneau de droite (illustration de scène + statut).
  - Les images sont chargées via Pillow si disponible, sinon Tk PhotoImage.
  - Les chemins suivent la convention définie dans core/images.py.
  - Si une image est manquante, le panneau affiche une plaque grise avec
    le nom de la scène — le jeu continue normalement.

Lancement :
    from core.ui_gui import GraphicalUI
    from core.engine import run
    run(GraphicalUI())
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext

from core.ui import TextUI, format_date_fr, _wrap
from core import images

# Pillow est optionnel mais fortement recommandé : il gère PNG, JPEG,
# le redimensionnement, et la transparence.
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# --- Palette ---
BG       = "#1a1a26"
PANEL    = "#252535"
PANEL_LT = "#33334a"
INK      = "#e8e0c8"
INK_DIM  = "#9a9aae"
GOLD     = "#f0c060"
TEAL     = "#7ec8e3"
GREEN    = "#90c590"
RED      = "#e08080"
PURPLE   = "#d8a8ff"
BORDER   = "#3a3a5a"


class GraphicalUI(TextUI):
    """Interface graphique Tkinter. API compatible TextUI."""

    SCENE_W, SCENE_H = 520, 360       # taille d'affichage du fond de scène

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("La Course des Indes")
        self.root.geometry("1180x780")
        self.root.minsize(1000, 680)
        self.root.configure(bg=BG)

        # File d'attente pour les inputs bloquants
        self._wait_var = tk.IntVar(value=0)
        self._wait_seq = 0
        self._result = None
        self._closed = False

        # Variables de statut
        self._sv = {k: tk.StringVar(value="—") for k in (
            "date", "captain", "ship", "hull", "crew",
            "supplies", "morale", "gold", "loot", "prisoners", "reputation", "port",
        )}
        self._sv_companions = tk.StringVar(value="(aucun)")

        # Références d'images (Tk libère sinon)
        self._img_refs = []

        self._build_style()
        self._build_layout()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ===============================================================
    # Construction de la fenêtre
    # ===============================================================

    def _build_style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Pirate.TButton",
                        background=PANEL_LT, foreground=INK,
                        bordercolor=BORDER, focuscolor=GOLD,
                        font=("Helvetica", 10), padding=8)
        style.map("Pirate.TButton",
                  background=[("active", GOLD), ("pressed", GOLD)],
                  foreground=[("active", BG), ("pressed", BG)])
        style.configure("PirateBig.TButton",
                        background=PANEL_LT, foreground=GOLD,
                        font=("Helvetica", 11, "bold"), padding=10)
        style.map("PirateBig.TButton",
                  background=[("active", GOLD)],
                  foreground=[("active", BG)])
        style.configure("Pirate.TEntry",
                        fieldbackground=PANEL_LT, foreground=INK,
                        insertcolor=GOLD)

    def _build_layout(self):
        root = self.root

        # Cadre principal divisé en deux colonnes
        main = tk.Frame(root, bg=BG)
        main.pack(fill="both", expand=True, padx=8, pady=8)

        # --- Colonne gauche : journal + actions ---
        left = tk.Frame(main, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))

        title = tk.Label(left, text="LA COURSE DES INDES",
                         bg=BG, fg=GOLD,
                         font=("Helvetica", 16, "bold"))
        title.pack(anchor="w", pady=(0, 4))

        # Zone de journal (texte défilant)
        self.text = scrolledtext.ScrolledText(
            left,
            wrap="word",
            bg=PANEL, fg=INK,
            font=("Georgia", 11),
            insertbackground=GOLD,
            relief="flat", borderwidth=0, padx=12, pady=10,
            state="disabled",
        )
        self.text.pack(fill="both", expand=True)

        # Tags de coloration
        self.text.tag_config("title",   foreground=GOLD,   font=("Georgia", 13, "bold"), spacing1=8, spacing3=4)
        self.text.tag_config("info",    foreground=INK)
        self.text.tag_config("narrate", foreground=TEAL,   font=("Georgia", 11, "italic"), spacing1=4)
        self.text.tag_config("success", foreground=GREEN)
        self.text.tag_config("fail",    foreground=RED)
        self.text.tag_config("event",   foreground=PURPLE, font=("Georgia", 12, "bold"), spacing1=10, spacing3=4)
        self.text.tag_config("prompt",  foreground=GOLD,   font=("Georgia", 11, "bold"), spacing1=6)
        self.text.tag_config("divider", foreground=INK_DIM)

        # Zone d'action (boutons / saisie) — hauteur fixe
        self.action_frame = tk.Frame(left, bg=PANEL, height=170,
                                     highlightbackground=BORDER, highlightthickness=1)
        self.action_frame.pack(fill="x", pady=(6, 0))
        self.action_frame.pack_propagate(False)

        self.action_prompt = tk.Label(
            self.action_frame, text="", bg=PANEL, fg=GOLD,
            font=("Georgia", 11, "italic"), anchor="w", justify="left",
            wraplength=600,
        )
        self.action_prompt.pack(fill="x", padx=10, pady=(8, 4))

        self.action_widgets = tk.Frame(self.action_frame, bg=PANEL)
        self.action_widgets.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        # --- Colonne droite : scène + statut ---
        right = tk.Frame(main, bg=BG, width=560)
        right.pack(side="right", fill="y", padx=(6, 0))
        right.pack_propagate(False)

        # Cadre image (fond de scène)
        self.scene_frame = tk.Frame(right, bg=PANEL, width=self.SCENE_W, height=self.SCENE_H,
                                    highlightbackground=BORDER, highlightthickness=1)
        self.scene_frame.pack(pady=(0, 8))
        self.scene_frame.pack_propagate(False)
        self.scene_canvas = tk.Canvas(self.scene_frame,
                                      width=self.SCENE_W, height=self.SCENE_H,
                                      bg=PANEL, highlightthickness=0)
        self.scene_canvas.pack(fill="both", expand=True)
        # Placeholder de départ
        self._draw_placeholder("À vos ordres, capitaine")

        # Panneau de statut
        status = tk.Frame(right, bg=PANEL,
                          highlightbackground=BORDER, highlightthickness=1)
        status.pack(fill="both", expand=True)
        tk.Label(status, text="ÉTAT DE BORD", bg=PANEL, fg=GOLD,
                 font=("Helvetica", 11, "bold")).pack(anchor="w", padx=10, pady=(8, 4))

        rows = [
            ("Date",        "date"),
            ("Capitaine",   "captain"),
            ("Navire",      "ship"),
            ("Coque",       "hull"),
            ("Équipage",    "crew"),
            ("Vivres",      "supplies"),
            ("Moral",       "morale"),
            ("Caisse (P8)", "gold"),
            ("Butin brut",  "loot"),
            ("Prisonniers", "prisoners"),
            ("Réputation",  "reputation"),
            ("Mouillage",   "port"),
        ]
        for label, key in rows:
            row = tk.Frame(status, bg=PANEL)
            row.pack(fill="x", padx=10, pady=1)
            tk.Label(row, text=f"{label} :", bg=PANEL, fg=INK_DIM,
                     font=("Helvetica", 10), anchor="w", width=12).pack(side="left")
            tk.Label(row, textvariable=self._sv[key], bg=PANEL, fg=INK,
                     font=("Helvetica", 10, "bold"), anchor="w").pack(side="left")

        # Sous-panneau compagnons
        tk.Label(status, text="ÉQUIPAGE NOMMÉ", bg=PANEL, fg=GOLD,
                 font=("Helvetica", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 4))
        self.companions_label = tk.Label(
            status, textvariable=self._sv_companions, bg=PANEL, fg=INK,
            font=("Helvetica", 10), justify="left", anchor="nw",
            wraplength=540,
        )
        self.companions_label.pack(anchor="w", padx=10, pady=(0, 8), fill="x")

    # ===============================================================
    # Cycle UI
    # ===============================================================

    def _on_close(self):
        self._closed = True
        # Réveille tous les waits en cours
        self._wait_seq += 1
        self._wait_var.set(self._wait_seq)
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def _wait_for_input(self):
        if self._closed:
            raise KeyboardInterrupt()
        target = self._wait_seq + 1
        self._wait_var.set(self._wait_seq)
        self.root.wait_variable(self._wait_var)
        if self._closed:
            raise KeyboardInterrupt()

    def _resolve_input(self, value):
        """Appelé depuis un callback : enregistre la réponse et relâche le wait."""
        self._result = value
        self._wait_seq += 1
        self._wait_var.set(self._wait_seq)

    def _clear_action_widgets(self):
        for w in self.action_widgets.winfo_children():
            w.destroy()

    def _set_prompt(self, text):
        self.action_prompt.config(text=text or "")

    def _safe_update(self):
        try:
            self.root.update_idletasks()
        except tk.TclError:
            pass

    # ===============================================================
    # Sortie texte (journal)
    # ===============================================================

    def _append(self, text, tag="info"):
        if self._closed:
            return
        self.text.config(state="normal")
        self.text.insert("end", text + "\n", tag)
        self.text.see("end")
        self.text.config(state="disabled")
        self._safe_update()

    def title(self, text):
        self._append("")
        self._append(f"━━━  {text}  ━━━", "title")

    def divider(self):
        self._append("─" * 50, "divider")

    def info(self, text):
        self._append(text, "info")

    def narrate(self, text):
        self._append("")
        self._append(text, "narrate")

    def success(self, text):
        self._append(f"✓ {text}", "success")

    def fail(self, text):
        self._append(f"✗ {text}", "fail")

    def event_banner(self, title):
        self._append("")
        self._append(f"◆ ÉVÉNEMENT : {title} ◆", "event")

    # ===============================================================
    # Images / scènes
    # ===============================================================

    def _draw_placeholder(self, label_text):
        """Plaque grise avec une étiquette, quand aucune image n'est trouvée."""
        c = self.scene_canvas
        c.delete("all")
        # Gradient simple : deux rectangles
        c.create_rectangle(0, 0, self.SCENE_W, self.SCENE_H,
                           fill="#2a2a3a", outline="")
        # Étiquette centrée
        c.create_text(self.SCENE_W // 2, self.SCENE_H // 2 - 10,
                      text=label_text, fill=INK_DIM,
                      font=("Georgia", 13, "italic"), justify="center")
        c.create_text(self.SCENE_W // 2, self.SCENE_H // 2 + 20,
                      text="(illustration à venir)", fill=INK_DIM,
                      font=("Helvetica", 9), justify="center")

    def _load_and_show_image(self, path, caption=None):
        """Affiche l'image à `path` comme fond de scène, avec caption optionnelle."""
        if self._closed:
            return
        c = self.scene_canvas
        c.delete("all")
        try:
            if PIL_AVAILABLE:
                img = Image.open(path)
                # Convertit en RGB(A) pour éviter les surprises
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA")
                # Redimensionne pour remplir le cadre en conservant l'aspect
                img = self._fit_to(img, self.SCENE_W, self.SCENE_H)
                photo = ImageTk.PhotoImage(img)
            else:
                # Tk PhotoImage : PNG (Python 3.6+) ou GIF
                photo = tk.PhotoImage(file=path)
            self._img_refs.clear()
            self._img_refs.append(photo)
            c.create_image(self.SCENE_W // 2, self.SCENE_H // 2,
                           image=photo, anchor="center")
            if caption:
                # Bandeau semi-transparent en bas pour le titre de la scène
                c.create_rectangle(0, self.SCENE_H - 32, self.SCENE_W, self.SCENE_H,
                                   fill="#000000", outline="", stipple="gray50")
                c.create_text(self.SCENE_W // 2, self.SCENE_H - 16,
                              text=caption, fill=GOLD,
                              font=("Georgia", 11, "italic"))
        except Exception as exc:
            self._draw_placeholder(f"image illisible\n({exc.__class__.__name__})")

    def _fit_to(self, img, max_w, max_h):
        """Redimensionne sans déformer pour entrer dans max_w × max_h."""
        w, h = img.size
        ratio = min(max_w / w, max_h / h)
        new_w, new_h = max(1, int(w * ratio)), max(1, int(h * ratio))
        resampler = getattr(Image, "Resampling", Image).LANCZOS if hasattr(Image, "Resampling") \
                    else Image.LANCZOS
        return img.resize((new_w, new_h), resampler)

    def show_image(self, path):
        if path and os.path.isfile(path):
            self._load_and_show_image(path)
        # Sinon : on ne touche pas (le fond précédent reste)

    def show_scene(self, category, instance_id, variant=None):
        path = self._resolve_scene(category, instance_id, variant)
        caption = self._scene_caption(category, instance_id, variant)
        if path:
            self._load_and_show_image(path, caption=caption)
        else:
            self._draw_placeholder(caption or "—")

    def _scene_caption(self, category, instance_id, variant):
        """Petit titre affiché en bas de l'image. Aide pendant le développement
        quand les illustrations ne sont pas encore produites."""
        if category == "ports":
            scene_fr = {
                "main": "Mouillage",
                "tavern": "Taverne",
                "shipyard": "Chantier naval",
                "recruit": "Embauche",
                "supplies": "Magasin",
                "fence": "Receleur",
                "repair": "Carénage",
            }.get(variant or "main", variant or "")
            return f"{instance_id.replace('_', ' ').title()} — {scene_fr}"
        if category == "port_events":
            return f"{instance_id.replace('_', ' ').title()} — événement"
        if category == "captains":
            return instance_id.replace("_", " ").title()
        if category == "ships":
            return instance_id.replace("_", " ").title()
        if category == "companions":
            return instance_id.replace("_", " ").title()
        return instance_id

    # ===============================================================
    # Saisie
    # ===============================================================

    def choose(self, prompt, options):
        if self._closed:
            raise KeyboardInterrupt()
        self._append("")
        self._append(prompt, "prompt")
        self._set_prompt(prompt)
        self._clear_action_widgets()

        # Boutons sur une grille à 2 colonnes si > 4 options
        cols = 2 if len(options) > 4 else 1
        for i, (label, value) in enumerate(options):
            btn = ttk.Button(self.action_widgets, text=label, style="Pirate.TButton",
                             command=lambda v=value: self._resolve_input(v))
            if cols == 2:
                btn.grid(row=i // 2, column=i % 2, sticky="ew", padx=3, pady=2)
            else:
                btn.pack(fill="x", padx=2, pady=2)
        if cols == 2:
            self.action_widgets.grid_columnconfigure(0, weight=1)
            self.action_widgets.grid_columnconfigure(1, weight=1)

        self._wait_for_input()
        self._clear_action_widgets()
        self._set_prompt("")
        return self._result

    def ask_text(self, prompt):
        if self._closed:
            raise KeyboardInterrupt()
        self._append("")
        self._append(f"> {prompt}", "prompt")
        self._set_prompt(prompt)
        self._clear_action_widgets()

        var = tk.StringVar()
        entry = ttk.Entry(self.action_widgets, textvariable=var, style="Pirate.TEntry",
                          font=("Helvetica", 11))
        entry.pack(fill="x", padx=2, pady=(4, 6))
        entry.focus_set()

        def submit():
            self._resolve_input(var.get().strip())
        entry.bind("<Return>", lambda e: submit())
        btn = ttk.Button(self.action_widgets, text="Valider", style="Pirate.TButton",
                         command=submit)
        btn.pack(fill="x", padx=2)

        self._wait_for_input()
        self._clear_action_widgets()
        self._set_prompt("")
        return self._result or ""

    def ask_int(self, prompt, min_val=0, max_val=9999):
        if self._closed:
            raise KeyboardInterrupt()
        while True:
            self._append("")
            self._append(f"> {prompt}", "prompt")
            self._set_prompt(f"{prompt}  [{min_val}–{max_val}]")
            self._clear_action_widgets()

            var = tk.StringVar(value=str(min_val))
            entry = ttk.Entry(self.action_widgets, textvariable=var, style="Pirate.TEntry",
                              font=("Helvetica", 11))
            entry.pack(fill="x", padx=2, pady=(4, 6))
            entry.focus_set()
            entry.select_range(0, "end")

            def submit():
                self._resolve_input(var.get().strip())
            entry.bind("<Return>", lambda e: submit())
            ttk.Button(self.action_widgets, text="Valider", style="Pirate.TButton",
                       command=submit).pack(fill="x", padx=2)

            self._wait_for_input()
            self._clear_action_widgets()
            self._set_prompt("")
            raw = self._result or ""
            if raw == "":
                return min_val
            try:
                v = int(raw)
                if min_val <= v <= max_val:
                    return v
            except ValueError:
                pass
            self.fail(f"Nombre attendu entre {min_val} et {max_val}.")

    # ===============================================================
    # Cards
    # ===============================================================

    def show_captain_card(self, captain):
        self.divider()
        nick = f" « {captain['nickname']} »" if captain.get("nickname") else ""
        self._append(f"{captain['name']}{nick}", "title")
        self._append(f"{captain['period']}  —  {captain['region']}", "info")
        self.show_scene("captains", captain["id"])
        self._append("")
        for line in _wrap(captain["biography"], 70):
            self._append(line, "info")
        if captain["bonus"]:
            b = ", ".join(f"{k} +{v}" for k, v in captain["bonus"].items())
            self._append(f"Bonus : {b}", "success")
        self._append(f"Or : {captain['starting_gold']}   Équipage : {captain['starting_crew']}", "info")

    def show_ship_card(self, ship):
        self.divider()
        self._append(f"{ship['name']}  ({ship['period']})", "title")
        self.show_scene("ships", ship["id"])
        self._append(
            f"Mâts : {ship['masts']}   Canons : {ship['guns']}   "
            f"Coque : {ship['hull']}/10   Vitesse : {ship['speed']}/10", "info")
        self._append(
            f"Équipage : {ship['crew_min']}–{ship['crew_max']}   "
            f"Cale : {ship['cargo']}/10   Coût : {ship['cost']} pièces", "info")
        for line in _wrap(ship["description"], 70):
            self._append(line, "info")

    # ===============================================================
    # Statut (panneau latéral)
    # ===============================================================

    def render_status(self, state):
        self._sv["date"].set(format_date_fr(state.current_date()))
        nick = f" « {state.captain['nickname']} »" if state.captain.get("nickname") else ""
        self._sv["captain"].set(f"{state.captain['name']}{nick}")
        self._sv["ship"].set(f"{state.ship['name']} ({state.ship['guns']} canons)")
        self._sv["hull"].set(f"{state.ship['hull_current']} / {state.ship['hull_max']}")
        self._sv["crew"].set(f"{state.crew} hommes")
        self._sv["supplies"].set(f"{state.supplies} / 100")
        self._sv["morale"].set(f"{state.morale} / 100")
        self._sv["gold"].set(f"{state.gold}")
        self._sv["loot"].set(f"{state.loot}" if state.loot else "—")
        if state.prisoners:
            from data.prisoners import count_by_type, PRISONER_TYPES
            counts = count_by_type(state.prisoners)
            parts = [f"{n} {PRISONER_TYPES[t]['label']}" for t, n in counts.items()]
            if state.pending_ransoms:
                parts.append(f"+{len(state.pending_ransoms)} rançon(s) en attente")
            self._sv["prisoners"].set(", ".join(parts))
        elif state.pending_ransoms:
            total = sum(r["amount"] for r in state.pending_ransoms)
            self._sv["prisoners"].set(f"{len(state.pending_ransoms)} rançon(s) à venir ({total} P8)")
        else:
            self._sv["prisoners"].set("—")
        self._sv["reputation"].set(f"{state.reputation}")
        self._sv["port"].set(state.current_port["name"] if (state.in_port and state.current_port) else "—")

        if state.companions:
            lines = []
            for c in state.companions:
                nick = f" « {c['nickname']} »" if c.get("nickname") else ""
                lines.append(f"• {c['name']}{nick}\n   {c['role']}")
            self._sv_companions.set("\n".join(lines))
        else:
            self._sv_companions.set("(aucun)")

    # ===============================================================
    # Boucle finale
    # ===============================================================

    def mainloop(self):
        """À appeler après run() pour garder la fenêtre ouverte sur l'écran de fin."""
        try:
            if not self._closed:
                self.root.mainloop()
        except tk.TclError:
            pass
