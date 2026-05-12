from __future__ import annotations
from typing import Self

class Scooter():
    Pi = 2.5
    Pm = 120.0
    Er = 120.0
    Aa = 0.75
    Ka = 1.1
    Vv = 15.0
    Ca = 0.0037
    Cr = 0.0153
    Kb = 5.0

    def __init__(self:Self):
        self.__speed = 100
        self.__battery = Battery()

    @property
    def speed(self:Self) -> float:
        return self.__speed   

    @property
    def battery(self:Self) -> Battery:
        return self.__battery
    
    def accelerate(self:Self, delta_time:float) -> None:
        self.__speed += delta_time*(Scooter.Ka*Scooter.Aa*(1-self.speed/Scooter.Vv)-Scooter.Ca*self.speed**2)

    def decelerate(self:Self, delta_time:float, breaking_strength:float = 0) -> None:
        self.__speed = max(0, self.speed - delta_time*(Scooter.Cr + Scooter.Kb*breaking_strength + Scooter.Ca*self.speed**2))


class Battery():
    def __init__(self:Self):
        self.__temperature = 0
        self.__power = 100

    @property
    def temperature(self:Self) -> float:
        return self.__temperature

    @temperature.setter
    def temperature(self:Self, value:float) -> None:
        if not isinstance(value, float):
            raise TypeError("Battery temperature must be a float")
        else:
            self.__temperature = value

    @property
    def power(self:Self) -> float:
        return self.__power

    @power.setter
    def power(self:Self, value:float) -> None:
        if not isinstance(value, float):
            raise TypeError("Battery charge must be a float")
        elif value < 0 or value > 100:
            raise ValueError("Battery charge must be between 0 and 100")
        else:
            self.__power = value
