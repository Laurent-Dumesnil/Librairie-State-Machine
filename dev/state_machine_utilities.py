"""
Module utilitaire pour la gestion d'automates d'états et de transitions conditionnelles.

Ce module fournit des classes pour la gestion d'états, de transitions conditionnelles, d'actions associées aux transitions et aux états, ainsi que des états surveillés permettant de mesurer le temps et le nombre d'entrées/sorties.

Exemple d'utilisation :
    >>> from condition import AlwaysTrueCondition
    >>> s1 = MonitoredState(name="A")
    >>> s2 = MonitoredState(name="B")
    >>> t = ConditionalTransition(condition=AlwaysTrueCondition(), next_state=s2)
    >>> t.valid
    True
"""

from time import perf_counter
from state_machine_device import Transition, State
from typing import final, override, TypeAlias, Iterable, Any, Self
from type_utilities import GenericCallback
from condition import Condition

Action:TypeAlias = GenericCallback

class ConditionalTransition(Transition):
    """
    Transition conditionnelle basée sur un objet Condition.

    Args:
        condition (Condition | None): Condition à évaluer pour la transition.
        next_state (State | None): État suivant.
        name (str | None): Nom de la transition.
        enabled (bool): Si la transition est activée.
    """
    def __init__(self:Self, condition: Condition | None = None, next_state: State | None = None, name: str | None = None, enabled:bool = True):
        self.__condition:Condition | None
        self.__condition = condition
        super().__init__(next_state, name, enabled)

    @override
    @property
    def valid(self) -> bool:
        return super().valid and self.__condition is not None 

    @property
    def condition(self) -> Condition | None:
        """
        Retourne la condition associée à la transition.

        Returns:
            Condition: La condition de transition.
        """
        return self.__condition

    @condition.setter
    def condition(self:Self, value:Condition) -> None:
        if not isinstance(value, Condition):
            raise TypeError('condition must be a Condition')     
        self.__condition = value
        
    @final
    def is_transiting(self:Self) -> bool:
        """
        Indique si la transition doit s'effectuer (condition vraie).

        Returns:
            bool: True si la condition est vraie.
        """
        return bool(self.__condition)
    
class ActionTransition(ConditionalTransition):
    """
    Transition conditionnelle avec actions à exécuter lors de la transition.

    Args:
        condition (Condition | None): Condition à évaluer pour la transition.
        next_state (State | None): État suivant.
        name (str | None): Nom de la transition.
        enabled (bool): Si la transition est activée.
    """
    def __init__(self:Self, condition:Condition | None = None, next_state:State | None = None, name: str | None = None, enabled:bool = True):
        super().__init__(condition=condition, next_state=next_state, name=name, enabled=enabled)
        self.__actions: list[Action] = list()

    @property
    def transiting_action_count(self:Self) -> int:
        """
        Retourne le nombre d'actions associées à la transition.

        Returns:
            int: Nombre d'actions.
        """
        return len(self.__actions)
        
    def _do_transiting_action(self:Self) -> None:
        for action in self.__actions:
            action()

    def clear_transiting_actions(self:Self) -> None:
        self.__actions.clear()

    def add_transiting_action(self:Self, action:Action | Iterable[Action]) -> None:
        """
        Ajoute une ou plusieurs actions à exécuter lors de la transition.

        Args:
            action (Action | Iterable[Action]): Action(s) à ajouter.
        Raises:
            TypeError: Si l'élément n'est pas callable.
        """
        if callable(action):
            self.__actions.append(action)
            return
        elif isinstance(action, Iterable) and not isinstance(action, str):
            for element in action:
                if callable(element):
                    self.__actions.append(element)
                else:
                    raise TypeError("Doit être un callable")
            return
        raise TypeError("Doit être de type action ou un iterable d'actions")
    
class MonitoredTransition(ActionTransition):
    """
    Transition conditionnelle surveillée, comptant le nombre de transitions et mesurant le temps.

    Args:
        condition (Condition | None): Condition à évaluer pour la transition.
        next_state (State | None): État suivant.
        name (str | None): Nom de la transition.
        enabled (bool): Si la transition est activée.
    """
    def __init__(self, condition:Condition | None = None, next_state:State | None = None, name: str | None = None, enabled:bool = True):
        super().__init__(condition=condition, next_state=next_state, name=name, enabled=enabled)
        self.__transit_count: int = 0
        self.__creation_reference_time:float = perf_counter()
        self.__last_transit_reference_time: float | None = None
        self.custom_value: Any = None

    @property
    def transit_count(self) -> int:
        """
        Retourne le nombre de transitions effectuées.

        Returns:
            int: Nombre de transitions.
        """
        return self.__transit_count
    
    @property
    def creation_reference_time(self) -> float:
        """
        Retourne le temps écoulé depuis la création de la transition.

        Returns:
            float: Temps en secondes.
        """
        return self.__creation_reference_time
    
    @property
    def elapsed_time_since_creation(self) -> float:
        """
        Retourne le temps écoulé depuis la création de la transition.

        Returns:
            float: Temps en secondes.
        """
        return perf_counter() - self.__creation_reference_time
    
    @property
    def last_transit_reference_time(self) -> float | None:
        """
        Retourne le temps écoulé depuis la dernière transition.

        Returns:
            float | None: Temps en secondes ou None si aucune transition.
        """
        return self.__last_transit_reference_time
    
    @property
    def elapsed_since_last_transit(self) -> float | None:
        """
        Retourne le temps écoulé depuis la dernière transition.

        Returns:
            float | None: Temps en secondes ou None si aucune transition.
        """
        if self.__last_transit_reference_time is None:
            return None
        return perf_counter() - self.__last_transit_reference_time
    
    @override
    def _execute_transiting_action(self) -> None:
        self.__transit_count += 1
        self.__last_transit_reference_time = perf_counter()
        super()._execute_transiting_action()
                

class ActionState(State):
    """
    État avec actions associées à l'entrée, à l'intérieur et à la sortie de l'état.

    Args:
        name (str | None): Nom de l'état.
        enabled (bool): Si l'état est activé.
        terminal (bool): Si l'état est terminal.
        do_in_state_action_when_entering (bool): Exécute l'action d'état à l'entrée.
        do_in_state_action_when_exiting (bool): Exécute l'action d'état à la sortie.
    """
    def __init__(self, name:str | None=None, /,*, enabled:bool=True, terminal: bool=False, do_in_state_action_when_entering: bool=False, do_in_state_action_when_exiting: bool=False):
        super().__init__(name, enabled=enabled, terminal=terminal, do_in_state_action_when_entering=do_in_state_action_when_entering, do_in_state_action_when_exiting=do_in_state_action_when_exiting)
        self.__entering_actions: list[Action] = list()
        self.__in_state_actions: list[Action] = list()
        self.__exiting_actions: list[Action] = list()

    @property
    def entering_action_count(self) -> int:
        """
        Retourne le nombre d'actions à l'entrée de l'état.

        Returns:
            int: Nombre d'actions.
        """
        return len(self.__entering_actions)
    
    @property
    def in_state_action_count(self) -> int:
        """
        Retourne le nombre d'actions dans l'état.

        Returns:
            int: Nombre d'actions.
        """
        return len(self.__in_state_actions)
    
    @property
    def exiting_action_count(self) -> int:
        """
        Retourne le nombre d'actions à la sortie de l'état.

        Returns:
            int: Nombre d'actions.
        """
        return len(self.__exiting_actions)
    
    def clear_entering_actions(self) -> None:
        """
        Efface toutes les actions d'entrée de l'état.
        """
        self.__entering_actions.clear()

    def clear_in_state_actions(self) -> None:
        """
        Efface toutes les actions de l'état.
        """
        self.__in_state_actions.clear()

    def clear_exiting_actions(self) -> None:
        """
        Efface toutes les actions de sortie de l'état.
        """
        self.__exiting_actions.clear()

    def add_entering_action(self, action: Action | Iterable[Action]) -> None:
        """
        Ajoute une ou plusieurs actions à exécuter à l'entrée de l'état.

        Args:
            action (Action | Iterable[Action]): Action(s) à ajouter.
        Raises:
            TypeError: Si l'élément n'est pas callable.
        """
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
        """
        Ajoute une ou plusieurs actions à exécuter dans l'état.

        Args:
            action (Action | Iterable[Action]): Action(s) à ajouter.
        Raises:
            TypeError: Si l'élément n'est pas callable.
        """
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
        """
        Ajoute une ou plusieurs actions à exécuter à la sortie de l'état.

        Args:
            action (Action | Iterable[Action]): Action(s) à ajouter.
        Raises:
            TypeError: Si l'élément n'est pas callable.
        """
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
        """
        Exécute toutes les actions d'entrée de l'état.
        """
        super()._do_entering_action()
        for action in self.__entering_actions:
            action()

    
    @override
    def _do_in_state_action(self) -> None:
        """
        Exécute toutes les actions de l'état.
        """
        super()._do_in_state_action()
        for action in self.__in_state_actions:
            action()
    
    @override
    def _do_exiting_action(self) -> None:
        """
        Exécute toutes les actions de sortie de l'état.
        """
        super()._do_exiting_action()
        for action in self.__exiting_actions:
            action()

class MonitoredState(ActionState):
    """
    État surveillé permettant de compter les entrées/sorties et de mesurer les temps associés.

    Args:
        name (str | None): Nom de l'état.
        enabled (bool): Si l'état est activé.
        terminal (bool): Si l'état est terminal.
        do_in_state_action_when_entering (bool): Exécute l'action d'état à l'entrée.
        do_in_state_action_when_exiting (bool): Exécute l'action d'état à la sortie.

    Exemple:
        >>> s = MonitoredState(name="A")
        >>> s.entry_count
        0
    """
    def __init__(self, name:str | None=None, /,*, enabled:bool=True, terminal: bool=False, do_in_state_action_when_entering: bool=False, do_in_state_action_when_exiting: bool=False):
        super().__init__(name, enabled=enabled, terminal=terminal, do_in_state_action_when_entering=do_in_state_action_when_entering, do_in_state_action_when_exiting=do_in_state_action_when_exiting)
        self.__entry_count:int = 0
        self.__exit_count:int = 0
        self.__creation_reference_time:float = perf_counter()
        self.__last_entry_reference_time: float | None = None
        self.__last_exit_reference_time: float | None = None
        self.custom_value: Any = None

    @property
    def entry_count(self) -> int:
        """
        Retourne le nombre d'entrées dans l'état.

        Returns:
            int: Nombre d'entrées.
        """
        return self.__entry_count
    
    @property
    def exit_count(self) -> int:
        """
        Retourne le nombre de sorties de l'état.

        Returns:
            int: Nombre de sorties.
        """
        return self.__exit_count
    
    @property
    def creation_reference_time(self) -> float:
        """
        Retourne le temps écoulé depuis la création de l'état.

        Returns:
            float: Temps en secondes.
        """
        return self.__creation_reference_time
    
    @property
    def elapsed_time_since_creation(self) -> float:
        """
        Retourne le temps écoulé depuis la création de l'état.

        Returns:
            float: Temps en secondes.
        """
        return perf_counter() - self.__creation_reference_time
    
    @property
    def last_entry_reference_time(self) -> float | None:
        """
        Retourne le temps écoulé depuis la dernière entrée dans l'état.

        Returns:
            float | None: Temps en secondes ou None si aucune entrée.
        """
        return self.__last_entry_reference_time
    
    @property
    def elapsed_since_last_entry(self) -> float | None:
        """
        Retourne le temps écoulé depuis la dernière entrée dans l'état.

        Returns:
            float | None: Temps en secondes ou None si aucune entrée.
        """
        if self.__last_entry_reference_time is None:
            return None
        return perf_counter() - self.__last_entry_reference_time
    
    @property
    def last_exit_reference_time(self) -> float | None:
        """
        Retourne le temps écoulé depuis la dernière sortie de l'état.

        Returns:
            float | None: Temps en secondes ou None si aucune sortie.
        """
        return self.__last_exit_reference_time
    
    @property
    def elapsed_since_last_exit(self) -> float | None:
        """
        Retourne le temps écoulé depuis la dernière sortie de l'état.

        Returns:
            float | None: Temps en secondes ou None si aucune sortie.
        """
        if self.__last_exit_reference_time is None:
            return None
        return perf_counter() - self.__last_exit_reference_time
    
    @override
    def _execute_entering_action(self) -> None:
        """
        Exécute l'action d'entrée et met à jour le compteur d'entrées.
        """
        self.__entry_count += 1
        self.__last_entry_reference_time = perf_counter()
        super()._execute_entering_action()
    
    @override
    def _execute_exiting_action(self) -> None:
        """
        Exécute l'action de sortie et met à jour le compteur de sorties.
        """
        self.__exit_count += 1
        self.__last_exit_reference_time = perf_counter()
        super()._execute_exiting_action()

class MonitoredStateCondition(Condition):
    """
    Condition abstraite basée sur un MonitoredState.

    Args:
        monitored_state (MonitoredState | None): L'état surveillé.
        invert (bool): Si True, la condition est inversée.
    """
    def __init__(self: Self, monitored_state: MonitoredState | None = None, invert: bool = False):
        super().__init__(invert)
        self.monitored_state : MonitoredState | None = monitored_state

    @property
    def monitored_state(self) -> MonitoredState | None:
        """
        Retourne l'état surveillé.

        Returns:
            MonitoredState | None: L'état surveillé ou None si non défini.
        """
        return self.__monitored_state

    @monitored_state.setter
    def monitored_state(self, value:MonitoredState | None) -> None:
        """
        Définit l'état surveillé.

        Args:
            value (MonitoredState | None): Le nouvel état surveillé.

        Raises:
            ValueError: Si la valeur n'est pas un MonitoredState.
        """
        if not isinstance(value, MonitoredState):
            raise ValueError("value must be a MonitoredState")
        self.__monitored_state = value
        self._update_from_setting_new_monitored_state(value)

    def _update_from_setting_new_monitored_state(self, monitored_state: MonitoredState | None) -> None:
        """
        Méthode appelée lors du changement d'état surveillé.

        Args:
            monitored_state (MonitoredState | None): Le nouvel état surveillé.
        """
        pass
        
class DelayStateCondition(MonitoredStateCondition):
    """
    Condition abstraite de délai basée sur un MonitoredState.

    Args:
        duration (float): Durée du délai.
        monitored_state (MonitoredState | None): L'état surveillé.
        invert (bool): Si True, la condition est inversée.
    """
    def __init__(self:Self, duration:float, monitored_state:MonitoredState | None = None, invert:bool = False):
        super().__init__(monitored_state, invert)
        self.__duration : float = duration

    @property
    def duration(self) -> float:
        """
        Retourne la durée du délai.

        Returns:
            float: Durée en secondes.
        """
        return self.__duration


class DelaySinceEnteredCondition(DelayStateCondition):
    """
    Condition vraie si la durée depuis l'entrée dans l'état surveillé dépasse un seuil.

    Exemple:
        >>> class DummyState(MonitoredState):
        ...     def __init__(self):
        ...         super().__init__(name="dummy")
        ...         self._MonitoredState__last_entry_reference_time = 0
        ...     @property
        ...     def elapsed_since_last_entry(self):
        ...         return 2.0
        >>> c = DelaySinceEnteredCondition(1.5, DummyState())
        >>> bool(c)
        True
    """
    def __init__(self:Self, duration:float, monitored_state:MonitoredState | None = None, invert:bool = False):
        super().__init__(duration, monitored_state, invert)

    @override
    def _compare(self) -> bool:
        """
        Retourne True si le temps depuis la dernière entrée >= durée.

        Returns:
            bool: Résultat de la comparaison.
        """
        if self.monitored_state is None or self.monitored_state.elapsed_since_last_entry is None:
            return False
        else :
            return self.monitored_state.elapsed_since_last_entry >= self.duration


class DelaySinceExitedCondition(DelayStateCondition):
    """
    Condition vraie si la durée depuis la sortie de l'état surveillé dépasse un seuil.

    Exemple:
        >>> class DummyState(MonitoredState):
        ...     def __init__(self):
        ...         super().__init__(name="dummy")
        ...         self._MonitoredState__last_exit_reference_time = 0
        ...     @property
        ...     def elapsed_since_last_exit(self):
        ...         return 3.0
        >>> c = DelaySinceExitedCondition(2.5, DummyState())
        >>> bool(c)
        True
    """
    def __init__(self:Self, duration:float, monitored_state:MonitoredState | None = None, invert:bool = False):
        super().__init__(duration, monitored_state, invert)

    @override
    def _compare(self) -> bool:
        """
        Retourne True si le temps depuis la dernière sortie >= durée.

        Returns:
            bool: Résultat de la comparaison.
        """
        if self.monitored_state is None or self.monitored_state.elapsed_since_last_exit is None:
            return False
        else :
            return self.monitored_state.elapsed_since_last_exit >= self.duration


class StateEntryCountCondition(MonitoredStateCondition):
    """
    Condition vraie si le nombre d'entrées dans l'état surveillé atteint un seuil.
    """
    def __init__(self:Self, expected_count:int, monitored_state:MonitoredState | None = None, invert:bool = False):
        super().__init__(monitored_state, invert)
        self.__expected_count:int = expected_count
        self.__reference_count:int = 0
        if monitored_state:
            self._update_from_setting_new_monitored_state(monitored_state)

    @property
    def expected_count(self) -> int:
        """
        Retourne le nombre d'entrées attendu.

        Returns:
            int: Nombre d'entrées attendu.
        """
        return self.__expected_count

    @override
    def _update_from_setting_new_monitored_state(self, monitored_state:MonitoredState|None) -> None:
        """
        Met à jour le compteur de référence lors du changement d'état surveillé.

        Args:
            monitored_state (MonitoredState | None): Le nouvel état surveillé.
        """
        self.__reference_count = monitored_state.entry_count if monitored_state else 0

    @override 
    def _compare(self) -> bool:
        """
        Retourne True si le nombre d'entrées depuis la référence >= attendu.

        Returns:
            bool: Résultat de la comparaison.
        """
        if self.monitored_state is None:
            return False
        current_diff = self.monitored_state.entry_count - self.__reference_count
        return current_diff >= self.__expected_count



class StateValueCondition(MonitoredStateCondition):
    """
    Condition vraie si la valeur personnalisée de l'état surveillé correspond à la valeur attendue.

    Exemple:
        >>> class DummyState(MonitoredState):
        ...     def __init__(self):
        ...         super().__init__(name="dummy")
        ...         self.custom_value = 42
        >>> c = StateValueCondition(42, DummyState())
        >>> bool(c)
        True
        >>> c = StateValueCondition(99, DummyState())
        >>> bool(c)
        False
    """
    def __init__(self:Self, expected_value:Any = None, monitored_state:MonitoredState | None = None, invert:bool = False):
        super().__init__(monitored_state, invert)
        self.expected_value:Any = expected_value 

    @override 
    def _compare(self) -> bool:
        """
        Retourne True si la valeur personnalisée de l'état == valeur attendue.

        Returns:
            bool: Résultat de la comparaison.
        """
        if self.monitored_state is None:
            return False
        return bool(self.monitored_state.custom_value == self.expected_value)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
    print('state_machine_utilities module test completed.')