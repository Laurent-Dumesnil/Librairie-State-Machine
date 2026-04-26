from blinker_device import BlinkerDevice
from state_machine_utilities import MonitoredState
from tracking_device import TrackingApplication
from typing import override, Self

class BlinkerStateFactory:
        def __init__(self:Self, state:str):
            if not isinstance(state, str):
                raise TypeError('message must be of type string')
            self.__state = state
            
        def __call__(self)-> MonitoredState:
            state = MonitoredState()

            def entering_action() -> None:
                print(f"\r{self.__state} ", end="", sep="")

            state.add_entering_action(entering_action)
            return state

def main() -> int:
    off_state_factory = BlinkerStateFactory('off')
    on_state_factory = BlinkerStateFactory('on')
    blinkerDevice = BlinkerDevice(off_state_factory, on_state_factory)

    # blinkerDevice.turn_on(5.0)
    # blinkerDevice.blink(cycle_duration=5.0, percent_on=0.2, begin_on=True) 
    # blinkerDevice.blink(total_duration=5.0, cycle_duration=1.0, percent_on=0.2, begin_on=True, end_off=True)
    # blinkerDevice.blink(total_duration=5.0, n_cycle=3, percent_on=0.2, begin_on=True, end_off=True)
    # blinkerDevice.blink(n_cycle=3,cycle_duration=1.0, percent_on=0.2, begin_on=True, end_off=True)

    app = TrackingApplication()
    app.add_device(blinkerDevice)
    app.run_forever()
    return 0

if __name__ == "__main__":
    quit(main())
