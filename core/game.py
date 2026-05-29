"""
État de jeu : tout ce qui change pendant une partie.

GameState centralise les attributs du joueur, du navire, des compagnons
recrutés et des compteurs de tour. Le rendu visuel est délégué à l'UI.

Compagnons :
  - state.companions : liste de dicts (cf. data/companions.py)
  - state.affection  : dict port_id -> int (cadeaux offerts à l'hôtesse)
  - state.get_effective_bonus(name) : agrégation capitaine + compagnons

Effets passifs des compagnons (morale_per_turn, hull_per_turn, etc.)
sont appliqués automatiquement à chaque advance_turn().
"""

import datetime

from data.companions import aggregate_bonuses


class GameState:
    def __init__(self, captain: dict, ship: dict):
        # Personnages et navire
        self.captain = captain
        self.ship = ship

        # Ressources
        self.gold = captain["starting_gold"]
        self.crew = captain["starting_crew"]
        self.supplies = 30
        self.loot = 0

        # Caractéristiques dynamiques
        self.morale = 70
        # La réputation du capitaine (Morgan, Roberts…) est un héritage de
        # carrière, appliquée une seule fois au départ.
        self.reputation = 1 + captain.get("bonus", {}).get("reputation", 0)

        # Compagnons
        self.companions = []            # liste de dicts
        self.affection = {}             # port_id -> nombre de cadeaux offerts

        # Prisonniers (capturés lors d'abordages ou de prises de négriers)
        self.prisoners = []             # liste de dicts (cf. data/prisoners.py)
        # Rançons en attente : prisonniers envoyés par lettre, valeur à
        # encaisser au tour `due_turn`. Format :
        #   {"prisoner": <dict>, "due_turn": int, "amount": int}
        self.pending_ransoms = []
        
        # Repaire
        self.base = None          # cf. core/base.Hideout — None tant que non fondé
        self.cargo_hold = {}      # mati\u00e8res ramen\u00e9es de la mer, à débarquer au repaire

        # Temporalité
        self.turn = 0
        self.start_date = datetime.date(1716, 4, 1)

        # Contexte
        self.in_port = False
        self.current_port = None
        self.flags = {}

        # Fin de partie
        self.game_over = False
        self.victory = False
        self.defeat_reason = None      # libellé court : "Naufrage", "Mutinerie"…
        self.defeat_narrative = None   # texte d'ambiance
        # Cause précise — sert à l'écran de fin (cf. core/engine.py)
        # Valeurs possibles : crew_loss, shipwreck, mutiny, abandon,
        #                     pardon (victoire).
        self.defeat_cause = None

    # ----- Temps -----
    def current_date(self) -> datetime.date:
        return self.start_date + datetime.timedelta(days=self.turn * 14)

    def advance_turn(self):
        self.turn += 1
        # Effets passifs des compagnons à chaque tour
        bonuses = self.effective_bonuses()
        if "morale_per_turn" in bonuses:
            self.morale = min(100, self.morale + bonuses["morale_per_turn"])
        if "hull_per_turn" in bonuses:
            self.ship["hull_current"] = min(
                self.ship["hull_max"],
                self.ship["hull_current"] + bonuses["hull_per_turn"],
            )
        # Plancher de moral
        if "morale_floor" in bonuses:
            self.morale = max(self.morale, bonuses["morale_floor"])
        # Rançons échues
        self._settle_due_ransoms()
        # Cycle de vie de la base
        if self.base is not None:
            self.base.tick(self)

    def _settle_due_ransoms(self):
        """Encaisse toutes les rançons dont le tour est venu."""
        remaining = []
        for ransom in self.pending_ransoms:
            if self.turn >= ransom["due_turn"]:
                self.gold += ransom["amount"]
                # Note : l'UI est notifiée par celui qui appelle advance_turn
                # (les actions log un message). Pour le statut, on stocke
                # une note dans flags pour que l'UI puisse en parler.
                self.flags.setdefault("recent_ransom_news", []).append(ransom)
            else:
                remaining.append(ransom)
        self.pending_ransoms = remaining

    # ----- Compagnons -----
    def has_companion(self, companion_id: str) -> bool:
        return any(c["id"] == companion_id for c in self.companions)

    def add_companion(self, companion: dict):
        if not self.has_companion(companion["id"]):
            self.companions.append(dict(companion))

    def effective_bonuses(self) -> dict:
        """Renvoie le dict agrégé capitaine + compagnons (cache léger)."""
        return aggregate_bonuses(self.captain.get("bonus", {}), self.companions)

    def get_effective_bonus(self, name: str, default=0):
        """Bonus de statistique additif (combat, intimidation, etc.)."""
        return self.effective_bonuses().get(name, default)

    def get_modifier(self, name: str, default=0.0):
        """Idem mais sémantique « modificateur » (ristourne, économie, etc.)."""
        return self.effective_bonuses().get(name, default)

    def has_trait(self, name: str) -> bool:
        """Pour les modificateurs binaires (scurvy_resist, spanish_intel…)."""
        return bool(self.effective_bonuses().get(name))

    # ----- Affection (hôtesses de taverne) -----
    def affection_for(self, port_id: str) -> int:
        return self.affection.get(port_id, 0)

    def increase_affection(self, port_id: str, amount: int = 1):
        self.affection[port_id] = self.affection_for(port_id) + amount

    # ----- Capacité du cargo -----
    def hold_capacity(self) -> int:
        return self.ship.get("cargo", 0) * 15

    def hold_total(self) -> int:
        return sum(self.cargo_hold.values())

    def add_to_hold(self, rid: str, qty: int) -> int:
        """Ajoute jusqu'\u00e0 `qty` unit\u00e9s à la cale, born\u00e9 par la capacit\u00e9.
        Renvoie ce qui est r\u00e9ellement entr\u00e9."""
        room = max(0, self.hold_capacity() - self.hold_total())
        added = max(0, min(qty, room))
        if added:
            self.cargo_hold[rid] = self.cargo_hold.get(rid, 0) + added
        return added

    # ----- Défaite -----
    def _trigger_defeat(self, ui, reason: str, narrative: str):
        """Enregistre la cause et termine la partie."""
        self.defeat_reason = reason
        self.defeat_narrative = narrative
        self.game_over = True
        self.victory = False
        ui.fail(narrative)

    def check_defeat(self, ui):
        if self.game_over:
            return
        if self.crew <= 5:
            self._trigger_defeat(
                ui,
                "Équipage décimé",
                "Plus assez d'hommes pour manœuvrer. Le navire dérive jusqu'à "
                "ce qu'un patrouilleur le récupère. Votre carrière s'achève "
                "au bout d'une corde.",
            )
            return
        if self.ship["hull_current"] <= 0:
            self._trigger_defeat(
                ui,
                "Naufrage",
                "La coque cède sous les coups de mer. Le navire sombre. "
                "Quelques planches flottent — votre légende avec elles.",
            )
            return
        if self.supplies <= 0 and self.crew > 0:
            # Pas mort instantanément, mais grosse perte d'équipage et de moral.
            # La défaite finale viendra par crew_lost ou morale=0 au tour suivant.
            self.crew = max(0, self.crew - max(2, self.crew // 6))
            self.morale = max(0, self.morale - 20)
            ui.fail(
                "Plus une once de biscuit dans les barriques. La faim décime "
                "l'équipage et brise le moral."
            )
            self.supplies = 1
        if self.morale <= 0:
            self._trigger_defeat(
                ui,
                "Mutinerie générale",
                "Le moral est tombé à zéro. L'équipage se mutine en masse, "
                "abandonne le capitaine sur une île et part avec le navire.",
            )

    # ----- Affichage : on délègue à l'UI -----
    def render_status(self, ui):
        ui.render_status(self)
