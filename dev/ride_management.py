from typing import Self, override
from state_machine_device import StateMachineDevice, State
from state_machine_utilities import ConditionalTransition, ActionState
from condition import ReaderCondition
from console import Console
from scooter import Scooter

class RideManagement(StateMachineDevice):
    def __init__(self:Self,console:Console, scooter:Scooter, initialized:bool = False, name:str = None, enabled:bool = True) -> None:
        self.__delta_time = 0
        self.__scooter = scooter
        self.__console = console
        self.__free_wheel_state = ActionState("Free Wheel")
        self.__accelerating_state = ActionState("Accelerating")
        self.__breaking_state = ActionState("Breaking")

        self.__free_wheel_state.add_transition(ConditionalTransition(ReaderCondition(True, self.__read_up_arrow),self.__accelerating_state))
        self.__free_wheel_state.add_transition(ConditionalTransition(ReaderCondition(True, self.__read_down_arrow),self.__breaking_state))
        self.__accelerating_state.add_transition(ConditionalTransition(ReaderCondition(True, self.__read_down_arrow),self.__breaking_state))
        self.__accelerating_state.add_transition(ConditionalTransition(ReaderCondition(False, self.__read_up_arrow), self.__free_wheel_state))
        self.__breaking_state.add_transition(ConditionalTransition(ReaderCondition(False, self.__read_down_arrow), self.__free_wheel_state))

        self.__accelerating_state.add_in_state_action(self.__accelerate)
        self.__breaking_state.add_in_state_action(self.__decelerate)
        self.__free_wheel_state.add_in_state_action(self.__decelerate)

        layout = self.Layout((self.__free_wheel_state, self.__accelerating_state, self.__breaking_state))
        super().__init__(layout, initialized, name, enabled)


    @override
    def _do_tracking(self:Self, elapsed_time: float) -> None:
        self.__delta_time = elapsed_time
        
    def __read_up_arrow(self:Self) -> bool:
        return True if self.__console.SpecialKey.UP_ARROW in self.__console.actual_key_pressed else False
    
    def __read_down_arrow(self:Self) -> bool:
        return True if self.__console.SpecialKey.UP_ARROW in self.__console.actual_key_pressed else False

    def __accelerate(self:Self) -> None:
        self.__scooter.accelerate(self.__delta_time)

    def __decelerate(self:Self) -> None:
        self.__scooter.decelerate(self.__delta_time)