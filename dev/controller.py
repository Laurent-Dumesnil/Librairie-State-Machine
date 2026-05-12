from scooter import Scooter
from console import Console
from ElectricScooterPanel import ElectricScooterPanel
from tracking_device import TrackingApplication
from scooter_state_machine import ScooterStateMachine, Scooting, Charging

def main():
    console = Console()
    panel = ElectricScooterPanel(console)
    scooter = Scooter(panel)
    app = TrackingApplication()
    ride_management = Scooting.RideManagement(console, scooter)
    scooter_state_machine = ScooterStateMachine(console, scooter, ride_management)
    app.add_device(ride_management)

    app.add_device(scooter_state_machine)
    app.run_forever()

if __name__ == "__main__":
    quit(main())