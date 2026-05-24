from __future__ import annotations
from typing import Self, Callable
from abc import ABC, abstractmethod
from electric_scooter_panel import ElectricScooterPanel, SimpleLed, BarLed
from console import Console

ER = 120.0
PMax = 1.5e6

PI = 2.5
PM = 120.0
PS = 0.05

AA = 0.75
AB = 0.5
AT = 1.0

KA = 1.1
KB = 5.0
VV = 15.0
CA = 0.0037
CR = 0.0153

TE = 5.0e-8
TD = 5.0e-4
TA = 20.0

class Scooter:
    def __init__(self:Self, panel:ElectricScooterPanel) -> None:
        self.__speed = 0.0
        self.__battery = Battery()
        self.top_left_blinker = Light(panel.top_left_blinker, Console.Color.YELLOW)
        self.top_right_blinker = Light(panel.top_right_blinker, Console.Color.YELLOW)
        self.bottom_left_blinker = Light(panel.bottom_left_blinker, Console.Color.YELLOW)
        self.bottom_right_blinker = Light(panel.bottom_right_blinker, Console.Color.YELLOW)
        self.headlight = Light(panel.headlight, Console.Color.WHITE)
        self.rearlight = Light(panel.rearlight, Console.Color.LIGHT_RED)
        self.left_indicator = Light(panel.left_indicator, Console.Color.BLUE)
        self.right_indicator = Light(panel.right_indicator, Console.Color.LIGHT_GREEN)
        self.speed_indicator = BarLight(panel.speed_indicator)
        self.charge_indicator = BarLight(panel.charge_indicator)
        self.temp_indicator = BarLight(panel.temp_indicator)

    @property
    def speed(self:Self) -> float:
        return self.__speed
    
    @property
    def speed_percent(self:Self) -> float:
        return self.__speed*100/9.25

    @property
    def battery(self:Self) -> Battery:
        return self.__battery
    
    def accelerate(self:Self, delta_time:float | Callable[[], float]) -> None:
        if isinstance(delta_time, float):
            self.__speed += delta_time*(KA*AA*(1-self.speed/VV)-CA*self.speed**2)
        elif callable(delta_time):
            self.__speed += delta_time()*(KA*AA*(1-self.speed/VV)-CA*self.speed**2)
        else:
            raise TypeError("delta_time must be float or callable type")

    def decelerate(self:Self, delta_time:float | Callable[[], float], breaking_strength:float = 0.0) -> None:
        if isinstance(delta_time, float):
            self.__speed = max(0, self.speed - delta_time*(CR + KB*breaking_strength + CA*self.speed**2))
        elif callable(delta_time):
             self.__speed = max(0, self.speed - delta_time()*(CR + KB*breaking_strength + CA*self.speed**2))
        else:
            raise TypeError("delta_time must be float or callable type")
    

class Battery():
    def __init__(self:Self) -> None:
        self.__temperature = 30.0
        self.__power = 0.0
        self.__energy_level = PMax

    @property
    def energy_level(self:Self) -> float:
        return self.__energy_level
    
    @property
    def energy_level_percent(self:Self):
        return self.__energy_level*100/PMax
    
    @property
    def temp_percent(self:Self) -> None:
        return self.__temperature*100/85

    @property
    def temperature(self:Self) -> float:
        return self.__temperature

    def __update_battery(self:Self, elapsed_time: float | Callable[[], float]) -> None:
        if isinstance(elapsed_time, float):
            self.__energy_level = max(0, min(self.energy_level + (elapsed_time * self.__power), PMax))
            self.__temperature = self.__temperature + elapsed_time * (TE * abs(self.__power)**2 - TD*(self.__temperature - TA))
        elif callable(elapsed_time):
            self.__energy_level = max(0, min(self.energy_level + (elapsed_time() * self.__power), PMax))
            self.__temperature = self.__temperature + elapsed_time() * (TE * abs(self.__power)**2 - TD*(self.__temperature - TA))
        else:
            raise TypeError("elapsed_time must be float or callable type")

    def set_power_device_off(self:Self, elapsed_time: float | Callable[[], float]) -> None:
        if isinstance(elapsed_time, float) or callable(elapsed_time):
            self.__power = -PS
            self.__update_battery(elapsed_time)
        else:
            raise TypeError("elapsed_time must be float or callable type")
        
    def set_power_based_usage(self:Self, elapsed_time: float | Callable[[], float]) -> None:
        if isinstance(elapsed_time, float) or callable(elapsed_time):
            self.__power = -PI
            self.__update_battery(elapsed_time)
        else:
            raise TypeError("elapsed_time must be float or callable type")

    def set_power_device_charging(self:Self, elapsed_time: float | Callable[[], float]) -> None:
        if isinstance(elapsed_time, float) or callable(elapsed_time):
            self.__power = PM * AT - PI
            self.__update_battery(elapsed_time)
        else:
            raise TypeError("elapsed_time must be float or callable type")

    def set_power_device_accelerating(self:Self, elapsed_time: float | Callable[[], float]) -> None:
        if isinstance(elapsed_time, float) or callable(elapsed_time):
            self.__power = -(PI + PM * AA)
            self.__update_battery(elapsed_time)
        else:
            raise TypeError("elapsed_time must be float or callable type")

    def set_power_device_breaking(self:Self, elapsed_time: float | Callable[[], float], speed:float | Callable[[], float]) -> None:
        if isinstance(elapsed_time, float) or callable(elapsed_time):
            self.__power = ER * AB * speed - PI
            self.__update_battery(elapsed_time)
        else:
            raise TypeError("elapsed_time must be float or callable type")

class Light():
    def __init__(self:Self, light:SimpleLed, default_color:Console.Color) -> None:
        self.__light = light
        self.__color = default_color

    @property
    def color(self:Self) -> Console.Color:
        return self.__color
    
    @color.setter
    def color(self:Self, color:Console.Color):
        self.__color = color

    def close(self:Self) -> None:
        self.__light.draw_led(Console.Color.DARK_GREY)

    def colorize(self:Self) -> None:
        self.__light.draw_led(self.__color)

class BarLight():
    def __init__(self:Self, light:BarLed) -> None:
        self.__light = light
        self.__percent_on = 0

    @property
    def percent_on(self:Self) -> float:
        return self.__percent_on
    
    @percent_on.setter
    def percent_on(self:Self, percent_on:float):
        self.__percent_on = percent_on

    def close(self:Self) -> None:
        self.__light.draw_led(0)

    def colorize(self:Self) -> None:
        self.__light.draw_led(self.__percent_on)
     