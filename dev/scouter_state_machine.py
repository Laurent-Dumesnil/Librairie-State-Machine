from typing import override, Self
from state_machine_device import StateMachineDevice
from state_machine_utilities import MonitoredState, ActionState, State, DelaySinceEnteredCondition, ConditionalTransition
from condition import Condition, ReaderCondition, AllConditions, AnyConditions, AbstractValueCondition
from tracking_device import TrackingApplication
from blinker_device import BlinkerDevice
from console import Console
from scooter import Scooter

##À finir ca na pas été testé
class LessThanCondition(AbstractValueCondition):
    def __init__(self, max_value, actual_value_reader):
        self.__max_value = max_value
        self.__actual_value_reader = actual_value_reader
        super().__init__(max_value)

    @override
    def _compare(self) -> bool:
        return self.__actual_value_reader() < self.__max_value
        
class KeyPressCondition(Condition):
    def __init__(self, scooter_state_machine, expected_key_value):
        self.__scooter_state_machine = scooter_state_machine
        self.__expected_key_value = expected_key_value
        super().__init__()

    @override
    def _compare(self):
        super()._compare()
        if self.__expected_key_value in self.__scooter_state_machine.key_pressed:
            return True
        return False
    
class NotKeyPressCondition(Condition):
    def __init__(self, scooter_state_machine, not_expected_key_value):
        self.__scooter_state_machine = scooter_state_machine
        self.__not_expected_key_value = not_expected_key_value
        super().__init__()

    @override
    def _compare(self):
        super()._compare()
        if self.__not_expected_key_value in self.__scooter_state_machine.key_pressed:
            return True
        return False

class ActualKeyPressCondition(Condition):
    def __init__(self, scooter_state_machine, expected_key_value):
        self.__scooter_state_machine = scooter_state_machine
        self.__expected_key_value = expected_key_value
        super().__init__()

    @override
    def _compare(self):
        super()._compare()
        if self.__expected_key_value in self.__scooter_state_machine.actual_key_pressed:
            return True
        return False
    
class ActualKeyReleasedCondition(Condition):
    def __init__(self, console: Console, expected_key_value):
        self.__console = console
        self.__expected_key_value = expected_key_value
        super().__init__()

    @override
    def _compare(self) -> bool:
        return self.__expected_key_value not in self.__console.actual_key_pressed

class Charging(ActionState):
    
    class BatteryManagement(StateMachineDevice):
        def __init__(self, console):
            pass

    def __init__(self, name, console: Console):
        battery_management = Charging.BatteryManagement(console)
        super().__init__(name)

class Scooting(ActionState):
    
    class RideManagement(StateMachineDevice):
        def __init__(self:Self,console:Console, scooter:Scooter, initialized:bool = True, name:str = None, enabled:bool = False) -> None:
            self.__delta_time = 0
            self.__scooter = scooter
            self.__console = console
            self.__free_wheel_state = ActionState("Free Wheel")
            self.__accelerating_state = ActionState("Accelerating")
            self.__breaking_state = ActionState("Breaking")

            self.__free_wheel_state.add_transition(ConditionalTransition(ReaderCondition(True, self.__read_up_arrow),self.__accelerating_state))
            self.__free_wheel_state.add_transition(ConditionalTransition(ReaderCondition(True, self.__read_down_arrow),self.__breaking_state))
            self.__accelerating_state.add_transition(ConditionalTransition(ReaderCondition(True, self.__read_down_arrow),self.__breaking_state))
            self.__accelerating_state.add_transition(ConditionalTransition(ReaderCondition(False, self.__read_up_arrow), self.__free_wheel_state))
            self.__breaking_state.add_transition(ConditionalTransition(ReaderCondition(False, self.__read_down_arrow), self.__free_wheel_state))

            self.__accelerating_state.add_in_state_action(self.__accelerate)
            self.__accelerating_state.add_entering_action(self._on_accelerate)
            self.__breaking_state.add_in_state_action(self.__breaking)
            self.__free_wheel_state.add_in_state_action(self.__decelerate)
            self.__free_wheel_state.add_entering_action(self._on_free_wheel)

            layout = self.Layout((self.__free_wheel_state, self.__accelerating_state, self.__breaking_state))
            super().__init__(layout, initialized, name, enabled)


        @property
        def free_wheel_state(self:Self) -> None:
            return self.__free_wheel_state

        @override
        def _do_tracking(self:Self, elapsed_time: float) -> None:
            self.__delta_time = elapsed_time
        
        def __read_up_arrow(self:Self) -> bool:
            return True if self.__console.SpecialKey.UP_ARROW in self.__console.actual_key_pressed else False
    
        def __read_down_arrow(self:Self) -> bool:
            return True if self.__console.SpecialKey.UP_ARROW in self.__console.actual_key_pressed else False
        
        def _on_accelerate(self):
            print("ACCELERATE")

        def _on_free_wheel(self):
            print("FREE WHEEL")

        def __accelerate(self:Self) -> None:
            self.__scooter.accelerate(self.__delta_time)

        def __decelerate(self:Self) -> None:
            print("DECELERATE")
            self.__scooter.decelerate(self.__delta_time)

        def __breaking(self:Self) -> None:
            self.__scooter.decelerate(self.__delta_time, 0.5)

    def __init__(self, name, ridemanagement:RideManagement):
        self.__ridemanagement = ridemanagement
        super().__init__(name)
    
    @override
    def _do_entering_action(self):
        print("SCOOTING")
        self.__ridemanagement.enabled = True
        self.__ridemanagement._transit_to(self.__ridemanagement.free_wheel_state)

# class PowerOffState(State):
#     def __init__(self, name, enabled, scooter_state_machine):
#         self.__scooter_state_machine = scooter_state_machine
#         super().__init__(name, enabled=enabled)

#     @override
#     def _do_entering_action(self):
#         print("POWER_OFF")


#     @override
#     def _do_in_state_action(self):
#         pass
        #print(f"Touches clavier : {self.__scooter_state_machine.key_pressed}                         ", end="\r", flush=True)


class ScooterStateMachine(StateMachineDevice):
    def __init__(self, console, scooter, ridemanagement):
        self.__console = console
        self.__scooter = scooter
        self.__plugged_in = False

        #States
        # power_off_state = PowerOffState("power_off", True, self.__console)
        power_off_state = ActionState("power_off")
        power_off_state.add_entering_action(self._on_power_off)
        power_off_state.add_in_state_action(self._plug_charging_cable)
        unlocking_state = MonitoredState("unlocking")
        powering_up_state = MonitoredState("powerring_up")
        idle_state = MonitoredState("idle")
        locking_state = MonitoredState("locking")
        charging_failed_state = MonitoredState("charging_failed")
        powering_down_state = MonitoredState("powering_down")
        intygrity_failed_state = MonitoredState("intygrity_failed")
        charging_state = Charging("charging", console)
        charging_state.add_entering_action(self._on_charging)
        charging_state.add_in_state_action(self._unplug_charging_cable)
        scooting_state = Scooting("scooting", ridemanagement)

        #Conditions
        plugged_in_condition = ReaderCondition(True, lambda:self.__plugged_in)
        plugged_out_condition = ReaderCondition(False, lambda:self.__plugged_in)
        power_less_then_condition = LessThanCondition(0.03, lambda:self.__scooter.battery.power)
        speed_less_then_condition = LessThanCondition(0.01, lambda:self.__scooter.speed)

        #Transitions
        power_off_state.add_transition(ConditionalTransition(plugged_in_condition, charging_state))
        power_off_state.add_transition(ConditionalTransition(AllConditions([ActualKeyPressCondition(console, "p"), plugged_out_condition]), unlocking_state))
        charging_state.add_transition(ConditionalTransition(ReaderCondition(False, lambda:self.__plugged_in), power_off_state)) 
        #À vérifier si ya meilleure solution
        charging_state.add_transition(ConditionalTransition(ReaderCondition(True, lambda:charging_state.BatteryManagement.current_state.terminal), charging_failed_state)) 
        charging_failed_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, charging_failed_state), powering_down_state)) 
        unlocking_state.add_transition(ConditionalTransition(ActualKeyReleasedCondition(console, "p"), power_off_state))
        unlocking_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, unlocking_state), powering_up_state))
        powering_up_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, powering_up_state), idle_state))
        powering_up_state.add_transition(ConditionalTransition(KeyPressCondition(console, "f"), intygrity_failed_state))
        intygrity_failed_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, intygrity_failed_state), powering_down_state))
        idle_state.add_transition(ConditionalTransition(ActualKeyPressCondition(console, "p"), locking_state))
        idle_state.add_transition(ConditionalTransition(AnyConditions([DelaySinceEnteredCondition(30.0, idle_state), ]), powering_down_state))
        idle_state.add_transition(ConditionalTransition(power_less_then_condition, powering_down_state))
        idle_state.add_transition(ConditionalTransition(KeyPressCondition(console, "a"), scooting_state))
        scooting_state.add_transition(ConditionalTransition(AllConditions([AnyConditions([power_less_then_condition, speed_less_then_condition]), AllConditions([NotKeyPressCondition(console, "a"), DelaySinceEnteredCondition(1.5, scooting_state)])]), idle_state)) 
        locking_state.add_transition(ConditionalTransition(ActualKeyReleasedCondition(console, "p"), idle_state)) 
        locking_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, locking_state), powering_down_state)) 
        powering_down_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, powering_down_state), power_off_state))

        #Actions
        #power_off_state.add_entering_action(self._on_power_off)
        unlocking_state.add_entering_action(self._on_unlocking)
        powering_up_state.add_entering_action(self._on_powering_up)
        powering_down_state.add_entering_action(self._on_powering_down)
        idle_state.add_entering_action(self._on_idle)
        intygrity_failed_state.add_entering_action(self._on_integrity_failed)
        locking_state.add_entering_action(self._on_locking)
        charging_failed_state.add_entering_action(self._on_charing_failed)

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

    @property
    def key_pressed(self):
        return self.__console.key_pressed

    @property
    def actual_key_pressed(self):
        return self.__console.actual_key_pressed
    
    @property
    def plugged_in(self):
        return self.__plugged_in
    
    @plugged_in.setter
    def plugged_in(self, value):
        if isinstance(value, bool):
            self.__plugged_in = value

    def _on_power_off(self):
        print("POWER OFF")
    def _on_unlocking(self):
        print("UNLOCKING")
    def _on_powering_up(self):
        print("POWERING UP")
        self.__console.actual_key_pressed
        self.__console.key_pressed
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
    def _on_charging(self):
        print("CHARGING")  

    def _plug_charging_cable(self):
        if "i" in self.actual_key_pressed:
            self.__plugged_in = True

    def _unplug_charging_cable(self):
        if "o" in self.actual_key_pressed:
            self.__plugged_in = False

def main():
    scooter = Scooter()
    console = Console()
    app = TrackingApplication()
    ride_management = Scooting.RideManagement(console,scooter)
    scooter_state_machine = ScooterStateMachine(console, scooter, ride_management)
    app.add_device(ride_management)

    app.add_device(scooter_state_machine)
    app.run_forever()

if __name__ == "__main__":
    main()