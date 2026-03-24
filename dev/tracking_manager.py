from base_component import BaseComponent
from elapsed_timer import ElapsedTimer
from typing import Iterable, Callable
from abc import ABC, abstractmethod

# à enlever d'ici plus tard
class TrackingDevice(BaseComponent):
    def __init__(self, name: str):
        super().__init__(name)

        self._active = True

    @property
    def active(self) -> bool: # {readOnly}
        return self._active
    
    @active.setter
    def active(self, is_active):
        self._active = is_active



class TrackingManager():
    def __init__(self):
        self.__tracking_devices : dict[str, TrackingDevice] = {}
        self.__valid = True

    @property
    def valid(self) -> bool:
        return self.__valid
    
    @property
    def device_count(self) -> int:
        return len(self.__tracking_devices)
    
    def clear_devices(self):
        self.__tracking_devices = {}

    def add_device(self, device : TrackingDevice | Iterable[TrackingDevice]):

        if isinstance(device, TrackingDevice):
            self.__tracking_devices[device.name] = device # dico pas de append

        elif isinstance(device, Iterable):
            for d in device:
                if isinstance(d, TrackingDevice):
                    self.__tracking_devices[d.name] = d
        else:
            raise TypeError(f'Le type de {device} doit être un TrackingDevice ou un iterable de TrackingDevice. Présentement {type(device)}')

    def remove_device(self, device : TrackingDevice | Iterable[str] | Iterable[TrackingDevice]):

        if isinstance(device, TrackingDevice):
            self.__tracking_devices.pop(device.name)

        elif isinstance(device, Iterable):
            for d in device:
                if d in self.__tracking_devices:
                    if isinstance(d, TrackingDevice):
                        self.__tracking_devices.pop(d.name)
                    elif isinstance (d, str) and d in self.__tracking_devices:
                        self.__tracking_devices.pop(d)
                     
        else:
            raise TypeError(f'Le type de {device} doit être un TrackingDevice ou un iterable de TrackingDevice. Présentement {type(device)}')

    def track(self, elapsed_time : float):
        for device in self.__tracking_devices.values():
                device.track(elapsed_time)

    def reset(self):
        for device in self.__tracking_devices.values():
                device.reset()

class TrackingApplication(TrackingManager):
    type RunningCondition = Callable

    def __init__(self):
        self.__elapsed_timer = ElapsedTimer()

    def run_forever(self):
        while True:
            self.track(self.__elapsed_timer.elapsed)
            

    def run_until(self, running_condition : RunningCondition):
        result = running_condition()
        while result is None:
            self.track(self.__elapsed_timer.elapsed)
            result = running_condition()

        return result

    