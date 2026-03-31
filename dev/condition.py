from typing import Self, override, Any
from abc import ABC, abstractmethod
from elapsed_timer import ElapsedTimer

class Condition(ABC):
    def __init__(self:Self, invert:bool = False):
        self.__invert:bool = invert

    def __bool__(self:Self):
        pass

    @property
    def invert(self:Self) -> bool:
        return self.__invert
    
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
    
    @override
    def _compare(self:Self)-> bool:
        return True if self.__elapsed_timer.elapsed >= self.__duration else False

    def reset(self:Self):
        self.__elapsed_timer.reset()

class AbstractValueCondition(Condition, ABC):
    def __init__(self:Self, expected_value: Any , invert:bool = False):
        super.__init__(invert)
        self._expected_value = expected_value

    @property
    def expected_value(self:Self) -> Any:
        return self._expected_value