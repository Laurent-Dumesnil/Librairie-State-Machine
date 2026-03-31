from __future__ import annotations
from typing import Iterable, Callable, TypeAlias, Any, NoReturn, Self
from typing import override, Self
from abc import ABC, abstractmethod
from base_component import BaseComponent
from tracking_device import TrackingDevice

#Commande our corriger le fichier:
#mypy --strict --check-untyped-defs state_machine_device.py

class StateMachineDevice(TrackingDevice) :

    class Layout :
        def __init__(self: Self, states:tuple[State, ...]):
            if len(states) <= 0 :
                raise ValueError('Tuple size of states must be bigger than 0')

            for state in states :
                if not isinstance (state, State) :
                    raise TypeError('Must be a State')
                if not state.valid :
                    raise ValueError('All states must be valid.')
            
            # self._initial_state : State - si on initialise pas, on aura des problemes
            self._states : tuple[State, ...] = states
            self._initial_state = states[0]
        
        def __contains__(self: Self, state:State) -> bool:
            return state in self._states

        @property
        def initial_state(self) -> State :
            return self._initial_state 


    def __init__(self: Self, layout: Layout, initialized: bool = False, name: str | None = None, enabled: bool = True):
        self.__layout = layout
        self.__current_state: State | None = layout.initial_state if initialized else None 
        super().__init__(name=name, enabled=enabled)
        # Question: activation de l'etat initial engendre do_entering_action? 

    @property
    def current_state(self) -> State | None:
        return self.__current_state    
    
    def __transit_by(self, transition: Transition) -> None :
        if self.__current_state is not None:
            self.__current_state._execute_exiting_action()
            transition._execute_transiting_action()

            if self.__current_state.terminal is False:
                self.__current_state = transition.next_state
                if self.__current_state is not None:
                    self.__current_state._execute_entering_action()

    def _transit_to(self, state: State) -> None :
        pass

    @override
    def _do_tracking(self, elapsed_time: float) -> None:
        if self.__current_state is None:
            return
        
        transition = self.__current_state.is_transiting()

        if transition is not None and transition.is_transiting():
            self.__transit_by(transition)
        else:
            self.__current_state._execute_in_state_action()

    @override
    def _do_reset(self) -> None:
        self.__current_state = self.__layout.initial_state


class State(BaseComponent):
    def __init__(self, name: str | None = None, *, enabled:bool = True, terminal:bool = False, do_in_state_action_when_entering:bool = False, do_in_state_action_when_exiting:bool = False):
        super().__init__(name=name, enabled=enabled)
        self.__terminal = terminal #est ce que lon doit faire une validation sur bool ??
        self.__do_in_state_action_when_entering = do_in_state_action_when_entering #est ce que lon doit faire une validation sur bool ??
        self.__do_in_state_action_when_exiting = do_in_state_action_when_exiting #est ce que lon doit faire une validation sur bool ??

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
    def terminal(self) -> bool:
        return self.__terminal
    
    @property
    def do_in_state_action_when_entering(self) -> bool:
        return self.__do_in_state_action_when_entering
    
    @property
    def do_in_state_action_when_exiting(self) -> bool:
        return self.__do_in_state_action_when_exiting
    
    def is_transiting(self) -> Transition | None:
        for transition in self.__transitions:
            if transition.is_transiting():
                return transition
        return None

    def add_transition(self, transition: Transition | Iterable[Transition]) -> None:
        if isinstance(transition, Transition):
            self.__transitions.append(transition)
        elif isinstance(transition, Iterable):
            for t in transition:
                if not isinstance(t, Transition):
                    raise TypeError("Il faut ajouter uniquement des éléments de type Transition")
                self.__transitions.append(t)

    def _execute_entering_action(self) -> None:
        self._do_entering_action()
        if self.__do_in_state_action_when_entering:
            self._do_in_state_action()

    def _execute_in_state_action(self) -> None:
        self._do_in_state_action()

    def _execute_exiting_action(self) -> None: #Est ce que l'on fait l'action in state avant ou apres la exiting action?
        if self.__do_in_state_action_when_exiting:
            self._do_in_state_action()
        self._do_exiting_action()

    def _do_entering_action(self) -> None:
        pass

    def _do_in_state_action(self) -> None:
        pass

    def _do_exiting_action(self) -> None:
        pass

class Transition(BaseComponent, ABC):
    def __init__(self : Self, next_state : State | None = None, name : str | None = None, enabled : bool = True):
        super().__init__(name=name, enabled=enabled)
        self.__next_state : State | None = next_state #Besoin de type int ?
 
        
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
    