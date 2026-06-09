# Librairie de Machine à États — Projet Scooter Électrique

Projet scolaire de conception d'une librairie générique de machine à états en Python, appliquée à la simulation d'un scooter électrique interactif en console.

L'objectif principal était de concevoir une architecture réutilisable, découplée et extensible — où la logique de la machine à états est complètement indépendante de son domaine d'application.

---

## 🛠️ Technologies utilisées

`Python` · `Mypy` · `pytest` · `pdoc`

---

## Architecture de la librairie

La librairie est organisée en couches d'abstraction superposées :

```
BaseComponent                                       ← Gestion du nom, état activé/désactivé, validation
    └── TrackingDevice                              ← Dispositif de suivi en flux tiré (pattern composite)
            ├── StateMachineDevice                  ← Machine à états générique
            │       └── BlinkerDevice               ← Clignotant multifonctionnel
            │               └── SideBlinkersDevice  ← Paire gauche/droite
            └── TriggerDevice                       ← Déclenchement périodique d'action
```

La machine à états repose sur trois concepts fondamentaux : les **états** (`State`), les **transitions** (`Transition`) et les **conditions** (`Condition`). Chacun est extensible via des classes dérivées.

---

## Fonctionnalités de la librairie

**Gestion des états :**
- `State` — état de base avec actions d'entrée, en cours et de sortie
- `ActionState` — état enrichi avec listes d'actions configurables dynamiquement
- `MonitoredState` — état instrumenté mesurant le temps passé et le nombre d'entrées/sorties

**Gestion des transitions :**
- `ConditionalTransition` — transition déclenchée par une condition évaluable
- `ActionTransition` — transition avec actions exécutées au moment du transit
- `MonitoredTransition` — transition instrumentée comptant les transits et mesurant les délais

**Conditions disponibles :**
- `AlwaysTrueCondition` / `AlwaysFalseCondition` — conditions statiques
- `DelaySinceEnteredCondition` — vraie après X secondes dans un état
- `DelaySinceExitedCondition` — vraie après X secondes depuis la sortie d'un état
- `StateEntryCountCondition` — vraie après N entrées dans un état
- `StateValueCondition` — vraie si la valeur personnalisée d'un état correspond à une valeur attendue
- `ReaderCondition` — basée sur la lecture d'une touche clavier

**Infrastructure de suivi :**
- `TrackingDevice` — classe de base en flux tiré (pull-based) avec patron composite
- `TrackingManager` / `TrackingApplication` — orchestration de la boucle principale avec `run_forever()` et `run_until()`
- `TriggerDevice` — déclencheur périodique d'action configurable
- `ElapsedTimer` — mesure du temps en mode accumulé ou intervalle

---

## Implémentation : Scooter électrique

Le projet scooter démontre concrètement l'utilisation de la librairie dans un contexte de simulation embarquée.

**Ce qui est simulé :**
- Accélération et décélération du scooter via les flèches du clavier
- Gestion thermique et niveau de charge de la batterie (modèle physique simplifié)
- Clignotants gauche/droite avec modes allumé, éteint, clignotant continu et clignotant minuté
- Tableau de bord visuel en console avec indicateurs LED (vitesse, charge, température)

**Affichage console :**

Le panneau `ElectricScooterPanel` affiche en temps réel un tableau de bord coloré avec barres de progression et LEDs simulées directement dans le terminal.

---

## Installation

**Prérequis :** Python 3.11+

```bash
git clone https://github.com/votre-utilisateur/state-machine-scooter.git
cd state-machine-scooter

pip install numpy matplotlib
```

---

## ⚙️ Utilisation

### Lancer la simulation du scooter

```bash
python controller_scooter.py
```

#### États du scooter

Le scooter suit une machine à états principale avec les modes suivants :

| État | Description |
|---|---|
| `power_off` | Scooter éteint — en attente d'action |
| `unlocking` | Déverrouillage en cours (3 secondes) |
| `powering_up` | Démarrage en cours (3 secondes) |
| `idle` | Scooter allumé, à l'arrêt — timeout automatique après 30 secondes |
| `scooting` | En déplacement |
| `charging` | En charge (câble branché) |
| `powering_down` | Extinction en cours (3 secondes) |
| `locking` | Verrouillage en cours (3 secondes) |
| `integrity_failed` | Échec de l'intégrité au démarrage |
| `charging_failed` | Erreur de charge détectée |

#### Contrôles clavier

**Gestion de l'alimentation**

| Touche | Action | État requis |
|---|---|---|
| `p` (maintenu) | Déverrouiller / allumer le scooter | `power_off` |
| `p` (maintenu) | Verrouiller / éteindre le scooter | `idle` |
| `p` (relâché) | Annuler le déverrouillage | `unlocking` |

**Conduite** *(disponible en état `scooting`)*

| Touche | Action |
|---|---|
| `↑` (maintenu) | Accélérer |
| `↓` (maintenu) | Freiner |
| `c` | Activer le régulateur de vitesse (cruise control) |

> Le scooter repasse automatiquement en `idle` s'il reste à moins de 0.5 km/h pendant 30 secondes.

**Éclairage** *(disponible en `idle`, `scooting`, `power_off`, `charging`)*

| Touche | Action |
|---|---|
| `Espace` | Allumer / éteindre le phare avant |
| `←` | Activer / désactiver le clignotant gauche |
| `→` | Activer / désactiver le clignotant droit |

**Recharge**

| Touche | Action |
|---|---|
| `i` | Brancher le câble de recharge |
| `o` | Débrancher le câble de recharge |
| `f` | Arrêter la charge manuellement |

> Brancher le câble (`i`) depuis l'état `power_off` démarre automatiquement la recharge. La charge s'arrête automatiquement en cas de surchauffe (> 85°C) ou de batterie pleine (≥ 99%).

---

### Tester le BlinkerDevice seul

```bash
python project_blinker.py
```

### Tester le TrackingDevice

```bash
python project_tracking_device.py
```

---

## Structure du projet

```
├── base_component.py           # Classe de base commune à tous les composants
├── elapsed_timer.py            # Utilitaire de mesure du temps (ACCUMULATED / INTERVAL)
├── type_utilities.py           # Alias de types génériques (GenericCallback, GenericPredicate, ...)
│
├── tracking_device.py          # TrackingDevice, TrackingManager, TrackingApplication, TriggerDevice
├── state_machine_device.py     # StateMachineDevice, State, Transition, Layout
├── state_machine_utilities.py  # ActionState, MonitoredState, ConditionalTransition, conditions...
├── condition.py                # Hiérarchie de conditions (Condition, AlwaysTrue, ReaderCondition...)
│
├── blinker_device.py           # BlinkerDevice et SideBlinkersDevice
├── console_reader.py           # Lecture des touches clavier via TrackingDevice
│
├── scooter.py                  # Modèle physique du scooter (vitesse, batterie, lumières)
├── electric_scooter_panel.py   # Tableau de bord console (LEDs, barres de progression)
├── ride_management.py          # Machine à états de conduite (accélérer / freiner / roue libre)
├── controller_scooter.py       # Point d'entrée principal de la simulation
│
├── project_blinker.py          # Test isolé du BlinkerDevice
└── project_tracking_device.py  # Test isolé du TrackingDevice
```

---

## Ce que j'ai appris

Ce projet m'a permis de mettre en pratique des principes avancés de conception orientée objet : hiérarchies d'abstraction profondes, patron composite, programmation en flux tiré (*pull-based*), et séparation stricte entre l'infrastructure générique et le domaine applicatif.

La partie la plus exigeante a été de concevoir une architecture où `StateMachineDevice` ne connaît pas les conditions ni les types d'états concrets — c'est entièrement la responsabilité des couches supérieures. Ça m'a confronté directement aux compromis entre flexibilité et complexité dans la conception de librairies réutilisables.