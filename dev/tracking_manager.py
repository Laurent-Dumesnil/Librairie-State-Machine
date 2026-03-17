from base_component import BaseComponent
from elapsed_timer import ElapsedTimer
from typing import Iterable
from abc import ABC, abstractmethod

# à enlever d'ici plus tard
class TrackingDevice(BaseComponent):
    def __init__(self, name: str):
        super().__init__(name)

        self._active = True

    @property
    def active(self) -> int: # {readOnly}
        return self._active
    
    @active.setter
    def active(self, is_active):
        self._active = is_active



class TrackingManager():
    __tracking_devices : dict[str, TrackingDevice]
    valid = True

    def __init__():
        pass

    @property
    def valid(self) -> bool:
        return TrackingManager.valid
    
    @property
    def device_count(self) -> int:
        return len(TrackingManager.__tracking_devices)
    
    def clear_devices():
        TrackingManager.__tracking_devices = {}

    def add_device(device : TrackingDevice | Iterable[TrackingDevice]):

        if isinstance(device, TrackingDevice):
            TrackingManager.__tracking_devices.append(device)

        elif isinstance(device, Iterable[TrackingDevice]):
            for d in device:
                TrackingManager.__tracking_devices.append(d) 
        else:
            raise TypeError(f'Le type de {device} doit être un TrackingDevice ou un iterable de TrackingDevice. Présentement {type(device)}')

    def remove_device(device : TrackingDevice | Iterable[str] | Iterable[TrackingDevice]):

        if isinstance(device, TrackingDevice):
            TrackingManager.__tracking_devices.pop(device)

        elif isinstance(device, Iterable[TrackingDevice]):
            for d in device:
                if d in TrackingManager.__tracking_devices:
                    TrackingManager.__tracking_devices.pop(d) 
        else:
            raise TypeError(f'Le type de {device} doit être un TrackingDevice ou un iterable de TrackingDevice. Présentement {type(device)}')

    @abstractmethod 
    def track(elapsed_time : float):
        pass 

    def reset():
        pass

class RunningCondition():

    running_condition = callable[[], any | None]

    def __init__(self):
        pass

    def should_stop(self) -> bool:
        pass # si on doit arrêter, true sinon false

class TrackingApplication(TrackingManager):
    elapsed_timer = ElapsedTimer()

    def run_forever():
        while True:
            pass

    def run_until(running_condition : RunningCondition): # RunningCondition
        while running_condition:
            pass



# NOTES MJ :
# premier design pattern : composite
# différence entre valid et do_valid



    