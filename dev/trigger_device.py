from type_utilities import GenericCallback
from abc import ABC
from base_component import BaseComponent

class TrackingDevice:
    def do_reset(self):
        pass

    def do_tracking(self):
        pass

class TriggerDevice(TrackingDevice, ABC, BaseComponent):
    def __init__(self, duration: float, action: GenericCallback, /, name: str | None = None, enabled: bool = True, *, initial_time: float = 0.0, auto_reset_when_enabling: bool = True):
        self.__duration = duration
        self.__action = action
        self.__accumulator = 0.0
        self.__auto_reset_when_enabling = auto_reset_when_enabling

        self._name = name
        self.enabled = enabled
        self.initial_time = initial_time

        self.__elapsed_time_from_last_trigger = 0.0
        self.__remaining_time_until_next_trigger = 0.0

    @property
    def action(self) -> GenericCallback:
        return self.__action
       
    @action.setter
    def action(self, value) -> None:
        if not isinstance(value, GenericCallback):
            raise TypeError('Must be a GenericCallback')
        
        self.__action = value 

    @property
    def duration(self) -> float:
        return self.__duration
        
    @duration.setter
    def duration(self, value) -> None:
        if not isinstance(value, float):
            raise TypeError('Duration must be a float')         
        if value <= 0:
            raise ValueError('Duration must be over 0')     
          
        self.__duration = value
        
    @property
    def auto_reset_when_enabling(self) -> bool:
        return self.__auto_reset_when_enabling   
         
    @auto_reset_when_enabling.setter
    def auto_reset_when_enabling(self, value) -> None:
        if not isinstance(value, bool):
            raise TypeError('Auto reset must be a boolean')      
          
        self.__auto_reset_when_enabling = value

    @property
    def elapsed_time_from_last_trigger(self) -> float:
        return self.__elapsed_time_from_last_trigger

    @property
    def remaining_time_until_next_trigger(self) -> float:
        return self.__remaining_time_until_next_trigger     
    
    def enabling(self) -> None:
        if self.__auto_reset_when_enabling:
            self.do_reset()
    
    def do_reset(self) -> None:
        self.__accumulator = 0.0
    
    def do_tracking(self, elapsed_time: float) -> None:
        self.__accumulator += elapsed_time
        if self.__accumulator > self.__duration:
            self.__action() 
            self.do_reset()

    
    

    

    
