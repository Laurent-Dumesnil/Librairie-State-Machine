"""
The `elapsed_timer` module provides the utility class `ElapsedTimer` for 
measuring elapsed time. 

It supports two modes: `ACCUMULATED` and `INTERVAL`, making it suitable for 
a variety of timing use cases, such as performance monitoring or interval 
measurement.

Typical usage example:
```python
    from elapsed_timer import ElapsedTimer
    timer = ElapsedTimer(mode=ElapsedTimer.Mode.ACCUMULATED)
    timer.reset()
    # Simulate some elapsed time here...
    elapsed_time = timer.elapsed
    print(isinstance(elapsed_time, float))  # Expected output: True
```
"""

from enum import Enum, auto
from time import perf_counter


class ElapsedTimer:
    """
    A timer utility class for measuring elapsed time in seconds.

    The `ElapsedTimer` can operate in two modes: cumulative (`Mode.ACCUMULATED`)
    or delta (`Mode.INTERVAL`). In cumulative mode, the timer measures the
    total elapsed time since the last reset, while in delta mode, it measures
    the time elapsed between consecutive reads.

    Properties:
        mode (Mode): Defines the timing mode for the timer (accumulated or interval).
        elapsed (float): Provides the elapsed time based on the current mode.
    """

    class Mode(Enum):
        """
        Enumeration of timing modes for `ElapsedTimer`.

        Enumerators:
            `ACCUMULATED`

            Measures the total cumulative time elapsed since the last reset.

            `INTERVAL`

            Measures the time elapsed between consecutive reads of the property `elapsed`.

        Usage:
            Use `ACCUMULATED` mode when you need to measure the entire
            duration of a process from start to finish without intermediate resets.
            
            Use `INTERVAL` mode for measuring time intervals between successive events,
            such as tracking frame times in a game loop or latency between steps.
        """
        ACCUMULATED = auto()
        INTERVAL = auto()

    def __init__(self, mode: Mode = Mode.INTERVAL) -> None:
        """
        Initializes the ElapsedTimer instance.

        Args `__init__`:
            `mode` (`Mode`, optional):
                The timing mode. Determines if the elapsed time is measured
                cumulatively (`Mode.ACCUMULATED`) or between
                consecutive reads (`Mode.INTERVAL`). Defaults to `Mode.INTERVAL`.

        Raises:
            `TypeError`: If the provided mode is not an instance of `ElapsedTimer.Mode`.

        Example:
            >>> timer_1 = ElapsedTimer()
            >>> timer_2 = ElapsedTimer(mode=ElapsedTimer.Mode.ACCUMULATED)
        """
        self.__mode: ElapsedTimer.Mode
        self.mode = mode
        self.__reference_time: float = perf_counter()

    @property
    def mode(self) -> Mode:
        """
        The mode of the timer. _{ read-write }_

        The timing mode determines whether the timer measures the total
        elapsed time since the last reset (`Mode.ACCUMULATED`)
        or the time elapsed since the last read (`Mode.INTERVAL`).

        Raises:
            `TypeError`: If the provided mode is not an instance of `ElapsedTimer.Mode`.
        """
        return self.__mode
    
    @mode.setter
    def mode(self, mode: Mode) -> None:
        if not isinstance(mode, ElapsedTimer.Mode):
            raise TypeError(f'mode must be a Mode type. Invalid type for mode: {type(mode).__name__}')
        self.__mode = mode

    @property
    def elapsed(self) -> float:
        """
        The elapsed time according to the current mode. _{ read-only }_

        Notes:
            - In `Mode.ACCUMULATED`, returns the total time elapsed since the last
              reset.
            - In `Mode.INTERVAL`, returns the time elapsed since the last read
              and updates the reference time.

        Example:
            >>> from time import sleep
            >>> timer = ElapsedTimer(mode=ElapsedTimer.Mode.INTERVAL)
            >>> timer.reset()
            >>> sleep(1.0)  # Simulate some elapsed time
            >>> elapsed_time = timer.elapsed
            >>> 0.9 < elapsed_time < 1.1
            True
        """
        current_time = perf_counter()
        elapsed_time = current_time - self.__reference_time
        if self.__mode is ElapsedTimer.Mode.INTERVAL:
            self.__reference_time = current_time
        return elapsed_time

    def reset(self, mode: Mode | None = None) -> None:
        """
        Resets the timer and optionally sets the timing mode.

        This method resets the elapsed time to zero and can also change
        the timer mode if specified.

        Args:
            mode (Mode, optional):
                The timing mode to set upon reset. If `None`, the current mode
                is retained. Defaults to `None`.

        Raises:
            `TypeError`: If the provided mode is not an instance of 
            `ElapsedTimer.Mode` or `None`.

        Example:
            >>> from time import sleep
            >>> timer = ElapsedTimer()
            >>> timer.reset()
            >>> tests = [0] * 10
            >>> for i in range(len(tests)):
            ...    sleep(0.1)
            ...    tests[i] = 0.075 < timer.elapsed < 0.125
            >>> all(tests)
            True
            >>> timer.reset(mode=ElapsedTimer.Mode.ACCUMULATED)
            >>> tests = [0] * 10
            >>> for i in range(len(tests)):
            ...     sleep(0.1)
            ...     tests[i] = (i + 1) * 0.075 < timer.elapsed < (i + 1) * 0.125
            >>> all(tests)
            True
        """
        if isinstance(mode, ElapsedTimer.Mode):
            self.__mode = mode
        elif mode is not None:
            raise TypeError(f'Invalid type for mode: {type(mode).__name__}')
        
        self.__reference_time = perf_counter()


if __name__ == "__main__":
    import doctest
    doctest.testmod()
    print('elapsed_timer module test completed.')
