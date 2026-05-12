from console import Console
from state_machine_utilities import MonitoredState
from typing import Self
# from controleur import Controleur

class SimpleLed:
    def __init__(self: Self, pos: tuple[int, int], size: tuple[int, int]):
        self.pos: tuple[int, int] = pos
        self.size: int = size
        self.color: Console.Color = Console.Color.DARK_GREY

    def on(self: Self, color:Console.Color) -> None:
        self.color = color

    def off(self: Self) -> None:
        self.color = Console.Color.DARK_GREY

class BarLed:
    def __init__(self: Self, pos: tuple[int, int], size: tuple[int, int]):
        self.pos: tuple[int, int] = pos
        self.size: int = size
        self.list_color: list[Console.Color] = []
        self.list_led: list[SimpleLed] = []

    def on(self: Self, percent_on: float) -> None:
        led_to_open = int(percent_on*len(self.list_led)/100)
        for i, led in enumerate(self.list_led):
            if i <= led_to_open:
                led.on(self.list_color[i])
            else:
                led.off()

    def off(self: Self) -> None:
        for led in self.list_led:
            led.color = Console.Color.DARK_GREY


class ElectricScooterPanel:
    def __init__(self: Self, console: Console):
        self.console: Console = console
        self.controleur = None # mettre controleur après
        self.top_left_blinker:SimpleLed = SimpleLed((2,2), 10)
        self.bottom_left_blinker:SimpleLed = SimpleLed((2,30), 10)
        self.top_right_blinker:SimpleLed
        self.bottom_right_blinker:SimpleLed
        self.left_side_light:SimpleLed
        self.right_side_light:SimpleLed
        self.headlight:SimpleLed
        self.rearlight:SimpleLed
        self.left_indicator:SimpleLed
        self.right_indicator:SimpleLed
        self.speed_indicator:BarLed
        self.charge_indicator:BarLed
        self.temp_indicator:BarLed
        self.list_simpleled = [self.top_left_blinker]
        self.list_barled = [self.top_left_blinker]
        self.__initial_setup()

    def __initial_setup(self: Self) -> None:
        console.window_size = (31,31)
        console.background_color = Console.Color.DARK_GREY
        console.write(' ' * self.top_left_blinker.size, self.top_left_blinker.pos)
        console.write(' ' * self.bottom_left_blinker.size, self.bottom_left_blinker.pos)
        console.reset_colors()

if __name__ == '__main__':
    console = Console()
    console.clear()
    panel = ElectricScooterPanel(console)