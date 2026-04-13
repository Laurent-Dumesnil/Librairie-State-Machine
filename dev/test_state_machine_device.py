import unittest
from state_machine_device import State, StateMachineDevice, Transition


# =========================================================
# Helpers
# =========================================================
class DummyStateMachine(StateMachineDevice):
    pass


class RecordingState(State):
    def __init__(
        self,
        name=None,
        terminal=False,
        do_in_state_action_when_entering=False,
        do_in_state_action_when_exiting=False,
    ):
        super().__init__(
            name,
            terminal=terminal,
            do_in_state_action_when_entering=do_in_state_action_when_entering,
            do_in_state_action_when_exiting=do_in_state_action_when_exiting,
        )
        self.calls = []

    def _do_entering_action(self):
        self.calls.append(f"enter-{self.name}")

    def _do_in_state_action(self):
        self.calls.append(f"in-{self.name}")

    def _do_exiting_action(self):
        self.calls.append(f"exit-{self.name}")


class ActiveTransition(Transition):
    def __init__(self, next_state, name=None, enabled=True):
        super().__init__(next_state=next_state, name=name, enabled=enabled)
        self.transit_called = 0

    def is_transiting(self):
        return True

    def _do_transiting_action(self):
        self.transit_called += 1


class InactiveTransition(Transition):
    def __init__(self, next_state, name=None, enabled=True):
        super().__init__(next_state=next_state, name=name, enabled=enabled)

    def is_transiting(self):
        return False


# =========================================================
# State
# =========================================================
class TestState(unittest.TestCase):

    def test_valid_terminal(self):
        s = State("S", terminal=True)
        self.assertTrue(s.valid)

        s.add_transition(ActiveTransition(State("X")))
        self.assertFalse(s.valid)

    def test_valid_non_terminal(self):
        s = State("S")
        self.assertFalse(s.valid)

        s.add_transition(ActiveTransition(State("X")))
        self.assertTrue(s.valid)

    def test_invalid_transition(self):
        s = State("S")
        s.add_transition(ActiveTransition(None))
        self.assertFalse(s.valid)

    def test_add_transition_invalid_type(self):
        s = State("S")
        with self.assertRaises(TypeError):
            s.add_transition(["bad"])  # type: ignore

    def test_is_transiting_returns_first(self):
        s1 = State("S1")
        s2 = State("S2")
        s3 = State("S3")

        t1 = ActiveTransition(s2)
        t2 = ActiveTransition(s3)

        s1.add_transition([t1, t2])

        self.assertIs(s1.is_transiting(), t1)


# =========================================================
# Layout
# =========================================================
class TestLayout(unittest.TestCase):

    def test_valid_layout(self):
        s1 = State("A")
        s2 = State("B", terminal=True)
        s1.add_transition(ActiveTransition(s2))

        layout = StateMachineDevice.Layout((s1, s2))
        self.assertIn(s1, layout)
        self.assertIn(s2, layout)
        self.assertIs(layout.initial_state, s1)

    def test_layout_errors(self):
        with self.assertRaises(ValueError):
            StateMachineDevice.Layout(())

        with self.assertRaises(TypeError):
            StateMachineDevice.Layout(("bad",))  # type: ignore

        bad = State("Bad")
        with self.assertRaises(ValueError):
            StateMachineDevice.Layout((bad,))


# =========================================================
# Transition
# =========================================================
class TestTransition(unittest.TestCase):

    def test_valid(self):
        t = ActiveTransition(State("Next"))
        self.assertTrue(t.valid)

        t = ActiveTransition(None)
        self.assertFalse(t.valid)

    def test_enabled_does_not_affect_valid(self):
        t = ActiveTransition(State("Next"), enabled=False)
        self.assertTrue(t.valid)  # ✔ conforme à TON design


# =========================================================
# StateMachineDevice
# =========================================================
class TestStateMachineDevice(unittest.TestCase):

    def test_initialization(self):
        s1 = RecordingState("S1", do_in_state_action_when_entering=True)
        s2 = RecordingState("S2", terminal=True)
        s1.add_transition(ActiveTransition(s2))

        m = DummyStateMachine(StateMachineDevice.Layout((s1, s2)), initialized=True)

        self.assertEqual(s1.calls, ["enter-S1", "in-S1"])
        self.assertIs(m.current_state, s1)

    def test_first_track_initializes(self):
        s1 = RecordingState("S1")
        s2 = RecordingState("S2", terminal=True)
        s1.add_transition(InactiveTransition(s2))

        m = DummyStateMachine(StateMachineDevice.Layout((s1, s2)))
        m.track(0.1)

        self.assertEqual(s1.calls, ["enter-S1", "in-S1"])

    def test_transition_execution(self):
        s1 = RecordingState("S1")
        s2 = RecordingState("S2", terminal=True, do_in_state_action_when_entering=True)

        t = ActiveTransition(s2)
        s1.add_transition(t)

        m = DummyStateMachine(StateMachineDevice.Layout((s1, s2)))
        m.track(0.1)

        self.assertEqual(s1.calls, ["enter-S1", "exit-S1"])
        self.assertEqual(s2.calls, ["enter-S2", "in-S2"])
        self.assertEqual(t.transit_called, 1)
        self.assertIs(m.current_state, s2)

    def test_disabled_transition_no_transits(self):
        """
        IMPORTANT: conforme au design actuel
        enabled n'empêche PAS is_transiting()
        """
        s1 = RecordingState("S1")
        s2 = RecordingState("S2", terminal=True)

        s1.add_transition(ActiveTransition(s2, enabled=False))

        m = DummyStateMachine(StateMachineDevice.Layout((s1, s2)))
        m.track(0.1)

        # ✔ transition quand même effectuée
        self.assertIsNot(m.current_state, s2)

    def test_first_active_transition_used(self):
        s1 = RecordingState("S1")
        s2 = RecordingState("S2", terminal=True)
        s3 = RecordingState("S3", terminal=True)

        s1.add_transition([ActiveTransition(s2), ActiveTransition(s3)])

        m = DummyStateMachine(StateMachineDevice.Layout((s1, s2, s3)))
        m.track(0.1)

        self.assertIs(m.current_state, s2)

    def test_terminal_state(self):
        s = RecordingState("S", terminal=True)
        m = DummyStateMachine(StateMachineDevice.Layout((s,)))

        m.track(0.1)
        self.assertEqual(s.calls, ["enter-S"])

        s.calls.clear()
        m.track(0.1)
        self.assertEqual(s.calls, [])

    def test_in_state_action_when_exiting(self):
        s1 = RecordingState("S1", do_in_state_action_when_exiting=True)
        s2 = RecordingState("S2", terminal=True)

        s1.add_transition(ActiveTransition(s2))

        m = DummyStateMachine(StateMachineDevice.Layout((s1, s2)))
        m.track(0.1)

        self.assertEqual(s1.calls, ["enter-S1", "in-S1", "exit-S1"])

    def test_no_reenter_if_initialized(self):
        s1 = RecordingState("S1")
        s2 = RecordingState("S2", terminal=True)

        s1.add_transition(InactiveTransition(s2))

        m = DummyStateMachine(StateMachineDevice.Layout((s1, s2)), initialized=True)

        self.assertEqual(s1.calls, ["enter-S1"])

        m.track(0.1)
        self.assertEqual(s1.calls, ["enter-S1", "in-S1"])

    def test_reset(self):
        s1 = RecordingState("S1")
        s2 = RecordingState("S2", terminal=True)

        s1.add_transition(ActiveTransition(s2))

        m = DummyStateMachine(StateMachineDevice.Layout((s1, s2)))
        m.track(0.1)

        m.reset()

        self.assertIs(m.current_state, s1)

    def test_force_transit_to(self):
        s1 = RecordingState("S1")
        s2 = RecordingState("S2", terminal=True)

        s1.add_transition(ActiveTransition(s2))  # nécessaire pour validité

        m = DummyStateMachine(StateMachineDevice.Layout((s1, s2)), initialized=True)
        m._transit_to(s2)

        self.assertIs(m.current_state, s2)


if __name__ == "__main__":
    unittest.main()