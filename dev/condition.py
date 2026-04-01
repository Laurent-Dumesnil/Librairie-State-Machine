from typing import Self, override
from abc import ABC, abstractmethod
from elapsed_timer import ElapsedTimer
from type_utilities import GenericGenerator, OptionalOneOrMany, OneOrMany

class Condition(ABC):
    def __init__(self:Self, invert:bool = False):
        self.__invert:bool = invert

    def __bool__(self:Self):
        pass

    @property
    def invert(self:Self) -> bool:
        return self.__invert
    
    @invert.setter
    def invert(self:Self, value:bool) -> None:
        self.__invert = bool(value)
    
    @abstractmethod
    def _compare(self:Self)-> bool:
        pass

    def toogle_invert(self:Self) -> None:
        self.__invert = not self.__invert

class AlwaysTrueCondition(Condition):
    def __init__(self:Self, invert:bool = False):
        super.__init__(invert)

    @override
    def _compare(self:Self)-> bool:
        return True
    
class AlwaysFalseCondition(Condition):
    def __init__(self:Self, invert:bool = False):
        super.__init__(invert)

    @override
    def _compare(self:Self)-> bool:
        return False
    
class ElapsedTimerCondition(Condition):
    def __init__(self:Self, duration:float, invert:bool = False):
        super.__init__(invert)
        self.__duration:float = float(duration)
        self.__elapsed_timer:ElapsedTimer = ElapsedTimer()

    @property
    def duration(self:Self) -> float:
        return self.__duration
    
    @duration.setter
    def duration(self:Self, value:float) -> None:
        self.duration = float(value)
    
    @override
    def _compare(self:Self)-> bool:
        return self.__elapsed_timer.elapsed >= self.__duration

    def reset(self:Self):
        self.__elapsed_timer.reset()

class AbstractValueCondition[T](Condition):
    def __init__(self:Self, expected_value: T , invert:bool = False):
        super.__init__(invert)
        self._expected_value:T = expected_value

    @property
    def expected_value(self:Self) -> T:
        return self._expected_value
    
    @expected_value.setter
    def expected_value(self:Self, value:T) -> None:
        self._expected_value = value
    
class ReaderCondition[T](AbstractValueCondition):
    def __init__(self:Self, expected_value, value_reader:GenericGenerator[T], invert:bool = False):
        super.__init__(expected_value, invert)
        self._value_reader:GenericGenerator[T] = value_reader

    @property
    def value_reader(self:Self) -> GenericGenerator[T]:
        return self._value_reader
    
    @value_reader.setter
    def expected_value(self:Self, value:GenericGenerator[T]) -> None:
        if not callable(value):
            raise "The value_reader must be a Callable"
        self.value_reader = value
    
    @override
    def _compare(self:Self)-> bool:
        return self.expected_value == self.value_reader()
    
class ValueCondition[T](AbstractValueCondition):
    def __init__(self:Self, expected_value, actual_value:T, invert:bool = False):
        super.__init__(expected_value, invert)
        self._actual_value:T = actual_value

    @property
    def actual_value(self:Self) -> T:
        return self._actual_value
    
    @actual_value.setter
    def actual_value(self:Self, value:T) -> None:
        self.actual_value = value
    
    @override
    def _compare(self:Self)-> bool:
        return self.expected_value == self.actual_value

class ManyConditions(Condition):
    def __init__(self:Self, condition : OptionalOneOrMany[Condition], invert:bool = False):
        super.__init__(invert)
        self._condition : OptionalOneOrMany[Condition] = condition
    
    def clear_conditions(self:Self):
        self._condition.clear()

    def add_condition(self:Self, condition:OneOrMany[Condition]):
        self._condition[condition.name] = condition

    def remove_condition(self:Self, condition:OneOrMany[Condition]):
        del self._condition[condition.name] 

class AllConditions(ManyConditions):
    def __init__(self:Self, condition : OptionalOneOrMany[Condition] = None, invert:bool = False):
        super.__init__(condition, invert)
        pass
    @override
    def _compare(self:Self)-> bool:
        all(self._condition)

class AnyConditions(ManyConditions):
    def __init__(self:Self, condition : OptionalOneOrMany[Condition] = None, invert:bool = False):
        super.__init__(condition, invert)
    
    @override
    def _compare(self:Self)-> bool:
        return any(self._condition)

class CountConditions(ManyConditions):
    def __init__(self:Self, n : int, condition : OptionalOneOrMany[Condition] = None, expected_condition_value : bool = True , exact_count : bool = True, invert:bool = False):
        super.__init__(condition, invert)
        self.__n : int = n
        self.__expected_condition_value : bool = expected_condition_value
        self.__exact_count : bool = exact_count

    @property
    def n(self:Self) -> int:
        return self.__n
    
    @n.setter
    def n (self:Self, value : int):
        self.n = value

    @property
    def expected_condition_value(self:Self) -> bool:
        return self.__expected_condition_value
    
    @expected_condition_value.setter
    def expected_condition_value (self:Self, value : bool):
        self.expected_condition_value = value

    @property
    def exact_count(self:Self) -> bool:
        return self.__exact_count
    
    @exact_count.setter
    def exact_count (self:Self, value : bool):
        self.exact_count = value

    @override
    def _compare(self:Self)-> bool:
        return exact_count
