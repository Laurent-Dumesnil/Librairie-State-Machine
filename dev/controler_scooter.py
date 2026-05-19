from typing import override, Self, Callable, TypeAlias
from state_machine_device import StateMachineDevice
from state_machine_utilities import MonitoredState, ActionState, State, DelaySinceEnteredCondition, ConditionalTransition
from condition import Condition, ReaderCondition, AllConditions, AnyConditions, AbstractValueCondition, ElapsedTimerCondition
from tracking_device import TrackingApplication
from blinker_device_julien import BlinkerDevice
from console_reader import ConsoleReader
from console import Console
from scooter import Scooter
from electric_scooter_panel import ElectricScooterPanel
from elapsed_timer import ElapsedTimer

Number: TypeAlias = int | float
KeyboardValue: TypeAlias = str | Console.SpecialKey

class Scooting(MonitoredState):
    class RideManagement(StateMachineDevice):
        def __init__(self:Self, console_reader:ConsoleReader, scooter:Scooter, initialized:bool = False, name:str = None, enabled:bool = False) -> None:
            self.__elapsed_time = 0.0
            self.__scooter = scooter
            self.__console_reader = console_reader
            self.__free_wheel_state = ActionState("Free Wheel")
            self.__accelerating_state = ActionState("Accelerating")
            self.__breaking_state = ActionState("Breaking")
            self.__end_state = State("Ending State", terminal=True)
            #self.__cruise_control_state = ActionState("Cruise Control")

            ########################################
            #               TRANSITIONS
            ########################################
            self.__free_wheel_state.add_transition(ConditionalTransition(KeyPressCondition(Console.SpecialKey.UP_ARROW, lambda:self.__console_reader.actual_key_pressed),self.__accelerating_state))
            self.__accelerating_state.add_transition(ConditionalTransition(KeyPressCondition(Console.SpecialKey.UP_ARROW, lambda:self.__console_reader.actual_key_pressed, invert=True), self.__free_wheel_state))
            self.__free_wheel_state.add_transition(ConditionalTransition(KeyPressCondition(Console.SpecialKey.DOWN_ARROW, lambda:self.__console_reader.actual_key_pressed),self.__breaking_state))
            self.__breaking_state.add_transition(ConditionalTransition(KeyPressCondition(Console.SpecialKey.DOWN_ARROW, lambda:self.__console_reader.actual_key_pressed, invert=True), self.__free_wheel_state))
            self.__accelerating_state.add_transition(ConditionalTransition(KeyPressCondition(Console.SpecialKey.DOWN_ARROW, lambda:self.__console_reader.actual_key_pressed),self.__breaking_state))
            
            #######################################
            #           CRUISE CONTROL
            #######################################
            #self.__free_wheel_state.add_transition(ConditionalTransition(KeyPressCondition("c", lambda:self.__console_reader.actual_key_pressed), self.__cruise_control_state))
            #self.__cruise_control_state.add_transition(ConditionalTransition(ReaderCondition(Console.SpecialKey.LEFT_ARROW, lambda:self.__console_reader.actual_key_pressed),self.__accelerating_state))
            #self.__cruise_control_state.add_transition(ConditionalTransition(KeyPressCondition(Console.SpecialKey.LEFT_ARROW, lambda:self.__console_reader.actual_key_pressed),self.__breaking_state))

            ##########################################
            #               ACTIONS
            ##########################################
            self.__accelerating_state.add_in_state_action(self.__accelerate)
            self.__free_wheel_state.add_in_state_action(self._in_free_wheel)
            self.__breaking_state.add_in_state_action(self.__breaking)
            #self.__cruise_control_state.add_in_state_action(self.__cruise)

            layout = self.Layout((self.__free_wheel_state, self.__accelerating_state, self.__breaking_state, self.__end_state))
            super().__init__(layout, initialized, name, enabled)
        
        @property
        def elapsed_time(self):
            return self.__elapsed_time
        
        @elapsed_time.setter
        def elapsed_time(self, value):
            self.__elapsed_time = value

        def __accelerate(self:Self) -> None:
            #print(f'\rACCELERATE{self.__scooter.speed}  KEY_PRESSED: {self.__console_reader.actual_key_pressed}', end="                        ")
            self.__scooter.accelerate(lambda:self.elapsed_time)
            self.__scooter.battery.set_power_device_accelerating(lambda:self.elapsed_time)
            self.__scooter.speed_indicator.colorize(self.__scooter.speed_percent)

        def __breaking(self:Self) -> None:
            #print(f'\rDECELERATE{self.__scooter.speed}  KEY_PRESSED: {self.__console_reader.actual_key_pressed}', end="                        ")
            self.__scooter.decelerate(lambda:self.elapsed_time, 0.5)
            self.__scooter.battery.set_power_device_breaking(lambda:self.elapsed_time, lambda:self.__scooter.speed)
            self.__scooter.speed_indicator.colorize(self.__scooter.speed_percent)

        def __cruise(self:Self) -> None:
            print("CRUISE")
            self.__scooter.battery.set_power_based_usage(lambda:self.__elapsed_time)

        def _in_free_wheel(self):
            #print(f'\rFREE WHEEL{self.__scooter.speed} KEY_PRESSED: {self.__console_reader.actual_key_pressed}', end="                          ")
            self.__scooter.decelerate(lambda:self.elapsed_time, 0.0)
            self.__scooter.battery.set_power_based_usage(lambda:self.elapsed_time)
            self.__scooter.speed_indicator.colorize(self.__scooter.speed_percent)

        def start(self: Self) -> None:
            self.enabled = True
            self._transit_to(self.__free_wheel_state)

        def stop(self:Self):
            self._transit_to(self.__end_state)
            self.enabled = False

        @override
        def _do_tracking(self, elapsed_time):
            super()._do_tracking(elapsed_time)
            self.__elapsed_time = elapsed_time

    def __init__(self, name, ridemanagement: RideManagement):
        self.__ridemanagement = ridemanagement
        super().__init__(name)
    
    @override
    def _do_entering_action(self) -> None:
        print("SCOOTING")
        self.__ridemanagement.start()

    @override
    def _do_exiting_action(self) -> None:
        self.__ridemanagement.stop()

class Charging(MonitoredState):
    class BatteryManagement(StateMachineDevice):
        def __init__(self:Self, console_reader:ConsoleReader, scooter:Scooter, initialized:bool = False, name:str | None = None, enabled:bool = True) -> None:
            self.__delta_time = 0.0
            self.__battery = scooter.battery
            self.__console_reader = console_reader
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

    def __init__(self:Self, name:str, console, model):
        #self.__battery_management = self.BatteryManagement(console, model, initialized=False)
        super().__init__(name)

    @property
    def charging_error(self:Self) -> bool:
        return self.__battery_management.current_state.terminal
    
    @override
    def _do_entering_action(self) -> None:
        #print("CHARGING")
        self.__battery_management.reset()
        self.__battery_management.enabled = True

    @override
    def _do_exiting_action(self) -> None:
        if not self.charging_error:
            self.__battery_management._transit_to(self.__battery_management.charging_off)

class DelaySinceBelowThresholdCondition(ReaderCondition[Number]):
    """
    Initialise la DelaySinceValueCondition.
    Condition qui devient vraie un certain temps après avoir atteint une certaine valeur

        Args:
            expected_value: La valeur attendue.
            value_reader: Un callable qui retourne la valeur réelle.
            duration: Le temps en seconde depuis qu'on a atteint la expected_value
            invert: Si True, la condition est inversée.
    """
    def __init__(self:Self, threshold:Number, value_reader:Callable[[], Number], duration:float, invert:bool=False):
        self.__duration:Number
        self.duration = duration
        self.__elapsed_timer = ElapsedTimer(ElapsedTimer.Mode.ACCUMULATED)
        self.__enabled = False
        super().__init__(expected_value=threshold, value_reader=value_reader, invert=invert)

    @property
    def duration(self:Self) -> float:
        return self.__duration
    
    @duration.setter
    def duration(self, value):
        if not isinstance(value, float):
            raise TypeError("Must be float type")
        if value < 0:
            raise ValueError("Duration must be positive")
        self.__duration = value

    @override
    def _compare(self) -> bool:
        actual_value = self.value_reader()
        if actual_value > self.expected_value:
            self.__enabled = False
            return False

        elif actual_value <= self.expected_value and not self.__enabled:
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

class LessThanValueCondition(ReaderCondition[Number]):
    def __init__(self:Self, target_value:Number, value_reader:Callable[[], Number], invert:bool=False):
        """
        Condition qui retourne True quand une valeur dynamique est plus petite que la target_value
        Args:
            target_value: La valeur sous laquelle on veut se retrouver quand on va comparer avec la actual_value.
            value_reader: Callable qui retourne un float ou un int.
            invert: Si True, la condition est inversée.
        """
        if not isinstance(target_value, int | float) or isinstance(target_value, bool):
            raise TypeError("target_value must be int or float")
        super().__init__(expected_value=target_value, value_reader=value_reader, invert=invert)

    @override
    def _compare(self) -> bool:
        return self.value_reader() < self.expected_value

class KeyPressCondition(AbstractValueCondition[KeyboardValue]):
    """
        Condition qui retourne True quand une touche appuyé au clavier correspond à la touche voulu
        Args:
            expected_key_value: La touche du clavier que l'on s'attend à avoir de type string.
            key_reader: Callable qui retourne une liste de touche appuyé au clavier.
            invert: Si True, la condition est inversée donc vérifie si expected_key_value n'est pas dans le key_reader.
        """
    def __init__(self:Self, expected_key_value: KeyboardValue, key_reader:Callable[[], list[KeyboardValue]], invert:bool=False):
        if not isinstance(expected_key_value, KeyboardValue):
            raise TypeError("Must be str or Console.SpecialKey type")
        super().__init__(expected_value=expected_key_value, invert=invert)
        self.__key_reader: Callable[[], list[KeyboardValue]]
        self.key_reader = key_reader

    @property
    def key_reader(self):
        return self.__key_reader
    
    @key_reader.setter
    def key_reader(self, value):
        if not callable(value):
            raise TypeError("key_reader must be callable")
        self.__key_reader = value

    @override
    def _compare(self):
        return self.expected_value in self.key_reader()

class ScooterStateMachine(StateMachineDevice):
    def __init__(self: Self, console_reader:ConsoleReader, model:Scooter):
        self.__console_reader = console_reader
        self.__scooter = model
        self.__plugged_in = False
        self.__ridemanagement = Scooting.RideManagement(self.__console_reader, self.__scooter, initialized=False, enabled=False)
        
        #############################################
        #               LIGHTS FACTORY
        #############################################
        def make_off_state():
            def light_off():
                self.__scooter.headlight.colorize()
            off_state = MonitoredState("off_state")
            off_state.add_entering_action(light_off)
            return off_state
        
        def make_on_state():
            def light_on():
                self.__scooter.headlight.colorize(Console.Color.GREY)
            on_state = MonitoredState("on_state")
            on_state.add_entering_action(light_on)
            return on_state
        
        self.__front_light = BlinkerDevice(make_off_state, make_on_state)

        #States
        power_off_state = ActionState("power_off")
        power_off_state.add_in_state_action(self._plug_charging_cable)
        unlocking_state = MonitoredState("unlocking")
        powering_up_state = MonitoredState("powerring_up")
        idle_state = MonitoredState("idle")
        locking_state = MonitoredState("locking")
        charging_failed_state = MonitoredState("charging_failed")
        powering_down_state = MonitoredState("powering_down")
        intygrity_failed_state = MonitoredState("intygrity_failed")
        charging_state = Charging("charging", self.__console_reader, self.__scooter)
        #charging_state.add_entering_action(self._on_charging)
        #charging_state.add_in_state_action(self._unplug_charging_cable)
        scooting_state = Scooting("scooting", self.__ridemanagement)

        # #Conditions
        plugged_in_condition = ReaderCondition(True, lambda:self.plugged_in)
        plugged_out_condition = ReaderCondition(False, lambda:self.plugged_in)
        power_less_than_condition = LessThanValueCondition(0.03, lambda:self.__scooter.battery.energy_level)
        speed_less_than_condition = LessThanValueCondition(0.5/3.6, lambda:self.__scooter.speed)
        delay_since_min_speed = DelaySinceBelowThresholdCondition(0.5/3.6, lambda:self.__scooter.speed, 30.0)

        # #Transitions
        power_off_state.add_transition(ConditionalTransition(plugged_in_condition, charging_state))
        power_off_state.add_transition(ConditionalTransition(AllConditions([KeyPressCondition("p", lambda:self.__console_reader.actual_key_pressed), plugged_out_condition]), unlocking_state))
        charging_state.add_transition(ConditionalTransition(ReaderCondition(False, lambda:self.plugged_in), power_off_state)) 
        #À vérifier si ya meilleure solution
        charging_state.add_transition(ConditionalTransition(ReaderCondition(True, lambda:charging_state.charging_error), charging_failed_state)) 
        charging_failed_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, charging_failed_state), powering_down_state)) 
        unlocking_state.add_transition(ConditionalTransition(KeyPressCondition("p", lambda:self.__console_reader.actual_key_pressed, invert=True), power_off_state))
        unlocking_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, unlocking_state), powering_up_state))
        powering_up_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, powering_up_state), idle_state))
        powering_up_state.add_transition(ConditionalTransition(KeyPressCondition("f", lambda:self.__console_reader.key_pressed), intygrity_failed_state))
        intygrity_failed_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, intygrity_failed_state), powering_down_state))
        idle_state.add_transition(ConditionalTransition(KeyPressCondition("p", lambda:self.__console_reader.key_pressed), locking_state))
        idle_state.add_transition(ConditionalTransition(AnyConditions([DelaySinceEnteredCondition(30.0, idle_state), ]), powering_down_state))
        idle_state.add_transition(ConditionalTransition(power_less_than_condition, powering_down_state))
        idle_state.add_transition(ConditionalTransition(KeyPressCondition("a", lambda:self.__console_reader.key_pressed), scooting_state))
        #scooting_state.add_transition(ConditionalTransition(AllConditions([AllConditions([KeyPressCondition("a", lambda:self.key_pressed, invert=True), delay_since_min_speed]) ,AnyConditions([power_less_than_condition, speed_less_than_condition])]), idle_state))
        scooting_state.add_transition(ConditionalTransition(delay_since_min_speed, idle_state))
        locking_state.add_transition(ConditionalTransition(KeyPressCondition("p", lambda:self.__console_reader.actual_key_pressed, invert=True), idle_state)) 
        locking_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, locking_state), powering_down_state)) 
        powering_down_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, powering_down_state), power_off_state))

        # #Actions
        #power_off_state.add_entering_action(self._on_power_off)
        #power_off_state.add_exiting_action(self._exit_power_off)
        #unlocking_state.add_entering_action(self._on_unlocking)
        #powering_up_state.add_entering_action(self._on_powering_up)
        #powering_down_state.add_entering_action(self._on_powering_down)
        #idle_state.add_entering_action(self._on_idle)
        #intygrity_failed_state.add_entering_action(self._on_integrity_failed)
        #locking_state.add_entering_action(self._on_locking)
        #charging_failed_state.add_entering_action(self._on_charing_failed)

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
        
        super().__init__(StateMachineDevice.Layout(layout), initialized=True)
        self.add_sub_device(self.__console_reader)
        self.add_sub_device(self.__ridemanagement)
        self.add_sub_device(self.__front_light)
    
    @property
    def plugged_in(self):
        return self.__plugged_in
    
    @plugged_in.setter
    def plugged_in(self, value):
        if isinstance(value, bool):
            self.__plugged_in = value

    def _on_power_off(self):
        print("POWER OFF")
        self.__front_light.blink(cycle_duration=5.0, percent_on=0.5, begin_on=True)
        #self.__front_light.turn_off()
    def _exit_power_off(self):
        self.__front_light.enabled = False
    def _on_unlocking(self):
        print("UNLOCKING")
    def _on_powering_up(self):
        print("POWERING UP")
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
        if "i" in self.__console_reader.actual_key_pressed:
            self.__plugged_in = True

    def _unplug_charging_cable(self):
        if "o" in self.__console_reader.actual_key_pressed:
            self.__plugged_in = False

def main():
    app = TrackingApplication()
    console = Console()
    console.cursor_visible = False
    console_reader = ConsoleReader("console_reader", console)
    panel = ElectricScooterPanel(console)
    model = Scooter(panel)
   
    controler = ScooterStateMachine(console_reader, model)

    app.add_device(controler)
    app.add_device(console_reader)
    app.run_forever()

if __name__ == "__main__":
    main()