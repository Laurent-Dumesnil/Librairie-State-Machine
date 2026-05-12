from __future__ import annotations
from typing import Self
from state_machine_utilities import State

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
    
    @speed.setter
    def speed(self:Self, value:float) -> None:
        if not isinstance(value, float):
            raise TypeError("Speed must be a float")
        elif value < 0:
            raise ValueError("Speed must be greater than 0")
        else:
            self.__speed = value

    @property
    def battery(self:Self) -> Battery:
        return self.__battery
    
    def accelerate(self:Self, delta_time:float) -> None:
        self.speed += delta_time*(Scooter.Ka*Scooter.Aa*(1-self.speed/Scooter.Vv)-Scooter.Ca*self.speed**2)
        print(f'speed: {self.__speed}')

    def decelerate(self:Self, delta_time:float, breaking_strength:float = 0) -> None:
        self.speed = max(0, self.speed - delta_time*(Scooter.Cr + Scooter.Kb*breaking_strength + Scooter.Ca*self.speed**2))


class Battery():
    Ps = 0.05
    Pi = 2.5 # ici ou dans Scooter les constantes de la batterie?
    Aa = 0.75
    Er = 120.0
    Pm = 120.0
    Te = 5.0e-8
    Td = 5.0e-4
    Ta = 20.0
    def __init__(self:Self):
        self.__temperature = 0
        self.__power = 100
        self.__energy = 0

    @property
    def energy(self:Self) -> float:
        return self.__energy

    #TODO Changer les valeurs  
    @energy.setter
    def energy(self:Self, value:float) -> None: 
        if not isinstance(value, float):
            raise TypeError("Battery energy must be a float")
        elif value < 0 or value > 100:
            raise ValueError("Battery energy must be between 0 and 100")
        else:
            self.__energy = value

    @property
    def temperature(self:Self) -> float: # En tout temps elle est calculée.
        return self.__temperature

    @temperature.setter
    def temperature(self:Self, value:float) -> None:
        if not isinstance(value, float):
            raise TypeError("Battery temperature must be a float")
        else:
            self.__temperature = value

    @property #  La puissance net c'est ce qui influence l'energie 
    def power(self:Self) -> float:
        return self.__power

    @power.setter
    def power(self:Self, value:float) -> None:
        if not isinstance(value, float):
            raise TypeError("Battery power must be a float")
        elif value < 0 or value > 100:
            raise ValueError("Battery power must be between 0 and 100")
        else:
            self.__power = value

    def update(self:Self, delta_time:float) -> None: # delta_time: temps entre les deux tics
        self.energy = max(0, min(self.energy + delta_time * self.power))
        self.temperature = self.temperature + delta_time * (Battery.Te * abs(self.power)**2 - Battery.Td*(Battery.temperature - Battery.Ta))

    # def set_power_device_off(self:Self):
    #     self.power = -Battery.Ps

    # def set_power_based_usage(self:Self):
    #     self.power = -Battery.Pi

    # def set_power_device_charging(self:Self):
    #     ... # self.power = TODO mettre la bonne formule

    # def set_power_device_accelerating(self:Self):
    #     self.power = -(Battery.Pi + Battery.Pm * Battery.Aa)

    # def set_power_device_breaking(self:Self):
    #     self.power = Battery.Er * Battery.Aa * Battery.Vt - Battery.Pi




