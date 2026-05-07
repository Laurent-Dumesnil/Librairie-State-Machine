from typing import override
from state_machine_device import StateMachineDevice
from state_machine_utilities import MonitoredState, State, DelaySinceEnteredCondition
from condition import Condition, ReaderCondition, AllConditions, AnyConditions, AbstractValueCondition
from tracking_device import TrackingApplication
from blinker_device import BlinkerDevice
from console import Console


##Pour test uniquement
class Scouter():
    class Battery():
        def __init__(self):
            self.power = 100

    def __init__(self):
        self.battery = Scouter.Battery()
        self.speed = 30
#######################################

##À finir ca na pas été testé
class LessThenCondition(AbstractValueCondition):
    def __init__(self, max_value, actual_value):
        self.__max_value = max_value
        self.__actual_value = actual_value

    @override
    def _compare(self):
        if self.__actual_value < self.__max_value:
            return True
        else:
            return False

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
        self.__scouter = Scouter()
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
        plugged_out_condition = ReaderCondition(False, lambda:self.__plugged_in)
        power_less_then_condition = LessThenCondition(0.03, lambda:self.__scouter.battery.power)
        speed_less_then_condition = LessThenCondition(0.01, lambda:self.__scouter.speed)

        #Transitions
        power_off_state.add_transition(plugged_in_condition, charging_state)
        power_off_state.add_transition(AllConditions([KeyPressCondition(console, "P"), plugged_out_condition]), unlocking_state)
        charging_state.add_transition(ReaderCondition(False, lambda:self.__plugged_in), power_off_state)
        #À vérifier si ya meilleure solution
        charging_state.add_transition(ReaderCondition(True, lambda:charging_state.BatteryManagement.current_state.terminal), charging_failed_state)
        charging_failed_state.add_transition(DelaySinceEnteredCondition(3.0, charging_failed_state), powering_down_state)
        unlocking_state.add_transition(NotKeyPressCondition(console, "P"), power_off_state)
        unlocking_state.add_transition(DelaySinceEnteredCondition(3.0, unlocking_state), powering_up_state)
        powering_up_state.add_transition(DelaySinceEnteredCondition(3.0, powering_up_state), idle_state)
        powering_up_state.add_transition(KeyPressCondition(console, "F"), intygrity_failed_state)
        intygrity_failed_state.add_transition(DelaySinceEnteredCondition(3.0, intygrity_failed_state), powering_down_state)
        idle_state.add_transition(KeyPressCondition(console, "P"), locking_state)
        idle_state.add_transition(AnyConditions([DelaySinceEnteredCondition(30.0, idle_state), ]), powering_down_state)
        idle_state.add_transition(power_less_then_condition, powering_down_state)
        idle_state.add_transition(KeyPressCondition(console, "A"), scooting_state)
        scooting_state.add_transition(AnyConditions([power_less_then_condition, speed_less_then_condition], idle_state))
        locking_state.add_transition(NotKeyPressCondition(console, "P"), idle_state)
        locking_state.add_transition(DelaySinceEnteredCondition(3.0, locking_state), powering_down_state)
        powering_down_state.add_transition(DelaySinceEnteredCondition(3.0, powering_down_state), power_off_state)


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