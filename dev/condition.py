from typing import Self, override
from abc import ABC, abstractmethod
from collections.abc import Iterable
from elapsed_timer import ElapsedTimer
from type_utilities import GenericGenerator, OptionalOneOrMany, OneOrMany

#Commande pour corriger le fichier:
#mypy --strict --check-untyped-defs condition.py

class Condition(ABC):
    def __init__(self:Self, invert:bool = False):
        self.__invert:bool = invert

    def __bool__(self:Self) -> bool:
        return self._compare() != self.invert

    @property
    def invert(self:Self) -> bool:
        return self.__invert
    
    @invert.setter
    def invert(self:Self, value:bool) -> None:
        if not isinstance(value, bool):
            raise "Value must be a bool"
        self.__invert = bool(value)
    
    @abstractmethod
    def _compare(self:Self)-> bool:
        pass

    def toogle_invert(self:Self) -> None:
        self.__invert = not self.__invert

class AlwaysTrueCondition(Condition):
    def __init__(self:Self, invert:bool = False):
        super().__init__(invert)

    @override
    def _compare(self:Self)-> bool:
        return True
    
class AlwaysFalseCondition(Condition):
    def __init__(self:Self, invert:bool = False):
        super().__init__(invert)

    @override
    def _compare(self:Self)-> bool:
        return False
    
class ElapsedTimerCondition(Condition):
    def __init__(self:Self, duration:float, invert:bool = False):
        super().__init__(invert)
        self.__duration:float = float(duration)
        self.__elapsed_timer:ElapsedTimer = ElapsedTimer()

    @property
    def duration(self:Self) -> float:
        return self.__duration
    
    @duration.setter
    def duration(self:Self, value:float) -> None:
        self.__duration = float(value)
    
    @override
    def _compare(self:Self)-> bool:
        return self.__elapsed_timer.elapsed >= self.__duration

    def reset(self:Self) -> None:
        self.__elapsed_timer.reset()

class AbstractValueCondition[T](Condition):
    def __init__(self:Self, expected_value: T , invert:bool = False):
        super().__init__(invert)
        self._expected_value:T = expected_value

    @property
    def expected_value(self:Self) -> T:
        return self._expected_value
    
    @expected_value.setter
    def expected_value(self:Self, value:T) -> None:
        self._expected_value = value
    
class ReaderCondition[T](AbstractValueCondition[T]):
    def __init__(self:Self, expected_value : T, value_reader:GenericGenerator[T], invert:bool = False):
        super().__init__(expected_value, invert)
        self._value_reader:GenericGenerator[T] = value_reader

    @property
    def value_reader(self:Self) -> GenericGenerator[T]:
        return self._value_reader
    
    @value_reader.setter
    def value_reader(self:Self, value:GenericGenerator[T]) -> None:
        if not callable(value):
            raise "The value_reader must be a Callable"
        self._value_reader = value
    
    @override
    def _compare(self:Self)-> bool:
        return bool(self.expected_value == self.value_reader())
    
class ValueCondition[T](AbstractValueCondition[T]):
    def __init__(self:Self, expected_value : T, actual_value:T, invert:bool = False):
        super().__init__(expected_value, invert)
        self._actual_value:T = actual_value

    @property
    def actual_value(self:Self) -> T:
        return self._actual_value
    
    @actual_value.setter
    def actual_value(self:Self, value:T) -> None:
        self._actual_value = value
    
    @override
    def _compare(self:Self)-> bool:
        return bool(self.expected_value == self.actual_value)

class ManyConditions(Condition):
    def __init__(self:Self, condition : OptionalOneOrMany[Condition], invert:bool = False):
        super().__init__(invert)
        self._condition : OptionalOneOrMany[Condition] = condition
    
    def clear_conditions(self:Self) -> None:
        self._condition = None

    def add_condition(self: Self, condition: OneOrMany[Condition]) -> None:
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

# class AllConditions(ManyConditions):
#     def __init__(self:Self, condition : OptionalOneOrMany[Condition] = None, invert:bool = False):
#         super().__init__(condition, invert)
#         pass
#     @override
#     def _compare(self:Self)-> bool:
#         if self._condition is None:
#             return False
#         if isinstance(self._condition, Condition):
#             return bool(self._condition)
#         return all(self._condition)

# class AnyConditions(ManyConditions):
#     def __init__(self:Self, condition : OptionalOneOrMany[Condition] = None, invert:bool = False):
#         super().__init__(condition, invert)
    
#     @override
#     def _compare(self:Self)-> bool:
#         if self._condition is None:
#             return False
#         if isinstance(self._condition, Condition):
#             return bool(self._condition)
#         return any(self._condition)

class AllConditions(ManyConditions):
    def __init__(self:Self, condition : OptionalOneOrMany[Condition] = None, invert:bool = False):
            super().__init__(invert, condition)

    @override
    def _compare(self:Self)-> bool:
        for c in self._condition():
            if not c._compare():
                return False
        return True
    
class AnyConditions(ManyConditions):
    def __init__(self:Self, condition : OptionalOneOrMany[Condition] = None, invert:bool = False):
            super().__init__(invert, condition)

    @override
    def _compare(self:Self)-> bool:
        for c in self._condition():
            if c._compare():
                return True
        return False
    
class CountConditions(ManyConditions):
    def __init__(self:Self, n:int, condition : OptionalOneOrMany[Condition] = None, expected_condition_value:bool = True, exact_bool_count=True , invert:bool = False):
        super().__init__(invert, condition)
        self.__n:int = n
        self.__expected_condition_value:bool = expected_condition_value
        self.exact_bool_count = exact_bool_count

    @property
    def n(self:Self) -> int:
        return self.__n
    
    @n.setter
    def n (self:Self, value : int) -> None:
        self.__n = int(value)

    @property
    def expected_condition_value(self:Self) -> bool:
        return self.__expected_condition_value
    
    @expected_condition_value.setter
    def expected_condition_value(self:Self, value : bool) -> None:
        if not isinstance(value, bool):
            raise "Value must be a bool"
        self.__expected_condition_value = bool(value)

    @property
    def exact_bool_count(self:Self) -> bool:
        return self.__exact_bool_count
    
    @exact_bool_count.setter
    def exact_bool_count(self:Self, value : bool) -> None:
        if not isinstance(value, bool):
            raise "Value must be a bool"
        
    @override
    def _compare(self:Self)-> bool:
        valid_conditions:int = 0
        for c in self._condition():
            if c._compare() == self.expected_condition_value:
                valid_conditions += 1
        if self.exact_bool_count:
            return True if valid_conditions == self.n else False
        else:
            return True if valid_conditions >= self.n else False

