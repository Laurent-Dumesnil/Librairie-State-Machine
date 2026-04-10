
from state_machine_device import StateMachineDevice, State, Transition
from state_machine_utilities import ActionState, ConditionalTransition, MonitoredState, DelaySinceEnteredCondition
from condition import ElapsedTimerCondition, ReaderCondition
from tracking_device import TrackingApplication
from typing import Self, override

class TrafficLightByAction(StateMachineDevice):
    def __init__(self:Self, initialized:bool = False, name:str|None = None, enabled:bool = True):
        self.red_state = MonitoredState(name="red")
        self.red_state.add_entering_action(lambda: self.reset_timer(1))
        self.red_state.add_entering_action(self.print_red)
        self.yellow_state = ActionState(name="yellow")
        self.yellow_state.add_entering_action(lambda: self.reset_timer(0.2))
        self.yellow_state.add_entering_action(self.print_yellow)
        self.green_state = ActionState(name="green")
        self.green_state.add_entering_action(lambda : self.reset_timer(0.8))
        self.green_state.add_entering_action(self.print_green)
        self.terminal_state = ActionState(name="Fin",terminal=True,enabled=False)
        self.terminal_state.add_entering_action(self.print_end)
        self.timer = ElapsedTimerCondition(1)
        self.red_state.add_transition(ConditionalTransition(self.timer, self.green_state))
        self.red_state.add_transition(ConditionalTransition(ReaderCondition(5,self.read_red_count),self.terminal_state))
        self.green_state.add_transition(ConditionalTransition(self.timer, self.yellow_state))
        self.yellow_state.add_transition(ConditionalTransition(self.timer, self.red_state))
        tuple_states = (self.red_state, self.green_state , self.yellow_state, self.terminal_state)
        layout = StateMachineDevice.Layout(tuple_states)
        super().__init__(layout, initialized, name, enabled)

    def read_red_count(self:Self) -> int:
        return self.red_state.entry_count

    def print_red(self:Self) -> None:
        print(f"\rRouge!", end="", sep="")

    def print_yellow(self:Self)-> None:
        print(f"\rJaune!", end="", sep="")

    def print_green(self:Self)-> None:
        print(f"\rVert! ", end="", sep="")

    def print_end(self:Self)-> None:
        print(f"\rFin de la simulation", end="", sep="")

    def reset_timer(self:Self, new_duration:float)-> None:
        self.timer.duration = new_duration
        self.timer.reset()





class TrafficLightByHeritage(StateMachineDevice):
    def __init__(self:Self, initialized:bool = False, name:str|None = None, enabled:bool = True):
        self.red_state = TrafficLightState("Rouge",name="red")
        self.yellow_state = TrafficLightState("Jaune", name="yellow")
        self.green_state = TrafficLightState("Vert", name="green")
        self.terminal_state = TrafficLightState("Fin",name="Fin",terminal=True,enabled=False)
        self.red_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(1, self.red_state), self.green_state))
        self.red_state.add_transition(ConditionalTransition(ReaderCondition(5, self.read_red_count),self.terminal_state))
        self.green_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(0.8, self.green_state), self.yellow_state))
        self.yellow_state.add_transition(ConditionalTransition(DelaySinceEnteredCondition(0.2, self.yellow_state), self.red_state))
        tuple_states = (self.red_state, self.green_state , self.yellow_state, self.terminal_state)
        layout = StateMachineDevice.Layout(tuple_states)
        super().__init__(layout, initialized, name, enabled)

    def read_red_count(self:Self) -> int:
        return self.red_state.entry_count

class TrafficLightState(MonitoredState):
    def __init__(self:Self, color:str, name:str|None = None, *, enabled:bool = True, terminal:bool = False, do_in_state_action_when_entering:bool = False, do_in_state_action_when_exiting:bool = False):
        self.color = color
        super().__init__(name, enabled=enabled, terminal=terminal, do_in_state_action_when_entering=do_in_state_action_when_entering, do_in_state_action_when_exiting=do_in_state_action_when_exiting)

    @override
    def _do_entering_action(self:Self):
        print(f"\r{self.color}! ", end="", sep="")



   
def main() -> int:
    try:
        #app = TrackingApplication()
        #app.add_device(TrafficLightByAction())
        #app.run_forever()

        app2 = TrackingApplication()
        app2.add_device(TrafficLightByHeritage())
        app2.run_forever()

    except Exception as e:
        print(e)
        return 1

    return 0

if __name__ == "__main__":
    quit(main())