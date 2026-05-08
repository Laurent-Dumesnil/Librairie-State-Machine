from console import Console
from blinker_device import BlinkerDevice
from state_machine_utilities import MonitoredState
from typing import Self
# from controleur import Controleur

class SimpleLed:
    def __init__(self: Self, pos: tuple[int, int], size: tuple[int, int]):
        self.pos: tuple[int, int] = pos
        self.size: tuple[int, int] = size
        self.color: Console.Color = Console.Color.BLACK # eteint
        self.blinker: BlinkerDevice = BlinkerDevice(MonitoredState, MonitoredState)

    def on(self: Self, color: Console.Color) -> None:
        self.color = color
        self.blinker.turn_on()

    def off(self: Self) -> None:
        self.color = Console.Color.BLACK
        self.blinker.turn_off()


class BarLed:
    def __init__(self: Self, pos: tuple[int, int], size: tuple[int, int]):
        self.pos: tuple[int, int] = pos
        self.size: tuple[int, int] = size
        self.list_color: list[Console.Color] = []
        self.list_led: list[SimpleLed] = []
        self.blinker: BlinkerDevice = BlinkerDevice(MonitoredState, MonitoredState)
        self.percent_on : float = 0.0

    def on(self: Self, percent_on: float) -> None:
        self.percent_on = percent_on
        self.blinker.turn_on()

    def off(self: Self) -> None:
        self.percent_on = 0.0
        self.blinker.turn_off()


class ElectricScooterPanel:
    def __init__(self: Self, console: Console):
        self.console: Console = console
        self.controleur = None # mettre controleur après
        self.initial_setup()

    def initial_setup(self: Self) -> None:
        # déterminer les variables à initialiser ?
        self.top_left_blinker: SimpleLed
        self.bottom_left_blinker: SimpleLed
        self.top_right_blinker: SimpleLed
        self.bottom_right_blinker: SimpleLed
        self.left_side_light: SimpleLed
        self.right_side_light: SimpleLed
        self.headlight: SimpleLed
        self.rearlight: SimpleLed
        self.left_indicator: SimpleLed
        self.right_indicator: SimpleLed
        self.speed_indicator: BarLed
        self.charge_indicator: BarLed
        self.temp_indicator: BarLed