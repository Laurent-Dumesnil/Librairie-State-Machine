from console import Console
from blinker_device import BlinkerDevice
from state_machine_utilities import MonitoredState
from typing import Self
# from controleur import Controleur

class SimpleLed():
    def __init__(self:Self, pos : tuple[int, int], size : tuple[int, int]):
        self.pos : tuple[int, int] = pos
        self.size : tuple[int, int] = size
        #self.color : Console.Color = color
        self.blinker : BlinkerDevice = BlinkerDevice(MonitoredState, MonitoredState)

    def on(self:Self, color : Console.Color):
        #self.color = color
        self.blinker.turn_on()
        # return MonitoredState()

    def off(self:Self):
        self.blinker.turn_off()

class BarLed():
    def __init__(self:Self, pos : tuple[int, int], size : tuple[int, int]):
        self.pos : tuple[int, int] = pos
        self.size : tuple[int, int] = size
        #self.colors : list[Console.Color] = colors
        #self.leds : list[SimpleLed] = leds
        self.blinker : BlinkerDevice = BlinkerDevice(MonitoredState, MonitoredState)

    def on(self:Self, percent_on : float):
        self.blinker.turn_on()
        # return MonitoredState()

    def off(self:Self):
        self.blinker.turn_off()

class ElectricScooterPanel():
    def __init__(self:Self, console:Console):
        self.console : Console = console
        self.initial_setup()
        

    def initial_setup(self:Self):
        self.top_left_blinker : SimpleLed
        self.bottom_left_blinker : SimpleLed
        self.top_right_blinker : SimpleLed
        self.bottom_right_blinker : SimpleLed
        self.left_side_light : SimpleLed
        self.right_side_light : SimpleLed
        self.headlight : SimpleLed
        self.rearlight : SimpleLed
        self.left_indicator : SimpleLed
        self.right_indicator : SimpleLed
        self.speed_indicator : BarLed
        self.charge_indicator : BarLed
        self.temp_indicator : BarLed

if __name__ == "__main__":
    #blinkerDevice = BlinkerDevice(on, off)
    pass