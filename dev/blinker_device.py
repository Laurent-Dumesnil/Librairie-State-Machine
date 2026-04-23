from typing import Self, TypeAlias, Callable, overload, Any
from state_machine_device import StateMachineDevice 
from state_machine_utilities import MonitoredState, ConditionalTransition, DelaySinceEnteredCondition, StateValueCondition
from tracking_device import TrackingDevice
from enum import Enum, auto
from random import choice

BlinkerStateFactory:TypeAlias = Callable[[], MonitoredState]

class BlinkerDevice(StateMachineDevice) :

    def __init__(self, off_state_factory : BlinkerStateFactory, on_state_factory : BlinkerStateFactory):

        self.__off = off_state_factory()
        self.__on = on_state_factory()

        self.__off_duration = off_state_factory()
        self.__blink_off = off_state_factory()
        self.__blink_stop_off = off_state_factory()

        self.__on_duration = on_state_factory()
        self.__blink_on = on_state_factory()
        self.__blink_stop_on = on_state_factory()

        self.__blink_begin = MonitoredState()
        self.__blink_stop_begin = MonitoredState()
        self.__blink_stop_end = MonitoredState()

        self.__delay_since_entered_condition = DelaySinceEnteredCondition(0)

        self.__off_duration.add_transition(ConditionalTransition(self.__delay_since_entered_condition, self.__on))
        self.__on_duration.add_transition(ConditionalTransition(self.__delay_since_entered_condition, self.__off))

        self.__blink_begin.custom_value = False
        self.__blink_begin.add_transition(ConditionalTransition(StateValueCondition(False, self.__blink_begin), self.__blink_off))
        self.__blink_begin.add_transition(ConditionalTransition(StateValueCondition(True, self.__blink_begin), self.__blink_on))

        self.__blink_off.add_transition(ConditionalTransition(self.__delay_since_entered_condition,self.__blink_on))
        self.__blink_on.add_transition(ConditionalTransition(self.__delay_since_entered_condition,self.__blink_off))

        self.__blink_stop_begin.custom_value = False
        self.__blink_stop_begin.add_transition(ConditionalTransition(StateValueCondition(False, self.__blink_stop_begin), self.__blink_off))
        self.__blink_stop_begin.add_transition(ConditionalTransition(StateValueCondition(True, self.__blink_stop_begin), self.__blink_on))

        self.__blink_stop_off.add_transition(ConditionalTransition(self.__delay_since_entered_condition,self.__blink_stop_on))
        self.__blink_stop_on.add_transition(ConditionalTransition(self.__delay_since_entered_condition,self.__blink_stop_off))
        self.__blink_stop_off.add_transition(ConditionalTransition(self.__delay_since_entered_condition,self.__blink_stop_end))
        self.__blink_stop_on.add_transition(ConditionalTransition(self.__delay_since_entered_condition,self.__blink_stop_end))

        self.__blink_stop_end.custom_value = False
        self.__blink_stop_end.add_transition(ConditionalTransition(StateValueCondition(False, self.__blink_stop_end), self.__blink_on))
        self.__blink_stop_end.add_transition(ConditionalTransition(StateValueCondition(True, self.__blink_stop_end), self.__blink_off))

        layout = (self.__off, self.__off_duration, self.__blink_off, self.__blink_stop_off, self.__on, self.__on_duration, self.__blink_on,self.__blink_stop_on, self.__blink_begin, self.__blink_stop_begin, self.__blink_stop_end)

        super().__init__(layout)

    @property
    def is_off(self) -> bool :
        return True if self.current_state in [self.__off, self.__off_duration, self.__blink_off, self.__blink_stop_off] else False
    
    @property
    def is_on(self) -> bool :
        return True if self.current_state in [self.__on, self.__on_duration, self.__blink_on, self.__blink_stop_on] else False

    def __set_delay_since_entered_condition_values(self:Self, duration:float, monitered_state:MonitoredState):
        self.__delay_since_entered_condition.duration = duration
        self.__delay_since_entered_condition.monitored_state = monitered_state

    @overload
    def turn_off(self:Self) -> None: ...

    @overload
    def turn_off(self:Self, duration:float) -> None: ...

    def turn_off(self:Self, duration:float|None = None) -> None:
        if duration == None:
            self._transit_to(self.__off)
        elif isinstance(duration, float):
            if duration < 0:
                raise ValueError("Duration must be greater than 0")
            else:
                self.__set_delay_since_entered_condition_values(duration, self.__off_duration)
                self._transit_to(self.__off_duration)
        else:
            raise TypeError("Duration must be a float")
        
    @overload
    def turn_on(self:Self) -> None: ...

    @overload
    def turn_on(self:Self, duration:float) -> None: ...

    def turn_on(self:Self, duration:float|None = None) -> None:
        if duration == None:
            self._transit_to(self.__on)
        elif isinstance(duration, float):
            if duration < 0:
                raise ValueError("Duration must be greater than 0")
            else:
                self.__set_delay_since_entered_condition_values(duration, self.__on_duration)
                self._transit_to(self.__on_duration)
        else:
            raise TypeError("Duration must be a float")

class SideBlinkersDevice(TrackingDevice):
    """
    Gère deux clignotants latéraux (gauche et droit) en tant que sous-appareils.

    Permet de contrôler indépendamment ou simultanément les clignotants.

    Args:
        left_off_state_factory (BlinkerStateFactory): Fabrique d'état OFF pour le clignotant gauche.
        left_on_state_factory (BlinkerStateFactory): Fabrique d'état ON pour le clignotant gauche.
        right_off_state_factory (BlinkerStateFactory): Fabrique d'état OFF pour le clignotant droit.
        right_on_state_factory (BlinkerStateFactory): Fabrique d'état ON pour le clignotant droit.
        name (str, optionnel): Nom du dispositif.
        enabled (bool, optionnel): Si le dispositif est activé.
    """

    class Side(Enum):
        """
        Enumération des côtés contrôlables pour les clignotants.
        """
        LEFT = auto()
        RIGHT = auto()
        ANY = auto()
        BOTH = auto()
        LEFT_RECIPROCAL = auto()
        RIGHT_RECIPROCAL = auto()

    def __init__(self:Self, left_off_state_factory:BlinkerStateFactory, left_on_state_factory:BlinkerStateFactory, right_off_state_factory:BlinkerStateFactory, right_on_state_factory:BlinkerStateFactory, name:str|None = None, enabled:bool = True) -> None:
        """
        Initialise le dispositif de clignotants latéraux.

        Args:
            left_off_state_factory (BlinkerStateFactory): Fabrique d'état OFF pour le clignotant gauche.
            left_on_state_factory (BlinkerStateFactory): Fabrique d'état ON pour le clignotant gauche.
            right_off_state_factory (BlinkerStateFactory): Fabrique d'état OFF pour le clignotant droit.
            right_on_state_factory (BlinkerStateFactory): Fabrique d'état ON pour le clignotant droit.
            name (str, optionnel): Nom du dispositif.
            enabled (bool, optionnel): Si le dispositif est activé.
        """
        super().__init__(name, enabled)
        self.__left_blinker:BlinkerDevice = BlinkerDevice(left_off_state_factory, left_on_state_factory)
        self.__right_blinker:BlinkerDevice = BlinkerDevice(right_off_state_factory, right_on_state_factory)
        self.add_sub_device([self.__left_blinker, self.__right_blinker])

    def is_off(self: Self, side: Side) -> bool:
        """
        Vérifie si le(s) clignotant(s) spécifié(s) est/sont éteint(s).

        Args:
            side (SideBlinkersDevice.Side): Le ou les côtés à vérifier.

        Returns:
            bool: True si le(s) clignotant(s) est/sont éteint(s), False sinon.

        Raises:
            ValueError: Si le côté n'est pas valide.
        """
        if side is SideBlinkersDevice.Side.LEFT:
            return self.__left_blinker.is_off()
        elif side is SideBlinkersDevice.Side.RIGHT:
            return self.__right_blinker.is_off()
        elif side is SideBlinkersDevice.Side.BOTH:
            return all((self.__left_blinker.is_off(), self.__right_blinker.is_off()))
        elif side is SideBlinkersDevice.Side.ANY:
            return any((self.__left_blinker.is_off(), self.__right_blinker.is_off()))
        elif side is SideBlinkersDevice.Side.LEFT_RECIPROCAL:
            return all((self.__left_blinker.is_off(), self.__right_blinker.is_on()))
        elif side is SideBlinkersDevice.Side.RIGHT_RECIPROCAL:
            return all((self.__left_blinker.is_on(), self.__right_blinker.is_off()))
        else:
            raise ValueError(f"{side} n'est pas une donnée valide")
    
    def is_on(self:Self, side:Side) -> bool:
        """
        Vérifie si le(s) clignotant(s) spécifié(s) est/sont allumé(s).

        Args:
            side (SideBlinkersDevice.Side): Le ou les côtés à vérifier.

        Returns:
            bool: True si le(s) clignotant(s) est/sont allumé(s), False sinon.

        Raises:
            ValueError: Si le côté n'est pas valide.
        """
        if side is SideBlinkersDevice.Side.LEFT:
            return self.__left_blinker.is_on()
        elif side is SideBlinkersDevice.Side.RIGHT:
            return self.__right_blinker.is_on()
        elif side is SideBlinkersDevice.Side.BOTH:
            return all((self.__left_blinker.is_on(), self.__right_blinker.is_on()))
        elif side is SideBlinkersDevice.Side.ANY:
            return any((self.__left_blinker.is_on(), self.__right_blinker.is_on()))
        elif side is SideBlinkersDevice.Side.LEFT_RECIPROCAL:
            return all((self.__left_blinker.is_on(), self.__right_blinker.is_off()))
        elif side is SideBlinkersDevice.Side.RIGHT_RECIPROCAL:
            return all((self.__left_blinker.is_off(), self.__right_blinker.is_on()))
        else:
            raise ValueError(f"{side} n'est pas une donnée valide")
        
    @overload
    def turn_off(self:Self, side:Side) -> None: ...

    @overload
    def turn_off(self:Self, side:Side, duration:float) -> None: ...

    def turn_off(self:Self, side:Side, duration:float|None = None) -> None:
        """
        Éteint le(s) clignotant(s) spécifié(s), éventuellement pour une durée donnée.

        Args:
            side (SideBlinkersDevice.Side): Le ou les côtés à éteindre.
            duration (float, optionnel): Durée pendant laquelle éteindre.

        Raises:
            ValueError: Si le côté n'est pas valide.
        """
        if side is SideBlinkersDevice.Side.LEFT:
            self.__left_blinker.turn_off(duration)
        elif side is SideBlinkersDevice.Side.RIGHT:
            self.__right_blinker.turn_off(duration)
        elif side is SideBlinkersDevice.Side.BOTH:
            self.__left_blinker.turn_off(duration)
            self.__right_blinker.turn_off(duration)
        elif side is SideBlinkersDevice.Side.ANY:
            rng = choice([self.__left_blinker.turn_off, self.__right_blinker.turn_off])
            rng(duration)
        elif side is SideBlinkersDevice.Side.LEFT_RECIPROCAL:
            self.__left_blinker.turn_off(duration)
            self.__right_blinker.turn_on(duration)
        elif side is SideBlinkersDevice.Side.RIGHT_RECIPROCAL:
            self.__left_blinker.turn_on(duration)
            self.__right_blinker.turn_off(duration)
        else:
            raise ValueError(f"{side} n'est pas une donnée valide")
        
    @overload
    def turn_on(self:Self, side:Side) -> None: ...
    
    @overload
    def turn_on(self:Self, side:Side, duration:float) -> None: ...

    def turn_on(self:Self, side:Side, duration:float|None = None) -> None:
        """
        Allume le(s) clignotant(s) spécifié(s), éventuellement pour une durée donnée.

        Args:
            side (SideBlinkersDevice.Side): Le ou les côtés à allumer.
            duration (float, optionnel): Durée pendant laquelle allumer.

        Raises:
            ValueError: Si le côté n'est pas valide.
        """
        if side is SideBlinkersDevice.Side.LEFT:
            self.__left_blinker.turn_on(duration)
        elif side is SideBlinkersDevice.Side.RIGHT:
            self.__right_blinker.turn_on(duration)
        elif side is SideBlinkersDevice.Side.BOTH:
            self.__left_blinker.turn_on(duration)
            self.__right_blinker.turn_on(duration)
        elif side is SideBlinkersDevice.Side.ANY:
            rng = choice([self.__left_blinker.turn_on, self.__right_blinker.turn_on])
            rng(duration)
        elif side is SideBlinkersDevice.Side.LEFT_RECIPROCAL:
            self.__left_blinker.turn_on(duration)
            self.__right_blinker.turn_off(duration)
        elif side is SideBlinkersDevice.Side.RIGHT_RECIPROCAL:
            self.__left_blinker.turn_off(duration)
            self.__right_blinker.turn_on(duration)
        else:
            raise ValueError(f"{side} n'est pas une donnée valide")
        
    @overload
    def blink(self:Self, side:Side, *, cycle_duration:float, percent_on:float, begin_on:bool) -> None: ...

    @overload
    def blink(self:Self, side:Side, *, total_duration:float, cycle_duration:float, percent_on:float, begin_on:bool, end_off:bool) -> None: ...

    @overload
    def blink(self:Self, side:Side, *, total_duration:float, n_cycle:int, percent_on:float, begin_on:bool, end_off:bool) -> None: ...

    @overload
    def blink(self:Self, side:Side, *, n_cycle:int, cycle_duration:float, percent_on:float, begin_on:bool, end_off:bool) -> None: ...

    def blink(self:Self, side:Side, **kwargs:Any) -> None:
        """
        Fait clignoter le(s) clignotant(s) spécifié(s) selon les paramètres donnés.

        Args:
            side (SideBlinkersDevice.Side): Le ou les côtés à faire clignoter.
            **kwargs: Paramètres de clignotement (voir documentation de BlinkerDevice.blink).

        Raises:
            ValueError: Si le côté n'est pas valide.
        """
        if side is SideBlinkersDevice.Side.LEFT:
            self.__left_blinker.blink(**kwargs)
        elif side is SideBlinkersDevice.Side.RIGHT:
            self.__right_blinker.blink(**kwargs)
        elif side is SideBlinkersDevice.Side.BOTH:
            self.__left_blinker.blink(**kwargs)
            self.__right_blinker.blink(**kwargs)
        elif side is SideBlinkersDevice.Side.ANY:
            rng = choice([self.__left_blinker.blink, self.__right_blinker.blink])
            rng(**kwargs)
        elif side is SideBlinkersDevice.Side.LEFT_RECIPROCAL:
            self.__left_blinker.blink(**kwargs)
            self.__right_blinker.blink(**kwargs)
        elif side is SideBlinkersDevice.Side.RIGHT_RECIPROCAL:
            self.__left_blinker.blink(**kwargs)
            self.__right_blinker.blink(**kwargs)
        else:
            raise ValueError(f"{side} n'est pas une donnée valide")

def main():
    def factory_off():
        off_state = MonitoredState()
        return off_state
    
    b = BlinkerDevice(factory_off)

    