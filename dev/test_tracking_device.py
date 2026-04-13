import unittest

from state_machine_utilities import (
    ConditionalTransition,
    ActionTransition,
    MonitoredTransition,
    ActionState,
    MonitoredState,
    DelaySinceEnteredCondition,
    DelaySinceExitedCondition,
    StateEntryCountCondition,
    StateValueCondition,
)

from condition import AlwaysTrueCondition, AlwaysFalseCondition
from state_machine_device import State


# =========================================================
# Helpers
# =========================================================
class DummyState(MonitoredState):
    """Contrôle du temps sans dépendre du système."""

    def __init__(self):
        super().__init__("dummy")
        self._MonitoredState__last_entry_reference_time = 0
        self._MonitoredState__last_exit_reference_time = 0

    @property
    def elapsed_since_last_entry(self):
        return 2.0

    @property
    def elapsed_since_last_exit(self):
        return 3.0


# =========================================================
# Transitions
# =========================================================
class TestTransitions(unittest.TestCase):

    def test_conditional_transition(self):
        s = State("S")
        t = ConditionalTransition(AlwaysTrueCondition(), s)

        self.assertTrue(t.valid)
        self.assertTrue(t.is_transiting())

        t.condition = AlwaysFalseCondition()
        self.assertFalse(t.is_transiting())

    def test_condition_setter_invalid(self):
        t = ConditionalTransition(AlwaysTrueCondition(), State("S"))

        with self.assertRaises(TypeError):
            t.condition = 123  # type: ignore

    def test_conditional_transition_invalid(self):
        t = ConditionalTransition(None, State("S"))
        self.assertFalse(t.valid)

    def test_inverted_condition(self):
        s = State("S")
        c = AlwaysTrueCondition(invert=True)

        t = ConditionalTransition(c, s)
        self.assertFalse(t.is_transiting())

    def test_action_transition_execution(self):
        called = []

        def action():
            called.append(1)

        t = ActionTransition(AlwaysTrueCondition(), State("S"))
        t.add_transiting_action(action)

        t._do_transiting_action()
        self.assertEqual(len(called), 1)

    def test_action_transition_multiple_actions_order(self):
        called = []

        def a(): called.append("a")
        def b(): called.append("b")

        t = ActionTransition(AlwaysTrueCondition(), State("S"))
        t.add_transiting_action([a, b])

        t._do_transiting_action()
        self.assertEqual(called, ["a", "b"])

    def test_action_transition_invalid_action(self):
        t = ActionTransition(AlwaysTrueCondition(), State("S"))

        with self.assertRaises(TypeError):
            t.add_transiting_action(42)  # type: ignore

    def test_monitored_transition(self):
        t = MonitoredTransition(AlwaysTrueCondition(), State("S"))

        self.assertEqual(t.transit_count, 0)

        t._execute_transiting_action()
        t._execute_transiting_action()

        self.assertEqual(t.transit_count, 2)
        self.assertIsNotNone(t.last_transit_reference_time)


# =========================================================
# ActionState
# =========================================================
class TestActionState(unittest.TestCase):

    def test_entering_actions(self):
        called = []

        def action():
            called.append(1)

        s = ActionState("S")
        s.add_entering_action(action)

        s._do_entering_action()
        self.assertEqual(len(called), 1)

    def test_in_state_actions(self):
        called = []

        def action():
            called.append(1)

        s = ActionState("S")
        s.add_in_state_action(action)

        s._do_in_state_action()
        self.assertEqual(len(called), 1)

    def test_exiting_actions(self):
        called = []

        def action():
            called.append(1)

        s = ActionState("S")
        s.add_exiting_action(action)

        s._do_exiting_action()
        self.assertEqual(len(called), 1)

    def test_invalid_action(self):
        s = ActionState("S")

        with self.assertRaises(TypeError):
            s.add_entering_action(123)  # type: ignore


# =========================================================
# MonitoredState
# =========================================================
class TestMonitoredState(unittest.TestCase):

    def test_entry_exit_count(self):
        s = MonitoredState("S")

        s._execute_entering_action()
        s._execute_entering_action()
        s._execute_exiting_action()

        self.assertEqual(s.entry_count, 2)
        self.assertEqual(s.exit_count, 1)

    def test_timing(self):
        s = MonitoredState("S")

        self.assertIsNotNone(s.creation_reference_time)
        self.assertGreaterEqual(s.elapsed_time_since_creation, 0)

# =========================================================
# Conditions
# =========================================================
class TestConditions(unittest.TestCase):

    def test_delay_since_entered(self):
        s = DummyState()
        c = DelaySinceEnteredCondition(1.5, s)

        self.assertTrue(bool(c))

    def test_delay_since_exited(self):
        s = DummyState()
        c = DelaySinceExitedCondition(2.5, s)

        self.assertTrue(bool(c))

    def test_entry_count_condition(self):
        s = MonitoredState("S")
        c = StateEntryCountCondition(2, s)

        s._execute_entering_action()
        self.assertFalse(bool(c))

        s._execute_entering_action()
        self.assertTrue(bool(c))

    def test_state_value_condition(self):
        s = MonitoredState("S")
        s.custom_value = 42

        c = StateValueCondition(42, s)
        self.assertTrue(bool(c))

        c = StateValueCondition(0, s)
        self.assertFalse(bool(c))


if __name__ == "__main__":
    unittest.main()