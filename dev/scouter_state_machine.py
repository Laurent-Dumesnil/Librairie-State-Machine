from typing import override
from state_machine_device import StateMachineDevice
from state_machine_utilities import MonitoredState, State, ConditionalTransition
from condition import Condition, ValueCondition, ReaderCondition, AllConditions
from tracking_device import TrackingApplication
from blinker_device import BlinkerDevice
from console import Console

class KeyPressCondition(Condition):
    def __init__(self, console: Console, expected_key_value):
        self.__console = console
        self.__expected_key_value = expected_key_value.upper()

    @override
    def _compare(self):
        super()._compare()
        if self.__console.actual_key_pressed == self.__expected_key_value:
            return True
        return False
    
class NotKeyPressCondition(Condition):
    def __init__(self, console: Console, not_expected_key_value):
        self.__console = console
        self.__not_expected_key_value = not_expected_key_value.upper()

    @override
    def _compare(self):
        super()._compare()
        if self.__not_expected_key_value not in self.__console.actual_key_pressed:
            return True
        return False

class Charging(State):
    
    class BatteryManagement(StateMachineDevice):
        def __init__(self, console):
            pass

    def __init__(self, console: Console):
        battery_management = Charging.BatteryManagement(console)

class Scooting(State):
    
    class RideManagement(StateMachineDevice):
        def __init__(self, console: Console):
            pass

    def __init__(self, console):
        ride_management = Scooting.RideManagement(console)

class ScooterStateMachine(StateMachineDevice):
    def __init__(self, console):
        self.__plugged_in = False

        #States
        power_off_state = State("power_off")
        unlocking_state = MonitoredState("unlocking")
        powering_up_state = MonitoredState("powerring_up")
        idle_state = MonitoredState("idle")
        locking_state = MonitoredState("locking")
        charging_failed_state = MonitoredState("charging_failed")
        powering_down_state = MonitoredState("powering_down")
        intygrity_failed_state = MonitoredState("intygrity_failed")
        charging_state = Charging("charging", console)
        scooting_state = Scooting("scooting", console)

        #Conditions
        plugged_in_condition = ReaderCondition(True, lambda:self.__plugged_in)

        #Transitions
        power_off_state.add_transition(plugged_in_condition, charging_state)
        power_off_state.add_transition(AllConditions([KeyPressCondition(console, "P"), plugged_in_condition]), unlocking_state)
        charging_state.add_transition(ReaderCondition(False, lambda:self.__plugged_in), power_off_state)
        #À vérifier si ya meilleure solution
        charging_state.add_transition(ReaderCondition(True, lambda:charging_state.BatteryManagement.current_state.terminal), charging_failed_state)
        unlocking_state.add_transition(NotKeyPressCondition(console, "P"))


        layout = (power_off_state, 
                  unlocking_state, 
                  powering_up_state, 
                  idle_state, locking_state, 
                  charging_failed_state, 
                  powering_down_state, 
                  intygrity_failed_state, 
                  charging_state, 
                  scooting_state
                )
        
        super().__init__(StateMachineDevice.Layout(layout))

def main():
    console = Console()
    app = TrackingApplication()
    scooter = ScooterStateMachine(console)

    app.add_device(scooter)

if __name__ == "__main__":
    main()