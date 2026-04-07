"""
Module de gestion de dispositifs de suivi basé sur l'approche de programmation en flux tiré.

Ce module permet le développement d'applications exploitant une architecture de suivi de composants utilisant deux paradigmes :
- Programmation orientée objet (OOP) : Les composants respectent une interface polymorphe pour généraliser et simplifier le développement.
- Programmation en flux tiré : Le suivi de l'état est initié explicitement par des appels réguliers dans une boucle de contrôle principale.

Classes principales :
    TrackingDevice : Classe abstraite représentant un dispositif de suivi générique. Gère l'état, les sous-dispositifs et la logique de suivi.
    TrackingManager : Classe permettant la gestion de plusieurs dispositifs de suivi.
    TrackingApplication : Classe spécialisée de TrackingManager qui gère l'application de suivi globale, la boucle principale et la synchronisation.
    TriggerDevice : Classe concrète dérivée de TrackingDevice permettant le déclenchement périodique d'une action à un intervalle spécifié.

Exemple minimal d'utilisation :
    from tracking_device import TriggerDevice, TrackingApplication
    def action():
        print("Action!")
    device = TriggerDevice(duration=5.0, action=action, name="MyDevice")
    app = TrackingApplication()
    app.add_device(device)
    app.run_forever()
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import final, override
from base_component import BaseComponent
from type_utilities import GenericCallback

from base_component import BaseComponent
from elapsed_timer import ElapsedTimer
from typing import Iterable, Callable, TypeAlias, Any, NoReturn, Self
from abc import ABC, abstractmethod

#Commande pour corriger le fichier:
#mypy --strict --check-untyped-defs tracking_device.py

class TrackingDevice(BaseComponent, ABC):
    """
    Classe de base représentant un dispositif de suivi.

    Pour maintenir son état, le dispositif doit être mis à jour par un appel formel de la méthode `track`. 
    Tous les dispositifs restent synchronisés s'ils sont tous maintenus à jour simultanément. 
    Un dispositif peut posséder des sous-dispositifs (patron composite).

    Attributs:
        name (str | None): Le nom du dispositif de suivi.
        enabled (bool): Indique si le dispositif est activé.
        sub_devices_count (int): Le nombre de sous-dispositifs gérés par ce dispositif.
    """
    def __init__(self, name: str | None = None, enabled: bool = True):
        """
        Initialise une nouvelle instance de la classe TrackingDevice.

        Args:
            name (str | None): Le nom du dispositif de suivi. Par défaut, None.
            enabled (bool, optionnel): Indique si le dispositif est activé. Par défaut, True.
        """
        self.__sub_devices: dict[str, TrackingDevice] = {}
        super().__init__(name=name, enabled=enabled)

    @property
    @final
    def valid(self) -> bool:
        """
        Établit la validation/conformité du dispositif conditionnel à tous ses sous-dispositifs.

        Returns:
            bool: True si le dispositif et tous ses sous-dispositifs sont valides, sinon False.
        """
        if not self._do_valid():
            return False
        for tracking_device in self.__sub_devices.values():
            if not tracking_device.valid:
                return False
        return True
    
    def _do_valid(self) -> bool:
        """
        Effectue la logique de validation spécifique au dispositif.

        Returns:
            bool: True si valide, sinon False.
        """
        return True
    
    @property
    def sub_devices_count(self) -> int:
        """
        Le nombre de sous-dispositifs présents.

        Returns:
            int: Nombre de sous-dispositifs.
        """
        return len(self.__sub_devices)

    def _do_reset(self) -> None:
        """
        Réinitialise l'état du dispositif de suivi.

        Ne fait rien par défaut. Les classes dérivées doivent substituer cette méthode si nécessaire.
        """
        pass

    @abstractmethod
    def _do_tracking(self, elapsed_time: float) -> None:
        """
        Effectue la logique de suivi du dispositif.

        Args:
            elapsed_time (float): Le temps écoulé depuis la dernière mise à jour du suivi.
        """
        pass

    def clear_sub_devices(self) -> None:
        """
        Supprime tous les sous-dispositifs.
        """
        self.__sub_devices.clear()

    def add_sub_device(self, device: TrackingDevice | Iterable[TrackingDevice]) -> None:
        """
        Ajoute un ou plusieurs sous-dispositifs.

        Args:
            device (TrackingDevice | Iterable[TrackingDevice]): Le ou les sous-dispositifs à ajouter.
        Raises:
            ValueError: Si un sous-dispositif portant le même nom existe déjà.
            TypeError: Si l'élément n'est pas de type TrackingDevice.
        """
        if isinstance(device, TrackingDevice):
            if device.name in self.__sub_devices:
                raise ValueError(f'{device.name} existe déjà comme nom de device')
            self.__sub_devices[device.name] = device
        elif isinstance(device, Iterable):
            for d in device:
                if not isinstance(d, TrackingDevice):
                    raise TypeError("Il faut ajouter un élément de type TrackingDevice")
                if d.name in self.__sub_devices:
                    raise ValueError(f'{d.name} existe déjà comme nom de device')   
                self.__sub_devices[d.name] = d
        else:
            raise TypeError("Il faut ajouter un élément de type TrackingDevice")

    def remove_sub_device(self, name: str | Iterable[str]) -> None:
        """
        Supprime un ou plusieurs sous-dispositifs.

        Args:
            name (str | Iterable[str]): Le ou les noms des sous-dispositifs à supprimer.
        Raises:
            TypeError: Si l'élément à supprimer n'est pas de type str.
        """
        if isinstance(name, str):
            if name in self.__sub_devices:
                del self.__sub_devices[name]
        elif isinstance(name, Iterable):
            for n in name:
                if isinstance(n, str):
                    if n in self.__sub_devices:
                        del self.__sub_devices[n]
                else:
                    raise TypeError("Il faut supprimer un élément de type str")
        else:
            raise TypeError("Il faut supprimer un élément de type str")

    @final
    def reset(self) -> None:
        """
        Réinitialise l'état du dispositif de suivi et de tous ses sous-dispositifs.
        """
        for tracking_device in self.__sub_devices.values():
            tracking_device.reset()
        self._do_reset()

    @final
    def track(self, elapsed_time: float) -> None:
        """
        Suit l'état du dispositif et de tous ses sous-dispositifs.

        Args:
            elapsed_time (float): Le temps écoulé depuis la dernière mise à jour du suivi.
        """
        if not self.enabled or not self.valid:
            return
        for tracking_device in self.__sub_devices.values():
            tracking_device.track(elapsed_time)
        self._do_tracking(elapsed_time)



class TrackingManager():
    """
    Classe gérant une collection d'instances de TrackingDevice.

    Fournit une interface pour ajouter, supprimer et gérer ces dispositifs collectivement. 
    Permet de suivre, réinitialiser et valider plusieurs dispositifs de manière synchronisée.

    Attributs:
        device_count (int): Le nombre de dispositifs de suivi actuellement gérés.
        valid (bool): Indique si tous les dispositifs sont valides.
    """
    def __init__(self:Self):
        """
        Initialise une nouvelle instance de TrackingManager.
        """
        self.__tracking_devices:dict[str, TrackingDevice] = {}

    @property
    def valid(self:Self) -> bool:
        """
        Indique si tous les dispositifs sont valides.

        Returns:
            bool: True si tous les dispositifs sont valides, sinon False.
        """
        for device in self.__tracking_devices.values():
            if not device.valid:
                return False
        return True
    
    @property
    def device_count(self:Self) -> int:
        """
        Le nombre de dispositifs actuellement gérés.

        Returns:
            int: Nombre de dispositifs gérés.
        """
        return len(self.__tracking_devices)
    
    def clear_devices(self:Self) -> None:
        """
        Supprime tous les dispositifs de suivi du gestionnaire.
        """
        self.__tracking_devices.clear()

    def add_device(self:Self, device : TrackingDevice | Iterable[TrackingDevice]) -> None:
        """
        Ajoute un ou plusieurs dispositifs de suivi au gestionnaire.

        Args:
            device (TrackingDevice | Iterable[TrackingDevice]): Le ou les dispositifs à ajouter.
        Raises:
            TypeError: Si le type n'est pas un TrackingDevice ou un itérable de TrackingDevice.
        """
        if isinstance(device, TrackingDevice):
            self.__tracking_devices[device.name] = device

        elif isinstance(device, Iterable):
            for d in device:
                if isinstance(d, TrackingDevice):
                    self.__tracking_devices[d.name] = d
        else:
            raise TypeError(f'Le type de {device} doit être un TrackingDevice ou un iterable de TrackingDevice. Présentement {type(device)}')

    def remove_device(self:Self, device : str | TrackingDevice | Iterable[str] | Iterable[TrackingDevice]) -> None:
        """
        Supprime un ou plusieurs dispositifs de suivi par nom ou par instance.

        Args:
            device (str | TrackingDevice | Iterable[str] | Iterable[TrackingDevice]): Le ou les dispositifs à supprimer.
        Raises:
            TypeError: Si le type n'est pas un TrackingDevice ou un itérable de TrackingDevice.
        """
        if isinstance(device, str):
            if device in self.__tracking_devices:
                del self.__tracking_devices[device]
        
        elif isinstance(device, TrackingDevice):
            if device.name in self.__tracking_devices:
                del self.__tracking_devices[device.name] 
          
        elif isinstance(device, Iterable):
            for d in device:
                if isinstance(d, str):
                    if d in self.__tracking_devices:
                        del self.__tracking_devices[d]
                elif isinstance(d, TrackingDevice):
                    if d.name in self.__tracking_devices:
                        del self.__tracking_devices[d.name]
        else:
            raise TypeError(f'Le type de {device} doit être un TrackingDevice ou un iterable de TrackingDevice. Présentement {type(device)}')
    
    def track(self:Self, elapsed_time : float) -> None:
        """
        Met à jour l'état de suivi de tous les dispositifs en fonction du temps écoulé.

        Args:
            elapsed_time (float): Le temps écoulé depuis la dernière mise à jour.
        """
        for device in self.__tracking_devices.values():
                device.track(elapsed_time)

    def reset(self:Self) -> None:
        """
        Réinitialise tous les dispositifs de suivi à leur état initial.
        """
        for device in self.__tracking_devices.values():
                device.reset()

class TrackingApplication(TrackingManager):
    """
    Classe représentant une application exploitant les dispositifs TrackingManager.

    Fournit un cadre pour créer des applications qui effectuent des opérations de suivi en continu. 
    Permet de gérer des TrackingDevice qui doivent fonctionner de manière ininterrompue tout en les synchronisant.
    """
    RunningCondition:TypeAlias = Callable[[], Any|None]

    def __init__(self:Self) -> None:
        """
        Initialise l'application de suivi.
        """
        super().__init__()
        self.__elapsed_timer:ElapsedTimer = ElapsedTimer()

    def run_forever(self:Self) -> NoReturn:
        """
        Exécute l'application indéfiniment.

        Cette méthode exécute une boucle infinie qui suit le temps et appelle la méthode `track` de tous les dispositifs.
        """
        while True:
            self.track(self.__elapsed_timer.elapsed)
            

    def run_until(self:Self, running_condition:RunningCondition) -> Any:
        """
        Exécute l'application jusqu'à ce que la condition fournie soit remplie.

        La boucle continue jusqu'à ce que la condition renvoie une valeur autre que None. 
        Chaque itération suit le temps et appelle la méthode `track` de tous les dispositifs.

        Args:
            running_condition (Callable[[], Any | None]): La condition à remplir pour arrêter l'itération.
        Returns:
            Any: Le résultat renvoyé par la condition lorsqu'elle est remplie.
        """
        result:Any = running_condition()
        while result is None:
            self.track(self.__elapsed_timer.elapsed)
            result = running_condition()

        return result

class TriggerDevice(TrackingDevice):
    """
    Classe représentant un dispositif déclencheur qui exécute une action après une certaine durée.

    Attributs:
        duration (float): La durée après laquelle l'action est déclenchée.
        action (GenericCallback): L'action à exécuter lorsque la durée est atteinte.
        name (str | None): Le nom du dispositif.
        enabled (bool): Indique si le dispositif est activé.
        initial_time (float): Le temps initial accumulé.
        auto_reset_when_enabling (bool): Indique si le compteur doit être réinitialisé lors de l'activation.
    """
    def __init__(self, duration: float, action: GenericCallback, /, name: str | None = None, enabled: bool = True, *, initial_time: float = 0.0, auto_reset_when_enabling: bool = True):
        """
        Initialise un nouveau TriggerDevice.

        Args:
            duration (float): La durée après laquelle l'action est déclenchée.
            action (GenericCallback): L'action à exécuter lorsque la durée est atteinte.
            name (str | None, optionnel): Le nom du dispositif. Par défaut None.
            enabled (bool, optionnel): Indique si le dispositif est activé. Par défaut True.
            initial_time (float, optionnel): Le temps initial accumulé. Par défaut 0.0.
            auto_reset_when_enabling (bool, optionnel): Indique si le compteur doit être réinitialisé lors de l'activation. Par défaut True.
        Raises:
            TypeError: Si un argument n'est pas du bon type.
            ValueError: Si la durée est inférieure ou égale à zéro.
        """
        super().__init__(name, enabled)
        self.__duration:float
        self.duration = duration
        self.__action:GenericCallback
        self.action = action

        if not isinstance(initial_time, float):
            raise TypeError('Initial time must be a float')   
        else:
            self.__accumulator:float = initial_time

        self.__auto_reset_when_enabling:bool
        self.auto_reset_when_enabling = auto_reset_when_enabling

    @property
    def action(self) -> GenericCallback:
        """
        Correspond à l'action à exécuter lorsque la durée est atteinte.

        Returns:
            GenericCallback: L'action à exécuter.
        Raises:
            TypeError: Si l'action n'est pas un exécutable.
        """
        return self.__action
       
    @action.setter
    def action(self, value:GenericCallback) -> None:
        """
        Définit l'action à exécuter lorsque la durée est atteinte.

        Args:
            value (GenericCallback): L'action à exécuter.
        Raises:
            TypeError: Si l'action n'est pas exécutable.
        """
        if not callable(value):
            raise TypeError('Must be a GenericCallback')
        
        self.__action = value 

    @property
    def duration(self) -> float:
        """
        La durée après laquelle l'action est déclenchée.

        Returns:
            float: La durée.
        Raises:
            TypeError: Si la durée n'est pas un nombre.
            ValueError: Si la durée est inférieure ou égale à zéro.
        """
        return self.__duration
        
    @duration.setter
    def duration(self, value : float) -> None:
        """
        Définit la durée après laquelle l'action est déclenchée.

        Args:
            value (float): La durée.
        Raises:
            TypeError: Si la durée n'est pas un nombre.
            ValueError: Si la durée est inférieure ou égale à zéro.
        """
        if not isinstance(value, float):
            raise TypeError('Duration must be a float')         
        if value <= 0:
            raise ValueError('Duration must be over 0')     
          
        self.__duration = value
        
    @property
    def auto_reset_when_enabling(self) -> bool:
        """
        Indique si le compteur doit être réinitialisé lors de l'activation.

        Returns:
            bool: True si le compteur est réinitialisé lors de l'activation.
        Raises:
            TypeError: Si la valeur n'est pas un booléen.
        """
        return self.__auto_reset_when_enabling   
         
    @auto_reset_when_enabling.setter
    def auto_reset_when_enabling(self, value : bool) -> None:
        """
        Définit si le compteur doit être réinitialisé lors de l'activation.

        Args:
            value (bool): True pour réinitialiser lors de l'activation.
        Raises:
            TypeError: Si la valeur n'est pas un booléen.
        """
        if not isinstance(value, bool):
            raise TypeError('Auto reset must be a boolean')      
          
        self.__auto_reset_when_enabling = value

    @property
    def elapsed_time_from_last_trigger(self) -> float:
        """
        Le temps écoulé depuis le dernier déclenchement de l'action.

        Returns:
            float: Temps écoulé depuis le dernier déclenchement.
        """
        return self.__accumulator

    @property
    def remaining_time_until_next_trigger(self) -> float:
        """
        Le temps restant avant le prochain déclenchement de l'action.

        Returns:
            float: Temps restant avant le prochain déclenchement.
        """
        return self.__duration - self.__accumulator    
    
    @override
    def _enabling(self) -> None:
        """
        Lorsque le dispositif est activé, réinitialise le compteur si auto_reset_when_enabling.
        """
        if self.__auto_reset_when_enabling:
            self._do_reset()
    
    @override
    def _do_reset(self) -> None:
        """
        Réinitialise le compteur à zéro.
        """
        self.__accumulator = 0.0
    
    @override
    def _do_tracking(self, elapsed_time: float) -> None:
        """
        Met à jour le compteur et déclenche l'action si la durée est atteinte.

        Args:
            elapsed_time (float): Le temps écoulé depuis la dernière mise à jour du suivi.
        """
        self.__accumulator += elapsed_time
        if self.__accumulator > self.__duration:
            self.__action() 
            self.__accumulator -= self.__duration





