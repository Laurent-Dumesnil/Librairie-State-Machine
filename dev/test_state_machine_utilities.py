import unittest
from unittest.mock import Mock

from condition import AlwaysTrueCondition
from state_machine_utilities import (
    ActionState,
    ActionTransition,
    ConditionalTransition,
    DelaySinceEnteredCondition,
    DelaySinceExitedCondition,
    MonitoredState,
    MonitoredStateCondition,
    MonitoredTransition,
    StateEntryCountCondition,
    StateValueCondition,
)


class DummyState(MonitoredState):
    def __init__(self, *, entry_elapsed: float | None = None, exit_elapsed: float | None = None) -> None:
        super().__init__('dummy')
        self._entry_elapsed = entry_elapsed
        self._exit_elapsed = exit_elapsed

    @property
    def elapsed_since_last_entry(self) -> float | None:
        if self._entry_elapsed is None:
            return super().elapsed_since_last_entry
        return self._entry_elapsed

    @property
    def elapsed_since_last_exit(self) -> float | None:
        if self._exit_elapsed is None:
            return super().elapsed_since_last_exit
        return self._exit_elapsed


class DummyMonitoredStateCondition(MonitoredStateCondition):
    def _compare(self) -> bool:
        return True


class TestConditionalTransition(unittest.TestCase):
    def test_valid_and_is_transiting_require_condition(self) -> None:
        target = ActionState('next')
        transition = ConditionalTransition(condition=AlwaysTrueCondition(), next_state=target)
        self.assertTrue(transition.valid)
        self.assertTrue(transition.is_transiting())

    def test_condition_setter_rejects_invalid_type(self) -> None:
        target = ActionState('next')
        transition = ConditionalTransition(condition=AlwaysTrueCondition(), next_state=target)
        with self.assertRaises(TypeError):
            transition.condition = 'bad'  # type: ignore

    def test_transition_without_condition_is_invalid(self) -> None:
        transition = ConditionalTransition(condition=None, next_state=ActionState('next'))
        self.assertFalse(transition.valid)
        self.assertFalse(transition.is_transiting())


class TestActionTransition(unittest.TestCase):
    def test_add_transiting_actions_and_execute(self) -> None:
        transition = ActionTransition(condition=AlwaysTrueCondition(), next_state=ActionState('next'))
        action_1 = Mock()
        action_2 = Mock()

        transition.add_transiting_action(action_1)
        transition.add_transiting_action([action_2])

        self.assertEqual(transition.transiting_action_count, 2)
        transition._do_transiting_action()
        action_1.assert_called_once()
        action_2.assert_called_once()

    def test_add_transiting_action_rejects_invalid_object(self) -> None:
        transition = ActionTransition(condition=AlwaysTrueCondition(), next_state=ActionState('next'))
        with self.assertRaises(TypeError):
            transition.add_transiting_action([1])  # type: ignore


class TestMonitoredTransition(unittest.TestCase):
    def test_transit_count_and_timing_update(self) -> None:
        transition = MonitoredTransition(condition=AlwaysTrueCondition(), next_state=ActionState('next'))
        transition._execute_transiting_action()
        self.assertEqual(transition.transit_count, 1)
        self.assertIsNotNone(transition.last_transit_reference_time)
        self.assertIsNotNone(transition.elapsed_since_last_transit)


class TestActionState(unittest.TestCase):
    def test_state_action_lists_and_execution(self) -> None:
        state = ActionState('state')
        entry_action = Mock()
        in_state_action = Mock()
        exit_action = Mock()

        state.add_entering_action(entry_action)
        state.add_in_state_action(in_state_action)
        state.add_exiting_action(exit_action)

        self.assertEqual(state.entering_action_count, 1)
        self.assertEqual(state.in_state_action_count, 1)
        self.assertEqual(state.exiting_action_count, 1)

        state._do_entering_action()
        state._do_in_state_action()
        state._do_exiting_action()

        entry_action.assert_called_once()
        in_state_action.assert_called_once()
        exit_action.assert_called_once()

    def test_add_state_actions_rejects_invalid_iterable(self) -> None:
        state = ActionState('state')
        with self.assertRaises(TypeError):
            state.add_entering_action([1])  # type: ignore


class TestMonitoredState(unittest.TestCase):
    def test_entry_and_exit_counters_update(self) -> None:
        monitored = MonitoredState('monitored')
        monitored._execute_entering_action()
        self.assertEqual(monitored.entry_count, 1)
        self.assertIsNotNone(monitored.elapsed_since_last_entry)

        monitored._execute_exiting_action()
        self.assertEqual(monitored.exit_count, 1)
        self.assertIsNotNone(monitored.elapsed_since_last_exit)


class TestMonitoredStateCondition(unittest.TestCase):
    def test_rejects_non_monitored_state(self) -> None:
        with self.assertRaises(ValueError):
            DummyMonitoredStateCondition(monitored_state='wrong')  # type: ignore

    def test_delay_since_entered_condition(self) -> None:
        dummy = DummyState(entry_elapsed=2.5)
        condition = DelaySinceEnteredCondition(1.0, monitored_state=dummy)
        self.assertTrue(bool(condition))

    def test_delay_since_exited_condition(self) -> None:
        dummy = DummyState(exit_elapsed=3.5)
        condition = DelaySinceExitedCondition(2.0, monitored_state=dummy)
        self.assertTrue(bool(condition))

    def test_state_entry_count_condition(self) -> None:
        state = MonitoredState('counted')
        condition = StateEntryCountCondition(1, monitored_state=state)
        state._execute_entering_action()
        self.assertTrue(bool(condition))

    def test_state_value_condition_compares_custom_value(self) -> None:
        state = MonitoredState('value')
        state.custom_value = 42
        condition = StateValueCondition(42, monitored_state=state)
        self.assertTrue(bool(condition))
        state.custom_value = 99
        self.assertFalse(bool(condition))

    def test_state_value_condition_requires_monitored_state(self) -> None:
        with self.assertRaises(ValueError):
            StateValueCondition(42)

    def test_state_entry_count_condition_requires_monitored_state(self) -> None:
        with self.assertRaises(ValueError):
            StateEntryCountCondition(1)

    def test_delay_conditions_require_monitored_state(self) -> None:
        with self.assertRaises(ValueError):
            DelaySinceEnteredCondition(1.0)
        with self.assertRaises(ValueError):
            DelaySinceExitedCondition(1.0)

    def test_action_transition_clear_actions(self) -> None:
        transition = ActionTransition(condition=AlwaysTrueCondition(), next_state=ActionState('next'))
        action = Mock()
        transition.add_transiting_action(action)
        self.assertEqual(transition.transiting_action_count, 1)
        transition.clear_transiting_actions()
        self.assertEqual(transition.transiting_action_count, 0)

    def test_action_state_helpers_clear_actions(self) -> None:
        state = ActionState('state')
        action = Mock()
        state.add_entering_action(action)
        state.add_in_state_action(action)
        state.add_exiting_action(action)
        self.assertEqual(state.entering_action_count, 1)
        self.assertEqual(state.in_state_action_count, 1)
        self.assertEqual(state.exiting_action_count, 1)

        state.clear_entering_actions()
        state.clear_in_state_actions()
        state.clear_exiting_actions()

        self.assertEqual(state.entering_action_count, 0)
        self.assertEqual(state.in_state_action_count, 0)
        self.assertEqual(state.exiting_action_count, 0)

    def test_action_state_add_in_state_and_exiting_invalid_iterable(self) -> None:
        state = ActionState('state')
        with self.assertRaises(TypeError):
            state.add_in_state_action([1])  # type: ignore
        with self.assertRaises(TypeError):
            state.add_exiting_action([1])  # type: ignore

    def test_monitored_state_initial_counts(self) -> None:
        monitored = MonitoredState('monitored')
        self.assertEqual(monitored.entry_count, 0)
        self.assertEqual(monitored.exit_count, 0)

    def test_monitored_transition_elapsed_since_last_transit_none_before_transit(self) -> None:
        transition = MonitoredTransition(condition=AlwaysTrueCondition(), next_state=ActionState('next'))
        self.assertIsNone(transition.elapsed_since_last_transit)

    def test_monitored_state_condition_setter_allows_valid_state(self) -> None:
        state = MonitoredState('state')
        condition = DummyMonitoredStateCondition(monitored_state=state)
        self.assertIs(condition.monitored_state, state)
        state2 = MonitoredState('state2')
        condition.monitored_state = state2
        self.assertIs(condition.monitored_state, state2)

if __name__ == '__main__':
    unittest.main()
