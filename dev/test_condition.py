# import unittest
# from time import sleep

# from condition import (
#     AllConditions,
#     AnyConditions,
#     CountConditions,
#     ElapsedTimerCondition,
#     AlwaysFalseCondition,
#     AlwaysTrueCondition,
#     ReaderCondition,
#     ValueCondition,
# )


# class TestCondition(unittest.TestCase):

#     # ========================
#     # Base & inversion
#     # ========================
#     def test_always_true_false_and_inversion(self):
#         self.assertTrue(bool(AlwaysTrueCondition()))
#         self.assertFalse(bool(AlwaysTrueCondition(invert=True)))
#         self.assertFalse(bool(AlwaysFalseCondition()))
#         self.assertTrue(bool(AlwaysFalseCondition(invert=True)))

#     def test_toggle_invert(self):
#         c = AlwaysTrueCondition()
#         self.assertTrue(bool(c))
#         c.toogle_invert()
#         self.assertFalse(bool(c))
#         c.toogle_invert()
#         self.assertTrue(bool(c))

#     def test_invert_setter_rejects_non_bool(self):
#         c = AlwaysTrueCondition()
#         with self.assertRaises(ValueError):
#             c.invert = "not bool"  # type: ignore

#     def test_bool_inversion_logic(self):
#         c = AlwaysTrueCondition(invert=True)
#         self.assertFalse(bool(c))


#     # ========================
#     # ElapsedTimerCondition
#     # ========================
#     def test_elapsed_timer_condition(self):
#         c = ElapsedTimerCondition(0.01)
#         self.assertFalse(bool(c))
#         sleep(0.02)
#         self.assertTrue(bool(c))

#     def test_elapsed_timer_reset(self):
#         c = ElapsedTimerCondition(0.01)
#         sleep(0.02)
#         self.assertTrue(bool(c))
#         c.reset()
#         self.assertFalse(bool(c))


#     # ========================
#     # ReaderCondition
#     # ========================
#     def test_reader_condition_logic(self):
#         val = 10
#         c = ReaderCondition(10, lambda: val)
#         self.assertTrue(bool(c))
#         val = 5
#         self.assertFalse(bool(c))

#     def test_reader_condition_rejects_non_callable(self):
#         c = ReaderCondition(1, lambda: 1)
#         with self.assertRaises(ValueError):
#             c.value_reader = 42  # type: ignore


#     # ========================
#     # ValueCondition
#     # ========================
#     def test_value_condition(self):
#         c = ValueCondition(10, 10)
#         self.assertTrue(bool(c))
#         c.actual_value = 5
#         self.assertFalse(bool(c))

#     def test_value_condition_setters(self):
#         c = ValueCondition(1, 1)
#         c.expected_value = 2
#         self.assertFalse(bool(c))


#     # ========================
#     # AllConditions / AnyConditions
#     # ========================
#     def test_all_conditions(self):
#         self.assertFalse(bool(AllConditions()))
#         self.assertTrue(bool(AllConditions([AlwaysTrueCondition(), AlwaysTrueCondition()])))
#         self.assertFalse(bool(AllConditions([AlwaysTrueCondition(), AlwaysFalseCondition()])))

#     def test_any_conditions(self):
#         self.assertFalse(bool(AnyConditions()))
#         self.assertTrue(bool(AnyConditions([AlwaysFalseCondition(), AlwaysTrueCondition()])))
#         self.assertFalse(bool(AnyConditions([AlwaysFalseCondition(), AlwaysFalseCondition()])))

#     def test_single_condition_behavior(self):
#         c = AlwaysTrueCondition()
#         self.assertTrue(bool(AllConditions(c)))
#         self.assertTrue(bool(AnyConditions(c)))


#     # ========================
#     # ManyConditions (add/remove/clear)
#     # ========================
#     def test_add_condition_to_none(self):
#         conds = AllConditions(None)
#         self.assertFalse(bool(conds))
#         conds.add_condition(AlwaysTrueCondition())
#         self.assertTrue(bool(conds))

#     def test_add_condition_rejects_invalid_type(self):
#         conds = AllConditions()
#         with self.assertRaises(ValueError):
#             conds.add_condition("invalid")  # type: ignore

#     def test_remove_condition(self):
#         c1 = AlwaysTrueCondition()
#         c2 = AlwaysFalseCondition()
#         conds = AllConditions([c1, c2])

#         conds.remove_condition(c1)
#         self.assertEqual(len(conds._condition), 1)  # type: ignore

#         conds.remove_condition(c2)
#         self.assertIsNone(conds._condition)

#     def test_remove_nonexistent_condition(self):
#         c1 = AlwaysTrueCondition()
#         conds = AllConditions([c1])

#         conds.remove_condition(AlwaysTrueCondition())  # différent objet
#         self.assertEqual(len(conds._condition), 1)  # type: ignore

#     def test_clear_conditions(self):
#         conds = AllConditions([AlwaysTrueCondition()])
#         conds.clear_conditions()
#         self.assertFalse(bool(conds))


#     # ========================
#     # Composition avancée
#     # ========================
#     def test_recursive_composition(self):
#         c_true = AlwaysTrueCondition()
#         c_false = AlwaysFalseCondition()

#         inner = AllConditions([c_true, c_false])  # False
#         root = AnyConditions([inner, c_true])     # True

#         self.assertTrue(bool(root))


#     # ========================
#     # CountConditions
#     # ========================
#     def test_count_conditions_exact(self):
#         c = CountConditions(2, [AlwaysTrueCondition(), AlwaysTrueCondition(), AlwaysFalseCondition()])
#         self.assertTrue(bool(c))

#         c = CountConditions(3, [AlwaysTrueCondition(), AlwaysTrueCondition(), AlwaysFalseCondition()])
#         self.assertFalse(bool(c))

#     def test_count_conditions_at_least(self):
#         c = CountConditions(1, [AlwaysFalseCondition(), AlwaysTrueCondition()], exact_bool_count=False)
#         self.assertTrue(bool(c))

#         c = CountConditions(2, [AlwaysFalseCondition(), AlwaysTrueCondition()], exact_bool_count=False)
#         self.assertFalse(bool(c))

#     def test_count_conditions_expected_false(self):
#         c = CountConditions(
#             2,
#             [AlwaysFalseCondition(), AlwaysFalseCondition(), AlwaysTrueCondition()],
#             expected_condition_value=False
#         )
#         self.assertTrue(bool(c))

#     def test_count_conditions_n_setter(self):
#         c = CountConditions(2, [AlwaysTrueCondition(), AlwaysTrueCondition()])
#         self.assertTrue(bool(c))
#         c.n = 3
#         self.assertFalse(bool(c))

#     def test_count_conditions_setters_validation(self):
#         c = CountConditions(1, [AlwaysTrueCondition()])

#         with self.assertRaises(ValueError):
#             c.expected_condition_value = "true"  # type: ignore

#         with self.assertRaises(ValueError):
#             c.exact_bool_count = "yes"  # type: ignore

#     def test_count_conditions_without_conditions(self):
#         self.assertFalse(bool(CountConditions(1)))

#     def test_count_conditions_zero_case(self):
#         c = CountConditions(0, [AlwaysFalseCondition()], exact_bool_count=False)
#         self.assertTrue(bool(c))


# if __name__ == "__main__":
#     unittest.main()

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

    def test_always_true_false_and_inversion(self):
        self.assertTrue(bool(AlwaysTrueCondition()))
        self.assertFalse(bool(AlwaysTrueCondition(invert=True)))
        self.assertFalse(bool(AlwaysFalseCondition()))
        self.assertTrue(bool(AlwaysFalseCondition(invert=True)))

    def test_toggle_invert(self):
        c = AlwaysTrueCondition()
        self.assertTrue(bool(c))
        c.toogle_invert()
        self.assertFalse(bool(c))
        c.toogle_invert()
        self.assertTrue(bool(c))

    def test_invert_setter_rejects_non_bool(self):
        c = AlwaysTrueCondition()
        with self.assertRaises(ValueError):
            c.invert = "not bool"

    def test_bool_inversion_logic(self):
        c = AlwaysTrueCondition(invert=True)
        self.assertFalse(bool(c))

    def test_elapsed_timer_condition(self):
        c = ElapsedTimerCondition(0.01)
        self.assertFalse(bool(c))
        sleep(0.02)
        self.assertTrue(bool(c))

    def test_elapsed_timer_reset(self):
        c = ElapsedTimerCondition(0.01)
        sleep(0.02)
        self.assertTrue(bool(c))
        c.reset()
        self.assertFalse(bool(c))

    def test_reader_condition_logic(self):
        val = 10
        c = ReaderCondition(10, lambda: val)
        self.assertTrue(bool(c))
        val = 5
        self.assertFalse(bool(c))

    def test_reader_condition_rejects_non_callable(self):
        c = ReaderCondition(1, lambda: 1)
        with self.assertRaises(ValueError):
            c.value_reader = 42

    def test_value_condition(self):
        c = ValueCondition(10, 10)
        self.assertTrue(bool(c))
        c.actual_value = 5
        self.assertFalse(bool(c))

    def test_value_condition_setters(self):
        c = ValueCondition(1, 1)
        c.expected_value = 2
        self.assertFalse(bool(c))

    def test_all_conditions(self):
        self.assertFalse(bool(AllConditions()))
        self.assertTrue(bool(AllConditions([AlwaysTrueCondition(), AlwaysTrueCondition()])))
        self.assertFalse(bool(AllConditions([AlwaysTrueCondition(), AlwaysFalseCondition()])))

    def test_any_conditions(self):
        self.assertFalse(bool(AnyConditions()))
        self.assertTrue(bool(AnyConditions([AlwaysFalseCondition(), AlwaysTrueCondition()])))
        self.assertFalse(bool(AnyConditions([AlwaysFalseCondition(), AlwaysFalseCondition()])))

    def test_single_condition_behavior(self):
        c = AlwaysTrueCondition()
        self.assertTrue(bool(AllConditions(c)))
        self.assertTrue(bool(AnyConditions(c)))

    def test_add_condition_to_none(self):
        conds = AllConditions(None)
        self.assertFalse(bool(conds))
        conds.add_condition(AlwaysTrueCondition())
        self.assertTrue(bool(conds))

    def test_add_condition_rejects_invalid_type(self):
        conds = AllConditions()
        with self.assertRaises(ValueError):
            conds.add_condition(42)

    def test_remove_condition(self):
        c1 = AlwaysTrueCondition()
        c2 = AlwaysFalseCondition()
        conds = AllConditions([c1, c2])

        conds.remove_condition(c1)
        self.assertEqual(len(conds._condition), 1)

        conds.remove_condition(c2)
        self.assertIsNone(conds._condition)

    def test_remove_nonexistent_condition(self):
        c1 = AlwaysTrueCondition()
        conds = AllConditions([c1])
        conds.remove_condition(AlwaysTrueCondition())  
        self.assertEqual(len(conds._condition), 1)

    def test_clear_conditions(self):
        conds = AllConditions([AlwaysTrueCondition()])
        conds.clear_conditions()
        self.assertFalse(bool(conds))

    def test_recursive_composition(self):
        c_true = AlwaysTrueCondition()
        c_false = AlwaysFalseCondition()
        inner = AllConditions([c_true, c_false])  
        root = AnyConditions([inner, c_true])     
        self.assertTrue(bool(root))

    def test_count_conditions_exact(self):
        c = CountConditions(2, [AlwaysTrueCondition(), AlwaysTrueCondition(), AlwaysFalseCondition()])
        self.assertTrue(bool(c))
        c = CountConditions(3, [AlwaysTrueCondition(), AlwaysTrueCondition(), AlwaysFalseCondition()])
        self.assertFalse(bool(c))

    def test_count_conditions_at_least(self):
        c = CountConditions(1, [AlwaysFalseCondition(), AlwaysTrueCondition()], exact_bool_count=False)
        self.assertTrue(bool(c))
        c = CountConditions(2, [AlwaysFalseCondition(), AlwaysTrueCondition()], exact_bool_count=False)
        self.assertFalse(bool(c))

    def test_count_conditions_expected_false(self):
        c = CountConditions(
            2,
            [AlwaysFalseCondition(), AlwaysFalseCondition(), AlwaysTrueCondition()],
            expected_condition_value=False
        )
        self.assertTrue(bool(c))

    def test_count_conditions_n_setter(self):
        c = CountConditions(2, [AlwaysTrueCondition(), AlwaysTrueCondition()])
        self.assertTrue(bool(c))
        c.n = 3
        self.assertFalse(bool(c))

    def test_count_conditions_setters_validation(self):
        c = CountConditions(1, [AlwaysTrueCondition()])
        with self.assertRaises(ValueError):
            c.expected_condition_value = "true" 
        with self.assertRaises(ValueError):
            c.exact_bool_count = "yes" 

    def test_count_conditions_without_conditions(self):
        self.assertFalse(bool(CountConditions(1)))

    def test_count_conditions_zero_case(self):
        c = CountConditions(0, [AlwaysFalseCondition()], exact_bool_count=False)
        self.assertTrue(bool(c))


if __name__ == "__main__":
    unittest.main()