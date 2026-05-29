"""
Le repaire (base secrète) du joueur.

Un seul repaire par partie. Le joueur le FONDE sur un mouillage discret
historiquement plausible (cf. LOCATIONS), y DÉPOSE des hommes (garnison),
y CONSTRUIT des bâtiments (cf. data/base_buildings.py) avec des matières
premières et du temps, puis l'EXPLOITE (production automatique de biens,
services, défense).

Modèle de temps : comme le reste du jeu, 1 tour ≈ 14 jours. La
construction et la production sont traitées dans `Hideout.tick(state)`,
appelé par GameState.advance_turn() à chaque tour.

Contraintes clés (ce qui rend les hommes déposés utiles) :
  - CONSTRUCTION : un seul chantier avance à la fois, et seulement si la
    garnison fournit assez de bras (workers du bâtiment).
  - PRODUCTION : chaque atelier réclame des bras ; la garnison disponible
    (déduction faite du chantier en cours) est répartie par priorité.
  - STOCKAGE : capacité bornée (entrepôt pour l'augmenter).
  - DÉFENSE : un repaire connu peut être razzié en votre absence ; la
    batterie et la garnison le protègent.

Repères historiques des sites proposés :
  - Île-à-Vache (sud de Saint-Domingue) : rendez-vous de flibuste, Morgan
    y rassembla sa flotte avant Panama (1670). Bétail marron → boucan.
  - Îlots des Aves : récifs où la flotte de d'Estrées se brisa en 1678,
    repaire de boucaniers, très à l'écart.
  - Roatán (îles de la Baie, golfe du Honduras) : côte à bois (campêche),
    mouillage de carénage des boucaniers.
  - Harbour Island / Eleuthera (Bahamas) : à portée de Nassau, donc commode
    pour le négoce… et exposé aux représailles.
  - Baie d'Antongil (Madagascar) : sphère de la « Pirate Round », débouchés
    de l'océan Indien (réseau Baldridge-Philipse).
"""

import random

from data.base_buildings import (
    BASE_BUILDINGS, VISIT_HANDLERS, producing_buildings, get_building,
)
from data.resources import RESOURCES, GOODS


BASE_STORAGE_DEFAULT = 120
BASE_GARRISON_DEFAULT = 12
BASE_DEFENSE_DEFAULT = 1
RAID_BASE_CHANCE = 0.06          # par tour d'absence, modulé ci-dessous


# ===================================================================
# Sites de repaire
# ===================================================================

LOCATIONS = {
    "ile_a_vache": {
        "id": "ile_a_vache",
        "name": "Île-à-Vache (sud de Saint-Domingue)",
        "default_name": "Repaire de l'Île-à-Vache",
        "region": "Caraïbes",
        "blurb": ("Mouillage de flibuste où Morgan rassembla sa flotte avant "
                  "Panama. Bétail marron à profusion pour le boucan."),
        "mods": {"boucan_rate": 1.6, "raid_risk": 1.0},
    },
    "las_aves": {
        "id": "las_aves",
        "name": "Îlots des Aves (au vent de Curaçao)",
        "default_name": "Repaire des Aves",
        "region": "Caraïbes",
        "blurb": ("Labyrinthe de récifs où sombra la flotte de d'Estrées en "
                  "1678. Introuvable pour qui ne connaît pas la passe."),
        "mods": {"raid_risk": 0.45, "supply_cost": 1.2},
    },
    "roatan": {
        "id": "roatan",
        "name": "Roatán (îles de la Baie, golfe du Honduras)",
        "default_name": "Repaire de Roatán",
        "region": "Caraïbes",
        "blurb": ("Côte à bois de campêche, criques de carénage. Loin des "
                  "routes des escadres, près des coupeurs de bois."),
        "mods": {"raid_risk": 0.85, "bois_gather": 1.5},
    },
    "eleuthera": {
        "id": "eleuthera",
        "name": "Harbour Island (Eleuthera, Bahamas)",
        "default_name": "Repaire d'Eleuthera",
        "region": "Caraïbes",
        "blurb": ("À une marée de Nassau : négoce facile avec les receleurs "
                  "du Banc — mais à portée des représailles royales."),
        "mods": {"raid_risk": 1.4, "trade_bonus": 0.12},
    },
    "antongil": {
        "id": "antongil",
        "name": "Baie d'Antongil (Madagascar)",
        "default_name": "Repaire d'Antongil",
        "region": "Océan Indien",
        "blurb": ("Au cœur de la Pirate Round. Débouchés de l'océan Indien, "
                  "comptoirs lointains, escadres rares."),
        "mods": {"raid_risk": 0.55, "trade_bonus": 0.15, "overseas": True},
    },
}


def list_locations() -> list:
    return list(LOCATIONS.values())


# ===================================================================
# Hideout
# ===================================================================

class Hideout:
    def __init__(self, location_id: str, name: str = None, founded_turn: int = 0):
        loc = LOCATIONS[location_id]
        self.location_id = location_id
        self.location_name = loc["name"]
        self.region = loc["region"]
        self.mods = dict(loc.get("mods", {}))
        self.name = name or loc["default_name"]
        self.founded_turn = founded_turn
        self.last_visit_turn = founded_turn

        self.buildings = {}      # bid -> {"built_turn": int}
        self.queue = []          # [{"id","name","turns_left","workers"}]
        self.resources = {r: 0 for r in RESOURCES}
        self.goods = {g: 0 for g in GOODS}
        self.garrison = 0

        # Rapport accumulé depuis la dernière visite (production, etc.)
        self.report = self._fresh_report()

    @staticmethod
    def _fresh_report():
        return {"produced": {}, "built": [], "income": 0, "notes": [], "stalled": False}

    # ---------------- Inventaire / capacités ----------------------

    def has(self, bid: str) -> bool:
        return bid in self.buildings

    def capacity(self) -> int:
        cap = BASE_STORAGE_DEFAULT
        for bid in self.buildings:
            cap += BASE_BUILDINGS[bid].get("storage_bonus", 0)
        return cap

    def stored_total(self) -> int:
        return sum(self.resources.values()) + sum(self.goods.values())

    def free_space(self) -> int:
        return max(0, self.capacity() - self.stored_total())

    def garrison_cap(self) -> int:
        cap = BASE_GARRISON_DEFAULT
        for bid in self.buildings:
            cap += BASE_BUILDINGS[bid].get("garrison_bonus", 0)
        return cap

    def defense_rating(self) -> int:
        d = BASE_DEFENSE_DEFAULT
        for bid in self.buildings:
            d += BASE_BUILDINGS[bid].get("defense", 0)
        d += self.garrison // 5
        return d

    def add_resource(self, rid: str, qty: int) -> int:
        """Ajoute jusqu'à `qty` unités, borné par la capacité. Renvoie la
        quantité réellement entrée."""
        room = self.free_space()
        added = max(0, min(qty, room))
        self.resources[rid] = self.resources.get(rid, 0) + added
        return added

    def add_good(self, gid: str, qty: int) -> int:
        room = self.free_space()
        added = max(0, min(qty, room))
        self.goods[gid] = self.goods.get(gid, 0) + added
        return added

    # ---------------- Construction --------------------------------

    def prerequisites_met(self, bid: str) -> bool:
        return all(self.has(r) for r in BASE_BUILDINGS[bid].get("requires", []))

    def is_queued(self, bid: str) -> bool:
        return any(q["id"] == bid for q in self.queue)

    def can_build(self, bid: str):
        """Renvoie (ok, raison). Ne vérifie pas l'or/ressources (cf. start_build)."""
        if self.has(bid):
            return False, "déjà construit"
        if self.is_queued(bid):
            return False, "déjà en chantier"
        if not self.prerequisites_met(bid):
            reqs = ", ".join(BASE_BUILDINGS[r]["name"]
                             for r in BASE_BUILDINGS[bid]["requires"])
            return False, f"requiert : {reqs}"
        return True, ""

    def affordable(self, bid: str, state) -> bool:
        cost = BASE_BUILDINGS[bid]["cost"]
        if state.gold < cost.get("gold", 0):
            return False
        for k, v in cost.items():
            if k == "gold":
                continue
            if self.resources.get(k, 0) < v:
                return False
        return True

    def missing_for(self, bid: str, state) -> dict:
        """Ce qui manque pour lancer le chantier (or + matières)."""
        cost = BASE_BUILDINGS[bid]["cost"]
        miss = {}
        if state.gold < cost.get("gold", 0):
            miss["gold"] = cost["gold"] - state.gold
        for k, v in cost.items():
            if k == "gold":
                continue
            have = self.resources.get(k, 0)
            if have < v:
                miss[k] = v - have
        return miss

    def start_build(self, bid: str, state) -> bool:
        """Déduit le coût et place le bâtiment en file. Suppose can_build +
        affordable déjà vérifiés."""
        bdef = BASE_BUILDINGS[bid]
        cost = bdef["cost"]
        state.gold -= cost.get("gold", 0)
        for k, v in cost.items():
            if k == "gold":
                continue
            self.resources[k] -= v
        self.queue.append({
            "id": bid,
            "name": bdef["name"],
            "turns_left": bdef["build_turns"],
            "workers": bdef.get("workers", 3),
        })
        return True

    # ---------------- Tour de jeu ---------------------------------

    def tick(self, state):
        """Appelé à chaque advance_turn(). Avance la construction, fait
        tourner les ateliers, encaisse les revenus, gère l'usure.
        N'écrit pas dans l'UI : tout est accumulé dans self.report et
        restitué à la prochaine visite."""
        workers_used = self._advance_construction(state)
        self._run_production(state, workers_used)
        self._collect_income(state)
        self._upkeep(state)

    def _advance_construction(self, state) -> int:
        """Un seul chantier avance par tour, s'il a assez de bras.
        Renvoie le nombre d'hommes mobilisés par le chantier (0 si aucun)."""
        if not self.queue:
            return 0
        proj = self.queue[0]
        if self.garrison < proj["workers"]:
            self.report["stalled"] = True
            return 0
        proj["turns_left"] -= 1
        if proj["turns_left"] <= 0:
            self.queue.pop(0)
            self.buildings[proj["id"]] = {"built_turn": state.turn}
            self.report["built"].append(proj["name"])
        return proj["workers"]

    def _run_production(self, state, workers_used: int):
        workers_avail = max(0, self.garrison - workers_used)
        for bid, bdef in producing_buildings(self.buildings):
            recipe = bdef["recipe"]
            w = recipe.get("workers", 2)
            if workers_avail < w:
                continue
            ins = recipe.get("in", {})
            if any(self.resources.get(k, 0) < v for k, v in ins.items()):
                continue
            # Consommer les intrants
            for k, v in ins.items():
                self.resources[k] -= v
            # Produire les sortants (avec modificateur de site éventuel)
            rate = float(self.mods.get(bdef.get("rate_key", ""), 1.0))
            for gid, qty in recipe.get("out", {}).items():
                produced = max(1, int(round(qty * rate)))
                added = self.add_good(gid, produced)
                if added:
                    self.report["produced"][gid] = \
                        self.report["produced"].get(gid, 0) + added
            workers_avail -= w

    def _collect_income(self, state):
        if not self.has("tripot"):
            return
        per = BASE_BUILDINGS["tripot"]["income"]["per_garrison"]
        take = int(self.garrison * per * random.uniform(0.5, 1.5))
        if take > 0:
            state.gold += take
            self.report["income"] += take

    def _upkeep(self, state):
        """Usure douce : sans cuisines pour nourrir la garnison, une grosse
        garnison s'étiole peu à peu (désertion)."""
        if self.garrison <= 8:
            return
        if not self.has("cuisines") and self.goods.get("boucan", 0) <= 0:
            lost = max(1, self.garrison // 20)
            self.garrison -= lost
            self.report["notes"].append(
                f"{lost} hommes ont déserté le repaire, faute de vivres frais.")

    # ---------------- Arrivée du joueur ---------------------------

    def resolve_arrival(self, state, ui):
        """À appeler quand le joueur rejoint son repaire. Restitue le
        rapport d'activité puis vérifie un éventuel raid pendant l'absence."""
        self._flush_report(state, ui)
        self._maybe_raid(state, ui)
        self.last_visit_turn = state.turn

    def _flush_report(self, state, ui):
        rep = self.report
        any_news = (rep["built"] or rep["produced"] or rep["income"]
                    or rep["notes"] or rep["stalled"])
        if any_news:
            ui.info("Depuis votre dernier passage :")
        for name in rep["built"]:
            ui.success(f"  Chantier achevé : {name}.")
        if rep["produced"]:
            from data.resources import label as _lbl
            parts = [f"{n} {_lbl(g)}" for g, n in rep["produced"].items()]
            ui.info("  Production des ateliers : " + ", ".join(parts) + ".")
        if rep["income"]:
            ui.info(f"  Le tripot a versé {rep['income']} P8 à la caisse.")
        for note in rep["notes"]:
            ui.info("  " + note)
        if rep["stalled"]:
            ui.info("  Le chantier est à l'arrêt : pas assez d'hommes à terre.")
        self.report = self._fresh_report()

    def _maybe_raid(self, state, ui):
        gap = max(0, state.turn - self.last_visit_turn)
        if gap <= 0:
            return
        # Un repaire ne devient une cible que si le capitaine est connu.
        if state.reputation < 4 or not self.buildings:
            return
        risk = RAID_BASE_CHANCE * gap * float(self.mods.get("raid_risk", 1.0))
        risk *= 1.0 + 0.05 * state.reputation
        risk = min(0.6, risk)
        if random.random() >= risk:
            return

        ui.event_banner("Raid sur le repaire")
        defense = self.defense_rating()
        attacker = random.randint(6, 16) + state.reputation
        if self.has("batterie"):
            ui.narrate(
                "La vigie a donné l'alerte à temps : des pinasses de chasseurs "
                "de primes se présentent devant la passe, la batterie tonne.")
        else:
            ui.narrate(
                "Des chasseurs de pirates ont remonté votre piste jusqu'ici. "
                "Ils débarquent dans l'aube grise.")

        if defense >= attacker:
            self.garrison = max(0, self.garrison - random.randint(0, 2))
            state.reputation += 1
            ui.success(
                "L'attaque est repoussée. Quelques égratignures à la garnison, "
                "et votre repaire gagne en notoriété parmi les Frères.")
        else:
            # Pillage : pertes de garnison et de stocks.
            g_lost = min(self.garrison, random.randint(2, 6))
            self.garrison -= g_lost
            looted = []
            for store in (self.resources, self.goods):
                for k in list(store):
                    if store[k] > 0 and random.random() < 0.5:
                        taken = store[k] // 2 + 1
                        store[k] = max(0, store[k] - taken)
                        looted.append(k)
            # Risque de destruction d'un bâtiment léger (sans batterie).
            destroyed = None
            if not self.has("batterie") and self.buildings and random.random() < 0.3:
                light = [b for b in self.buildings
                         if BASE_BUILDINGS[b].get("category") in ("service", "production")]
                if light:
                    destroyed = random.choice(light)
                    del self.buildings[destroyed]
            ui.fail(
                f"Le repaire est pillé. {g_lost} hommes perdus, une partie "
                "des réserves emportée.")
            if destroyed:
                ui.fail(f"Le bâtiment « {BASE_BUILDINGS[destroyed]['name']} » "
                        "est rasé. Il faudra le rebâtir.")
            state.morale = max(0, state.morale - 8)

    # ---------------- Affichage récapitulatif ---------------------

    def summary_lines(self) -> list:
        """Lignes de synthèse, utilisables par l'UI (statut/bilan)."""
        from data.resources import label as _lbl
        out = [
            f"Repaire : {self.name} — {self.location_name}",
            f"  Garnison : {self.garrison}/{self.garrison_cap()} hommes",
            f"  Stockage : {self.stored_total()}/{self.capacity()}",
            f"  Défense  : {self.defense_rating()}",
        ]
        if self.buildings:
            names = ", ".join(BASE_BUILDINGS[b]["name"] for b in self.buildings)
            out.append(f"  Bâtiments ({len(self.buildings)}) : {names}")
        if self.queue:
            q = ", ".join(f"{p['name']} ({p['turns_left']}t)" for p in self.queue)
            out.append(f"  En chantier : {q}")
        res = [f"{n} {_lbl(k)}" for k, n in self.resources.items() if n > 0]
        if res:
            out.append("  Matières : " + ", ".join(res))
        goods = [f"{n} {_lbl(k)}" for k, n in self.goods.items() if n > 0]
        if goods:
            out.append("  Biens : " + ", ".join(goods))
        return out
