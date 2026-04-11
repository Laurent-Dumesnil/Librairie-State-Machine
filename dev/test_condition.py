import unittest
from time import sleep

from condition import (
    AllConditions,
    AnyConditions,
    CountConditions,
    ElapsedTimerCondition,
    AlwaysFalseCondition,
    AlwaysTrueCondition,
    ReaderCondition,
    ValueCondition,
)


class TestCondition(unittest.TestCase):
    def test_always_true_false_and_inversion(self) -> None:
        self.assertTrue(bool(AlwaysTrueCondition()))
        self.assertFalse(bool(AlwaysTrueCondition(invert=True)))
        self.assertFalse(bool(AlwaysFalseCondition()))
        self.assertTrue(bool(AlwaysFalseCondition(invert=True)))

    def test_invert_setter_rejects_non_bool(self) -> None:
        condition = AlwaysTrueCondition()
        with self.assertRaises(ValueError):
            condition.invert = 'not bool'  # type: ignore

    def test_toggle_invert_changes_result(self) -> None:
        condition = AlwaysTrueCondition()
        self.assertTrue(bool(condition))
        condition.toogle_invert()
        self.assertFalse(bool(condition))
        condition.toogle_invert()
        self.assertTrue(bool(condition))

    def test_elapsed_timer_condition_becomes_true_after_duration_and_reset(self) -> None:
        condition = ElapsedTimerCondition(duration=0.01)
        self.assertFalse(bool(condition))
        sleep(0.02)
        self.assertTrue(bool(condition))
        condition.reset()
        self.assertFalse(bool(condition))

    def test_reader_condition_reads_callable_value(self) -> None:
        current = {'value': 3}

        def reader() -> int:
            return current['value']

        condition = ReaderCondition(3, reader)
        self.assertTrue(bool(condition))
        current['value'] = 4
        self.assertFalse(bool(condition))

    def test_reader_condition_value_reader_setter_rejects_non_callable(self) -> None:
        condition = ReaderCondition(1, lambda: 1)
        with self.assertRaises(ValueError):
            condition.value_reader = 42  # type: ignore

    def test_value_condition_compares_actual_value(self) -> None:
        condition = ValueCondition(10, 10)
        self.assertTrue(bool(condition))
        condition.actual_value = 5
        self.assertFalse(bool(condition))

    def test_all_conditions_with_none_and_mixed_values(self) -> None:
        self.assertFalse(bool(AllConditions()))
        self.assertTrue(bool(AllConditions([AlwaysTrueCondition(), AlwaysTrueCondition()])))
        self.assertFalse(bool(AllConditions([AlwaysTrueCondition(), AlwaysFalseCondition()])))

    def test_any_conditions_with_none_and_mixed_values(self) -> None:
        self.assertFalse(bool(AnyConditions()))
        self.assertTrue(bool(AnyConditions([AlwaysFalseCondition(), AlwaysTrueCondition()])))
        self.assertFalse(bool(AnyConditions([AlwaysFalseCondition(), AlwaysFalseCondition()])))

    def test_many_conditions_add_remove_clear(self) -> None:
        conditions = AllConditions([AlwaysTrueCondition()])
        self.assertTrue(bool(conditions))

        conditions.add_condition(AlwaysTrueCondition())
        self.assertTrue(bool(conditions))

        conditions.add_condition([AlwaysTrueCondition(), AlwaysTrueCondition()])
        self.assertTrue(bool(conditions))

        conditions.remove_condition(AlwaysTrueCondition())
        self.assertTrue(bool(conditions))

        conditions.clear_conditions()
        self.assertFalse(bool(conditions))

    def test_many_conditions_add_condition_when_none_no_error(self) -> None:
        conditions = AllConditions(None)
        self.assertFalse(bool(conditions))
        conditions.add_condition(AlwaysTrueCondition())
        self.assertFalse(bool(conditions))

    def test_count_conditions_exact_count(self) -> None:
        count = CountConditions(2, [AlwaysTrueCondition(), AlwaysTrueCondition(), AlwaysFalseCondition()])
        self.assertTrue(bool(count))
        count = CountConditions(3, [AlwaysTrueCondition(), AlwaysTrueCondition(), AlwaysFalseCondition()])
        self.assertFalse(bool(count))

    def test_count_conditions_at_least_count(self) -> None:
        count = CountConditions(1, [AlwaysFalseCondition(), AlwaysTrueCondition()], exact_bool_count=False)
        self.assertTrue(bool(count))
        count = CountConditions(2, [AlwaysFalseCondition(), AlwaysTrueCondition()], exact_bool_count=False)
        self.assertFalse(bool(count))

    def test_count_conditions_expected_condition_value_false(self) -> None:
        count = CountConditions(2, [AlwaysFalseCondition(), AlwaysFalseCondition(), AlwaysTrueCondition()], expected_condition_value=False)
        self.assertTrue(bool(count))

    def test_count_conditions_property_setter_rejects_invalid_types(self) -> None:
        count = CountConditions(1, [AlwaysTrueCondition()])
        with self.assertRaises(ValueError):
            count.expected_condition_value = 'true'  # type: ignore
        with self.assertRaises(ValueError):
            count.exact_bool_count = 'yes'  # type: ignore

    def test_count_conditions_n_setter_casts_to_int(self) -> None:
        count = CountConditions(1, [AlwaysTrueCondition()])
        count.n = 2.0
        self.assertFalse(bool(count))

    def test_count_conditions_without_conditions_returns_false(self) -> None:
        self.assertFalse(bool(CountConditions(1)))


if __name__ == '__main__':
    unittest.main()
