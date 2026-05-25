from console import Console
from typing import Self

class SimpleLed():
    def __init__(self: Self, console:Console, pos: tuple[int, int], size: tuple[int, int]) -> None:
        self.__console:Console = console
        self.__pos: tuple[int, int] = pos
        self.__size: tuple[int, int] = size

    def draw_led(self:Self, color:Console.Color) -> None:
        self.__console.background_color = color
        for row in range(self.__size[1]):
            self.__console.write(' ' * self.__size[0],(self.__pos[0], self.__pos[1] + row))


class BarLed():
    def __init__(self: Self, console:Console, pos: tuple[int, int], size: tuple[int, int], number_of_leds:int, list_color:list[Console.Color]) -> None:
        self.__console:Console = console
        self.__pos: tuple[int, int] = pos
        self.__size_of_leds: tuple[int, int] = size
        self.__number_of_leds:int = number_of_leds
        self.__list_color: list[Console.Color] = list_color
        self.__list_led: list[SimpleLed] = []
        self.__initialize_leds()

    def __initialize_leds(self:Self) -> None:
        for current_pos in range(self.__number_of_leds):
            self.__list_led.append(SimpleLed(self.__console, (self.__pos[0] + 2 * current_pos, self.__pos[1]), self.__size_of_leds))

    def draw_led(self:Self, percent_on:float) -> None:
        led_to_open = int(percent_on*len(self.__list_led)/100)
        for i, led in enumerate(self.__list_led):
            if i < led_to_open:
                led.draw_led(self.__list_color[i])
            else:
                led.draw_led(self.__console.Color.DARK_GREY)


class ElectricScooterPanel():
    def __init__(self: Self, console: Console) -> None:
        self.__console: Console = console
        self.__console.window_size = (100, 45)
        self.top_left_blinker:SimpleLed = SimpleLed(self.__console, (2,2), (11,1))
        self.bottom_left_blinker:SimpleLed = SimpleLed(self.__console, (2,18), (11,1))
        self.top_right_blinker:SimpleLed = SimpleLed(self.__console, (80,2), (11,1))
        self.bottom_right_blinker:SimpleLed = SimpleLed(self.__console, (80,18), (11,1))
        self.left_side_light:SimpleLed = SimpleLed(self.__console, (7,4),(1,13))
        self.right_side_light:SimpleLed = SimpleLed(self.__console, (85,4),(1,13))
        self.headlight:SimpleLed = SimpleLed(self.__console, (20,2), (50,1))
        self.rearlight:SimpleLed = SimpleLed(self.__console, (20,18), (50,1))
        self.left_indicator:SimpleLed = SimpleLed(self.__console, (20,4),(6,1))
        self.right_indicator:SimpleLed = SimpleLed(self.__console, (64,4),(6,1))
        self.speed_indicator:BarLed = BarLed(self.__console, (20,6), (1,2), 25, [Console.Color.GREEN]*25)
        self.charge_indicator:BarLed = BarLed(self.__console, (20,10), (1,2), 25, [Console.Color.BLUE]*5+[Console.Color.LIGHT_BLUE]*5+[Console.Color.CYAN]*5+[Console.Color.LIGHT_CYAN]*5+[Console.Color.WHITE]*5)
        self.temp_indicator:BarLed = BarLed(self.__console, (20,14), (1,2), 25, [Console.Color.LIGHT_BLUE]*5+[Console.Color.LIGHT_MAGENTA]*5+[Console.Color.MAGENTA]*5+[Console.Color.RED]*5+[Console.Color.WHITE]*5)
        self.__list_simpleled = [self.top_left_blinker, 
                               self.bottom_left_blinker, 
                               self.top_right_blinker, 
                               self.bottom_right_blinker,
                               self.left_side_light,
                               self.right_side_light,
                               self.headlight,
                               self.rearlight,
                               self.left_indicator,
                               self.right_indicator]
        self.__list_barled = [self.speed_indicator, self.charge_indicator, self.temp_indicator]
        self.__draw_all()

    def __draw_all(self:Self) -> None:
        for simple_led in self.__list_simpleled:
            simple_led.draw_led(self.__console.Color.DARK_GREY)
        for bar_led in self.__list_barled:
            bar_led.draw_led(0)
        self.__console.text_color = self.__console.Color.DARK_GREY
        self.__console.background_color = self.__console.Color.BLACK
        self.__console.write('Speed',(42,8))
        self.__console.write('Battery charge',(37,12))
        self.__console.write('Battery temperature',(35,16))

if __name__ == '__main__':
    console = Console()
    console.clear()
    panel = ElectricScooterPanel(console)
    console.reset_colors()