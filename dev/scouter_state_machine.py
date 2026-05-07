from typing import override
from state_machine_device import StateMachineDevice
from state_machine_utilities import MonitoredState, ActionState, State, DelaySinceEnteredCondition, ConditionalTransition
from condition import Condition, ReaderCondition, AllConditions, AnyConditions, AbstractValueCondition
from tracking_device import TrackingApplication
from blinker_device import BlinkerDevice
from console import Console
from scooter import Scooter

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

    def __init__(self, name, console: Console):
        battery_management = Charging.BatteryManagement(console)
        super().__init__(name)

    @override
    def _do_entering_action(self):
        print("CHARGING")

class Scooting(State):
    
    class RideManagement(StateMachineDevice):
        def __init__(self, console: Console):
            pass

    def __init__(self, name, console):
        ride_management = Scooting.RideManagement(console)
        super().__init__(name)
    
    @override
    def _do_entering_action(self):
        print("SCOOTING")

class ScooterStateMachine(StateMachineDevice):
    def __init__(self, console):
        self.__scooter = Scooter()
        self.__plugged_in = False

        #States
        power_off_state = ActionState("power_off")
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
        power_less_then_condition = LessThenCondition(0.03, lambda:self.__scooter.battery.power)
        speed_less_then_condition = LessThenCondition(0.01, lambda:self.__scooter.speed)

        #Transitions
        power_off_state.add_transition(ConditionalTransition(plugged_in_condition, unlocking_state))
        power_off_state.add_transition(ConditionalTransition(AllConditions([KeyPressCondition(console, "P"), plugged_out_condition]), unlocking_state))
        charging_state.add_transition(ConditionalTransition(ReaderCondition(False, lambda:self.__plugged_in), power_off_state)) 
        #À vérifier si ya meilleure solution
        charging_state.add_transition(ConditionalTransition(ReaderCondition(True, lambda:charging_state.BatteryManagement.current_state.terminal), charging_failed_state)) 
        charging_failed_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, charging_failed_state), powering_down_state)) 
        unlocking_state.add_transition(ConditionalTransition(NotKeyPressCondition(console, "P"), power_off_state))
        unlocking_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, unlocking_state), powering_up_state))
        powering_up_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, powering_up_state), idle_state))
        powering_up_state.add_transition(ConditionalTransition(KeyPressCondition(console, "F"), intygrity_failed_state))
        intygrity_failed_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, intygrity_failed_state), powering_down_state))
        idle_state.add_transition(ConditionalTransition(KeyPressCondition(console, "P"), locking_state))
        idle_state.add_transition(ConditionalTransition(AnyConditions([DelaySinceEnteredCondition(30.0, idle_state), ]), powering_down_state))
        idle_state.add_transition(ConditionalTransition(power_less_then_condition, powering_down_state))
        idle_state.add_transition(ConditionalTransition(KeyPressCondition(console, "A"), scooting_state))
        scooting_state.add_transition(ConditionalTransition(AnyConditions([power_less_then_condition, speed_less_then_condition]), idle_state)) 
        locking_state.add_transition(ConditionalTransition(NotKeyPressCondition(console, "P"), idle_state)) 
        locking_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, locking_state), powering_down_state)) 
        powering_down_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, powering_down_state), power_off_state))

        #Actions
        power_off_state.add_entering_action(self._on_power_off)
        unlocking_state.add_entering_action(self._on_unlocking)
        powering_up_state.add_entering_action(self._on_powering_up)
        powering_down_state.add_entering_action(self._on_powering_down)
        idle_state.add_entering_action(self._on_idle)
        intygrity_failed_state.add_entering_action(self._on_integrity_failed)
        locking_state.add_entering_action(self._on_locking)
        charging_failed_state.add_entering_action(self._on_charing_failed)

        # print(f'power_off: {power_off_state.valid}')
        # print(f'unlocking: {unlocking_state.valid}')
        # print(f'powering_up: {powering_up_state.valid}')
        # print(f'powering_down: {powering_down_state.valid}')
        # print(f'idle: {idle_state.valid}')
        # print(f'charging: {charging_state.valid}')
        # print(f'charging_failed: {charging_failed_state.valid}')
        # print(f'scooting: {scooting_state.valid}')
        # print(f'locking: {locking_state.valid}')
        # print(f'intygrity_failed: {intygrity_failed_state.valid}')

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

    def _on_power_off(self):
        print("POWER OFF")
    def _on_unlocking(self):
        print("UNLOCKING")
    def _on_powering_up(self):
        print("POWERING ON")
    def _on_idle(self):
        print("IDLE")
    def _on_powering_down(self):
        print("POWERING DOWN")
    def _on_integrity_failed(self):
        print("INTEGRITY FAILED")
    def _on_locking(self):
        print("LOCKING")
    def _on_charing_failed(self):
        print("CHARGING FAILED")

def main():
    console = Console()
    app = TrackingApplication()
    scooter = ScooterStateMachine(console)

    app.add_device(scooter)
    app.run_forever()

if __name__ == "__main__":
    main()