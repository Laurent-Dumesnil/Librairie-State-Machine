from __future__ import annotations
from typing import Iterable, Callable, TypeAlias, Any, NoReturn, Self
from typing import override, Self
from abc import ABC, abstractmethod
from base_component import BaseComponent
from tracking_device import TrackingDevice

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


class State(BaseComponent):
    def __init__(self, name: str | None = None, *, enabled:bool = True, terminal:bool = False, do_in_state_action_entering:bool = False, do_in_state_action_exiting:bool = False):
        super().__init__(name=name, enabled=enabled)
        self.__terminal = terminal #est ce que lon doit faire une validation sur bool ??
        self.__do_in_state_action_entering = do_in_state_action_entering #est ce que lon doit faire une validation sur bool ??
        self.__do_in_state_action_exiting = do_in_state_action_exiting #est ce que lon doit faire une validation sur bool ??

        self.__transitions: list[Transition] = []

    @override
    @property
    def valid(self) -> bool:
        if self.terminal:
            return len(self.__transitions) == 0

        if len(self.__transitions) == 0:
            return False

        for transition in self.__transitions:
            if not transition.valid:
                return False

        return True
            
    @property
    def terminal(self):
        return self.__terminal
    
    @property
    def do_in_state_action_entering(self):
        return self.__do_in_state_action_entering
    
    @property
    def do_in_state_action_exiting(self):
        return self.__do_in_state_action_exiting
    
    def is_transiting(self) -> Transition | None:
        for transition in self.__transitions:
            if transition.is_transiting():
                return Transition
        return None

    def add_transition(self, transition: Transition | Iterable[Transition]) -> None:
        if isinstance(transition, Transition):
            self.__transitions.append(transition)
        elif isinstance(transition, Iterable):
            for t in transition:
                if not isinstance(t, Transition):
                    raise TypeError("Il faut ajouter uniquement des éléments de type Transition")
                self.__transitions.append(t)

    def _execute_entering_action(self):
        self._do_entering_action()
        if self.__do_in_state_action_entering:
            self._do_in_state_action()

    def _execute_in_state_action(self):
        self._do_in_state_action()

    def _execute_exiting_action(self): #Est ce que l'on fait l'action in state avant ou apres la exiting action?
        if self.__do_in_state_action_exiting:
            self._do_in_state_action()
        self._do_exiting_action()

    def _do_entering_action(self):
        pass

    def _do_in_state_action(self):
        pass

    def _do_exiting_action(self):
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
    
