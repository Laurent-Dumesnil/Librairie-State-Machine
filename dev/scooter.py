from __future__ import annotations
from typing import Self
from state_machine_utilities import State

ER = 120.0

PI = 2.5
PM = 120.0
PS = 0.05

AA = 0.75
AB = 0.5
AT = 1.0

KA = 1.1
VV = 15.0
CA = 0.0037
CR = 0.0153
KB = 5.0

TE = 5.0e-8
TD = 5.0e-4
TA = 20.0

class Scooter:
    def __init__(self:Self):
        self.__speed = 100.0
        self.__battery = Battery()

    @property
    def speed(self:Self) -> float:
        return self.__speed   

    @property
    def battery(self:Self) -> Battery:
        return self.__battery
    
    def accelerate(self:Self, delta_time:float) -> None:
<<<<<<< HEAD
        self.__speed += delta_time*(Scooter.Ka*Scooter.Aa*(1-self.speed/Scooter.Vv)-Scooter.Ca*self.speed**2)

    def decelerate(self:Self, delta_time:float, breaking_strength:float = 0) -> None:
        self.__speed = max(0, self.speed - delta_time*(Scooter.Cr + Scooter.Kb*breaking_strength + Scooter.Ca*self.speed**2))

=======
        self.speed += delta_time*(KA*AA*(1-self.speed/VV)-CA*self.speed**2)
        print(f'speed: {self.__speed}')

    def decelerate(self:Self, delta_time:float, breaking_strength:float = 0) -> None:
        self.speed = max(0, self.speed - delta_time*(CR + KB*breaking_strength + CA*self.speed**2))
>>>>>>> isabela-battery

class Battery():
    def __init__(self:Self):
        self.__temperature = 30.0
        self.__power = 0.0
        self.__energy = 100.0

    @property
    def energy(self:Self) -> float:
        return self.__energy

    @property
    def temperature(self:Self) -> float:
        return self.__temperature

    @property
    def power(self:Self) -> float:
        return self.__power
    
    def __update_battery(self:Self, elapsed_time:float) -> None:
        self.__energy = max(0, min(self.energy + elapsed_time * self.__power, PM))
        self.__temperature = self.__temperature + elapsed_time * (TE * abs(self.power)**2 - TD*(self.__temperature - TA))

    def set_power_device_off(self:Self, elapsed_time:float) -> None:
        self.__power = -PS
        self.__update_battery(elapsed_time)

    def set_power_based_usage(self:Self, elapsed_time:float) -> None:
        self.__power = -PI
        self.__update_battery(elapsed_time)

    def set_power_device_charging(self:Self, elapsed_time:float) -> None:
        self.__power = PM * AT - PI
        self.__update_battery(elapsed_time)

    def set_power_device_accelerating(self:Self, elapsed_time:float) -> None:
        self.__power = -(PI + PM * AA)
        self.__update_battery(elapsed_time)

    def set_power_device_breaking(self:Self, elapsed_time, speed:float) -> None:
        self.__power = ER * AB * speed - PI
        self.__update_battery(elapsed_time)