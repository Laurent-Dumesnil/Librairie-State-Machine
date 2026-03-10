import unittest

from type_utilities import (
    OneOrMany,
    OptionalOneOrMany,
    GenericCallback,
    GenericPredicate,
    GenericGenerator,
    GenericValidator,
    GenericComparator,
    GenericTransformer,
    GenericReducer
)


class TestGenericTypeAliases(unittest.TestCase):

    def test_one_or_many(self) -> None:
        value: OneOrMany[int] = 42
        self.assertEqual(value, 42)

        value = [1, 2, 3]
        self.assertListEqual(list(value), [1, 2, 3])

    def test_generic_callback(self) -> None:
        def sample_callback() -> None:
            return None

        callback: GenericCallback = sample_callback
        result: None = callback() # type: ignore
        self.assertIsNone(result)

    def test_generic_predicate(self) -> None:
        def sample_predicate() -> bool:
            return True

        predicate: GenericPredicate = sample_predicate
        self.assertTrue(predicate())

    def test_generic_generator(self) -> None:
        def sample_generator() -> int:
            return 42

        generator: GenericGenerator[int] = sample_generator
        self.assertEqual(generator(), 42)

    def test_generic_validator(self) -> None:
        def sample_validator(value: int) -> bool:
            return value > 10

        validator: GenericValidator[int] = sample_validator
        self.assertTrue(validator(15))
        self.assertFalse(validator(5))

    def test_generic_comparator(self) -> None:
        def sample_comparator(a: int, b: int) -> bool:
            return a == b

        comparator: GenericComparator[int] = sample_comparator
        self.assertTrue(comparator(5, 5))
        self.assertFalse(comparator(5, 10))

    def test_generic_transformer(self) -> None:
        def sample_transformer(value: str) -> str:
            return value.upper()

        transformer: GenericTransformer[str] = sample_transformer
        self.assertEqual(transformer("hello"), "HELLO")

    def test_generic_reducer(self) -> None:
        def sample_reducer(a: int, b: int) -> int:
            return a + b

        reducer: GenericReducer[int] = sample_reducer
        self.assertEqual(reducer(5, 10), 15)
        self.assertEqual(reducer(-3, 3), 0)


if __name__ == "__main__":
    unittest.main()