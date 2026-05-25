from typing import override, Self, Callable, TypeAlias
from state_machine_device import StateMachineDevice
from state_machine_utilities import MonitoredState, ActionState, State, DelaySinceEnteredCondition, ConditionalTransition, ActionTransition
from condition import Condition, ReaderCondition, AllConditions, AnyConditions, AbstractValueCondition, ElapsedTimerCondition
from tracking_device import TrackingApplication
from blinker_device import BlinkerDevice, SideBlinkersDevice
#from blinker_device_julien import BlinkerDevice, SideBlinkersDevice
from console_reader import ConsoleReader
from console import Console
from scooter import Scooter, Light, BarLight
from electric_scooter_panel import ElectricScooterPanel
from elapsed_timer import ElapsedTimer
from functools import partial

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
            self.__cruise_control_state = ActionState("Cruise Control")

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
            self.__free_wheel_state.add_transition(ConditionalTransition(KeyPressCondition("c", lambda:self.__console_reader.actual_key_pressed), self.__cruise_control_state))
            self.__cruise_control_state.add_transition(ConditionalTransition(KeyPressCondition(Console.SpecialKey.UP_ARROW, lambda:self.__console_reader.actual_key_pressed),self.__accelerating_state))
            self.__cruise_control_state.add_transition(ConditionalTransition(KeyPressCondition(Console.SpecialKey.DOWN_ARROW, lambda:self.__console_reader.actual_key_pressed),self.__breaking_state))

            ##########################################
            #               IN ACTIONS
            ##########################################
            self.__accelerating_state.add_in_state_action(self.__in_accelerate)
            self.__free_wheel_state.add_in_state_action(self.__in_free_wheel)
            self.__breaking_state.add_in_state_action(self.__in_breaking)
            self.__cruise_control_state.add_in_state_action(self.__in_cruise)

            ##########################################
            #          ENTER/EXIT ACTIONS
            ##########################################
            self.__breaking_state.add_entering_action(self.__enter_breaking)
            self.__breaking_state.add_exiting_action(self.__exit_breaking)
            self.__cruise_control_state.add_entering_action(self.__enter_cruise)
            self.__cruise_control_state.add_exiting_action(self.__exit_cruise)

            layout = self.Layout((self.__free_wheel_state, self.__accelerating_state, self.__breaking_state, self.__end_state))
            super().__init__(layout, initialized, name, enabled)
        
        @property
        def elapsed_time(self):
            return self.__elapsed_time

        def __in_accelerate(self:Self) -> None:
            #print(f'\rACCELERATE{self.__scooter.speed}  KEY_PRESSED: {self.__console_reader.actual_key_pressed}', end="                        ")
            self.__scooter.accelerate(self.elapsed_time)
            self.__scooter.battery.set_power_device_accelerating(self.elapsed_time)
            self.__scooter.speed_indicator.percent_on = self.__scooter.speed_percent
            self.__scooter.charge_indicator.percent_on = self.__scooter.battery.energy_level_percent
            self.__scooter.temp_indicator.percent_on = self.__scooter.battery.temp_percent
            self.__scooter.speed_indicator.colorize()
            self.__scooter.charge_indicator.colorize()
            self.__scooter.temp_indicator.colorize()

        def __in_breaking(self:Self) -> None:
            #print(f'\rDECELERATE{self.__scooter.speed}  KEY_PRESSED: {self.__console_reader.actual_key_pressed}', end="                        ")
            self.__scooter.decelerate(lambda:self.elapsed_time, 0.5)
            self.__scooter.battery.set_power_device_breaking(lambda:self.elapsed_time, self.__scooter.speed)
            self.__scooter.speed_indicator.percent_on = self.__scooter.speed_percent
            self.__scooter.charge_indicator.percent_on = self.__scooter.battery.energy_level_percent
            self.__scooter.temp_indicator.percent_on = self.__scooter.battery.temp_percent
            self.__scooter.speed_indicator.colorize()
            self.__scooter.charge_indicator.colorize()
            self.__scooter.temp_indicator.colorize()

        def __in_cruise(self:Self) -> None:
            self.__scooter.battery.set_power_based_usage(lambda:self.__elapsed_time)
            self.__scooter.charge_indicator.percent_on = self.__scooter.battery.energy_level_percent
            self.__scooter.temp_indicator.percent_on = self.__scooter.battery.temp_percent
            self.__scooter.speed_indicator.colorize()
            self.__scooter.charge_indicator.colorize()
            self.__scooter.temp_indicator.colorize()

        def __in_free_wheel(self):
            #print(f'\rFREE WHEEL{self.__scooter.speed} KEY_PRESSED: {self.__console_reader.actual_key_pressed}', end="                          ")
            self.__scooter.decelerate(lambda:self.elapsed_time, 0.0)
            self.__scooter.battery.set_power_based_usage(lambda:self.elapsed_time)
            self.__scooter.speed_indicator.percent_on = self.__scooter.speed_percent
            self.__scooter.charge_indicator.percent_on = self.__scooter.battery.energy_level_percent
            self.__scooter.temp_indicator.percent_on = self.__scooter.battery.temp_percent
            self.__scooter.speed_indicator.colorize()
            self.__scooter.charge_indicator.colorize()
            self.__scooter.temp_indicator.colorize()

        def __enter_breaking(self:Self) -> None:
            self.__scooter.rearlight.color = Console.Color.LIGHT_RED
            self.__scooter.rearlight.colorize()

        def __exit_breaking(self:Self) -> None:
            self.__scooter.rearlight.color = Console.Color.RED
            self.__scooter.rearlight.colorize()

        def __enter_cruise(self:Self) -> None:
            self.__scooter.right_indicator.color = Console.Color.LIGHT_YELLOW
            self.__scooter.right_indicator.colorize()

        def __exit_cruise(self:Self) -> None:
            self.__scooter.right_indicator.off_color = Console.Color.DARK_GREY
            self.__scooter.right_indicator.close()

        def start(self: Self) -> None:
            self.__scooter.rearlight.color = Console.Color.RED
            self.enabled = True
            self._transit_to(self.__free_wheel_state)

        def stop(self:Self):
            self.__scooter.rearlight.close()
            self.__scooter.charge_indicator.close()
            self.__scooter.temp_indicator.close()
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
    def _do_entering_action(self:Self) -> None:
        super()._do_entering_action()
        self.__ridemanagement.start()

    @override
    def _do_exiting_action(self:Self) -> None:
        self.__ridemanagement.stop()

class Charging(MonitoredState):
    class BatteryManagement(StateMachineDevice):
        def __init__(self:Self, console_reader:ConsoleReader, scooter:Scooter, initialized:bool = False, name:str | None = None, enabled:bool = True) -> None:
            self.__delta_time = 0.0
            self.__scooter = scooter
            self.__battery = scooter.battery
            self.__console_reader = console_reader
            self.__charging_terminated = ActionState("Charging Terminated", terminal=True)
            self.__charging_complete = ActionState("Charging Complete")
            self.__charging_on = ActionState("Charging On")
            self.__charging_off = ActionState("Charging Off")
            self.__cooling = ActionState("Cooling")

            self.__charging_on.add_transition(ConditionalTransition(ReaderCondition(True, lambda: self.__battery.energy_level >= 99), self.__charging_complete))
            self.__charging_on.add_transition(ConditionalTransition(ReaderCondition(True, lambda: self.__battery.temperature > 85), self.__cooling))
            self.__charging_on.add_transition(ConditionalTransition(KeyPressCondition("f", lambda:self.__console_reader.key_pressed), self.__charging_terminated))
            self.__charging_complete.add_transition(ConditionalTransition(KeyPressCondition("f", lambda:self.__console_reader.key_pressed), self.__charging_terminated))
            self.__cooling.add_transition(ConditionalTransition(KeyPressCondition("f", lambda:self.__console_reader.key_pressed), self.__charging_terminated))
            self.__charging_complete.add_transition(ConditionalTransition(ReaderCondition(True, lambda:self.__battery.energy_level < 95), self.__charging_on))
            self.__cooling.add_transition(ConditionalTransition(ReaderCondition(True, lambda: self.__battery.temperature < 75), self.__charging_on))

            self.__charging_on.add_in_state_action(self.__charging)
            self.__charging_complete.add_in_state_action(self.__discharging)
            self.__cooling.add_in_state_action(self.__discharging)
                
            layout = self.Layout((self.__charging_on, self.__charging_complete, self.__cooling, self.__charging_terminated))
            super().__init__(layout, initialized, name, enabled)
            
            # if initialized : 
            #     self.reset()

        @property
        def charging_off(self:Self) -> ActionState:
            return self.__charging_off
        
        def __charging(self:Self) -> None:
            self.__battery.set_power_device_charging(self.__delta_time)
            print("f")
            self.__scooter.charge_indicator.percent_on = self.__scooter.battery.energy_level_percent
            self.__scooter.temp_indicator.percent_on = self.__scooter.battery.temp_percent

        def __discharging(self:Self) -> None:
            self.__battery.set_power_based_usage(self.__delta_time)
            self.__scooter.charge_indicator.percent_on = self.__scooter.battery.energy_level_percent
            self.__scooter.temp_indicator.percent_on = self.__scooter.battery.temp_percent

        @override
        def _do_tracking(self:Self, elapsed_time: float) -> None:
            super()._do_tracking(elapsed_time) 
            self.__delta_time = elapsed_time
        
        # def start(self:Self) -> None:
        #     self.reset()
        #     self.enabled = True
        #     self._transit_to(self.__charging_on)

        # def stop(self:Self) -> None:
        #     self.enabled = False
        #     self._transit_to(self.__charging_off)
        @override
        def _enabling(self):
            self.reset()
            self._transit_to(self.__charging_on)

        @override
        def _disabling(self):
            if not self.current_state.terminal:
                self._transit_to(self.__charging_off)
        
    def __init__(self:Self, name:str, console_reader:ConsoleReader, scooter:Scooter) -> None:
        self.__battery_management = Charging.BatteryManagement(console_reader, scooter, initialized=True, enabled=False)
        super().__init__(name)

    @property
    def charging_error(self:Self) -> bool:
        return self.__battery_management.current_state.terminal
    
    @override
    def _do_entering_action(self:Self) -> None:
        super()._do_entering_action()
        # self.__battery_management.start()
        self.__battery_management.enabled = True

    @override
    def _do_exiting_action(self:Self) -> None:
        super()._do_exiting_action()
        # self.__battery_management.stop()
        self.__battery_management.disabled = True

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
    


#############################################
#               LIGHTS FACTORY
#############################################
def make_off_state(light:Light|BarLight) -> MonitoredState:
    def light_off():
        light.close()
    off_state = MonitoredState("off_state")
    off_state.add_entering_action(light_off)
    return off_state

def make_on_state(light:Light|BarLight) -> MonitoredState:
    def light_on():
        light.colorize()
    on_state = MonitoredState("on_state")
    on_state.add_entering_action(light_on)
    return on_state

class ScooterStateMachine(StateMachineDevice):
    def __init__(self: Self, console_reader:ConsoleReader, model:Scooter):
        self.__console_reader = console_reader
        self.__scooter = model
        self.__plugged_in = False
        self.__ridemanagement = Scooting.RideManagement(self.__console_reader, self.__scooter, initialized=False, enabled=False)
        # self.__batterymanagement = Charging.BatteryManagement(self.__console_reader, self.__scooter, initialized=False, enabled=False)
        
        self.__left_blinker_on = False
        self.__right_blinker_on = False
        self.__headlight_on = False
        self.__left_arrow_consumed = False
        self.__spacebar_consumed = False
        self.__right_arrow_consumed = False

        self.__power_off_context = ""
        
        #Blinkers
        self.__headlight = BlinkerDevice(partial(make_off_state, self.__scooter.headlight), partial(make_on_state,self.__scooter.headlight))
        self.__charge_indicator = BlinkerDevice(partial(make_off_state, self.__scooter.charge_indicator), partial(make_on_state,self.__scooter.charge_indicator))
        self.__temp_indicator = BlinkerDevice(partial(make_off_state, self.__scooter.temp_indicator), partial(make_on_state,self.__scooter.temp_indicator))
        self.__left_blinkers = SideBlinkersDevice(partial(make_off_state, self.__scooter.top_left_blinker), 
                                            partial(make_on_state,self.__scooter.top_left_blinker),
                                            partial(make_off_state, self.__scooter.bottom_left_blinker), 
                                            partial(make_on_state,self.__scooter.bottom_left_blinker))
        self.__right_blinkers = SideBlinkersDevice(partial(make_off_state, self.__scooter.top_right_blinker), 
                                            partial(make_on_state,self.__scooter.top_right_blinker),
                                            partial(make_off_state, self.__scooter.bottom_right_blinker), 
                                            partial(make_on_state,self.__scooter.bottom_right_blinker))
        self.__left_side_light = BlinkerDevice(partial(make_off_state, self.__scooter.left_side_light), partial(make_on_state,self.__scooter.left_side_light))
        self.__right_side_light = BlinkerDevice(partial(make_off_state, self.__scooter.right_side_light), partial(make_on_state,self.__scooter.right_side_light))
        self.__rearlight = BlinkerDevice(partial(make_off_state, self.__scooter.rearlight), partial(make_on_state,self.__scooter.rearlight))
        self.__left_indicator = BlinkerDevice(partial(make_off_state, self.__scooter.left_indicator), partial(make_on_state,self.__scooter.left_indicator))
        self.__right_indicator = BlinkerDevice(partial(make_off_state, self.__scooter.right_indicator), partial(make_on_state,self.__scooter.right_indicator))

        #States
        power_off_state = ActionState("power_off")
        unlocking_state = MonitoredState("unlocking")
        powering_up_state = MonitoredState("powerring_up")
        idle_state = MonitoredState("idle", do_in_state_action_when_entering = False)
        locking_state = MonitoredState("locking")
        charging_failed_state = MonitoredState("charging_failed")
        powering_down_state = MonitoredState("powering_down")
        integrity_failed_state = MonitoredState("integrity_failed")
        charging_state = Charging("charging",self.__console_reader, self.__scooter)
        charging_state.add_in_state_action(self._unplug_charging_cable)
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
        charging_error_transition = ActionTransition(DelaySinceEnteredCondition(3.0, charging_failed_state), powering_down_state)
        charging_error_transition.add_transiting_action(partial(self.set_power_off_context, "ChargingError"))
        charging_failed_state.add_transition(charging_error_transition) 
        unlocking_state.add_transition(ConditionalTransition(KeyPressCondition("p", lambda:self.__console_reader.actual_key_pressed, invert=True), power_off_state))
        unlocking_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, unlocking_state), powering_up_state))
        powering_up_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, powering_up_state), idle_state))
        powering_up_state.add_transition(ConditionalTransition(KeyPressCondition("f", lambda:self.__console_reader.key_pressed), integrity_failed_state))
        integrity_failed_transition = ActionTransition(DelaySinceEnteredCondition(3.0, integrity_failed_state), powering_down_state)
        integrity_failed_transition.add_transiting_action(partial(self.set_power_off_context, "IntegrityFailed"))
        integrity_failed_state.add_transition(integrity_failed_transition)
        idle_state.add_transition(ConditionalTransition(KeyPressCondition("p", lambda:self.__console_reader.key_pressed), locking_state))
        idle_state.add_transition(ConditionalTransition(AnyConditions([DelaySinceEnteredCondition(30.0, idle_state), ]), powering_down_state))
        no_power_transition = ActionTransition(power_less_than_condition, powering_down_state)
        no_power_transition.add_transiting_action(partial(self.set_power_off_context, "NoPower"))
        idle_state.add_transition(no_power_transition)
        idle_state.add_transition(ConditionalTransition(KeyPressCondition("a", lambda:self.__console_reader.key_pressed), scooting_state))
        #scooting_state.add_transition(ConditionalTransition(AllConditions([AllConditions([KeyPressCondition("a", lambda:self.key_pressed, invert=True), delay_since_min_speed]) ,AnyConditions([power_less_than_condition, speed_less_than_condition])]), idle_state))
        scooting_state.add_transition(ConditionalTransition(delay_since_min_speed, idle_state))
        locking_state.add_transition(ConditionalTransition(KeyPressCondition("p", lambda:self.__console_reader.actual_key_pressed, invert=True), idle_state)) 
        locking_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, locking_state), powering_down_state)) 
        powering_down_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(3.0, powering_down_state), power_off_state))

        #Entering Actions
        power_off_state.add_in_state_action(self._plug_charging_cable)
        power_off_state.add_entering_action(self._on_power_off)
        unlocking_state.add_entering_action(self._on_unlocking)
        powering_up_state.add_entering_action(self._on_powering_up)
        powering_down_state.add_entering_action(self._on_powering_down)
        idle_state.add_entering_action(self._on_idle)
        integrity_failed_state.add_entering_action(self._on_integrity_failed)
        locking_state.add_entering_action(self._on_locking)
        charging_failed_state.add_entering_action(self._on_charging_failed)
        scooting_state.add_entering_action(self._on_scooting)
        charging_state.add_entering_action(self._on_charging)
        
        #Exiting Actions
        power_off_state.add_exiting_action(self._off_power_off)
        charging_state.add_exiting_action(self._off_charging)

        #Light Actions
        idle_state.add_in_state_action(partial(self._toggle_left_blinkers, SideBlinkersDevice.Side.LEFT_RECIPROCAL))
        idle_state.add_in_state_action(partial(self._toggle_right_blinkers, SideBlinkersDevice.Side.RIGHT_RECIPROCAL))
        idle_state.add_in_state_action(self._in_idle)
        scooting_state.add_in_state_action(self._toggle_left_blinkers)
        scooting_state.add_in_state_action(self._toggle_right_blinkers)
        power_off_state.add_in_state_action(self._toggle_headlight)
        charging_state.add_in_state_action(self._toggle_headlight)
        idle_state.add_in_state_action(self._toggle_headlight)
        scooting_state.add_in_state_action(self._toggle_headlight)

        layout = (power_off_state, 
                  unlocking_state, 
                  powering_up_state, 
                  idle_state, locking_state, 
                  charging_failed_state, 
                  powering_down_state, 
                  integrity_failed_state, 
                  charging_state, 
                  scooting_state
                )
        
        super().__init__(StateMachineDevice.Layout(layout), initialized=True)
        self.add_sub_device(self.__console_reader)
        self.add_sub_device(self.__ridemanagement)
        # self.add_sub_device(self.__batterymanagement)
        self.add_sub_device(self.__headlight)
        self.add_sub_device(self.__charge_indicator)
        self.add_sub_device(self.__temp_indicator)
        self.add_sub_device(self.__left_blinkers)
        self.add_sub_device(self.__right_blinkers)
        self.add_sub_device(self.__left_side_light)
        self.add_sub_device(self.__right_side_light)
        self.add_sub_device(self.__rearlight)
        self.add_sub_device(self.__left_indicator)
        self.add_sub_device(self.__right_indicator)
    
    @property
    def plugged_in(self:Self) -> bool:
        return self.__plugged_in
    
    @plugged_in.setter
    def plugged_in(self:Self, value:bool) -> None:
        if isinstance(value, bool):
            self.__plugged_in = value

    @property
    def power_off_context(self:Self) -> str:
        return self.__power_off_context
    
    @power_off_context.setter
    def power_off_context(self:Self, context:str) -> None:
        self.__power_off_context = context

    def set_power_off_context(self:Self, context:str) -> None:
        self.power_off_context = context

    def _on_power_off(self:Self) -> None:
        self.__scooter.left_side_light.off_color = Console.Color.DARK_GREY
        self.__scooter.right_side_light.off_color = Console.Color.DARK_GREY
        self.__scooter.rearlight.off_color = Console.Color.DARK_GREY
        self.__scooter.left_indicator.off_color = Console.Color.DARK_GREY
        self.__scooter.right_indicator.off_color = Console.Color.DARK_GREY
        self.__left_blinkers.turn_off(SideBlinkersDevice.Side.BOTH)
        self.__right_blinkers.turn_off(SideBlinkersDevice.Side.BOTH)
        self.__rearlight.turn_off()
        self.__charge_indicator.turn_off()
        self.__temp_indicator.turn_off()
        self.__left_indicator.turn_off()
        self.__right_indicator.turn_off()
        self.__right_side_light.turn_off()
        self.__left_side_light.turn_off()

    def _off_power_off(self:Self) -> None:
        self.__scooter.left_side_light.color = Console.Color.BLUE
        self.__scooter.left_side_light.off_color = Console.Color.LIGHT_BLUE
        self.__scooter.right_side_light.color = Console.Color.BLUE
        self.__scooter.right_side_light.off_color = Console.Color.LIGHT_BLUE

    def _on_unlocking(self:Self) -> None:
        self.__left_side_light.blink(cycle_duration = 0.5, percent_on = 0.5, begin_on = True)
        self.__right_side_light.blink(cycle_duration = 0.5, percent_on = 0.5, begin_on = False)
        self.__scooter.left_indicator.color = Console.Color.MAGENTA
        self.__scooter.right_indicator.color = Console.Color.MAGENTA
        self.__scooter.left_indicator.off_color = Console.Color.LIGHT_BLUE
        self.__scooter.right_indicator.off_color = Console.Color.LIGHT_BLUE
        self.__left_indicator.blink(cycle_duration = 0.5, percent_on = 0.75, begin_on = True)
        self.__right_indicator.blink(cycle_duration = 0.5, percent_on = 0.75, begin_on = True)

    def _on_powering_up(self:Self) -> None:
        self.__left_side_light.blink(cycle_duration = 0.75, percent_on = 0.75, begin_on = True)
        self.__right_side_light.blink(cycle_duration = 0.75, percent_on = 0.75, begin_on = True)
        self.__scooter.left_indicator.color = Console.Color.LIGHT_BLUE
        self.__scooter.right_indicator.color = Console.Color.LIGHT_BLUE
        self.__scooter.left_indicator.off_color = Console.Color.LIGHT_GREEN
        self.__scooter.right_indicator.off_color = Console.Color.LIGHT_GREEN
        self.__left_indicator.blink(cycle_duration = 0.75, percent_on = 0.75, begin_on = True)
        self.__right_indicator.blink(cycle_duration = 0.75, percent_on = 0.75, begin_on = True)

    def _on_idle(self:Self) -> None:
        self.__rearlight.turn_on()
        self.__left_side_light.blink(cycle_duration = 2, percent_on = 0.75, begin_on = True)
        self.__right_side_light.blink(cycle_duration = 2, percent_on = 0.75, begin_on = True)
        self.__scooter.left_indicator.color = Console.Color.LIGHT_GREEN
        self.__left_indicator.turn_on()
        self.__scooter.charge_indicator.percent_on = self.__scooter.battery.energy_level_percent
        self.__scooter.temp_indicator.percent_on = self.__scooter.battery.temp_percent
        self.__charge_indicator.turn_on()
        self.__temp_indicator.turn_on()

    def _on_powering_down(self:Self) -> None:
        self.__headlight.turn_off()
        self.__left_blinkers.turn_off(SideBlinkersDevice.Side.BOTH)
        self.__right_blinkers.turn_off(SideBlinkersDevice.Side.BOTH)
        self.__rearlight.turn_off()
        self.__charge_indicator.turn_off()
        self.__temp_indicator.turn_off()
        self.__left_indicator.turn_off()
        self.__right_indicator.turn_off()
        self.__left_side_light.blink(cycle_duration = 0.5, percent_on = 0.25, begin_on = True)
        self.__right_side_light.blink(cycle_duration = 0.5, percent_on = 0.25, begin_on = True)
        if self.power_off_context == "IntegrityFailed":
            self.__scooter.left_indicator.color = Console.Color.LIGHT_RED
            self.__scooter.right_indicator.off_color = Console.Color.YELLOW
            self.__scooter.left_indicator.off_color = Console.Color.YELLOW
            self.__scooter.right_indicator.off_color = Console.Color.LIGHT_RED
        elif self.power_off_context == "ChargingError":
            self.__scooter.left_indicator.color = Console.Color.LIGHT_BLUE
            self.__scooter.right_indicator.off_color = Console.Color.LIGHT_RED
            self.__scooter.left_indicator.off_color = Console.Color.LIGHT_RED
            self.__scooter.right_indicator.off_color = Console.Color.LIGHT_BLUE
        elif self.power_off_context == "NoPower":
            self.__scooter.left_indicator.color = Console.Color.LIGHT_BLUE
            self.__scooter.right_indicator.off_color = Console.Color.YELLOW
            self.__scooter.left_indicator.off_color = Console.Color.YELLOW
            self.__scooter.right_indicator.off_color = Console.Color.LIGHT_BLUE
        else:
            self.__scooter.left_indicator.color = Console.Color.LIGHT_GREEN
            self.__scooter.right_indicator.off_color = Console.Color.LIGHT_BLUE
            self.__scooter.left_indicator.off_color = Console.Color.LIGHT_BLUE
            self.__scooter.right_indicator.off_color = Console.Color.LIGHT_GREEN
        self.__left_indicator.blink(cycle_duration = 0.5, percent_on = 0.5, begin_on = True)
        self.__right_indicator.blink(cycle_duration = 0.5, percent_on = 0.5, begin_on = True)
        self.power_off_context = ""


    def _on_integrity_failed(self:Self) -> None:
        self.__scooter.left_side_light.off_color = Console.Color.DARK_GREY
        self.__scooter.right_side_light.off_color = Console.Color.DARK_GREY
        self.__left_side_light.turn_off()
        self.__right_side_light.turn_off()
        self.__scooter.rearlight.off_color = Console.Color.LIGHT_RED
        self.__rearlight.blink(cycle_duration = 0.5, percent_on = 0.25, begin_on = False)
        self.__scooter.left_indicator.color = Console.Color.LIGHT_RED
        self.__scooter.left_indicator.off_color = Console.Color.YELLOW
        self.__left_indicator.blink(cycle_duration = 0.5, percent_on = 0.25, begin_on = True)
        
    def _on_locking(self:Self) -> None:
        self.__left_side_light.blink(cycle_duration = 0.5, percent_on = 0.5, begin_on = True)
        self.__right_side_light.blink(cycle_duration = 0.5, percent_on = 0.5, begin_on = False)
        self.__scooter.left_indicator.color = Console.Color.LIGHT_BLUE
        self.__scooter.right_indicator.color = Console.Color.LIGHT_BLUE
        self.__scooter.left_indicator.off_color = Console.Color.MAGENTA
        self.__scooter.right_indicator.off_color = Console.Color.MAGENTA
        self.__left_indicator.blink(cycle_duration = 0.5, percent_on = 0.75, begin_on = True)
        self.__right_indicator.blink(cycle_duration = 0.5, percent_on = 0.75, begin_on = True)

    def _on_charging_failed(self:Self) -> None:
        self.__scooter.left_side_light.off_color = Console.Color.DARK_GREY
        self.__scooter.right_side_light.off_color = Console.Color.DARK_GREY
        self.__left_side_light.turn_off()
        self.__right_side_light.turn_off()
        self.__scooter.rearlight.off_color = Console.Color.LIGHT_RED
        self.__rearlight.blink(cycle_duration = 0.5, percent_on = 0.25, begin_on = False)
        self.__scooter.left_indicator.color = Console.Color.LIGHT_BLUE
        self.__scooter.left_indicator.off_color = Console.Color.LIGHT_RED
        self.__left_indicator.blink(cycle_duration = 0.5, percent_on = 0.75, begin_on = True)

    def _on_scooting(self:Self) -> None:
        self.__left_side_light.blink(cycle_duration = 2.5, percent_on = 0.9, begin_on = True)
        self.__right_side_light.blink(cycle_duration = 2.5, percent_on = 0.9, begin_on = True)
        self.__scooter.left_indicator.color = Console.Color.GREEN
        self.__scooter.left_indicator.off_color = Console.Color.LIGHT_GREEN
        self.__left_indicator.blink(cycle_duration = 2.5, percent_on = 0.9, begin_on = True)
        self.__scooter.right_indicator.off_color = Console.Color.DARK_GREY
        self.__right_indicator.turn_off()

    def _on_charging(self:Self) -> None:
        self.__left_side_light.blink(cycle_duration = 2.0, percent_on = 0.75, begin_on = True)
        self.__right_side_light.blink(cycle_duration = 2.0, percent_on = 0.75, begin_on = True)
        self.__charge_indicator.blink(cycle_duration = 2, percent_on = 0.75, begin_on = True)
        self.__temp_indicator.blink(cycle_duration = 2, percent_on = 0.75, begin_on = True)
        self.__scooter.left_indicator.color = Console.Color.BLUE
        self.__scooter.left_indicator.off_color = Console.Color.LIGHT_BLUE
        self.__left_indicator.blink(cycle_duration = 2.0, percent_on = 0.75, begin_on = True)
        self.__scooter.right_indicator.color = Console.Color.MAGENTA
        self.__scooter.right_indicator.off_color = Console.Color.MAGENTA
        self.__right_indicator.blink(cycle_duration = 2.0, percent_on = 1-0.05, begin_on = True)

    def _off_charging(self:Self) -> None:
        self.__charge_indicator.turn_off()
        self.__temp_indicator.turn_off()

    def _in_idle(self:Self) -> None:
        self.__scooter.charge_indicator.percent_on = self.__scooter.battery.energy_level_percent
        self.__scooter.temp_indicator.percent_on = self.__scooter.battery.temp_percent

    def _plug_charging_cable(self:Self) -> None:
        if "i" in self.__console_reader.actual_key_pressed:
            self.__plugged_in = True

    def _unplug_charging_cable(self:Self) -> None:
        if "o" in self.__console_reader.actual_key_pressed:
            self.__plugged_in = False

    def _toggle_left_blinkers(self:Self, mode:SideBlinkersDevice.Side = SideBlinkersDevice.Side.BOTH) -> None:
        if Console.SpecialKey.LEFT_ARROW in self.__console_reader.actual_key_pressed and not self.__left_arrow_consumed:
                self.__left_arrow_consumed = True
                if not self.__left_blinker_on:
                    self.__left_blinker_on = True
                    self.__left_blinkers.blink(side = mode, cycle_duration = 1, percent_on = 0.5 , begin_on = True)
                else:
                    self.__left_blinker_on = False
                    self.__left_blinkers.turn_off(side = SideBlinkersDevice.Side.BOTH)
                return

        if Console.SpecialKey.LEFT_ARROW not in self.__console_reader.actual_key_pressed:
            self.__left_arrow_consumed = False

    def _toggle_right_blinkers(self:Self, mode:SideBlinkersDevice.Side = SideBlinkersDevice.Side.BOTH) -> None:
        if Console.SpecialKey.RIGHT_ARROW in self.__console_reader.actual_key_pressed and not self.__right_arrow_consumed:
            self.__right_arrow_consumed = True
            if not self.__right_blinker_on:
                self.__right_blinker_on = True
                self.__right_blinkers.blink(side = mode, cycle_duration = 1, percent_on = 0.5 , begin_on = True)
            else:
                self.__right_blinker_on = False
                self.__right_blinkers.turn_off(side = SideBlinkersDevice.Side.BOTH)
            return

        if Console.SpecialKey.RIGHT_ARROW not in self.__console_reader.actual_key_pressed:
            self.__right_arrow_consumed = False
    
    def _toggle_headlight(self:Self) -> None:
        if  Console.SpecialKey.SPACE in self.__console_reader.actual_key_pressed and not self.__spacebar_consumed:
             self.__spacebar_consumed = True
             if not self.__headlight_on:
                self.__headlight_on = True
                self.__headlight.turn_on()
             else:
                self.__headlight_on = False
                self.__headlight.turn_off()
             return

        if Console.SpecialKey.SPACE not in self.__console_reader.actual_key_pressed:
            self.__spacebar_consumed = False

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