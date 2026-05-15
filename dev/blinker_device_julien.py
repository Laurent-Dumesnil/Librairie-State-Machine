from typing import TypeAlias, Callable, overload, Self
from enum import Enum
from tracking_device import TrackingApplication
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

        self.__on_state_transtion = ConditionalTransition(self.__delay_since_entered_on_condition, self.__off_state)
        self.__off_state_transtion = ConditionalTransition(self.__delay_since_entered_off_condition, self.__on_state)
                                                          
        self.__off_state.add_transition(self.__off_state_transtion)
        self.__on_state.add_transition(self.__on_state_transtion)
        self.__terminal_state.add_entering_action(test_terminal_state)

        layout = (self.__off_state, self.__on_state)
        super().__init__(StateMachineDevice.Layout(layout), initialized=True)

    def turn_on(self):
        self._transit_to(self.__on_state)

    def turn_off(self):
        self._transit_to(self.__off_state)

    @overload
    def blink(self:Self, cycle_duration:float, percent_on:float, begin_on:bool, end_off:bool) -> None:
        ...
    @overload
    def blink(self:Self, total_duration:float, cycle_duration:float, percent_on:float, begin_on:bool, end_off:bool) -> None:
        ...
    @overload
    def blink(self:Self, total_duration:float, n_cycle:int, cycle_duration:float, percent_on:float, begin_on:bool, end_off:bool) -> None:
        ...
    @overload
    def blink(self:Self, n_cycle:int, cycle_duration:float, percent_on:float, begin_on:bool, end_off:bool) -> None:
        ...
    
    def blink(self:Self, **kwargs):
        params = {**kwargs}

        if params.keys() == {"cycle_duration", "percent_on", "begin_on", "end_off"}:
            print("blink_1")
            #pourquoi utiliser end_off si on a un cycle blink à l'infini???
            self._blink_1(params["cycle_duration"], params["percent_on"], params["begin_on"], params["end_off"])
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
            raise TypeError("Un des paramètres contient une valeur par mot-clé non reconnu")

    def _blink_1(self:Self, cycle_duration:float, percent_on:float, begin_on:bool, end_off:bool) -> None:
        if begin_on:
            self.turn_on()
        else:
            self.turn_off()
        self.__delay_since_entered_on_condition.duration = cycle_duration*percent_on
        self.__delay_since_entered_off_condition.duration = cycle_duration*(1-percent_on)

    def _blink_2(self:Self, total_duration:float, cycle_duration:float, percent_on:float, begin_on:bool, end_off:bool) -> None:
        self._set_cycle_duration(cycle_duration, percent_on, begin_on)
        self._set_total_duration(total_duration, end_off)

    #Quest ce qui est le plus important entre finir le nombre de cycle demandé ou la durée totale? Ou on ajoute 2 transitions et la durée la plus courte transitera vers l'état terminal ?
    def _blink_3(self:Self, total_duration:float, n_cycle:int, cycle_duration:float, percent_on:float, begin_on:bool, end_off:bool) -> None:
        self._set_cycle_duration(cycle_duration, percent_on, begin_on)
        self._set_total_duration(total_duration, end_off)
        self._set_n_cycle(n_cycle, end_off)

    def _blink_4(self:Self, n_cycle:int, cycle_duration:float, percent_on:float, begin_on:bool, end_off:bool) -> None:
        self._set_cycle_duration(cycle_duration, percent_on, begin_on)
        self._set_n_cycle(n_cycle, end_off)

    def _set_n_cycle(self, n_cycle, end_off):
        monitored_state = self.__off_state if end_off else self.__off_state
        count_n_cycle_condition = StateEntryCountCondition(n_cycle, monitored_state)
        transit_to_terminal_transition = ConditionalTransition(count_n_cycle_condition, self.__terminal_state)
        monitored_state.add_transition(transit_to_terminal_transition)

    def _set_cycle_duration(self, cycle_duration, percent_on, begin_on):
        if begin_on:
            self.turn_on()
        else:
            self.turn_off()
        self.__delay_since_entered_on_condition.duration = cycle_duration*percent_on
        self.__delay_since_entered_off_condition.duration = cycle_duration*(1-percent_on)

    def _set_total_duration(self, total_duration, end_off):
        delay_to_terminal_condition = ElapsedTimerCondition(total_duration)
        transit_to_terminal_transition = ConditionalTransition(delay_to_terminal_condition, self.__terminal_state)
        
        if end_off:
            self.__off_state.add_transition(transit_to_terminal_transition)
        else:
            self.__on_state.add_transition(transit_to_terminal_transition)

def main():

    def light_on():
        print("switch on")

    def light_off():
        print("switch off")

    def get_on_state():
        on_state = MonitoredState("on")
        on_state.add_entering_action(light_on)
        return on_state
    
    def get_off_state():
        off_state = MonitoredState("off")
        off_state.add_entering_action(light_off)
        return off_state

    app = TrackingApplication()
    blinker = BlinkerDevice(get_off_state, get_on_state)
    #blinker.blink(cycle_duration=1.0, percent_on=0.5, begin_on=True, end_off=True)
    #blinker.blink(total_duration=5.0, cycle_duration=1.0, percent_on=0.5, begin_on=True, end_off=True)
    #blinker.blink(total_duration=5.0, n_cycle=20, cycle_duration=1.0, percent_on=0.5, begin_on=True, end_off=True)
    blinker.blink(n_cycle=1, cycle_duration=1.0, percent_on=0.5, begin_on=True, end_off=False)
    app.add_device(blinker)
    app.run_forever()


if __name__ == "__main__":
    main()






# class SideBlinkers():

#     class Side(Enum):
#         LEFT = "LEFT"
#         RIGHT = "RIGHT"
#         ANY = "ANY"
#         BOTH = "BOTH"
#         LEFT_RECIPROCAL = "LEFT_RECIPROCAL"
#         RIGHT_RECIPROCAL = "RIGHT_RECIPROCAL"

#     def __init__(self):
#         self.__left_blinker = BlinkerDevice()
#         self.__right_blinker = BlinkerDevice()