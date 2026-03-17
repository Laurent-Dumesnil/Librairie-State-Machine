"""
Module providing commun typing utilities. 

Two type aliases are defined to represent the concept of a single value or a
collection of values. These type aliases are useful for functions that can
accept either a single value or multiple values at once. The two type aliases
are:

- `OneOrMany[T]`: A type alias representing a single value or a collection of values of type `T`.
- `OptionalOneOrMany[T]`: A type alias representing an optional single value, a collection of values, or `None` of type `T`.

Seven types are dedicated to generic type aliases for commonly used functional 
programming patterns. These aliases facilitate and standardize the typing of 
classic generic callables, thereby improving code readability and 
maintainability. The seven generic type aliases are:

 - `GenericCallback`: A _callable_ that takes no arguments and returns `None`. Useful for representing simple actions or events.
 - `GenericPredicate`: A _callable_ that takes no arguments and returns a `bool`. Commonly used for representing a condition check.
 - `GenericGenerator[T]`: A _callable_ that takes no arguments and returns a value of type `T`. Allows specifying a specific type for the generated value.
 - `GenericValidator[T]`: A _callable_ that takes a single argument of type `T` and returns a `bool`. Used for validating values of a specific type.
 - `GenericComparator[T]`: A _callable_ that takes two arguments of type `T` and returns a `bool`. Used for comparing two values of the same type.
 - `GenericTransformer[T]`: A _callable_ that takes a single argument of type `T` and returns a value of type `T`. Useful for representing operations that transform values.
 - `GenericReducer[T]`: A _callable_ that takes two arguments of type `T` and returns a value of type `T`. Commonly used for reducing a sequence to a single value.
"""


from typing import TypeAlias, TypeVar, Callable, Iterable








T = TypeVar('T')
"""Type variable for a generic type."""



# À reconsidérer 
# OneOrMany: TypeAlias = TypeVar('OneOrMany', T, Iterable[T])
OneOrMany: TypeAlias = T | Iterable[T]
"""Type alias representing a single value or a collection of values.

This type alias is used to represent a value that can be either a single 
element or a collection of elements.

Example
-------
```python
def print_values(values: OneOrMany[int]) -> None:
    if isinstance(values, int):
        print(values)
    else:
        for value in values:
            print(value)

print_values(42)
print_values([1, 2, 3])

# Output:
# 42
# 1
# 2
# 3
```
"""


OptionalOneOrMany: TypeAlias = T | Iterable[T] | None # ZeroOrOneOrMany
"""Type alias representing an optional single value or a collection of values.

This type alias is used to represent a value that can be either a single
element, a collection of elements, or `None`.

Example
-------
```python
def print_values(values: OptionalOneOrMany[int]) -> None:
    if values is None:
        print("-no data available-")
    elif isinstance(values, int):
        print(values)
    else:
        for value in values:
            print(value)
            
print_values(None)
print_values(42)
print_values([1, 2, 3])

# Output:
# -no data available-
# 42
# 1
# 2
# 3
```
"""






GenericCallback: TypeAlias = Callable[[], None]
"""A simple action callback.

Example
-------
```python
def warning_print() -> None:
    print("Warning!")

def warning_beep() -> None:
    print("Beep! Beep!") # should beep the system

def warning_log() -> None:
    print("Warning logged.") # should log to a logger


warning_actions: list[GenericCallback] = (warning_print, warning_beep, warning_log)


is_warning_required: bool = True

if is_warning_required:
    for action in warning_actions:
        action()
```
"""

GenericPredicate: TypeAlias = Callable[[], bool]
"""A condition check callable.

Example
-------
```python
# Example of using GenericPredicate in a conditional context
def expect_7_after_rolling_dice() -> bool:
    return random.randint(1, 6) + random.randint(1, 6) == 7

good_luck: GenericPredicate = expect_7_after_rolling_dice

if good_luck():
    print("You win!!")
```
"""








GenericGenerator: TypeAlias = Callable[[], T]
"""Generates a value of type `T`.

Example
-------
```python
def generate_1_to_100() -> int:
    return random.randint(1, 100)

initializer: GenericGenerator[int] = generate_1_to_100

value = initializer()

# Example of using GenericGenerator in a loop to generate multiple values
for _ in range(3):
    print(generator())
```
"""

GenericValidator: TypeAlias = Callable[[T], bool]
"""Validates a value of type `T`.

Example
-------
```python
def is_positive(number: int) -> bool:
    return number > 0

def is_under_100(number: int) -> bool:
    return number < 100

# Example of using GenericValidator in a list filtering context
values = [100, 10, -1, 1000]
constraints = (is_positive, is_under_100)
validated_values = [value for value in values if
                    all(validator(value) for validator in constraints)]
print(validated_values)  # Output: [10]
```
"""

GenericComparator: TypeAlias = Callable[[T, T], bool]
"""Compares two values of type `T`.

Example
-------
```python
def less_than(a: int, b: int) -> bool:
    return a < b

comparator: GenericComparator[int] = less_than

# Example of using GenericComparator in conditional selection
pairs = [(5, 3), (8, 1), (3, 4)]
selected_pairs = [pair for pair in pairs if comparator(pair[0], pair[1])]
print(selected_pairs)  # Output: [(3, 4)]
```
"""

GenericTransformer: TypeAlias = Callable[[T], T]
"""Transforms a value of type `T`.

Example
-------
```python
def fahrenheit_to_celsius(temp_f: float) -> float:
    return (temp_f - 32.0) * 5.0 / 9.0

temperature_converter: GenericTransformer[float] = fahrenheit_to_celsius

temperature: float = 98.6 # in celcius

print(f'{temperature}°F -> {temperature_converter(temperature)}°C')
```
"""

GenericReducer: TypeAlias = Callable[[T, T], T]
"""Reduces two values of type `T` to one.

Example
-------
```python
def add(a: int, b: int) -> int:
    return a + b

reducer: GenericReducer[int] = add
print(reducer(4, 5))  # 9
```
"""




__pdoc__: dict[str, bool] = {
    'T': False
}

