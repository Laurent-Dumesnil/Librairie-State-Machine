from tracking_device import TrackingDevice
from typing import Iterable, Callable, TypeAlias, Any, NoReturn, Self


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
