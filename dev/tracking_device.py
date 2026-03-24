from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import final, override
from base_component import BaseComponent
from type_utilities import GenericCallback
import elapsed_timer

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
    
    @abstractmethod
    def _do_valid(self) -> bool:
        pass 

    @abstractmethod
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

    


        
