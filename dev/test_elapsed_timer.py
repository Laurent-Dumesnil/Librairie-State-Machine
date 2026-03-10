import unittest
from time import sleep


from elapsed_timer import ElapsedTimer


class TestElapsedTimer(unittest.TestCase):

    def test_initial_mode_default(self) -> None:
        timer: ElapsedTimer = ElapsedTimer()
        self.assertEqual(timer.mode, ElapsedTimer.Mode.INTERVAL)

    def test_initial_mode_accumulated(self) -> None:
        timer: ElapsedTimer = ElapsedTimer(mode=ElapsedTimer.Mode.ACCUMULATED)
        self.assertEqual(timer.mode, ElapsedTimer.Mode.ACCUMULATED)

    def test_set_mode_invalid_type(self) -> None:
        timer: ElapsedTimer = ElapsedTimer()
        with self.assertRaises(TypeError):
            timer.mode = "INVALID_MODE" # type: ignore

    def test_elapsed_accumulated_mode(self) -> None:
        timer: ElapsedTimer = ElapsedTimer(mode=ElapsedTimer.Mode.ACCUMULATED)
        timer.reset()
        sleep(0.1)
        elapsed = timer.elapsed
        self.assertGreater(elapsed, 0.09)
        self.assertLess(elapsed, 0.2)
        sleep(0.1)
        self.assertGreater(timer.elapsed, elapsed)

    def test_elapsed_interval_mode(self) -> None:
        timer: ElapsedTimer = ElapsedTimer(mode=ElapsedTimer.Mode.INTERVAL)
        timer.reset()
        sleep(0.1)
        elapsed_1 = timer.elapsed
        self.assertGreater(elapsed_1, 0.09)
        self.assertLess(elapsed_1, 0.2)
        sleep(0.1)
        elapsed_2 = timer.elapsed
        self.assertGreater(elapsed_2, 0.09)
        self.assertLess(elapsed_2, 0.2)

    def test_reset_accumulated_mode(self) -> None:
        timer: ElapsedTimer = ElapsedTimer(mode=ElapsedTimer.Mode.ACCUMULATED)
        sleep(0.1)
        timer.reset()
        self.assertAlmostEqual(timer.elapsed, 0, delta=0.01)

    def test_reset_interval_mode(self) -> None:
        timer: ElapsedTimer = ElapsedTimer(mode=ElapsedTimer.Mode.INTERVAL)
        sleep(0.1)
        timer.reset()
        self.assertAlmostEqual(timer.elapsed, 0, delta=0.01)

    def test_reset_with_mode_change(self) -> None:
        timer: ElapsedTimer = ElapsedTimer(mode=ElapsedTimer.Mode.INTERVAL)
        timer.reset(mode=ElapsedTimer.Mode.ACCUMULATED)
        self.assertEqual(timer.mode, ElapsedTimer.Mode.ACCUMULATED)
        timer.reset(mode=ElapsedTimer.Mode.INTERVAL)
        self.assertEqual(timer.mode, ElapsedTimer.Mode.INTERVAL)

    def test_reset_invalid_mode(self) -> None:
        timer: ElapsedTimer = ElapsedTimer()
        with self.assertRaises(TypeError):
            timer.reset(mode="INVALID_MODE") # type: ignore


if __name__ == "__main__":
    unittest.main()