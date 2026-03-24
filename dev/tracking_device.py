from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import final, override
from base_component import BaseComponent
from type_utilities import GenericCallback

from base_component import BaseComponent
from elapsed_timer import ElapsedTimer
from typing import Iterable, Callable, TypeAlias, Any, NoReturn, Self
from abc import ABC, abstractmethod

class TrackingDevice(BaseComponent, ABC):
    def __init__(self, name: str | None, enabled: bool = True):
        super().__init__(name=name, enabled=enabled)
        self._sub_devices: dict[str, TrackingDevice] = {}

    @property
    @final
    def valid(self) -> bool:
        if not self._do_valid():
            return False
        for value in self._sub_devices.values():
            if not value.valid:
                return False
        return True
    
    @property
    def sub_devices_count(self) -> int:
        return len(self._sub_devices)

    def _do_valid(self) -> bool:
        pass 

    def _do_reset(self) -> None:
        pass

    @abstractmethod
    def _do_tracking(self, elapsed_time: float) -> None:
        pass

    def clear_sub_devices(self) -> None:
        self._sub_devices.clear()

    def add_sub_device(self, device: TrackingDevice | Iterable[TrackingDevice]) -> None:
        if isinstance(device, TrackingDevice):
            if device.name in self._sub_devices:
                raise ValueError(f'{device.name} existe déjà comme nom de device')
            self._sub_devices[device.name] = device
        elif isinstance(device, Iterable):
            for d in device:
                if not isinstance(d, TrackingDevice):
                    raise TypeError("Il faut ajouter un élément de type TrackingDevice")
                if d.name in self._sub_devices:
                    raise ValueError(f'{d.name} existe déjà comme nom de device')   
                self._sub_devices[d.name] = d
        else:
            raise TypeError("Il faut ajouter un élément de type TrackingDevice")

    def remove_sub_device(self, name: str | Iterable[str]) -> None:
        if isinstance(name, str):
            del self._sub_devices[name]
        elif isinstance(name, Iterable):
            for n in name:
                if isinstance(n, str):
                    del self._sub_devices[n]
                else:
                    raise TypeError("Il faut supprimer un élément de type str")
        else:
            raise TypeError("Il faut supprimer un élément de type str")

    @final
    def reset(self) -> None:
        for value in self._sub_devices.values():
            value.reset()
        self._do_reset()

    @final
    def track(self, elapsed_time: float) -> None:
        if not self.enabled:
            return
        for value in self._sub_devices.values():
            value.track(elapsed_time)
        self._do_tracking(elapsed_time)



class TrackingManager():
    def __init__(self:Self):
        self.__tracking_devices:dict[str, TrackingDevice] = {}
        self.__valid:bool = True

    @property
    def valid(self:Self) -> bool:
        return self.__valid
    
    @property
    def device_count(self:Self) -> int:
        return len(self.__tracking_devices)
    
    def clear_devices(self:Self) -> None:
        self.__tracking_devices.clear()

    def add_device(self:Self, device : TrackingDevice | Iterable[TrackingDevice]) -> None:

        if isinstance(device, TrackingDevice):
            self.__tracking_devices[device.name] = device # dico pas de append

        elif isinstance(device, Iterable):
            for d in device:
                if isinstance(d, TrackingDevice):
                    self.__tracking_devices[d.name] = d
        else:
            raise TypeError(f'Le type de {device} doit être un TrackingDevice ou un iterable de TrackingDevice. Présentement {type(device)}')

    def remove_device(self:Self, device : str | TrackingDevice | Iterable[str] | Iterable[TrackingDevice]) -> None:

        if isinstance(device, str):
            self.__tracking_devices.pop(device)

        if isinstance(device, TrackingDevice):
            self.__tracking_devices.pop(device.name)

        elif isinstance(device, Iterable):
            for d in device:
                if d in self.__tracking_devices:
                    if isinstance(d, TrackingDevice):
                        self.__tracking_devices.pop(d.name)
                    elif isinstance (d, str):
                        self.__tracking_devices.pop(d)
                     
        else:
            raise TypeError(f'Le type de {device} doit être un TrackingDevice ou un iterable de TrackingDevice. Présentement {type(device)}')

    def track(self:Self, elapsed_time : float) -> None:
        for device in self.__tracking_devices.values():
                device.track(elapsed_time)

    def reset(self:Self) -> None:
        for device in self.__tracking_devices.values():
                device.reset()

class TrackingApplication(TrackingManager):
    RunningCondition:TypeAlias = Callable[[], Any|None]

    def __init__(self:Self) -> None:
        super().__init__()
        self.__elapsed_timer:ElapsedTimer = ElapsedTimer()

    def run_forever(self:Self) -> NoReturn:
        while True:
            self.track(self.__elapsed_timer.elapsed)
            

    def run_until(self:Self, running_condition:RunningCondition) -> Any:
        result:Any = running_condition()
        while result is None:
            self.track(self.__elapsed_timer.elapsed)
            result = running_condition()

        return result

class TriggerDevice(TrackingDevice):
    def __init__(self, duration: float, action: GenericCallback, /, name: str | None = None, enabled: bool = True, *, initial_time: float = 0.0, auto_reset_when_enabling: bool = True):
        super().__init__(name, enabled)
        self.__duration = duration
        self.__action = action
        self.__accumulator = 0.0
        self.__auto_reset_when_enabling = auto_reset_when_enabling

        self.initial_time = initial_time

        self.__elapsed_time_from_last_trigger = 0.0
        self.__remaining_time_until_next_trigger = 0.0

    @property
    def action(self) -> GenericCallback:
        return self.__action
       
    @action.setter
    def action(self, value:GenericCallback) -> None:
        if not callable(value):
            raise TypeError('Must be a GenericCallback')
        
        self.__action = value 

    @property
    def duration(self) -> float:
        return self.__duration
        
    @duration.setter
    def duration(self, value : float) -> None:
        if not isinstance(value, float):
            raise TypeError('Duration must be a float')         
        if value <= 0:
            raise ValueError('Duration must be over 0')     
          
        self.__duration = value
        
    @property
    def auto_reset_when_enabling(self) -> bool:
        return self.__auto_reset_when_enabling   
         
    @auto_reset_when_enabling.setter
    def auto_reset_when_enabling(self, value : bool) -> None:
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
            self._do_reset()
    
    @override
    def _do_reset(self) -> None:
        self.__accumulator = 0.0
    
    @override
    def _do_tracking(self, elapsed_time: float) -> None:
        self.__accumulator += elapsed_time
        if self.__accumulator > self.__duration:
            self.__action() 
            self._do_reset()

    
    

        
