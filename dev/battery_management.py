from typing import Self, override
from state_machine_device import StateMachineDevice, State
from state_machine_utilities import ConditionalTransition, ActionState
from condition import ReaderCondition
from console import Console
from scooter import Scooter

# va t-il falloir que j'ajoute des touches dans le fichier console
# Il faut réinitialiser son état

class BatteryManagement(StateMachineDevice):
    def __init__(self:Self,console:Console, scooter:Scooter, initialized:bool = False, name:str = None, enabled:bool = True) -> None:
        self.__delta_time = 0
        self.__scooter = scooter
        self.__console = console
        self.__charging_terminated = ActionState("Charging Terminated")
        self.__charging_complete = ActionState("Charging Complete")
        self.__charging_on = ActionState("Charging On")
        self.__cooling = ActionState("Cooling")
        self.__breaking = ActionState("Breaking")



        self.__charging_on.add_transition(ConditionalTransition(ReaderCondition(99, self.__battery_level), self.__charging_complete))
        self.__charging_on.add_transition(ConditionalTransition(ReaderCondition(85, self.__battery_temperature), self.__cooling))

        # self.__free_wheel_state.add_transition(ConditionalTransition(ReaderCondition(True, self.__read_up_arrow),self.__accelerating_state))
        # self.__free_wheel_state.add_transition(ConditionalTransition(ReaderCondition(True, self.__read_down_arrow),self.__breaking_state))
        # self.__accelerating_state.add_transition(ConditionalTransition(ReaderCondition(True, self.__read_down_arrow),self.__breaking_state))
        # self.__accelerating_state.add_transition(ConditionalTransition(ReaderCondition(False, self.__read_up_arrow), self.__free_wheel_state))
        # self.__breaking_state.add_transition(ConditionalTransition(ReaderCondition(False, self.__read_down_arrow), self.__free_wheel_state))

        self.__accelerating_state.add_in_state_action(self.__accelerate)
        self.__breaking_state.add_in_state_action(self.__decelerate)
        self.__free_wheel_state.add_in_state_action(self.__decelerate)

        layout = self.Layout((self.__free_wheel_state, self.__accelerating_state, self.__breaking_state))
        super().__init__(layout, initialized, name, enabled)


    @override
    def _do_tracking(self:Self, elapsed_time: float) -> None:
        self.__delta_time = elapsed_time
        
    # ne se trouve pas dans les specials keys, c'est un guess
    def __read_f(self:Self) -> bool:
        return True if "f" or "F" in self.__console.actual_key_pressed else False
    
    def __battery_level(self:Self) -> float:
        return self.__scooter.battery.power

    def __battery_temperature(self:Self) -> float:
        return self.__scooter.battery.temperature
    
    # faut ajouter les methodes pour la suite
    
    def __accelerate(self:Self) -> None:
        self.__scooter.accelerate(self.__delta_time)

    def __decelerate(self:Self) -> None:
        self.__scooter.decelerate(self.__delta_time)