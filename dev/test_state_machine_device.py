import unittest
from typing import Iterable
from unittest.mock import Mock

from state_machine_device import State, StateMachineDevice, Transition


class TestState(unittest.TestCase):

    def test_is_bool_accepts_bool(self) -> None:
        state = State(name="TestState")
        self.assertTrue(state.is_bool(True))
        self.assertFalse(state.is_bool(False))

    def test_is_bool_rejects_non_bool(self) -> None:
        state = State(name="TestState")
        with self.assertRaises(TypeError):
            state.is_bool(1)  # type: ignore

    def test_valid_returns_false_without_transitions_for_non_terminal_state(self) -> None:
        state = State(name="TestState", terminal=False)
        self.assertFalse(state.valid)

    def test_valid_returns_true_for_terminal_state_without_transitions(self) -> None:
        terminal_state = State(name="TerminalState", terminal=True)
        self.assertTrue(terminal_state.valid)

    def test_valid_returns_false_for_terminal_state_with_transitions(self) -> None:
        terminal_state = State(name="TerminalState", terminal=True)
        transition = self._create_transition(None)
        terminal_state.add_transition(transition)
        self.assertFalse(terminal_state.valid)

    def test_valid_returns_false_if_a_transition_is_invalid(self) -> None:
        state = State(name="TestState")
        transition = self._create_transition(None)
        state.add_transition(transition)
        self.assertFalse(state.valid)

    def test_add_transition_single_and_iterable(self) -> None:
        state = State(name="TestState")
        next_state = State(name="NextState")

        transition = self._create_transition(next_state)
        state.add_transition(transition)
        self.assertIs(state.is_transiting(), transition)

        state2 = State(name="TestState2")
        transitions = [
            self._create_transition(next_state),
            self._create_transition(next_state),
        ]
        state2.add_transition(transitions)
        self.assertEqual(len(list(transitions)), 2)

    def test_add_transition_invalid_type(self) -> None:
        state = State(name="TestState")
        with self.assertRaises(TypeError):
            state.add_transition(["not a transition"])  # type: ignore

    def _create_transition(self, next_state: State | None) -> Transition:
        class DummyTransition(Transition):
            def __init__(self, next_state: State | None):
                super().__init__(next_state=next_state)

            def is_transiting(self) -> bool:
                return True

        return DummyTransition(next_state)


class TestLayout(unittest.TestCase):

    def test_layout_accepts_valid_state_tuple(self) -> None:
        state_a = State(name="A")
        state_b = State(name="B", terminal=True)
        state_a.add_transition(self._create_transition(state_b))

        layout = StateMachineDevice.Layout((state_a, state_b))
        self.assertIs(layout.initial_state, state_a)
        self.assertIn(state_a, layout)
        self.assertIn(state_b, layout)

    def test_layout_rejects_empty_states(self) -> None:
        with self.assertRaises(ValueError):
            StateMachineDevice.Layout(())

    def test_layout_rejects_non_state(self) -> None:
        with self.assertRaises(TypeError):
            StateMachineDevice.Layout(("not a state",))  # type: ignore

    def test_layout_rejects_invalid_state(self) -> None:
        bad_state = State(name="BadState")
        with self.assertRaises(ValueError):
            StateMachineDevice.Layout((bad_state,))

    def test_layout_does_not_contain_unknown_state(self) -> None:
        state_a = State(name="A")
        state_b = State(name="B", terminal=True)
        state_a.add_transition(self._create_transition(state_b))
        layout = StateMachineDevice.Layout((state_a, state_b))
        self.assertNotIn(State(name="C"), layout)

    def _create_transition(self, next_state: State | None) -> Transition:
        class DummyTransition(Transition):
            def __init__(self, next_state: State | None):
                super().__init__(next_state=next_state)

            def is_transiting(self) -> bool:
                return True

        return DummyTransition(next_state)


class TestTransition(unittest.TestCase):

    def test_transition_valid_when_next_state_defined(self) -> None:
        next_state = State(name="NextState")
        transition = self._create_transition(next_state)
        self.assertTrue(transition.valid)

    def test_transition_invalid_when_no_next_state(self) -> None:
        transition = self._create_transition(None)
        self.assertFalse(transition.valid)

    def _create_transition(self, next_state: State | None) -> Transition:
        class DummyTransition(Transition):
            def __init__(self, next_state: State | None):
                super().__init__(next_state=next_state)

            def is_transiting(self) -> bool:
                return False

        return DummyTransition(next_state)


class TestStateMachineDevice(unittest.TestCase):

    class RecordingState(State):
        def __init__(
            self,
            name: str | None = None,
            terminal: bool = False,
            do_in_state_action_when_entering: bool = False,
            do_in_state_action_when_exiting: bool = False,
        ) -> None:
            super().__init__(
                name=name,
                terminal=terminal,
                do_in_state_action_when_entering=do_in_state_action_when_entering,
                do_in_state_action_when_exiting=do_in_state_action_when_exiting,
            )
            self.calls: list[str] = []

        def _do_entering_action(self) -> None:
            self.calls.append(f"enter-{self.name}")

        def _do_in_state_action(self) -> None:
            self.calls.append(f"in-{self.name}")

        def _do_exiting_action(self) -> None:
            self.calls.append(f"exit-{self.name}")

    class ActiveTransition(Transition):
        def __init__(self, next_state: State | None, name: str | None = None, enabled: bool = True) -> None:
            super().__init__(next_state=next_state, name=name, enabled=enabled)
            self.transit_called: int = 0

        def is_transiting(self) -> bool:
            return True

        def _do_transiting_action(self) -> None:
            self.transit_called += 1

    class InactiveTransition(Transition):
        def __init__(self, next_state: State | None, name: str | None = None, enabled: bool = True) -> None:
            super().__init__(next_state=next_state, name=name, enabled=enabled)

        def is_transiting(self) -> bool:
            return False

    def test_initialized_calls_entering_action_immediately(self) -> None:
        initial = self.RecordingState(name="Initial", do_in_state_action_when_entering=True)
        target = self.RecordingState(name="Target", terminal=True)
        initial.add_transition(self.ActiveTransition(target))

        machine = StateMachineDevice(StateMachineDevice.Layout((initial, target)), initialized=True)
        self.assertEqual(initial.calls, ["enter-Initial", "in-Initial"])
        self.assertIs(machine.current_state, initial)

    def test_track_initial_state_and_entering_action(self) -> None:
        initial = self.RecordingState(name="Initial")
        target = self.RecordingState(name="Target", terminal=True)
        initial.add_transition(self.InactiveTransition(target))

        machine = StateMachineDevice(StateMachineDevice.Layout((initial, target)), initialized=False)
        machine.track(0.1)

        self.assertEqual(initial.calls, ["enter-Initial", "in-Initial"])
        self.assertIs(machine.current_state, initial)

    def test_track_transitions_between_states(self) -> None:
        initial = self.RecordingState(name="Initial")
        target = self.RecordingState(name="Target", terminal=True, do_in_state_action_when_entering=True)
        transition = self.ActiveTransition(target)
        initial.add_transition(transition)

        machine = StateMachineDevice(StateMachineDevice.Layout((initial, target)), initialized=False)
        machine.track(0.1)

        self.assertEqual(initial.calls, ["enter-Initial", "exit-Initial"])
        self.assertEqual(target.calls, ["enter-Target", "in-Target"])
        self.assertIs(machine.current_state, target)
        self.assertEqual(transition.transit_called, 1)

    def test_terminal_state_does_not_transition(self) -> None:
        terminal = self.RecordingState(name="Terminal", terminal=True)
        machine = StateMachineDevice(StateMachineDevice.Layout((terminal,)), initialized=False)

        machine.track(0.1)
        self.assertEqual(terminal.calls, ["enter-Terminal"])
        self.assertIs(machine.current_state, terminal)

        terminal.calls.clear()
        machine.track(0.1)
        self.assertEqual(terminal.calls, [])

    def test_track_does_not_reenter_state_when_already_initialized(self) -> None:
        initial = self.RecordingState(name="Initial")
        target = self.RecordingState(name="Target", terminal=True)
        initial.add_transition(self.InactiveTransition(target))

        machine = StateMachineDevice(StateMachineDevice.Layout((initial, target)), initialized=True)
        self.assertEqual(initial.calls, ["enter-Initial"])

        machine.track(0.1)
        self.assertEqual(initial.calls, ["enter-Initial", "in-Initial"])
        self.assertIs(machine.current_state, initial)

    def test_reset_returns_to_initial_state_without_entering(self) -> None:
        initial = self.RecordingState(name="Initial")
        next_state = self.RecordingState(name="Next", terminal=True)
        initial.add_transition(self.ActiveTransition(next_state))

        machine = StateMachineDevice(StateMachineDevice.Layout((initial, next_state)), initialized=False)
        machine.track(0.1)
        self.assertIs(machine.current_state, next_state)

        initial.calls.clear()
        next_state.calls.clear()
        machine.reset()

        self.assertIs(machine.current_state, initial)
        self.assertEqual(initial.calls, [])
        self.assertEqual(next_state.calls, [])



if __name__ == '__main__':
    unittest.main()
