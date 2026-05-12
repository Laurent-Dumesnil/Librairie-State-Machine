from typing import Self, override
from state_machine_device import StateMachineDevice, State
from state_machine_utilities import ConditionalTransition, ActionState
from condition import ReaderCondition
from console import Console
from scooter import Scooter


class BatteryManagement(StateMachineDevice):
    def __init__(self:Self,console:Console, scooter:Scooter, initialized:bool = False, name:str = None, enabled:bool = True) -> None:
        self.__delta_time = 0
        self.__scooter = scooter
        self.__console = console
        self.__charging_terminated = ActionState("Charging Terminated", terminal=True)
        self.__charging_complete = ActionState("Charging Complete")
        self.__charging_on = ActionState("Charging On")
        self.__cooling = ActionState("Cooling")

        self.__charging_on.add_transition(ConditionalTransition(ReaderCondition(True, lambda: self.__battery_level() >= 99), self.__charging_complete))
        self.__charging_on.add_transition(ConditionalTransition(ReaderCondition(True, lambda: self.__battery_temperature() > 85), self.__cooling))
        self.__charging_on.add_transition(ConditionalTransition(ReaderCondition(True, lambda: self.__read_f()), self.__charging_terminated))
        self.__charging_complete.add_transition(ConditionalTransition(ReaderCondition(True, lambda:self.__battery_level() < 95), self.__charging_on))
        self.__cooling.add_transition(ConditionalTransition(ReaderCondition(True, lambda: self.__battery_temperature() < 75), self.__charging_on))

        self.__charging_on.add_in_state_action(self.__battery_charge, self.__temperature_up)
        self.__charging_complete.add_in_state_action(self.__battery_uncharge)
        self.__cooling.add_in_state_action(self.__temperature_down)
            
        layout = self.Layout((self.__charging_on, self.__charging_complete, self.__cooling, self.__charging_terminated))
        super().__init__(layout, initialized, name, enabled)
        
        if initialized : 
            self.reset()


    @override
    def _do_tracking(self:Self, elapsed_time: float) -> None:
        self.__delta_time = elapsed_time
        
    def __read_f(self:Self) -> bool:
        return "f" in self.__console.actual_key_pressed
    
    def __battery_level(self:Self) -> float:
        return self.__scooter.battery.power

    def __battery_temperature(self:Self) -> float:
        return self.__scooter.battery.temperature
    
    # À intégrer dans le modèle
    
    def __battery_charge(self:Self) -> None:
        self.__scooter.battery_charge(self.__delta_time)

    def __battery_uncharge(self:Self) -> None:
        self.__scooter.__battery_uncharge(self.__delta_time)

    def __temperature_up(self:Self) -> None:
        self.__scooter.temperature_up(self.__delta_time)
    
    def __temperature_down(self:Self) -> None:
        self.__scooter.temperature_down(self.__delta_time)