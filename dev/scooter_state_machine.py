from typing import override, Self, Callable
from state_machine_device import StateMachineDevice
from state_machine_utilities import MonitoredState, ActionState, State, DelaySinceEnteredCondition, ConditionalTransition
from condition import Condition, ReaderCondition, AllConditions, AnyConditions, AbstractValueCondition, ElapsedTimerCondition
from tracking_device import TrackingApplication
from blinker_device import BlinkerDevice
from console import Console
from scooter import Scooter
from elapsed_timer import ElapsedTimer

class DelaySinceValueCondition(Condition):
    """
    Condition qui part un ElapsedTimer quand une valeur atteint un certain seuil.
    paramètre value doit être un property pour lire la valeur provenant d'une classe du modèle
    paramètre activation threshold c'est le seuil en bas duquel le ElapsedTimer commence à compter.
    """
    def __init__(self, activation_threshold:float, value:Callable[[], float], duration:float):
        self.__activation_threshold = activation_threshold 
        self.__value = value
        self.__duration = duration
        self.__elapsed_timer = ElapsedTimer(ElapsedTimer.Mode.ACCUMULATED)
        self.__enabled = False
        super().__init__()

    @override
    def _compare(self):
        print(f'\rtemps: {self.__elapsed_timer.elapsed} seuil: {self.__activation_threshold} vitesse modele: {self.__value()}', end="")
        if self.__value() > self.__activation_threshold:
            self.__enabled = False
            return False

        elif self.__value() <= self.__activation_threshold and not self.__enabled:
            self.__enabled = True
            self.reset()
            return False

        elif self.__elapsed_timer.elapsed >= self.__duration and self.__enabled:
            self.__enabled = False
            return True

        return False
    
    def reset(self:Self) -> None:
        """Réinitialise le elapsed timer."""
        self.__elapsed_timer.reset()

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
        def __init__(self:Self, console:Console, scooter:Scooter, initialized:bool = False, name:str | None = None, enabled:bool = True) -> None:
            self.__delta_time = 0.0
            self.__battery = scooter.battery
            self.__console = console
            self.__charging_terminated = ActionState("Charging Terminated", terminal=True)
            self.__charging_complete = ActionState("Charging Complete")
            self.__charging_on = ActionState("Charging On")
            self.__charging_off = ActionState("Charging Off")
            self.__cooling = ActionState("Cooling")

            self.__charging_on.add_transition(ConditionalTransition(ReaderCondition(True, lambda: self.__battery.energy_level >= 99), self.__charging_complete))
            self.__charging_on.add_transition(ConditionalTransition(ReaderCondition(True, lambda: self.__battery.energy_level > 85), self.__cooling))
            self.__charging_on.add_transition(ConditionalTransition(ReaderCondition(True, lambda: self.__read_f()), self.__charging_terminated))
            self.__charging_complete.add_transition(ConditionalTransition(ReaderCondition(True, lambda:self.__battery.energy_level < 95), self.__charging_on))
            self.__cooling.add_transition(ConditionalTransition(ReaderCondition(True, lambda: self.__battery.energy_level < 75), self.__charging_on))

            self.__charging_on.add_in_state_action(self.__charging)
            self.__charging_complete.add_in_state_action(self.__decharging)
            self.__cooling.add_in_state_action(self.__decharging)
                
            layout = self.Layout((self.__charging_on, self.__charging_complete, self.__cooling, self.__charging_terminated))
            super().__init__(layout, initialized, name, enabled)
            
            if initialized : 
                self.reset()

        @property
        def charging_off(self:Self) -> ActionState:
            return self.__charging_off
        
        def __charging(self:Self) -> None:
            self.__battery.set_power_device_charging(self.__delta_time)

        def __decharging(self:Self) -> None:
            self.__battery.set_power_based_usage(self.__delta_time)    

        @override
        def _do_tracking(self:Self, elapsed_time: float) -> None:
            super()._do_tracking(elapsed_time)
            self.__delta_time = elapsed_time
            
        def __read_f(self:Self) -> bool:
            return "f" in self.__console.actual_key_pressed

    def __init__(self:Self, name:str, batteryManagement:BatteryManagement):
        self.__battery_management = batteryManagement
        super().__init__(name)

    @property
    def charging_error(self:Self) -> bool:
        return self.__battery_management.current_state.terminal
    
    @override
    def _do_entering_action(self) -> None:
        print("CHARGING")
        self.__battery_management.reset()
        self.__battery_management.enabled = True

    @override
    def _do_exiting_action(self) -> None:
        if not self.charging_error:
            self.__battery_management._transit_to(self.__battery_management.charging_off)

class Scooting(MonitoredState):
    
    class RideManagement(StateMachineDevice):
        def __init__(self:Self, console:Console, scooter:Scooter, initialized:bool = False, name:str = None, enabled:bool = False) -> None:
            self.__timer = ElapsedTimer(ElapsedTimer.Mode.INTERVAL)
            self.__scooter = scooter
            self.__console = console
            self.__free_wheel_state = ActionState("Free Wheel")
            self.__accelerating_state = ActionState("Accelerating")
            self.__breaking_state = ActionState("Breaking")
            self.__cruise_control_state = ActionState("Cruise Control")
            self.__end_state = State("Ending State", terminal=True)

            self.__free_wheel_state.add_transition(ConditionalTransition(ReaderCondition(True, self.__read_up_arrow),self.__accelerating_state))
            self.__free_wheel_state.add_transition(ConditionalTransition(ReaderCondition(True, self.__read_down_arrow),self.__breaking_state))
            self.__free_wheel_state.add_transition(ConditionalTransition(ReaderCondition(True, self.__read_c), self.__cruise_control_state))
            self.__accelerating_state.add_transition(ConditionalTransition(ReaderCondition(True, self.__read_down_arrow),self.__breaking_state))
            self.__accelerating_state.add_transition(ConditionalTransition(ReaderCondition(False, self.__read_up_arrow), self.__free_wheel_state))
            self.__breaking_state.add_transition(ConditionalTransition(ReaderCondition(False, self.__read_down_arrow), self.__free_wheel_state))
            self.__cruise_control_state.add_transition(ConditionalTransition(ReaderCondition(True, self.__read_up_arrow),self.__accelerating_state))
            self.__cruise_control_state.add_transition(ConditionalTransition(ReaderCondition(True, self.__read_down_arrow),self.__breaking_state))

            self.__accelerating_state.add_entering_action(self.__timer.reset)
            self.__breaking_state.add_entering_action(self.__timer.reset)
            self.__breaking_state.add_entering_action(self.__timer.reset)
            self.__cruise_control_state.add_entering_action(self.__timer.reset)

            self.__accelerating_state.add_in_state_action(self.__accelerate)
            self.__breaking_state.add_in_state_action(self.__breaking)
            self.__free_wheel_state.add_in_state_action(self.__decelerate)
            self.__cruise_control_state.add_in_state_action(self.__cruise)

            layout = self.Layout((self.__free_wheel_state, self.__accelerating_state, self.__breaking_state))
            super().__init__(layout, initialized, name, enabled)
        
        @property
        def end_state(self:Self) -> ActionState:
            return self.__end_state
        
        def __read_up_arrow(self:Self) -> bool:
            return True if self.__console.SpecialKey.UP_ARROW in self.__console.actual_key_pressed else False
    
        def __read_down_arrow(self:Self) -> bool:
            return True if self.__console.SpecialKey.DOWN_ARROW in self.__console.actual_key_pressed else False
        
        def __read_c(self:Self) -> bool:
            return True if "c" in self.__console.key_pressed else False

        def __accelerate(self:Self) -> None:
            self.__scooter.accelerate(self.__timer.elapsed)
            self.__scooter.battery.set_power_device_accelerating(self.__timer.elapsed)

        def __decelerate(self:Self) -> None:
            self.__scooter.decelerate(self.__timer.elapsed)
            self.__scooter.battery.set_power_based_usage(self.__timer.elapsed)

        def __breaking(self:Self) -> None:
            self.__scooter.decelerate(self.__timer.elapsed, 0.5)
            self.__scooter.battery.set_power_device_breaking(self.__timer.elapsed, self.__scooter.speed)

        def __cruise(self:Self) -> None:
            self.__scooter.battery.set_power_based_usage(self.__timer.elapsed)

    def __init__(self, name, ridemanagement:RideManagement):
        self.__ridemanagement = ridemanagement
        super().__init__(name)
    
    @override
    def _do_entering_action(self) -> None:
        print("SCOOTING")
        self.__ridemanagement.reset()
        self.__ridemanagement.enabled = True

    @override
    def _do_exiting_action(self) -> None:
        self.__ridemanagement._transit_to(self.__ridemanagement.end_state)
        

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
        power_less_than_condition = LessThanCondition(0.03, lambda:self.__scooter.battery.energy_level)
        speed_less_than_condition = LessThanCondition(0.5/3.6, lambda:self.__scooter.speed)
        delay_since_min_speed = DelaySinceValueCondition(0.5/3.6, lambda:self.__scooter.speed, 5.5)

        #Transitions
        power_off_state.add_transition(ConditionalTransition(plugged_in_condition, charging_state))
        power_off_state.add_transition(ConditionalTransition(AllConditions([ActualKeyPressCondition(console, "p"), plugged_out_condition]), unlocking_state))
        charging_state.add_transition(ConditionalTransition(ReaderCondition(False, lambda:self.__plugged_in), power_off_state)) 
        #À vérifier si ya meilleure solution
        charging_state.add_transition(ConditionalTransition(ReaderCondition(True, lambda:charging_state.charging_error), charging_failed_state)) 
        charging_failed_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, charging_failed_state), powering_down_state)) 
        unlocking_state.add_transition(ConditionalTransition(ActualKeyReleasedCondition(console, "p"), power_off_state))
        unlocking_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, unlocking_state), powering_up_state))
        powering_up_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, powering_up_state), idle_state))
        powering_up_state.add_transition(ConditionalTransition(KeyPressCondition(console, "f"), intygrity_failed_state))
        intygrity_failed_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, intygrity_failed_state), powering_down_state))
        idle_state.add_transition(ConditionalTransition(ActualKeyPressCondition(console, "p"), locking_state))
        idle_state.add_transition(ConditionalTransition(AnyConditions([DelaySinceEnteredCondition(30.0, idle_state), ]), powering_down_state))
        idle_state.add_transition(ConditionalTransition(power_less_than_condition, powering_down_state))
        idle_state.add_transition(ConditionalTransition(KeyPressCondition(console, "a"), scooting_state))
        scooting_state.add_transition(ConditionalTransition(AllConditions([AllConditions([ActualKeyReleasedCondition(console, "a"), delay_since_min_speed]) ,AnyConditions([power_less_than_condition, speed_less_than_condition])]), idle_state)) 
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