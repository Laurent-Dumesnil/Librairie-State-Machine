from typing import Self, override
from abc import ABC, abstractmethod
from collections.abc import Iterable
from elapsed_timer import ElapsedTimer
from type_utilities import GenericGenerator, OptionalOneOrMany, OneOrMany

#Commande pour corriger le fichier:
#mypy --strict --check-untyped-defs condition.py

class Condition(ABC):
    """Abstract base class for conditions that can be evaluated to a boolean value.

    This class provides a framework for creating conditions that can be inverted.
    Subclasses must implement the _compare method to define the condition logic.
    """

    def __init__(self:Self, invert:bool = False):
        """Initializes the condition with an optional invert flag.

        Args:
            invert: If True, the condition's result is inverted.
        """
        self.__invert:bool = invert

    def __bool__(self:Self) -> bool:
        """Evaluates the condition to a boolean value.

        Returns:
            The boolean result of the condition, potentially inverted.
        """
        return self._compare() != self.invert

    @property
    def invert(self:Self) -> bool:
        """Gets the invert flag.

        Returns:
            True if the condition is inverted, False otherwise.
        """
        return self.__invert
    
    @invert.setter
    def invert(self:Self, value:bool) -> None:
        """Sets the invert flag.

        Args:
            value: The new invert value.

        Raises:
            ValueError: If value is not a boolean.
        """
        if not isinstance(value, bool):
            raise ValueError("Value must be a bool")
        self.__invert = bool(value)
    
    @abstractmethod
    def _compare(self:Self)-> bool:
        """Abstract method to compare the condition.

        Returns:
            The raw boolean result of the condition before inversion.
        """
        pass

    def toogle_invert(self:Self) -> None:
        """Toggles the invert flag."""
        self.__invert = not self.__invert

class AlwaysTrueCondition(Condition):
    """A condition that always evaluates to True.

    This condition can be used as a placeholder or for testing purposes.
    """

    def __init__(self:Self, invert:bool = False):
        """Initializes the always true condition.

        Args:
            invert: If True, the condition is inverted (always False).
        """
        super().__init__(invert)

    @override
    def _compare(self:Self)-> bool:
        """Compares the condition, always returning True.

        Returns:
            True.
        """
        return True if not self.invert else False
    
class AlwaysFalseCondition(Condition):
    """A condition that always evaluates to False.

    This condition can be used as a placeholder or for testing purposes.
    """

    def __init__(self:Self, invert:bool = False):
        """Initializes the always false condition.

        Args:
            invert: If True, the condition is inverted (always True).
        """
        super().__init__(invert)

    @override
    def _compare(self:Self)-> bool:
        """Compares the condition, always returning False.

        Returns:
            False.
        """
        return False if not self.invert else True
    
class ElapsedTimerCondition(Condition):
    """A condition that becomes True after a specified duration has elapsed.

    Uses an ElapsedTimer to track time accumulation.
    """

    def __init__(self:Self, duration:float, invert:bool = False):
        """Initializes the elapsed timer condition.

        Args:
            duration: The duration in seconds after which the condition becomes True.
            invert: If True, the condition is inverted.
        """
        super().__init__(invert)
        self.__duration:float = float(duration)
        self.__elapsed_timer:ElapsedTimer = ElapsedTimer(ElapsedTimer.Mode.ACCUMULATED)

    @property
    def duration(self:Self) -> float:
        """Gets the duration.

        Returns:
            The duration in seconds.
        """
        return self.__duration
    
    @duration.setter
    def duration(self:Self, value:float) -> None:
        """Sets the duration.

        Args:
            value: The new duration in seconds.
        """
        self.__duration = float(value)
    
    @override
    def _compare(self:Self)-> bool:
        """Compares the condition based on elapsed time.

        Returns:
            True if the elapsed time is greater than or equal to the duration.
        """
        return self.__elapsed_timer.elapsed >= self.__duration if not self.invert else self.__elapsed_timer.elapsed < self.__duration

    def reset(self:Self) -> None:
        """Resets the elapsed timer."""
        self.__elapsed_timer.reset()

class AbstractValueCondition[T](Condition):
    """Abstract base class for conditions that compare against an expected value.

    Subclasses must define how to obtain the actual value for comparison.
    """

    def __init__(self:Self, expected_value: T , invert:bool = False):
        """Initializes the abstract value condition.

        Args:
            expected_value: The value to compare against.
            invert: If True, the condition is inverted.
        """
        super().__init__(invert)
        self._expected_value:T = expected_value

    @property
    def expected_value(self:Self) -> T:
        """Gets the expected value.

        Returns:
            The expected value.
        """
        return self._expected_value
    
    @expected_value.setter
    def expected_value(self:Self, value:T) -> None:
        """Sets the expected value.

        Args:
            value: The new expected value.
        """
        self._expected_value = value
    
class ReaderCondition[T](AbstractValueCondition[T]):
    """A condition that compares an expected value against a value read from a callable.

    The value is obtained by calling the value_reader function.
    """

    def __init__(self:Self, expected_value : T, value_reader:GenericGenerator[T], invert:bool = False):
        """Initializes the reader condition.

        Args:
            expected_value: The value to compare against.
            value_reader: A callable that returns the actual value.
            invert: If True, the condition is inverted.
        """
        super().__init__(expected_value, invert)
        self._value_reader:GenericGenerator[T] = value_reader

    @property
    def value_reader(self:Self) -> GenericGenerator[T]:
        """Gets the value reader callable.

        Returns:
            The callable that provides the actual value.
        """
        return self._value_reader
    
    @value_reader.setter
    def value_reader(self:Self, value:GenericGenerator[T]) -> None:
        """Sets the value reader callable.

        Args:
            value: The new callable.

        Raises:
            ValueError: If value is not callable.
        """
        if not callable(value):
            raise ValueError("The value_reader must be a Callable")
        self._value_reader = value
    
    @override
    def _compare(self:Self)-> bool:
        """Compares the expected value against the value from the reader.

        Returns:
            True if the values are equal.
        """
        return bool(self.expected_value == self.value_reader()) if not self.invert else bool(self.expected_value != self.value_reader())
    
class ValueCondition[T](AbstractValueCondition[T]):
    """A condition that compares an expected value against a static actual value."""

    def __init__(self:Self, expected_value : T, actual_value:T, invert:bool = False):
        """Initializes the value condition.

        Args:
            expected_value: The value to compare against.
            actual_value: The static actual value.
            invert: If True, the condition is inverted.
        """
        super().__init__(expected_value, invert)
        self._actual_value:T = actual_value

    @property
    def actual_value(self:Self) -> T:
        """Gets the actual value.

        Returns:
            The actual value.
        """
        return self._actual_value
    
    @actual_value.setter
    def actual_value(self:Self, value:T) -> None:
        """Sets the actual value.

        Args:
            value: The new actual value.
        """
        self._actual_value = value
    
    @override
    def _compare(self:Self)-> bool:
        """Compares the expected value against the actual value.

        Returns:
            True if the values are equal.
        """
        return bool(self.expected_value == self.actual_value) if not self.invert else bool(self.expected_value != self.actual_value)

class ManyConditions(Condition):
    """Base class for conditions that operate on multiple sub-conditions.

    Provides methods to add, remove, and clear conditions.
    """

    def __init__(self:Self, condition : OptionalOneOrMany[Condition], invert:bool = False):
        """Initializes the many conditions.

        Args:
            condition: Initial condition(s) to include.
            invert: If True, the condition is inverted.
        """
        super().__init__(invert)
        self._condition : OptionalOneOrMany[Condition] = condition
    
    def clear_conditions(self:Self) -> None:
        """Clears all conditions."""
        self._condition = None

    def add_condition(self: Self, condition: OneOrMany[Condition]) -> None:
        """Adds one or more conditions.

        Args:
            condition: The condition(s) to add.
        """
        if self._condition is not None:

            if isinstance(self._condition, Condition):
                conditions = [self._condition]
            else:
                conditions = list(self._condition)

            if isinstance(condition, Condition):
                conditions.append(condition)
            else:
                conditions.extend(condition)

            self._condition = conditions

    def remove_condition(self: Self, condition: OneOrMany[Condition]) -> None:
        """Removes one or more conditions.

        Args:
            condition: The condition(s) to remove.
        """
        if self._condition is not None:

            if isinstance(self._condition, Condition):
                conditions = [self._condition]
            else:
                conditions = list(self._condition)

            if isinstance(condition, Condition):
                if condition in conditions:
                    conditions.remove(condition)
            else: # iterable
                for c in condition:
                    if c in conditions:
                        conditions.remove(c)

            self._condition = conditions or None

class AllConditions(ManyConditions):
    """A condition that is True only if all sub-conditions are True."""

    def __init__(self:Self, condition : OptionalOneOrMany[Condition] = None, invert:bool = False):
        """Initializes the all conditions.

        Args:
            condition: Initial condition(s).
            invert: If True, the condition is inverted.
        """
        super().__init__(condition, invert)

    @override
    def _compare(self:Self)-> bool:
        """Compares by checking if all conditions are True.

        Returns:
            True if all sub-conditions are True, False otherwise.
        """
        if self._condition is None:
            return False if not self.invert else True
        if isinstance(self._condition, Condition):
            return self._condition._compare()
        for c in self._condition:
            if not c._compare():
                return False if not self.invert else True
        return True if not self.invert else False
    
class AnyConditions(ManyConditions):
    """A condition that is True if at least one sub-condition is True."""

    def __init__(self:Self, condition : OptionalOneOrMany[Condition] = None, invert:bool = False):
        """Initializes the any conditions.

        Args:
            condition: Initial condition(s).
            invert: If True, the condition is inverted.
        """
        super().__init__(condition, invert)

    @override
    def _compare(self:Self)-> bool:
        """Compares by checking if any condition is True.

        Returns:
            True if at least one sub-condition is True, False otherwise.
        """
        if self._condition is None:
            return False if not self.invert else True
        if isinstance(self._condition, Condition):
            return self._condition._compare()
        for c in self._condition:
            if c._compare():
                return True if not self.invert else False
        return False if not self.invert else True
    
class CountConditions(ManyConditions):
    """A condition that is True based on the count of sub-conditions meeting a criteria.

    Can check for exact count or at least count.
    """

    def __init__(self:Self, n:int, condition : OptionalOneOrMany[Condition] = None, expected_condition_value:bool = True, exact_bool_count:bool=True , invert:bool = False):
        """Initializes the count conditions.

        Args:
            n: The number of conditions to check for.
            condition: Initial condition(s).
            expected_condition_value: The value to match (True or False).
            exact_bool_count: If True, requires exactly n matches; if False, at least n.
            invert: If True, the condition is inverted.
        """
        super().__init__(condition, invert)
        self.__n:int = n
        self.__expected_condition_value:bool = expected_condition_value
        self.__exact_bool_count:bool = exact_bool_count

    @property
    def n(self:Self) -> int:
        """Gets the count n.

        Returns:
            The count value.
        """
        return self.__n
    
    @n.setter
    def n (self:Self, value : int) -> None:
        """Sets the count n.

        Args:
            value: The new count value.
        """
        self.__n = int(value)

    @property
    def expected_condition_value(self:Self) -> bool:
        """Gets the expected condition value.

        Returns:
            The expected boolean value.
        """
        return self.__expected_condition_value
    
    @expected_condition_value.setter
    def expected_condition_value(self:Self, value : bool) -> None:
        """Sets the expected condition value.

        Args:
            value: The new expected value.

        Raises:
            ValueError: If value is not a boolean.
        """
        if not isinstance(value, bool):
            raise ValueError("Value must be a bool")
        self.__expected_condition_value = bool(value)

    @property
    def exact_bool_count(self:Self) -> bool:
        """Gets the exact count flag.

        Returns:
            True if exact count is required.
        """
        return self.__exact_bool_count
    
    @exact_bool_count.setter
    def exact_bool_count(self:Self, value : bool) -> None:
        """Sets the exact count flag.

        Args:
            value: The new flag value.

        Raises:
            ValueError: If value is not a boolean.
        """
        if not isinstance(value, bool):
            raise ValueError("Value must be a bool")
        self.__exact_bool_count = value
        
    @override
    def _compare(self:Self)-> bool:
        """Compares based on the count of conditions matching the expected value.

        Returns:
            True if the count matches the criteria.
        """
        if self._condition is None:
            return False if self.expected_condition_value else True
        valid_conditions:int = 0
        if isinstance(self._condition, Condition):
            return self._condition._compare()
        else:
            for c in self._condition:
                if c._compare() == self.expected_condition_value:
                    valid_conditions += 1
        if self.exact_bool_count:
            result = True if valid_conditions == self.n else False
            return result if not self.invert else not result
        else:
            result = True if valid_conditions >= self.n else False
            return result if not self.invert else not result

