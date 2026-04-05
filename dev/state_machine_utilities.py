from time import perf_counter
from state_machine_device import Transition, State, Self
from typing import final, override, TypeAlias, Iterable, Any
from type_utilities import GenericCallback
from condition import Condition

Action:TypeAlias = GenericCallback

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
    
class ActionTransition(ConditionalTransition):
    def __init__(self, condition:Condition | None = None, next_state:State | None = None, name: str | None = None, enabled:bool = True):
        super().__init__(condition=condition, next_state=next_state, name=name, enabled=enabled)
        self.__actions: list[Action] = list()

    @property
    def transiting_action_count(self) -> int:
        return len(self.__actions)
        
    def _do_transiting_action(self):
        for action in self.__actions:
            action()

    def clear_transiting_actions(self):
        self.__actions.clear()

    def add_transiting_action(self, action:Action | Iterable[Action]):
        if callable(action):
            self.__actions.append(action)
            return
        elif isinstance(action, Iterable) and not isinstance(action, str):
            for element in action:
                if isinstance(element, action):
                    self.__actions.append(element)
                else:
                    raise TypeError("Doit être de type action")
            return
        raise TypeError("Doit être de type action ou un iterable d'actions")
    
class MonitoredTransition(ActionTransition):
    def __init__(self, condition:Condition | None = None, next_state:State | None = None, name: str | None = None, enabled:bool = True):
        super().__init__(condition=condition, next_state=next_state, name=name, enabled=enabled)
        self.__transit_count: int = 0
        self.__creation_reference_time:float = perf_counter()
        self.__last_transit_reference_time: float | None = None
        self.custom_value: Any = None

    @property
    def transit_count(self) -> int:
        return self.__transit_count
    
    @property
    def creation_reference_time(self) -> float:
        return self.__creation_reference_time
    
    @property
    def elapsed_time_since_creation(self) -> float:
        return perf_counter() - self.__creation_reference_time
    
    @property
    def last_transit_reference_time(self) -> float | None:
        return self.__last_transit_reference_time
    
    @property
    def elapsed_since_last_transit(self) -> float | None:
        if self.__last_transit_reference_time is None:
            return None
        return perf_counter() - self.__last_transit_reference_time
    
    @override
    def _execute_transiting_action(self) -> None:
        self.__transit_count += 1
        self.__last_transit_reference_time = perf_counter()
        super()._execute_transiting_action()
                

class ActionState(State):
    def __init__(self, name:str | None=None, *, enabled:bool=True, terminal: bool=False, do_in_state_action_when_entering: bool=False, do_in_state_action_when_exiting: bool=False):
        super().__init__(name=name, enabled=enabled, terminal=terminal, do_in_state_action_when_entering=do_in_state_action_when_entering, do_in_state_action_when_exiting=do_in_state_action_when_exiting)
        self.__entering_actions: list[Action] = list()
        self.__in_state_actions: list[Action] = list()
        self.__exiting_actions: list[Action] = list()

    @property
    def entering_action_count(self) -> int:
        return len(self.__entering_actions)
    
    @property
    def in_state_action_count(self) -> int:
        return len(self.__in_state_actions)
    
    @property
    def exiting_action_count(self) -> int:
        return len(self.__exiting_actions)
    
    def clear_entering_actions(self) -> None:
        self.__entering_actions.clear()

    def clear_in_state_actions(self) -> None:
        self.__in_state_actions.clear()

    def clear_exiting_actions(self) -> None:
        self.__exiting_actions.clear()

    def add_entering_action(self, action: Action | Iterable[Action]) -> None:
        if callable(action):
            self.__entering_actions.append(action)
            return
        elif isinstance(action, Iterable) and not isinstance(action, str):
            for element in action:
                if callable(element):
                    self.__entering_actions.append(element)
                else:
                    raise TypeError("Chaque élément doit être de type callable")
            return
        raise TypeError("Doit être de type callable ou être un Iterable de callable")

    def add_in_state_action(self, action: Action | Iterable[Action]) -> None:
        if callable(action):
            self.__in_state_actions.append(action)
            return
        elif isinstance(action, Iterable) and not isinstance(action, str):
            for element in action:
                if callable(element):
                    self.__in_state_actions.append(element)
                else:
                    raise TypeError("Chaque élément doit être de type callable")
            return
        raise TypeError("Doit être de type callable ou être un Iterable de callable")

    def add_exiting_action(self, action: Action | Iterable[Action]) -> None:
        if callable(action):
            self.__exiting_actions.append(action)
            return
        elif isinstance(action, Iterable) and not isinstance(action, str):
            for element in action:
                if callable(element):
                    self.__exiting_actions.append(element)
                else:
                    raise TypeError("Chaque élément doit être de type callable")
            return
        raise TypeError("Doit être de type callable ou être un Iterable de callable")

    @override
    def _do_entering_action(self) -> None:
        super()._do_entering_action()
        for action in self.__entering_actions:
            action()

    
    @override
    def _do_in_state_action(self) -> None:
        super()._do_in_state_action()
        for action in self.__in_state_actions:
            action()
    
    @override
    def _do_exiting_action(self) -> None:
        super()._do_exiting_action()
        for action in self.__exiting_actions:
            action()

#Où doit t-on prendre les références au temps pour cette classe??
#import time ou MonitorState connait un elapsed timer??
class MonitoredState(ActionState):
    def __init__(self, name:str | None=None, *, enabled:bool=True, terminal: bool=False, do_in_state_action_when_entering: bool=False, do_in_state_action_when_exiting: bool=False):
        super().__init__(name=name, enabled=enabled, terminal=terminal, do_in_state_action_when_entering=do_in_state_action_when_entering, do_in_state_action_when_exiting=do_in_state_action_when_exiting)
        self.__entry_count:int = 0
        self.__exit_count:int = 0
        self.__creation_reference_time:float = perf_counter()
        self.__last_entry_reference_time: float | None = None
        self.__last_exit_reference_time: float | None = None
        self.custom_value: Any = None

    @property
    def entry_count(self) -> int:
        return self.__entry_count
    
    @property
    def exit_count(self) -> int:
        return self.__exit_count
    
    @property
    def creation_reference_time(self) -> float:
        return self.__creation_reference_time
    
    @property
    def elapsed_time_since_creation(self) -> float:
        return perf_counter() - self.__creation_reference_time
    
    @property
    def last_entry_reference_time(self) -> float | None:
        return self.__last_entry_reference_time
    
    @property
    def elapsed_since_last_entry(self) -> float | None:
        if self.__last_entry_reference_time is None:
            return None
        return perf_counter() - self.__last_entry_reference_time
    
    @property
    def last_exit_reference_time(self) -> float | None:
        return self.__last_exit_reference_time
    
    @property
    def elapsed_since_last_exit(self) -> float | None:
        if self.__last_exit_reference_time is None:
            return None
        return perf_counter() - self.__last_exit_reference_time
    
    @override
    def _execute_entering_action(self) -> None:
        self.__entry_count += 1
        self.__last_entry_reference_time = perf_counter()
        super()._execute_entering_action()
    
    @override
    def _execute_exiting_action(self) -> None:
        self.__exit_count += 1
        self.__last_exit_reference_time = perf_counter()
        super()._execute_exiting_action()

            