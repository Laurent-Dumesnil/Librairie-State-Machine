from typing import Self, override, Iterable, TypeAlias, Callable
from abc import ABC, abstractmethod
from elapsed_timer import ElapsedTimer
from type_utilities import GenericGenerator, OptionalOneOrMany, OneOrMany

from state_machine_device import StateMachineDevice 
from state_machine_utilities import MonitoredState, ConditionalTransition, DelaySinceEnteredCondition, StateValueCondition
from condition import AlwaysTrueCondition

class BlinkerDevice(StateMachineDevice) :

    BlinkerStateFactory:TypeAlias = Callable[[], MonitoredState]



    def __init__(self, off_state_factory : BlinkerStateFactory, on_state_factory : BlinkerStateFactory):

        self.off = off_state_factory()

        self.off_duration = off_state_factory()
        self.blink_off = off_state_factory()
        self.blink_stop_off = off_state_factory()

        self.on = on_state_factory()
        self.on_duration = on_state_factory()
        self.blink_on = on_state_factory()
        self.blink_stop_on = on_state_factory()

        self.off_duration.add_transition(ConditionalTransition(DelaySinceEnteredCondition(0), self.on))

        layout = (self.off, self.off_duration, self.blink_off, self.blink_stop_off, self.on, self.on_duration, self.blink_on,self.blink_stop_on)

        super().__init__(layout)




    def main():
        def factory_off():
            off_state = MonitoredState()
            return off_state
        
        b = BlinkerDevice(factory_off)

    