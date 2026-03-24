from base_component import BaseComponent
from typing import Iterable, Callable, override, Self
from abc import ABC, abstractmethod

class State:
    pass

class Transition(BaseComponent, ABC):
    def __init__(self : Self, next_state : State | None, name : str | None = None, enabled : bool = True):
        super().__init__(name, enabled)
        self.__next_state : State | None = next_state
        self.__valid : bool = True
        
    @property
    @override
    def valid(self : Self) -> bool:
        return self.__valid
    
    @property
    def next_state(self : Self) -> State | None:
        return self.__next_state
    
    def _execute_transiting_action(self : Self) -> None:
        self._do_transiting_action()

    @abstractmethod
    def _do_transiting_action(self : Self) -> None:
        pass

    @abstractmethod
    def is_transiting(self : Self) -> bool:
        pass
    