from __future__ import annotations
"""
Module pour la machine à états et ses composants.

Ce module fournit des classes pour définir et exécuter une machine à
états simple : `StateMachineDevice` (qui pilote la logique de transit),
`State` (représente un état avec des actions d'entrée/en_cours/sortie),
et `Transition` (décrit une transition vers un état suivant). Une classe
imbriquée `Layout` permet de regrouper la liste des états et
définir l'état initial.

"""
from typing import override, Self, Any, Iterable
from abc import ABC, abstractmethod
from base_component import BaseComponent
from tracking_device import TrackingDevice


class StateMachineDevice(TrackingDevice) :
    """Appareil pilotant une machine à états.

    ``StateMachineDevice`` exécute un ensemble d'états (définis par
    ``Layout``) et effectue les transitions lorsque leurs conditions
    sont remplies. L'objet conserve l'état courant et appelle les
    actions d'entrée, de sortie et d'exécution en fonction du cycle de
    suivi.

    Args:
        layout (Layout): Objet décrivant la liste des états et l'état
            initial.
        initialized (bool): Si True, initialise la machine en appelant
            l'action d'entrée de l'état initial.
        name (str | None): Nom optionnel du composant.
        enabled (bool): Indique si le composant est activé.
    """

    class Layout :
        """Conteneur immuable d'états et définition de l'état initial.

        La classe vérifie la validité des états fournis et conserve le
        premier état comme état initial.

        Args:
            states (tuple[State, ...]): Tuple d'instances ``State``.

        Raises:
            ValueError: Si la tuple est vide ou si un état n'est pas
                valide.
            TypeError: Si un élément de ``states`` n'est pas une
                instance de ``State``.
        """
        def __init__(self: Self, states:tuple[State, ...]):
            """Initialise le layout d'états.

            Args:
                states (tuple[State, ...]): Tuple d'instances ``State``.

            Raises:
                ValueError: Si la tuple est vide ou si un état n'est pas valide.
                TypeError: Si un élément de ``states`` n'est pas une instance de
                    ``State``.
            """
            if len(states) <= 0 :
                raise ValueError('Tuple size of states must be bigger than 0')

            for state in states :
                if not isinstance (state, State) :
                    raise TypeError('Must be a State')
                if not state.valid :
                    raise ValueError('All states must be valid.')

            # self._initial_state : State - si on initialise pas, on aura des problemes
            self._states : tuple[State, ...] = states
            self._initial_state = states[0]
        
        def __contains__(self: Self, state:State) -> bool:
            """Vérifie si un état appartient au layout.

            Args:
                state (State): État à rechercher.

            Returns:
                bool: True si ``state`` est contenu dans le layout.
            """
            return state in self._states

        @property
        def initial_state(self) -> State :
            """État initial du layout.

            Returns:
                State: L'état initial (premier élément fourni).
            """
            return self._initial_state 


    def __init__(self: Self, layout: Layout, initialized: bool = False, name: str | None = None, enabled: bool = True):
        """Initialise le StateMachineDevice.

        Args:
            layout (Layout): Layout définissant les états et l'état initial.
            initialized (bool): Si True, l'état initial est exécuté immédiatement.
            name (str | None): Nom optionnel du composant.
            enabled (bool): Indique si le composant est activé.
        """
        self.__layout = layout
        self.__current_state: State | None = layout.initial_state if initialized else None 
        if initialized is True and self.__current_state is not None:
            self.__current_state._execute_entering_action()
			
        super().__init__(name=name, enabled=enabled)

    @property
    def current_state(self) -> State | None:
        """État courant de la machine.

        Returns:
            State | None: L'état courant ou None si non initialisé.
        """
        return self.__current_state
    
    def __transit_by(self, transition: Transition) -> None :
        """Effectue une transition en utilisant l'objet Transition fourni.

        Args:
            transition (Transition): Transition à exécuter.
        """
        if self.__current_state is not None:
            self.__current_state._execute_exiting_action()
            transition._execute_transiting_action()

            self.__current_state = transition.next_state
            if self.__current_state is not None:
                self.__current_state._execute_entering_action()

    def _transit_to(self, state: State) -> None :
        """Force la transition vers l'état fourni sans objet Transition.

        Args:
            state (State): État cible.
        """
        if self.__current_state is not None:
            self.__current_state._execute_exiting_action()

            self.__current_state = state
            if self.__current_state is not None:
                self.__current_state._execute_entering_action()

    @override
    def _do_tracking(self, elapsed_time: float) -> None:
        """Effectue un cycle de tracking : initialise si besoin et
        exécute transitions / actions d'état.

        Args:
            elapsed_time (float): Temps écoulé depuis la dernière itération
                (en secondes). (Non utilisé directement ici mais fourni par
                l'interface de TrackingDevice.)
        """
        if self.__current_state is None:
            self.__current_state = self.__layout.initial_state
            self.__current_state._execute_entering_action()

        if self.__current_state.terminal is False:
            transition = self.__current_state.is_transiting()

            if transition is not None:
                self.__transit_by(transition)
            else:
                self.__current_state._execute_in_state_action()

    @override
    def _do_reset(self) -> None:
        """Réinitialise la machine en positionnant l'état initial.

        Cette méthode ne déclenche pas d'action d'entrée.
        """
        self.__current_state = self.__layout.initial_state


class State(BaseComponent):
    """Représentation d'un état de la machine.

    Un ``State`` peut contenir des transitions sortantes et définir si
    la machine doit exécuter l'action d'état lors de l'entrée ou de la
    sortie. La propriété ``valid`` vérifie la cohérence des
    transitions associées.

    Args:
        name (str | None): Nom optionnel de l'état.
        enabled (bool): Indique si l'état est activé.
        terminal (bool): Si True, l'état est terminal (aucune
            transition autorisée).
        do_in_state_action_when_entering (bool): Si True, exécute
            l'action d'état lors de l'entrée.
        do_in_state_action_when_exiting (bool): Si True, exécute
            l'action d'état lors de la sortie.

    Raises:
        TypeError: Si les paramètres booléens fournis ne sont pas de
            type ``bool`` (méthode ``is_bool``).
    """
    def __init__(self:Self, name: str | None = None, /,*, enabled:bool = True, terminal:bool = False, do_in_state_action_when_entering:bool = False, do_in_state_action_when_exiting:bool = False):
        super().__init__(name=name, enabled=enabled)
        self.__terminal = self.is_bool(terminal)
        self.__do_in_state_action_when_entering = self.is_bool(do_in_state_action_when_entering)
        self.__do_in_state_action_when_exiting = self.is_bool(do_in_state_action_when_exiting)

        self.__transitions: list[Transition] = []

    def is_bool(self:Self, value:Any) -> bool:
        """Vérifie qu'une valeur est un booléen.

        Args:
            value: Valeur à tester.

        Returns:
            bool: La valeur si elle est un booléen.

        Raises:
            TypeError: Si la valeur n'est pas de type bool.
        """
        if isinstance(value, bool):
            return value
        raise TypeError("Valeur doit être de type bool")

    @override
    @property
    def valid(self) -> bool:
        """Vérifie si l'état est cohérent.

        Returns:
            bool: True si l'état est valide selon les règles (pas de
                transitions pour un état terminal, au moins une transition
                valide sinon).
        """
        if self.terminal:
            return len(self.__transitions) == 0

        if len(self.__transitions) == 0:
            return False

        for transition in self.__transitions:
            if not transition.valid:
                return False

        return True
            
    @property
    def terminal(self) -> bool:
        """Indique si l'état est terminal (pas de transitions)."""
        return self.__terminal
    
    @property
    def do_in_state_action_when_entering(self) -> bool:
        """Indique si l'action d'état doit être exécutée lors de l'entrée."""
        return self.__do_in_state_action_when_entering
    
    @property
    def do_in_state_action_when_exiting(self) -> bool:
        """Indique si l'action d'état doit être exécutée lors de la sortie."""
        return self.__do_in_state_action_when_exiting
    
    def is_transiting(self) -> Transition | None:
        """Parcours les transitions et retourne la première active.

        Returns:
            Transition | None: La transition active, ou None.
        """
        for transition in self.__transitions:
            if transition.enabled and transition.is_transiting():
                return transition
        return None

    def add_transition(self, transition: Transition | Iterable[Transition]) -> None:
        """Ajoute une ou plusieurs transitions à l'état.

        Args:
            transition (Transition | Iterable[Transition]): Transition ou
                itérable de transitions à ajouter.

        Raises:
            TypeError: Si un élément fourni n'est pas une ``Transition``.
        """
        if isinstance(transition, Transition):
            self.__transitions.append(transition)
        elif isinstance(transition, Iterable):
            for t in transition:
                if not isinstance(t, Transition):
                    raise TypeError("Il faut ajouter uniquement des éléments de type Transition")
                self.__transitions.append(t)

    def _execute_entering_action(self) -> None:
        """Exécute les actions liées à l'entrée d'état.

        Appelle `_do_entering_action` puis, selon le drapeau,
        `_do_in_state_action`.
        """
        self._do_entering_action()
        if self.__do_in_state_action_when_entering:
            self._do_in_state_action()

    def _execute_in_state_action(self) -> None:
        """Exécute l'action d'état principale (appel interne)."""
        self._do_in_state_action()

    def _execute_exiting_action(self) -> None:
        """Exécute les actions liées à la sortie d'état.

        Selon le drapeau, exécute `_do_in_state_action` avant
        `_do_exiting_action`.
        """
        if self.__do_in_state_action_when_exiting:
            self._do_in_state_action()
        self._do_exiting_action()

    def _do_entering_action(self) -> None:
        """Point d'extension pour l'action d'entrée d'état.

        Les sous-classes devraient surcharger cette méthode si nécessaire.
        """
        pass

    def _do_in_state_action(self) -> None:
        """Point d'extension pour l'action exécutée en cours d'état.

        Les sous-classes peuvent surcharger cette méthode.
        """
        pass

    def _do_exiting_action(self) -> None:
        """Point d'extension pour l'action de sortie d'état.

        Les sous-classes peuvent surcharger cette méthode.
        """
        pass

class Transition(ABC, BaseComponent):
    """Base abstraite pour une transition entre états.

    Une ``Transition`` référence l'état suivant (``next_state``) et peut
    exécuter une action de transit. Les sous-classes doivent
    implémenter ``is_transiting()`` pour indiquer si la transition doit
    être prise.

    Args:
        next_state (State | None): État cible de la transition.
        name (str | None): Nom optionnel de la transition.
        enabled (bool): Si False, la transition est ignorée.
    """

    def __init__(self : Self, next_state : State | None = None, name : str | None = None, enabled : bool = True):
        """Initialise la transition.

        Args:
            next_state (State | None): État cible de la transition.
            name (str | None): Nom optionnel.
            enabled (bool): Indique si la transition est activée.
        """
        super().__init__(name=name, enabled=enabled)
        self.__next_state : State | None = next_state

    @property
    @override
    def valid(self : Self) -> bool:
        """Indique si la transition est valide (référence d'état et validité).

        Returns:
            bool: True si ``next_state`` est défini et que le composant est
                valide selon la classe de base.
        """
        return True if self.__next_state and super().valid else False

    @property
    def next_state(self : Self) -> State | None:
        """Retourne l'état cible de la transition.

        Returns:
            State | None: État suivant ou None.
        """
        return self.__next_state

    def _execute_transiting_action(self : Self) -> None:
        """Appel interne pour exécuter l'action de transit."""
        self._do_transiting_action()

    def _do_transiting_action(self : Self) -> None:
        """Point d'extension pour l'action exécutée lors du transit.

        Les sous-classes peuvent surcharger cette méthode.
        """
        pass

    @abstractmethod
    def is_transiting(self : Self) -> bool:
        """Devrait être implémentée pour indiquer si la transition doit être prise.

        Returns:
            bool: True si la transition doit être exécutée.
        """
        pass
    