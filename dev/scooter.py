from __future__ import annotations
from typing import Self, Callable
from ElectricScooterPanel import ElectricScooterPanel

ER = 120.0

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
    def __init__(self:Self) -> None:
        self.__speed = 0.0
        self.__battery = Battery()
        #self.__panel = panel

    @property
    def speed(self:Self) -> float:
        return self.__speed   

    @property
    def battery(self:Self) -> Battery:
        return self.__battery
    
    def accelerate(self:Self, delta_time:float | Callable[[], float]) -> None:
        if isinstance(delta_time, float):
            self.__speed += delta_time*(KA*AA*(1-self.speed/VV)-CA*self.speed**2)
            #self.__panel.speed_indicator.draw_led(50)
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
        self.__energy_level = ER

    @property
    def energy_level(self:Self) -> float:
        return self.__energy_level

    @property
    def temperature(self:Self) -> float:
        return self.__temperature

    def __update_battery(self:Self, elapsed_time: float | Callable[[], float]) -> None:
        if isinstance(elapsed_time, float):
            self.__energy_level = max(0, min(self.energy_level + elapsed_time * self.__power, PM))
            self.__temperature = self.__temperature + elapsed_time * (TE * abs(self.__power)**2 - TD*(self.__temperature - TA))
        elif callable(elapsed_time):
            self.__energy_level = max(0, min(self.energy_level + elapsed_time() * self.__power, PM))
            self.__temperature = self.__temperature + elapsed_time() * (TE * abs(self.__power)**2 - TD*(self.__temperature - TA))
        else:
            raise TypeError("elapsed_time must be float or callable type")

    def set_power_device_off(self:Self, elapsed_time: float | Callable[[], float]) -> None:
        if isinstance(elapsed_time, float):
            self.__power = -PS
            self.__update_battery(elapsed_time)
        elif callable(elapsed_time):
            self.__power = -PS
            self.__update_battery(elapsed_time())
        else:
            raise TypeError("elapsed_time must be float or callable type")
        
    def set_power_based_usage(self:Self, elapsed_time: float | Callable[[], float]) -> None:
        if isinstance(elapsed_time, float):
            self.__power = -PI
            self.__update_battery(elapsed_time)
        elif callable(elapsed_time):
            self.__power = -PI
            self.__update_battery(elapsed_time())
        else:
            raise TypeError("elapsed_time must be float or callable type")

    def set_power_device_charging(self:Self, elapsed_time: float | Callable[[], float]) -> None:
        if isinstance(elapsed_time, float):
            self.__power = PM * AT - PI
            self.__update_battery(elapsed_time)
        elif callable(elapsed_time):
            self.__power = PM * AT - PI
            self.__update_battery(elapsed_time())
        else:
            raise TypeError("elapsed_time must be float or callable type")

    def set_power_device_accelerating(self:Self, elapsed_time: float | Callable[[], float]) -> None:
        if isinstance(elapsed_time, float):
            self.__power = -(PI + PM * AA)
            self.__update_battery(elapsed_time)
        elif callable(elapsed_time):
            self.__power = -(PI + PM * AA)
            self.__update_battery(elapsed_time())
        else:
            raise TypeError("elapsed_time must be float or callable type")

    def set_power_device_breaking(self:Self, elapsed_time: float | Callable[[], float], speed:float | Callable[[], float]) -> None:
        if isinstance(elapsed_time, float) and isinstance(speed, float):
            self.__power = ER * AB * speed - PI
            self.__update_battery(elapsed_time)
        elif callable(elapsed_time) and callable(speed):
            self.__power = ER * AB * speed() - PI
            self.__update_battery(elapsed_time())
        else:
            raise TypeError("elapsed_time must be float or callable type")