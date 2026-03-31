from state_machine_device import Transition, State, Self
from typing import final, override
class Condition:
    def __bool__():
        pass

class ConditionalTransition(Transition):
    def __init__(self:Self, condition: Condition | None = None, next_state: State | None = None, name: str | None = None, enabled:bool = True):
        self.__condition:Condition
        self.condition = condition
        super().__init__(next_state, name, enabled)

    @override
    @property
    def valid(self) -> bool:
        return super().valid and self.__condition is not None 

    @property
    def condition(self) -> Condition:
        return self.__condition

    @condition.setter
    def condition(self, value:Condition):
        if not isinstance(value, Condition):
            raise TypeError('condition must be a Condition')     
        self.__condition = value
        
    @final
    def is_transiting(self) -> bool:
        return bool(self.__condition)

            