"""
project_tracking_device.py

Objectif
--------
Micro-projet de test pour la bibliothèque tracking_device.

Ce fichier démontre explicitement :
- l'utilisation de TrackingApplication
- l'utilisation de TriggerDevice
- l'utilisation d'un dispositif personnalisé

Résultats attendus
------------------
1. TriggerDevice affiche un message automatiquement à intervalle régulier.
2. ConsoleEveryNCallsDevice affiche un message tous les N appels à track().
3. On peut observer concrètement la séparation entre :
   - _do_valid() : vérification de conformité
   - _do_tracking() : comportement dynamique à chaque itération
"""

from __future__ import annotations

from typing import override
from elapsed_timer import ElapsedTimer
from tracking_device import TrackingDevice, TriggerDevice, TrackingApplication


class ConsoleEveryNCallsDevice(TrackingDevice):
    """
    Device personnalisé très simple.

    Rôle :
    - compte le nombre d'appels à track()
    - affiche un message tous les `calls_before_print` appels

    Ici :
    - _do_valid() vérifie seulement que les paramètres internes sont acceptables
    - _do_tracking() gère le comportement dynamique
    """

    def __init__(self, message: str, calls_before_print: int, name: str | None = None, enabled: bool = True) -> None:
        super().__init__(name=name, enabled=enabled)
        self.__message: str = message
        self.__calls_before_print: int = calls_before_print
        self.__call_count: int = 0

    @override
    def _do_valid(self) -> bool:
        return self.__calls_before_print > 0

    @override
    def _do_reset(self) -> None:
        self.__call_count = 0

    @override
    def _do_tracking(self, elapsed_time: float) -> None:
        # Ici on fait évoluer l'état.
        self.__call_count += 1

        if self.__call_count % self.__calls_before_print == 0:
            print(f"[{self.name}] {self.__message} (appel track #{self.__call_count})")


def trigger_action_message() -> None:
    """Action simple appelée par TriggerDevice."""
    print("Trigger action!")


def stop_after_n_seconds(duration: float):
    """
    Fabrique une running condition pour TrackingApplication.run_until().

    Retourne None tant que le temps n'est pas écoulé.
    Retourne une valeur non-None quand il faut arrêter.
    """

    #ElapsedTimer pour condtion de fin
    timer = ElapsedTimer(mode=ElapsedTimer.Mode.ACCUMULATED)

    def condition():
        if timer.elapsed >= duration:
            return "Fin du test"
        return None

    return condition


def main() -> None:
    # Device 1 : TriggerDevice
    trigger = TriggerDevice(
        2.0,
        trigger_action_message,
        name="TriggerDevice",
        enabled=True,
        initial_time=0.0,
        auto_reset_when_enabling=True,
    )

    # Device 2 : device personnalisé
    every_n_calls = ConsoleEveryNCallsDevice(
        message="Affichage nombre d'appels",
        calls_before_print=100000,
        name="ConsoleEveryNCalls",
    )

    app = TrackingApplication()
    app.add_device(trigger)
    app.add_device(every_n_calls)

    print("Début du test...")
    print("Observation attendue :")
    print("- TriggerDevice affiche un message toutes les 2 secondes")
    print("- ConsoleEveryNCallsDevice affiche un message tous les 100 000 appels à track()")
    print("- Le programme arrête après 12 secondes")
    print()

    result = app.run_until(stop_after_n_seconds(12.0))
    print()
    print(result)


if __name__ == "__main__":
    main()