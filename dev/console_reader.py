from typing import Self, override, TypeAlias
from tracking_device import TrackingDevice
from console import Console

KeyboardValue: TypeAlias = str | Console.SpecialKey
class ConsoleReader(TrackingDevice):
    def __init__(self: Self, name: str | None, console: Console, enabled: bool=True):
        self.__console = console
        self.__key_pressed: list[KeyboardValue] = []
        self.__actual_key_pressed: list[KeyboardValue] = []
        super().__init__(name, enabled=enabled)

    @property
    def key_pressed(self: Self) -> list[KeyboardValue]:
        return self.__key_pressed
    
    @key_pressed.setter
    def key_pressed(self: Self, value: list[KeyboardValue]) -> None:
        self.__key_pressed = value
    
    @property
    def actual_key_pressed(self: Self) -> list[KeyboardValue]:
        return self.__actual_key_pressed
    
    @actual_key_pressed.setter
    def actual_key_pressed(self: Self, value: list[KeyboardValue]) -> None:
        self.__actual_key_pressed = value

    @override
    def _do_reset(self: Self) -> None:
        super()._do_reset()
        self.__key_pressed = []
        self.__actual_key_pressed = []

    @override
    def _do_tracking(self: Self, elapsed_time: float) -> None:
        self.__key_pressed = self.__console.key_pressed
        self.__actual_key_pressed = self.__console.actual_key_pressed
        