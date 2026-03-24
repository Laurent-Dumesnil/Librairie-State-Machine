from tracking_device import TrackingDevice
from typing import Iterable, Callable, TypeAlias, Any, NoReturn, Self
from base_component import BaseComponent
from typing import override, Self
from abc import ABC, abstractmethod


class State() :
    pass

class Transition() :
    pass

class Layout :
    def __init__(self : Self, states:tuple[State, ...]):

        if len(states) <= 0 :
            raise ValueError('Tuple size of states must be bigger than 0')

        for state in states :
            if not isinstance (state, State) :
                raise TypeError('Must be a State')

        self._states = states

        self._initial_state : State

        if not isinstance(states[0], State):
            raise TypeError('Must be a State')
        
        self._initial_state : State 
        self.initial_state = states[0]

            

    def __contains__(state:State) -> bool :
        pass

    @property
    def initial_state(self) -> State :
        return self._initial_state
    
    

class StateMachineDevice(TrackingDevice) :
    def __init__(self : Self, layout:Layout, current_state: State | None):
        pass


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
    
