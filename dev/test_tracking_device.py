import unittest
from typing import Any
from unittest.mock import Mock

from tracking_device import TrackingApplication, TrackingDevice, TrackingManager, TriggerDevice


class TestTrackingDevice(unittest.TestCase):

    class DummyTrackingDevice(TrackingDevice):
        def __init__(self, name: str | None = None, enabled: bool = True) -> None:
            super().__init__(name=name, enabled=enabled)
            self.tracked: list[float] = []
            self.reset_called: bool = False
            self.valid_override: bool = True

        def _do_valid(self) -> bool:
            return self.valid_override

        def _do_reset(self) -> None:
            self.reset_called = True

        def _do_tracking(self, elapsed_time: float) -> None:
            self.tracked.append(elapsed_time)

    def test_add_and_remove_sub_devices(self) -> None:
        parent = self.DummyTrackingDevice(name="Parent")
        child = self.DummyTrackingDevice(name="Child")

        parent.add_sub_device(child)
        self.assertEqual(parent.sub_devices_count, 1)

        parent.remove_sub_device("Child")
        self.assertEqual(parent.sub_devices_count, 0)

    def test_add_sub_device_invalid_type(self) -> None:
        device = self.DummyTrackingDevice(name="Parent")
        with self.assertRaises(TypeError):
            device.add_sub_device(123)  # type: ignore

    def test_add_sub_device_duplicate_name(self) -> None:
        device = self.DummyTrackingDevice(name="Parent")
        child = self.DummyTrackingDevice(name="Child")
        duplicate = self.DummyTrackingDevice(name="Child")

        device.add_sub_device(child)
        with self.assertRaises(ValueError):
            device.add_sub_device(duplicate)

    def test_remove_sub_device_iterable(self) -> None:
        device = self.DummyTrackingDevice(name="Parent")
        children = [
            self.DummyTrackingDevice(name="ChildA"),
            self.DummyTrackingDevice(name="ChildB"),
        ]

        device.add_sub_device(children)
        self.assertEqual(device.sub_devices_count, 2)

        device.remove_sub_device(["ChildA", "ChildB"])
        self.assertEqual(device.sub_devices_count, 0)

    def test_remove_sub_device_invalid_type(self) -> None:
        device = self.DummyTrackingDevice(name="Parent")
        with self.assertRaises(TypeError):
            device.remove_sub_device(["Child", 123])  # type: ignore

    def test_reset_propagates_to_sub_devices(self) -> None:
        parent = self.DummyTrackingDevice(name="Parent")
        child = self.DummyTrackingDevice(name="Child")
        parent.add_sub_device(child)

        parent.reset()
        self.assertTrue(parent.reset_called)
        self.assertTrue(child.reset_called)

    def test_track_propagates_to_sub_devices(self) -> None:
        parent = self.DummyTrackingDevice(name="Parent")
        child = self.DummyTrackingDevice(name="Child")
        parent.add_sub_device(child)

        parent.track(0.5)
        self.assertEqual(parent.tracked, [0.5])
        self.assertEqual(child.tracked, [0.5])

    def test_track_does_not_execute_when_disabled_or_invalid(self) -> None:
        disabled_device = self.DummyTrackingDevice(name="Disabled", enabled=False)
        disabled_device.track(0.5)
        self.assertEqual(disabled_device.tracked, [])

        invalid_device = self.DummyTrackingDevice(name="Invalid")
        invalid_device.valid_override = False
        invalid_device.track(0.5)
        self.assertEqual(invalid_device.tracked, [])

    def test_valid_with_invalid_sub_device(self) -> None:
        parent = self.DummyTrackingDevice(name="Parent")
        child = self.DummyTrackingDevice(name="Child")
        parent.add_sub_device(child)

        self.assertTrue(parent.valid)
        child.valid_override = False
        self.assertFalse(parent.valid)


class TestTrackingManager(unittest.TestCase):

    class DummyTrackingDevice(TrackingDevice):
        def __init__(self, name: str | None = None, enabled: bool = True) -> None:
            super().__init__(name=name, enabled=enabled)
            self.tracked: list[float] = []
            self.reset_called: bool = False

        def _do_tracking(self, elapsed_time: float) -> None:
            self.tracked.append(elapsed_time)

        def _do_reset(self) -> None:
            self.reset_called = True

    def test_add_and_remove_device_by_name_and_instance(self) -> None:
        manager = TrackingManager()
        device = self.DummyTrackingDevice(name="DeviceA")

        manager.add_device(device)
        self.assertEqual(manager.device_count, 1)

        manager.remove_device("DeviceA")
        self.assertEqual(manager.device_count, 0)

        manager.add_device(device)
        manager.remove_device(device)
        self.assertEqual(manager.device_count, 0)

    def test_add_and_remove_devices_iterable(self) -> None:
        manager = TrackingManager()
        devices = [
            self.DummyTrackingDevice(name="DeviceA"),
            self.DummyTrackingDevice(name="DeviceB"),
        ]

        manager.add_device(devices)
        self.assertEqual(manager.device_count, 2)

        manager.remove_device(["DeviceA", devices[1]])
        self.assertEqual(manager.device_count, 0)

    def test_add_device_invalid_type(self) -> None:
        manager = TrackingManager()
        with self.assertRaises(TypeError):
            manager.add_device(123)  # type: ignore

    def test_remove_device_invalid_type(self) -> None:
        manager = TrackingManager()
        with self.assertRaises(TypeError):
            manager.remove_device(3.14)  # type: ignore

    def test_track_and_reset_on_all_devices(self) -> None:
        manager = TrackingManager()
        devices = [
            self.DummyTrackingDevice(name="DeviceA"),
            self.DummyTrackingDevice(name="DeviceB"),
        ]

        manager.add_device(devices)
        manager.track(0.25)
        self.assertEqual(devices[0].tracked, [0.25])
        self.assertEqual(devices[1].tracked, [0.25])

        manager.reset()
        self.assertTrue(devices[0].reset_called)
        self.assertTrue(devices[1].reset_called)

    def test_valid_property(self) -> None:
        manager = TrackingManager()
        device = self.DummyTrackingDevice(name="DeviceA")
        manager.add_device(device)
        self.assertTrue(manager.valid)

        class InvalidDevice(self.DummyTrackingDevice):
            def _do_valid(self) -> bool:
                return False

        invalid_device = InvalidDevice(name="DeviceB")
        manager.add_device(invalid_device)
        self.assertFalse(manager.valid)


class TestTrackingApplication(unittest.TestCase):

    def test_run_until_stops_when_condition_is_met(self) -> None:
        app = TrackingApplication()
        iteration_count = 0

        def running_condition() -> str | None:
            nonlocal iteration_count
            iteration_count += 1
            return "finished" if iteration_count >= 2 else None

        result = app.run_until(running_condition)
        self.assertEqual(result, "finished")
        self.assertGreaterEqual(iteration_count, 2)


class TestTriggerDevice(unittest.TestCase):

    def test_init_validates_duration_type_and_value(self) -> None:
        with self.assertRaises(TypeError):
            TriggerDevice(1, lambda: None, "Trigger")  # type: ignore

        with self.assertRaises(ValueError):
            TriggerDevice(0.0, lambda: None, "Trigger")

    def test_init_validates_action_type(self) -> None:
        with self.assertRaises(TypeError):
            TriggerDevice(0.5, "not callable", "Trigger")  # type: ignore

    def test_init_validates_initial_time_type(self) -> None:
        with self.assertRaises(TypeError):
            TriggerDevice(0.5, lambda: None, "Trigger", initial_time=1)  # type: ignore

    def test_init_validates_auto_reset_when_enabling_type(self) -> None:
        with self.assertRaises(TypeError):
            TriggerDevice(0.5, lambda: None, "Trigger", auto_reset_when_enabling="yes")  # type: ignore

    def test_elapsed_and_remaining_time_properties(self) -> None:
        trigger = TriggerDevice(0.5, lambda: None, "Trigger")
        self.assertEqual(trigger.elapsed_time_from_last_trigger, 0.0)
        self.assertEqual(trigger.remaining_time_until_next_trigger, 0.5)

    def test_track_triggers_action_after_duration(self) -> None:
        action = Mock()
        trigger = TriggerDevice(0.5, action, "Trigger")

        trigger.track(0.4)
        action.assert_not_called()
        self.assertAlmostEqual(trigger.elapsed_time_from_last_trigger, 0.4, delta=1e-9)

        trigger.track(0.2)
        action.assert_called_once()
        self.assertAlmostEqual(trigger.elapsed_time_from_last_trigger, 0.1, delta=1e-9)

    def test_auto_reset_when_enabling(self) -> None:
        action = Mock()
        trigger = TriggerDevice(0.5, action, "Trigger", initial_time=0.4, auto_reset_when_enabling=True)

        trigger.enabled = False
        trigger.enabled = True
        self.assertAlmostEqual(trigger.elapsed_time_from_last_trigger, 0.0, delta=1e-9)

    def test_no_auto_reset_when_enabling(self) -> None:
        action = Mock()
        trigger = TriggerDevice(0.5, action, "Trigger", initial_time=0.4, auto_reset_when_enabling=False)

        trigger.enabled = False
        trigger.enabled = True
        self.assertAlmostEqual(trigger.elapsed_time_from_last_trigger, 0.4, delta=1e-9)


if __name__ == '__main__':
    unittest.main()
