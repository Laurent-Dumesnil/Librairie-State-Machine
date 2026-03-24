from base_component import BaseComponent
from elapsed_timer import ElapsedTimer
from typing import Iterable, Callable, TypeAlias, Any, NoReturn, Self
from abc import ABC, abstractmethod

# à enlever d'ici plus tard
class TrackingDevice(BaseComponent):
    def __init__(self, name: str) -> None:
        super().__init__(name)

        self._active:bool = True

    @property
    def active(self) -> bool: # {readOnly}
        return self._active
    
    @active.setter
    def active(self, is_active:bool) -> None:
        self._active = is_active

    def track(self, elapsed_time : float) -> None :
        pass



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

    