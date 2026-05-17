from typing import TypeAlias, Callable, overload, Self, Any, override
import random
from enum import Enum
from tracking_device import TrackingApplication, TrackingDevice
from state_machine_device import StateMachineDevice
from state_machine_utilities import MonitoredState, ConditionalTransition, DelaySinceEnteredCondition, StateEntryCountCondition
from condition import ElapsedTimerCondition

def test_terminal_state():
    print("terminal state")

class BlinkerDevice(StateMachineDevice):
    BlinkerStateFactory: TypeAlias = Callable[[], MonitoredState]

    def __init__(self:Self, off_state_factory:BlinkerStateFactory, on_state_factory:BlinkerStateFactory):
        self.__off_state = off_state_factory()
        self.__on_state = on_state_factory()
        self.__terminal_state = MonitoredState("terminal")

        self.__delay_since_entered_on_condition = DelaySinceEnteredCondition(10.0, self.__on_state)
        self.__delay_since_entered_off_condition = DelaySinceEnteredCondition(10.0, self.__off_state)

        #Condition et transition pour le total duration
        self.__delay_to_terminal_condition = ElapsedTimerCondition(10.0)
        self.__on_transit_to_terminal_transition = ConditionalTransition(self.__delay_to_terminal_condition, self.__terminal_state)
        self.__off_transit_to_terminal_transition = ConditionalTransition(self.__delay_to_terminal_condition, self.__terminal_state)
        self.__on_state.add_transition(self.__on_transit_to_terminal_transition)
        self.__off_state.add_transition(self.__off_transit_to_terminal_transition)

        #Condition et transition pour set n_cycle
        self.__on_count_n_cycle_condition = StateEntryCountCondition(10, self.__on_state)
        self.__off_count_n_cycle_condition = StateEntryCountCondition(10, self.__off_state)
        self.__on_n_cycle_to_terminal_transition = ConditionalTransition(self.__on_count_n_cycle_condition, self.__terminal_state)
        self.__off_n_cycle_to_terminal_transition = ConditionalTransition(self.__off_count_n_cycle_condition, self.__terminal_state)
        self.__on_state.add_transition(self.__on_n_cycle_to_terminal_transition)
        self.__off_state.add_transition(self.__off_n_cycle_to_terminal_transition)

        self.__on_state_transtion = ConditionalTransition(self.__delay_since_entered_on_condition, self.__off_state)
        self.__off_state_transtion = ConditionalTransition(self.__delay_since_entered_off_condition, self.__on_state)
                                                          
        self.__off_state.add_transition(self.__off_state_transtion)
        self.__on_state.add_transition(self.__on_state_transtion)
        self.__terminal_state.add_entering_action(test_terminal_state)
        #self.__terminal_state.add_entering_action(self._disable_blinker)

        layout = (self.__off_state, self.__on_state, self.__terminal_state)
        super().__init__(StateMachineDevice.Layout(layout), initialized=False, enabled=False)

    @property
    def is_on(self):
        return self.current_state == self.__on_state
    
    @property
    def is_off(self):
        return self.current_state == self.__off_state

    @overload
    def turn_on(self) -> None:
        ...
    @overload
    def turn_on(self, *, duration:float) -> None:
        ...
    def turn_on(self, **kwargs) -> None:
        if len(kwargs) == 0:
           self._transit_to(self.__on_state) 
        elif set(kwargs) == {"duration"}:
            if not isinstance(kwargs["duration"], float):
                raise TypeError("Duration must be float type")
            if kwargs["duration"] < 0:
                raise ValueError("Duration must be positive")
            self.__transit_by(ConditionalTransition(ElapsedTimerCondition(kwargs["duration"])))
        else:
            raise TypeError("turn_on() got an unexpected keyword argument")
        
    @overload
    def turn_off(self) -> None:
        ...
    @overload
    def turn_off(self, *, duration:float) -> None:
        ...
    def turn_off(self, **kwargs) -> None:
        if len(kwargs) == 0:
           self._transit_to(self.__off_state) 
        elif set(kwargs) == {"duration"}:
            if not isinstance(kwargs["duration"], float):
                raise TypeError("Duration must be float type")
            if kwargs["duration"] < 0:
                raise ValueError("Duration must be positive")
            self.__transit_by(ConditionalTransition(ElapsedTimerCondition(kwargs["duration"])))
        else:
            raise TypeError("turn_off() got an unexpected keyword argument")

    @overload
    def blink(self:Self, *, cycle_duration:float, percent_on:float, begin_on:bool) -> None:
        ...
    @overload
    def blink(self:Self, *, total_duration:float, cycle_duration:float, percent_on:float, begin_on:bool, end_off:bool) -> None:
        ...
    @overload
    def blink(self:Self, *, total_duration:float, n_cycle:int, cycle_duration:float, percent_on:float, begin_on:bool, end_off:bool) -> None:
        ...
    @overload
    def blink(self:Self, *, n_cycle:int, cycle_duration:float, percent_on:float, begin_on:bool, end_off:bool) -> None:
        ...
    
    def blink(self:Self, **kwargs):
        params = {**kwargs}

        if params.keys() == {"cycle_duration", "percent_on", "begin_on"}:
            print("blink_1")
            self._blink_1(params["cycle_duration"], params["percent_on"], params["begin_on"])
        elif params.keys() == {"total_duration", "cycle_duration", "percent_on", "begin_on", "end_off"}:
            print("blink_2")
            self._blink_2(params["total_duration"], params["cycle_duration"], params["percent_on"], params["begin_on"], params["end_off"])
        elif params.keys() == {"total_duration", "n_cycle", "cycle_duration", "percent_on", "begin_on", "end_off"}:
            print("blink_3")
            self._blink_3(params["total_duration"], params["n_cycle"], params["cycle_duration"], params["percent_on"], params["begin_on"], params["end_off"])
        elif params.keys() == {"n_cycle", "cycle_duration", "percent_on", "begin_on", "end_off"}:
            print("blink_4")
            self._blink_4(params["n_cycle"], params["cycle_duration"], params["percent_on"], params["begin_on"], params["end_off"])
        else:
            raise TypeError("blink() got an unexpected keyword argument")
        
    def _blink_1(self:Self, cycle_duration:float, percent_on:float, begin_on:bool) -> None:
        self.reset()
        self._disable_terminal_transitions()
        self._activate_blinker()
        self._set_cycle(cycle_duration, percent_on, begin_on)

    def _blink_2(self:Self, total_duration:float, cycle_duration:float, percent_on:float, begin_on:bool, end_off:bool) -> None:
        self.reset()
        self._disable_terminal_transitions()
        self._activate_blinker()
        self._set_cycle(cycle_duration, percent_on, begin_on)
        self._set_total_duration(total_duration, end_off)
        
    #Quest ce qui est le plus important entre finir le nombre de cycle demandé ou la durée totale? Ou on ajoute 2 transitions et la durée la plus courte transitera vers l'état terminal ?
    def _blink_3(self:Self, total_duration:float, n_cycle:int, cycle_duration:float, percent_on:float, begin_on:bool, end_off:bool) -> None:
        self.reset()
        self._disable_terminal_transitions()
        self._activate_blinker()
        self._set_cycle(cycle_duration, percent_on, begin_on)
        self._set_total_duration(total_duration, end_off)
        self._set_n_cycle(n_cycle, end_off)

    def _blink_4(self:Self, n_cycle:int, cycle_duration:float, percent_on:float, begin_on:bool, end_off:bool) -> None:
        self.reset()
        self._disable_terminal_transitions()
        self._activate_blinker()
        self._set_cycle(cycle_duration, percent_on, begin_on)
        self._set_n_cycle(n_cycle, end_off)
        
    def _set_n_cycle(self, n_cycle, end_off):
        if n_cycle == 0:
            self._transit_to(self.__terminal_state)
            return
        if end_off:
            self.__off_count_n_cycle_condition.expected_count = n_cycle
            self.__off_n_cycle_to_terminal_transition.enabled = True
        else:
            self.__on_count_n_cycle_condition.expected_count = n_cycle
            self.__on_n_cycle_to_terminal_transition.enabled = True

    def _set_cycle(self, cycle_duration, percent_on, begin_on):
        if begin_on:
            self.turn_on()
        else:
            self.turn_off()
        self.__delay_since_entered_on_condition.duration = cycle_duration*percent_on
        self.__delay_since_entered_off_condition.duration = cycle_duration*(1-percent_on)

    def _set_total_duration(self, total_duration, end_off):
        self.__delay_to_terminal_condition.duration = total_duration
        if end_off:
            self.__off_transit_to_terminal_transition.enabled = True
        else:
            self.__on_transit_to_terminal_transition.enabled = True

    def _activate_blinker(self):
        self.enabled = True

    def _disable_blinker(self):
        self.enabled = False

    def _disable_terminal_transitions(self) -> None:
        self.__on_transit_to_terminal_transition.enabled = False
        self.__off_transit_to_terminal_transition.enabled = False
        self.__on_n_cycle_to_terminal_transition.enabled = False
        self.__off_n_cycle_to_terminal_transition.enabled = False

class SideBlinkers(TrackingDevice):
    BlinkerStateFactory: TypeAlias = Callable[[], MonitoredState]

    class Side(Enum):
        LEFT = "LEFT"
        RIGHT = "RIGHT"
        ANY = "ANY"
        BOTH = "BOTH"
        LEFT_RECIPROCAL = "LEFT_RECIPROCAL"
        RIGHT_RECIPROCAL = "RIGHT_RECIPROCAL"

    def __init__(self:Self, left_off_state_factory:BlinkerStateFactory, left_on_state_factory:BlinkerStateFactory, right_off_state_factory:BlinkerStateFactory, right_on_state_factory:BlinkerStateFactory):
        super().__init__(name=None, enabled=True)
        self.__left_blinker = BlinkerDevice(left_off_state_factory, left_on_state_factory)
        self.__right_blinker = BlinkerDevice(right_off_state_factory, right_on_state_factory)
        self.__rng = random.Random()
        self.add_sub_device([self.__left_blinker, self.__right_blinker])
        
    def is_on(self, side: Side) -> bool:
        match side:
                case SideBlinkers.Side.LEFT:
                    return self.__left_blinker.is_on()
                case SideBlinkers.Side.RIGHT:
                    return self.__right_blinker.is_on()
                case SideBlinkers.Side.ANY:
                    return self.__left_blinker.is_on() or self.__right_blinker.is_on()
                case SideBlinkers.Side.BOTH:
                    return self.__left_blinker.is_on() and self.__right_blinker.is_on()
                case SideBlinkers.Side.LEFT_RECIPROCAL:
                    return self.__left_blinker.is_on() and self.__right_blinker.is_off()
                case SideBlinkers.Side.RIGHT_RECIPROCAL:
                    return self.__right_blinker.is_on() and self.__left_blinker.is_off()
                case _:
                    raise TypeError("side must be a Side enum")
            
    def is_off(self, side: Side) -> bool:
        match side:
                case SideBlinkers.Side.LEFT:
                    return self.__left_blinker.is_off()
                case SideBlinkers.Side.RIGHT:
                    return self.__right_blinker.is_off()
                case SideBlinkers.Side.ANY:
                    return self.__left_blinker.is_off() or self.__right_blinker.is_off()
                case SideBlinkers.Side.BOTH:
                    return self.__left_blinker.is_off() and self.__right_blinker.is_off()
                case SideBlinkers.Side.LEFT_RECIPROCAL:
                    return self.__left_blinker.is_off() and self.__right_blinker.is_on()
                case SideBlinkers.Side.RIGHT_RECIPROCAL:
                    return self.__right_blinker.is_off() and self.__left_blinker.is_on()
                case _:
                    raise TypeError("side must be a Side enum")
                
    @overload
    def turn_on(self:Self, *, side: Side) -> None:
        ...
    @overload
    def turn_on(self:Self, *, side: Side, duration:float) -> None:
        ...

    def turn_on(self:Self, **kwargs:Any) -> None:
        if set(kwargs) == {"side"}:
            self.__turn_on_by_side(kwargs["side"])

        elif set(kwargs) == {"side", "duration"}:
            self.__turn_on_by_side(kwargs["side"], kwargs["duration"])

        else:
            raise TypeError("turn_on() got an unexpected keyword argument")
        
    @overload
    def turn_off(self:Self, *, side: Side) -> None:
        ...
    @overload
    def turn_off(self:Self, *, side: Side, duration:float) -> None:
        ...

    def turn_off(self:Self, **kwargs:Any) -> None:
        if set(kwargs) == {"side"}:
            self.__turn_off_by_side(kwargs["side"])

        elif set(kwargs) == {"side", "duration"}:
            self.__turn_off_by_side(kwargs["side"], kwargs["duration"])

        else:
            raise TypeError("turn_off() got an unexpected keyword argument")

    def __turn_on_by_side(self:Self, side: Side, duration: float | None = None) -> None:
        match side:
            case SideBlinkers.Side.LEFT:
                self.__turn_blinker_on(self.__left_blinker, duration)

            case SideBlinkers.Side.RIGHT:
                self.__turn_blinker_on(self.__right_blinker, duration)

            case SideBlinkers.Side.ANY:
                random_blinker = self.__rng.choice([self.__left_blinker, self.__right_blinker])
                self.__turn_blinker_on(random_blinker, duration)

            case SideBlinkers.Side.BOTH:
                self.__turn_blinker_on(self.__left_blinker, duration)
                self.__turn_blinker_on(self.__right_blinker, duration)

            case SideBlinkers.Side.LEFT_RECIPROCAL:
                self.__turn_blinker_on(self.__left_blinker, duration)
                self.__turn_blinker_off(self.__right_blinker, duration)

            case SideBlinkers.Side.RIGHT_RECIPROCAL:
                self.__turn_blinker_on(self.__right_blinker, duration)
                self.__turn_blinker_off(self.__left_blinker, duration)

            case _:
                raise TypeError("side must be a Side enum")
            
    def __turn_off_by_side(self:Self, side: Side, duration: float | None = None) -> None:
        match side:
            case SideBlinkers.Side.LEFT:
                self.__turn_blinker_off(self.__left_blinker, duration)

            case SideBlinkers.Side.RIGHT:
                self.__turn_blinker_off(self.__right_blinker, duration)

            case SideBlinkers.Side.ANY:
                random_blinker = self.__rng.choice([self.__left_blinker, self.__right_blinker])
                self.__turn_blinker_off(random_blinker, duration)

            case SideBlinkers.Side.BOTH:
                self.__turn_blinker_off(self.__left_blinker, duration)
                self.__turn_blinker_off(self.__right_blinker, duration)

            case SideBlinkers.Side.LEFT_RECIPROCAL:
                self.__turn_blinker_off(self.__left_blinker, duration)
                self.__turn_blinker_on(self.__right_blinker, duration)

            case SideBlinkers.Side.RIGHT_RECIPROCAL:
                self.__turn_blinker_off(self.__right_blinker, duration)
                self.__turn_blinker_on(self.__left_blinker, duration)

            case _:
                raise TypeError("side must be a Side enum")
            
    def __turn_blinker_on(self, blinker: BlinkerDevice, duration: float | None) -> None:
        if duration is None:
            blinker.turn_on()
        else:
            blinker.turn_on(duration=duration)

    def __turn_blinker_off(self, blinker: BlinkerDevice, duration: float | None) -> None:
        if duration is None:
            blinker.turn_off()
        else:
            blinker.turn_off(duration=duration)

    @overload
    def blink(self:Self, *, side: Side, cycle_duration: float, percent_on: float, begin_on: bool) -> None:
        ...
    @overload
    def blink(self:Self, *,total_duration: float, side: Side, cycle_duration: float, percent_on: float, begin_on: bool, end_off: bool) -> None:
        ...
    @overload
    #Il semble avoir une erreur dans le uml on omet cycle duration mais on la retrouve dans blink_3 de blinkerdevice
    def blink(self:Self, *,side: Side, total_duration: float, n_cycle: int, cycle_duration: float, percent_on: float, begin_on: bool) -> None:
        ...
    @overload
    def blink(self:Self, *,side: Side, n_cycle: int, percent_on: float, begin_on: bool, end_off: bool) -> None:
        ...

    def blink(self: Self, **kwargs: Any) -> None:
        valid_signatures = (
        {"side", "cycle_duration", "percent_on", "begin_on"},
        {"side", "total_duration", "cycle_duration", "percent_on", "begin_on", "end_off"},
        {"side", "total_duration", "n_cycle", "cycle_duration", "percent_on", "begin_on", "end_off"},
        {"side", "n_cycle", "cycle_duration", "percent_on", "begin_on", "end_off"},
        )
        if set(kwargs) not in valid_signatures:
            raise TypeError("blink() received invalid keyword arguments")
        
        if "side" not in kwargs:
            raise TypeError("blink() missing required keyword argument: 'side'")
        self.__blink_by_side(**kwargs)
        
    def __blink_by_side(self: Self, **kwargs: Any) -> None:
        side = kwargs.pop("side")
        blink_kwargs = dict(kwargs)
        match side:
            case SideBlinkers.Side.LEFT:
                print("LEFT BLINKER")
                self.__left_blinker.blink(**blink_kwargs)

            case SideBlinkers.Side.RIGHT:
                print("RIGHT BLINKER")
                self.__right_blinker.blink(**blink_kwargs)

            case SideBlinkers.Side.ANY:
                random_blinker = self.__rng.choice([self.__left_blinker, self.__right_blinker])
                print("ANY BLINKER")
                random_blinker.blink(**blink_kwargs)

            case SideBlinkers.Side.BOTH:
                print("BOTH BLINKER")
                self.__left_blinker.blink(**blink_kwargs)
                self.__right_blinker.blink(**blink_kwargs)

            case SideBlinkers.Side.LEFT_RECIPROCAL:
                print("LEFT_RECIPROCAL BLINKER")
                self.__left_blinker.blink(**blink_kwargs)
                #On doit inverser percent_on et begin_on pour avoir l'effet inverse sur l'autre blinker
                self.__right_blinker.blink(**self.__reverse_dict(**blink_kwargs))

            case SideBlinkers.Side.RIGHT_RECIPROCAL:
                print("RIGHT_RECIPROCAL BLINKER")
                self.__right_blinker.blink(**blink_kwargs)
                #On doit inverser percent_on et begin_on pour avoir l'effet inverse sur l'autre blinker
                self.__left_blinker.blink(**self.__reverse_dict(**blink_kwargs))
            
            case _:
                raise TypeError("side must be a Side enum")
            
    def __reverse_dict(self: Self, **kwargs: Any) -> dict[str, Any]:
        reciprocal_kwargs = dict(kwargs)
        reciprocal_kwargs["begin_on"] = not reciprocal_kwargs["begin_on"]
        reciprocal_kwargs["percent_on"] = 1-reciprocal_kwargs["percent_on"]
        return reciprocal_kwargs
    
    #Est ce que l'on supposé utiliser do_tracking pour dire aux sous device le moment de blink ??
    @override
    def _do_tracking(self, elapsed_time):
        super()._do_tracking(elapsed_time)

def main():

    def light_on():
        print("switch on")

    def light_off():
        print("switch off")

    def get_on_left_state():
        on_state = MonitoredState("on")
        on_state.add_entering_action(light_on)
        return on_state
    
    def get_off_left_state():
        off_state = MonitoredState("off")
        off_state.add_entering_action(light_off)
        return off_state
    
    def get_on_right_state():
        on_state = MonitoredState("on")
        on_state.add_entering_action(light_on)
        return on_state
    
    def get_off_right_state():
        off_state = MonitoredState("off")
        off_state.add_entering_action(light_off)
        return off_state

    app = TrackingApplication()

    ###########################
    #       TEST BLINKERDEVICE
    #############################

    #blinker = BlinkerDevice(get_off_state, get_on_state)
    #blinker.blink(cycle_duration=1.0, percent_on=0.1, begin_on=True)
    #blinker.blink(total_duration=5.0, cycle_duration=1.0, percent_on=0.5, begin_on=False, end_off=True)
    #blinker.blink(total_duration=2.0, n_cycle=10, cycle_duration=1.0, percent_on=0.5, begin_on=True, end_off=True)
    #blinker.blink(n_cycle=2, cycle_duration=5.0, percent_on=0.5, begin_on=True, end_off=False)
    #app.add_device(blinker)
    #app.run_forever()

    ################################
    #       TEST SIDEBLINKER
    ################################

    side_blinker = SideBlinkers(get_off_left_state, get_on_left_state, get_off_right_state, get_on_right_state)
    app.add_device(side_blinker)
    #side_blinker.blink(side=SideBlinkers.Side.LEFT_RECIPROCAL, cycle_duration=1.0, percent_on=0.1, begin_on=True)
    #side_blinker.blink(side=SideBlinkers.Side.LEFT, total_duration=5.0, cycle_duration=1.0, percent_on=0.5, begin_on=False, end_off=True)
    #side_blinker.blink(side=SideBlinkers.Side.LEFT, total_duration=2.0, n_cycle=10, cycle_duration=1.0, percent_on=0.5, begin_on=True, end_off=True)
    #side_blinker.blink(side=SideBlinkers.Side.LEFT, n_cycle=2, cycle_duration=5.0, percent_on=0.5, begin_on=True, end_off=False)
    app.run_forever()


if __name__ == "__main__":
    main()