from base_component import BaseComponent
from typing import override, Self
from abc import ABC, abstractmethod

class State:
    pass

class Transition(BaseComponent, ABC):
    def __init__(self : Self, next_state : State | None, name : str | None = None, enabled : bool = True):
        super().__init__(name, enabled)
        self.__next_state : State | None = next_state
 
        
    @property
    @override
    def valid(self : Self) -> bool:
        return True if self.__next_state and super().valid else False
    
    @property
    def next_state(self : Self) -> State | None:
        return self.__next_state
    
    def _execute_transiting_action(self : Self) -> None:
        self._do_transiting_action()

    def _do_transiting_action(self : Self) -> None:
        pass

    @abstractmethod
    def is_transiting(self : Self) -> bool:
        pass
    