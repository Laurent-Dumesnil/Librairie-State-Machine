from time import perf_counter
from tracking_device import TriggerDevice, TrackingApplication

def five_sec():
    current_time = perf_counter()
    stop_time = perf_counter() + 5
    while current_time < stop_time:
        current_time = perf_counter()
    return "5 secondes se sont écoulées!"

def test_device():
    pass

if __name__ == "__main__":
    manager = TrackingApplication()
    device = TriggerDevice(1, test_device, "Test")
    manager.add_device(device)
    print(manager.run_until(five_sec))