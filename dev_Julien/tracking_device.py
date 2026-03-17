from abc import ABC, abstractmethod
import typing
from base_component import BaseComponent
import type_utilities
import elapsed_timer

class Trackingdevice(BaseComponent):
    def __init__(self, name: str | None, enabled: bool = True):
        self.sub_devices: dict[str, Trackingdevice] = {}
        self.valid: bool
        
