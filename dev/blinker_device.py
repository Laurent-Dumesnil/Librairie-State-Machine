from typing import Self, TypeAlias, Callable, overload, Any, override
from state_machine_device import StateMachineDevice
from state_machine_utilities import MonitoredState, ConditionalTransition, DelaySinceEnteredCondition, StateValueCondition
from tracking_device import TrackingDevice
from enum import Enum, auto
from random import choice

BlinkerStateFactory:TypeAlias = Callable[[], MonitoredState]

class BlinkerDevice(StateMachineDevice) :
    """
    Dispositif de clignotant multifonctionnel capable de gérer des états d'allumage/extinction,
    des temporisations et des séquences de clignotement complexes.

    La classe gère un état machine avec plusieurs configurations possibles:
    - Allumé/Éteint simple
    - Allumé/Éteint temporisé
    - Clignotement continu
    - Clignotement avec durée totale limitée

    Args:
        off_state_factory (BlinkerStateFactory): Fabrique pour créer les états OFF.
        on_state_factory (BlinkerStateFactory): Fabrique pour créer les états ON.
    """

    def __init__(self : Self, off_state_factory : BlinkerStateFactory, on_state_factory : BlinkerStateFactory, initialized):
        """
        Initialise le dispositif de clignotant.

        Args:
            off_state_factory (BlinkerStateFactory): Fabrique pour créer les états OFF.
            on_state_factory (BlinkerStateFactory): Fabrique pour créer les états ON.
        """
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

        self.__delay_since_entered_condition_off = DelaySinceEnteredCondition(0, self.__off)
        self.__delay_since_entered_condition_on = DelaySinceEnteredCondition(0, self.__on)
        self.__delay_since_entered_condition_total_duration = DelaySinceEnteredCondition(0, self.__off)

        self.__off_duration.add_transition(ConditionalTransition(self.__delay_since_entered_condition_off, self.__on))
        self.__on_duration.add_transition(ConditionalTransition(self.__delay_since_entered_condition_on, self.__off))

        self.__blink_begin.custom_value = False
        self.__blink_begin.add_exiting_action([self.__blink_off.clear_exiting_actions, self.__blink_on.clear_exiting_actions])
        self.__blink_begin.add_transition(ConditionalTransition(StateValueCondition(False, self.__blink_begin), self.__blink_off))
        self.__blink_begin.add_transition(ConditionalTransition(StateValueCondition(True, self.__blink_begin), self.__blink_on))

        self.__blink_off.add_transition(ConditionalTransition(self.__delay_since_entered_condition_off,self.__blink_on))
        self.__blink_on.add_transition(ConditionalTransition(self.__delay_since_entered_condition_on,self.__blink_off))

        self.__blink_stop_begin.custom_value = False
        self.__blink_stop_begin.add_transition(ConditionalTransition(StateValueCondition(False, self.__blink_stop_begin), self.__blink_stop_off))
        self.__blink_stop_begin.add_transition(ConditionalTransition(StateValueCondition(True, self.__blink_stop_begin), self.__blink_stop_on))

        self.__blink_stop_off.add_transition(ConditionalTransition(self.__delay_since_entered_condition_off,self.__blink_stop_on))
        self.__blink_stop_on.add_transition(ConditionalTransition(self.__delay_since_entered_condition_on,self.__blink_stop_off))
        self.__blink_stop_off.add_transition(ConditionalTransition(self.__delay_since_entered_condition_total_duration,self.__blink_stop_end))
        self.__blink_stop_on.add_transition(ConditionalTransition(self.__delay_since_entered_condition_total_duration,self.__blink_stop_end))

        self.__blink_stop_end.custom_value = False
        self.__blink_stop_end.add_transition(ConditionalTransition(StateValueCondition(False, self.__blink_stop_end), self.__on))
        self.__blink_stop_end.add_transition(ConditionalTransition(StateValueCondition(True, self.__blink_stop_end), self.__off))

        tuple_states = (self.__off, self.__off_duration, self.__blink_off, self.__blink_stop_off, self.__on, self.__on_duration, self.__blink_on,self.__blink_stop_on, self.__blink_begin, self.__blink_stop_begin, self.__blink_stop_end)
        layout = StateMachineDevice.Layout(tuple_states)
        super().__init__(layout, initialized=initialized)

    @property
    def is_off(self) -> bool :
        """
        Vérifie si le clignotant est dans un état éteint.

        Returns:
            bool: True si le clignotant est éteint, False sinon.
        """
        return True if self.current_state in [self.__off, self.__off_duration, self.__blink_off, self.__blink_stop_off] else False
    
    @property
    def is_on(self) -> bool :
        """
        Vérifie si le clignotant est dans un état allumé.

        Returns:
            bool: True si le clignotant est allumé, False sinon.
        """
        return True if self.current_state in [self.__on, self.__on_duration, self.__blink_on, self.__blink_stop_on] else False

    def __set_delay_since_entered_condition_values(self:Self, delay_since_entered_condition:DelaySinceEnteredCondition, duration:float, monitered_state:MonitoredState) -> None:
        delay_since_entered_condition.duration = duration
        delay_since_entered_condition.monitored_state = monitered_state

    @overload
    def turn_off(self:Self) -> None: ...

    @overload
    def turn_off(self:Self, duration:float) -> None: ...

    def turn_off(self:Self, duration:float|None = None) -> None:
        """
        Éteint le clignotant, optionnellement pour une durée définie.

        Args:
            duration (float, optionnel): Durée pendant laquelle le clignotant reste éteint.
                                        Si None, le clignotant reste éteint indéfiniment.

        Raises:
            ValueError: Si la durée est négative ou nulle.
            TypeError: Si la durée n'est pas un float.
        """
        if duration == None:
            self._transit_to(self.__off)
        elif isinstance(duration, float):
            if duration <= 0:
                raise ValueError("Duration must be greater than 0")
            else:
                self.__set_delay_since_entered_condition_values(self.__delay_since_entered_condition_off, duration, self.__off_duration)
                self._transit_to(self.__off_duration)
        else:
            raise TypeError("Duration must be a float")
        
    @overload
    def turn_on(self:Self) -> None: ...

    @overload
    def turn_on(self:Self, duration:float) -> None: ...

    def turn_on(self:Self, duration:float|None = None) -> None:
        """
        Allume le clignotant, optionnellement pour une durée définie.

        Args:
            duration (float, optionnel): Durée pendant laquelle le clignotant reste allumé.
                                        Si None, le clignotant reste allumé indéfiniment.

        Raises:
            ValueError: Si la durée est négative ou nulle.
            TypeError: Si la durée n'est pas un float.
        """
        if duration == None:
            self._transit_to(self.__on)
        elif isinstance(duration, float):
            if duration <= 0:
                raise ValueError("Duration must be greater than 0")
            else:
                self.__set_delay_since_entered_condition_values(self.__delay_since_entered_condition_on, duration, self.__on_duration)
                self._transit_to(self.__on_duration)
        else:
            raise TypeError("Duration must be a float")
        
    @overload
    def blink(self:Self, *, cycle_duration:float, percent_on:float, begin_on:bool) -> None: ...

    @overload
    def blink(self:Self, *, total_duration:float, cycle_duration:float, percent_on:float, begin_on:bool, end_off:bool) -> None: ...

    @overload
    def blink(self:Self, *, total_duration:float, n_cycle:int, percent_on:float, begin_on:bool, end_off:bool) -> None: ...

    @overload
    def blink(self:Self, *, n_cycle:int, cycle_duration:float, percent_on:float, begin_on:bool, end_off:bool) -> None: ...

    def blink(self:Self, **kwargs:Any) -> None:
        """
        Fait clignoter le dispositif selon les paramètres donnés.

        Supporte plusieurs variantes de clignotement:
        1. Clignotement continu avec cycle_duration et percent_on
        2. Clignotement avec durée totale limitée et cycle_duration
        3. Clignotement avec nombre de cycles défini et cycle_duration
        4. Clignotement avec nombre de cycles et durée totale

        Args:
            cycle_duration (float, optionnel): Durée d'un cycle complet de clignotement (en secondes).
            percent_on (float, optionnel): Pourcentage du cycle durant lequel le clignotant est allumé (0.0-1.0).
            begin_on (bool): Si True, le clignotement commence à l'état allumé; sinon à l'état éteint.
            total_duration (float, optionnel): Durée totale du clignotement (en secondes).
            n_cycle (int, optionnel): Nombre de cycles complets à effectuer.
            end_off (bool, optionnel): Si True, termine en état éteint; sinon en état allumé.

        Raises:
            ValueError: Si les paramètres sont invalides ou hors limites.
            SyntaxError: Si la combinaison de paramètres n'est pas valide.
        """
        self.__validate_kwargs_blink(kwargs)
        k = set(kwargs.keys())

        if k == {"cycle_duration", "percent_on", "begin_on"}:
            self.__blink_begin.custom_value = kwargs["begin_on"]
            self.__set_delay_since_entered_condition_values(self.__delay_since_entered_condition_on, kwargs["cycle_duration"]*kwargs["percent_on"], self.__blink_on)
            self.__set_delay_since_entered_condition_values(self.__delay_since_entered_condition_off, kwargs["cycle_duration"]*(1-kwargs["percent_on"]), self.__blink_off)
            self._transit_to(self.__blink_begin)
        elif k == {"total_duration", "cycle_duration", "percent_on", "begin_on", "end_off"}:
            self.__blink_stop_begin.custom_value = kwargs["begin_on"]
            self.__blink_stop_end.custom_value = kwargs["end_off"]
            self.__set_delay_since_entered_condition_values(self.__delay_since_entered_condition_total_duration, kwargs["total_duration"], self.__blink_stop_begin)
            self.__set_delay_since_entered_condition_values(self.__delay_since_entered_condition_on, kwargs["cycle_duration"]*kwargs["percent_on"], self.__blink_stop_on)
            self.__set_delay_since_entered_condition_values(self.__delay_since_entered_condition_off, kwargs["cycle_duration"]*(1-kwargs["percent_on"]), self.__blink_stop_off)
            self._transit_to(self.__blink_stop_begin)
        elif k == {"total_duration", "n_cycle", "percent_on", "begin_on", "end_off"}:
            self.__blink_stop_begin.custom_value = kwargs["begin_on"]
            self.__blink_stop_end.custom_value = kwargs["end_off"]
            self.__set_delay_since_entered_condition_values(self.__delay_since_entered_condition_total_duration, kwargs["total_duration"], self.__blink_stop_begin)
            self.__set_delay_since_entered_condition_values(self.__delay_since_entered_condition_on, kwargs["total_duration"]/kwargs["n_cycle"]*kwargs["percent_on"], self.__blink_stop_on)
            self.__set_delay_since_entered_condition_values(self.__delay_since_entered_condition_off, kwargs["total_duration"]/kwargs["n_cycle"]*(1-kwargs["percent_on"]), self.__blink_stop_off)
            self._transit_to(self.__blink_stop_begin)
        elif k == {"n_cycle", "cycle_duration", "percent_on", "begin_on", "end_off"}:
            self.__blink_stop_begin.custom_value = kwargs["begin_on"]
            self.__blink_stop_end.custom_value = kwargs["end_off"]
            self.__set_delay_since_entered_condition_values(self.__delay_since_entered_condition_total_duration, kwargs["cycle_duration"]*kwargs["n_cycle"], self.__blink_stop_begin)
            self.__set_delay_since_entered_condition_values(self.__delay_since_entered_condition_on, kwargs["cycle_duration"]*kwargs["percent_on"], self.__blink_stop_on)
            self.__set_delay_since_entered_condition_values(self.__delay_since_entered_condition_off, kwargs["cycle_duration"]*(1-kwargs["percent_on"]), self.__blink_stop_off)
            self._transit_to(self.__blink_stop_begin)
        else:
            raise SyntaxError("Combination of method arguments invalid")
        
    def __validate_kwargs_blink(self:Self, kwargs_blink: dict[str, Any]) -> None:
        if "cycle_duration" in kwargs_blink:
            float(kwargs_blink["cycle_duration"])
            if kwargs_blink["cycle_duration"] < 0:
                raise ValueError("cycle_duration must be a float greater than 0")
        if "percent_on" in kwargs_blink:
            float(kwargs_blink["percent_on"])
            if kwargs_blink["percent_on"] < 0 or kwargs_blink["percent_on"] > 1:
                raise ValueError("percent_on must be a float between 0 and 1")
        if "begin_on" in kwargs_blink:
            if not isinstance(kwargs_blink["begin_on"], bool):
                raise ValueError("begin_on must be a bool")
        if "total_duration" in kwargs_blink:
            float(kwargs_blink["total_duration"])
            if kwargs_blink["total_duration"] < 0:
                raise ValueError("total_duration must be a float greater than 0")
        if "end_off" in kwargs_blink:
            if not isinstance(kwargs_blink["end_off"], bool):
                raise ValueError("end_off must be a bool")
        if "n_cycle" in kwargs_blink:
            if kwargs_blink["n_cycle"] < 0 or not isinstance(kwargs_blink["n_cycle"], int):
                raise ValueError("n_cycle must be an integer greater than 0")


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
            return self.__left_blinker.is_off
        elif side is SideBlinkersDevice.Side.RIGHT:
            return self.__right_blinker.is_off
        elif side is SideBlinkersDevice.Side.BOTH:
            return all((self.__left_blinker.is_off, self.__right_blinker.is_off))
        elif side is SideBlinkersDevice.Side.ANY:
            return any((self.__left_blinker.is_off, self.__right_blinker.is_off))
        elif side is SideBlinkersDevice.Side.LEFT_RECIPROCAL:
            return all((self.__left_blinker.is_off, self.__right_blinker.is_on))
        elif side is SideBlinkersDevice.Side.RIGHT_RECIPROCAL:
            return all((self.__left_blinker.is_on, self.__right_blinker.is_off))
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
            return self.__left_blinker.is_on
        elif side is SideBlinkersDevice.Side.RIGHT:
            return self.__right_blinker.is_on
        elif side is SideBlinkersDevice.Side.BOTH:
            return all((self.__left_blinker.is_on, self.__right_blinker.is_on))
        elif side is SideBlinkersDevice.Side.ANY:
            return any((self.__left_blinker.is_on, self.__right_blinker.is_on))
        elif side is SideBlinkersDevice.Side.LEFT_RECIPROCAL:
            return all((self.__left_blinker.is_on, self.__right_blinker.is_off))
        elif side is SideBlinkersDevice.Side.RIGHT_RECIPROCAL:
            return all((self.__left_blinker.is_off, self.__right_blinker.is_on))
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
        if duration is not None:
            if not isinstance(duration, float):
                raise TypeError("duration must be a float")
            if duration <= 0:
                raise ValueError("duration must be positive")

        if side is SideBlinkersDevice.Side.LEFT:
            self.__left_blinker.turn_off() if duration is None else self.__left_blinker.turn_off(duration)
        elif side is SideBlinkersDevice.Side.RIGHT:
            self.__right_blinker.turn_off() if duration is None else self.__right_blinker.turn_off(duration)
        elif side is SideBlinkersDevice.Side.BOTH:
            self.__left_blinker.turn_off() if duration is None else self.__left_blinker.turn_off(duration)
            self.__right_blinker.turn_off() if duration is None else self.__right_blinker.turn_off(duration)
        elif side is SideBlinkersDevice.Side.ANY:
            blinker = choice([self.__left_blinker, self.__right_blinker])
            blinker.turn_off() if duration is None else blinker.turn_off(duration)
        elif side is SideBlinkersDevice.Side.LEFT_RECIPROCAL:
            self.__left_blinker.turn_off() if duration is None else self.__left_blinker.turn_off(duration)
            self.__right_blinker.turn_on() if duration is None else self.__right_blinker.turn_on(duration)
        elif side is SideBlinkersDevice.Side.RIGHT_RECIPROCAL:
            self.__left_blinker.turn_on() if duration is None else self.__left_blinker.turn_on(duration)
            self.__right_blinker.turn_off() if duration is None else self.__right_blinker.turn_off(duration)
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
        if duration is not None:
            if not isinstance(duration, float):
                raise TypeError("duration must be a float")
            if duration <= 0:
                raise ValueError("duration must be positive")

        if side is SideBlinkersDevice.Side.LEFT:
            self.__left_blinker.turn_on() if duration is None else self.__left_blinker.turn_on(duration)
        elif side is SideBlinkersDevice.Side.RIGHT:
            self.__right_blinker.turn_on() if duration is None else self.__right_blinker.turn_on(duration)
        elif side is SideBlinkersDevice.Side.BOTH:
            self.__left_blinker.turn_on() if duration is None else self.__left_blinker.turn_on(duration)
            self.__right_blinker.turn_on() if duration is None else self.__right_blinker.turn_on(duration)
        elif side is SideBlinkersDevice.Side.ANY:
            blinker = choice([self.__left_blinker, self.__right_blinker])
            blinker.turn_on() if duration is None else blinker.turn_on(duration)
        elif side is SideBlinkersDevice.Side.LEFT_RECIPROCAL:
            self.__left_blinker.turn_on() if duration is None else self.__left_blinker.turn_on(duration)
            self.__right_blinker.turn_off() if duration is None else self.__right_blinker.turn_off(duration)
        elif side is SideBlinkersDevice.Side.RIGHT_RECIPROCAL:
            self.__left_blinker.turn_off() if duration is None else self.__left_blinker.turn_off(duration)
            self.__right_blinker.turn_on() if duration is None else self.__right_blinker.turn_on(duration)
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
            begin_opposite = not kwargs["begin_on"]
            del kwargs["begin_on"]
            self.__right_blinker.blink(**kwargs, begin_on=begin_opposite)
        elif side is SideBlinkersDevice.Side.RIGHT_RECIPROCAL:
            self.__right_blinker.blink(**kwargs)
            begin_opposite = not kwargs["begin_on"]
            del kwargs["begin_on"]
            self.__left_blinker.blink(**kwargs, begin_on=begin_opposite)
        else:
            raise ValueError(f"{side} n'est pas une donnée valide")
        
    @override
    def _do_tracking(self, elapsed_time):
        return super()._do_tracking(elapsed_time)


    