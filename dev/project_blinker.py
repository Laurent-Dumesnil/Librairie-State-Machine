from blinker_device import BlinkerDevice
from state_machine_utilities import MonitoredState
from tracking_device import TrackingApplication

def main():

    def light_on():
        print(f"\r On   ", end="", sep="")

    def light_off():
        print(f"\r Off   ", end="", sep="")

    def get_on_state():
        on_state = MonitoredState("on")
        on_state.add_entering_action(light_on)
        return on_state
    
    def get_off_state():
        off_state = MonitoredState("off")
        off_state.add_entering_action(light_off)
        return off_state


    app = TrackingApplication()

    #############################
    #    TEST BLINKERDEVICE
    #############################

    blinker = BlinkerDevice(get_off_state, get_on_state, initialized=False)
    blinker.blink(cycle_duration=2.0, percent_on=0.5, begin_on=False)
    app.add_device(blinker)
    app.run_forever()

if __name__ == "__main__":
    quit(main())
