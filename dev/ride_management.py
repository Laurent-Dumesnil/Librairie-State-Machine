from typing import Self
from state_machine_device import StateMachineDevice, State
from state_machine_utilities import ConditionalTransition, ActionState
from condition import ValueCondition
from console import Console

class RideManagement(StateMachineDevice):
    Pi = 2.5
    Pm = 120.0
    Er = 120.0
    Aa = 0.75
    Ab = 0.5

    def __init__(self:Self ,console:Console, initialized:bool = False, name:str = None, enabled:bool = True) -> None:
        
        self.__free_wheel_state = State("Free Wheel")
        self.__accelerating_state = ActionState("Accelerating")
        self.__breaking_state = State("Breaking")

        self.__free_wheel_state.add_transition(ConditionalTransition(ValueCondition(console.SpecialKey.UP_ARROW,console.key_pressed),self.__accelerating_state))
        self.__free_wheel_state.add_transition(ConditionalTransition(ValueCondition(console.SpecialKey.DOWN_ARROW,console.key_pressed),self.__breaking_state))
        self.__accelerating_state.add_transition(ConditionalTransition(ValueCondition(console.SpecialKey.DOWN_ARROW,console.key_pressed),self.__breaking_state))

        self.__accelerating_state.add_in_state_action()

        layout = self.Layout((self.__free_wheel_state, self.__accelerating_state, self.__breaking_state))
        super().__init__(layout, initialized, name, enabled)

