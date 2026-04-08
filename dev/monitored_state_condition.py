from __future__ import annotations
"""
Module des conditions liées à un état surveillé.

Ce module définit des classes de conditions (sous-classe de
`Condition`) qui évaluent des critères basés sur un objet
`MonitoredState` (p. ex. délais depuis l'entrée/sortie d'un état,
compteur d'entrées, comparaison de valeur). Les docstrings suivent la
convention Google et sont fournies en français.

Exemples d'utilisation :
	>>> # Un objet MonitoredState est attendu pour évaluer ces conditions
	>>> # (exemples d'utilisation non exécutables ici)
"""
from typing import Self, Any, override
from abc import ABC, abstractmethod
from condition import Condition
from state_machine_utilities import MonitoredState

class MonitoredStateCondition(Condition, ABC):
	"""Condition de base liée à un MonitoredState.

	Cette classe abstraite associe une condition à un objet
	`MonitoredState`. Les sous-classes doivent implémenter
	`_compare()` pour définir la logique spécifique.

	Args:
		monitored_state (MonitoredState | None): L'état surveillé associé.
		invert (bool): Si True, inverse la valeur de la condition.

	Attributes:
		monitored_state (MonitoredState | None): L'état surveillé associé.
	"""
	def __init__(self: Self, monitored_state: MonitoredState | None = None, invert: bool = False):
		"""Initialise la condition liée à un `MonitoredState`.

		Args:
			monitored_state (MonitoredState | None): État surveillé à associer.
			invert (bool): Si True, inverse la logique de la condition.

		Notes:
			Le setter de `monitored_state` effectue une validation et
			appelle `_update_from_setting_new_monitored_state`.
		"""
		super().__init__(invert)
		self.monitored_state : MonitoredState | None = monitored_state
	
	@property
	def monitored_state(self) -> MonitoredState | None:
		"""Accède à l'objet MonitoredState associé.

		Returns:
			MonitoredState | None: L'état surveillé associé.

		Setter Args:
			value (MonitoredState): La nouvelle instance de MonitoredState.

		Raises:
			ValueError: Si ``value`` n'est pas une instance de MonitoredState.
		"""
		return self.__monitored_state
	
	@monitored_state.setter
	def monitored_state(self, value:MonitoredState | None) -> None:
		"""Assigne un `MonitoredState` à la condition.

		Args:
			value (MonitoredState | None): L'objet MonitoredState à assigner.

		Raises:
			ValueError: Si ``value`` n'est pas une instance de
			``MonitoredState`` (lorsqu'il n'est pas None).
		"""
		if value is not None and not isinstance(value, MonitoredState):
			raise ValueError("value must be a MonitoredState")
		self.__monitored_state = value
		self._update_from_setting_new_monitored_state(value)
	
	def _update_from_setting_new_monitored_state(self, monitored_state: MonitoredState | None):
		"""Hook appelé après l'association d'un nouveau MonitoredState.

		Les sous-classes peuvent surcharger cette méthode pour extraire
		des valeurs de référence depuis ``monitored_state`` (p. ex. compteur
		initial, horodatage de référence, ...).

		Args:
			monitored_state (MonitoredState | None): L'état surveillé
				nouvellement assigné.
		"""
		pass
        
class DelayStateCondition(MonitoredStateCondition):
	"""Base pour les conditions temporelles liées à un MonitoredState.

	Fournit l'attribut ``duration`` représentant la durée (en secondes)
	utilisée par les conditions temporelles dérivées.

	Args:
		duration (float): Durée en secondes à comparer.
		monitored_state (MonitoredState | None): État surveillé optionnel.
		invert (bool): Si True, inverse la condition.
	"""
	def __init__(self:Self, duration:float, monitored_state:MonitoredState | None = None, invert:bool = False):
		super().__init__(monitored_state, invert)
		self.__duration : float = duration

		"""Initialise une condition temporelle basée sur une durée.

		Args:
			duration (float): Durée en secondes.
			monitored_state (MonitoredState | None): État surveillé optionnel.
			invert (bool): Inversion éventuelle de la condition.
		"""

	@property
	def duration(self) -> float:
		"""Retourne la durée (en secondes) utilisée pour la comparaison.

		Returns:
			float: Durée en secondes.
		"""
		return self.__duration


class DelaySinceEnteredCondition(DelayStateCondition):
	"""Condition vraie quand la durée depuis l'entrée atteint ``duration``.

	La condition est évaluée à True si le ``MonitoredState`` associé a une
	référence de temps d'entrée valide et si le temps écoulé depuis la
	dernière entrée est supérieur ou égal à ``duration``.

	Args:
		duration (float): Durée en secondes.
		monitored_state (MonitoredState | None): État surveillé optionnel.
		invert (bool): Inversion optionnelle de la condition.
	"""
	def __init__(self:Self, duration:float, monitored_state:MonitoredState | None = None, invert:bool = False):
		super().__init__(duration, monitored_state, invert)

		"""Constructeur pour DelaySinceEnteredCondition.

		Args:
			duration (float): Durée seuil en secondes.
			monitored_state (MonitoredState | None): État surveillé.
			invert (bool): Inversion de la condition.
		"""

	@override
	def _compare(self) -> bool:
		"""Effectue la comparaison temporelle pour l'entrée d'état.

		Returns:
			bool: True si le temps écoulé depuis la dernière entrée est
				>= ``duration``, False sinon.
		"""
		if self.monitored_state is None or self.monitored_state.last_entry_reference_time is None:
			return False
		else :
			return self.monitored_state.elapsed_since_last_entry >= self.duration


class DelaySinceExitedCondition(DelayStateCondition):
	"""Condition vraie quand la durée depuis la sortie atteint ``duration``.

	La condition est évaluée à True si le ``MonitoredState`` associé a une
	référence de temps de sortie valide et si le temps écoulé depuis la
	dernière sortie est supérieur ou égal à ``duration``.

	Args:
		duration (float): Durée en secondes.
		monitored_state (MonitoredState | None): État surveillé optionnel.
		invert (bool): Inversion optionnelle de la condition.
	"""
	def __init__(self:Self, duration:float, monitored_state:MonitoredState | None = None, invert:bool = False):
		super().__init__(duration, monitored_state, invert)

		"""Constructeur pour DelaySinceExitedCondition.

		Args:
			duration (float): Durée seuil en secondes.
			monitored_state (MonitoredState | None): État surveillé.
			invert (bool): Inversion de la condition.
		"""

	@override
	def _compare(self) -> bool:
		"""Effectue la comparaison temporelle pour la sortie d'état.

		Returns:
			bool: True si le temps écoulé depuis la dernière sortie est
				>= ``duration``, False sinon.
		"""
		if self.monitored_state is None or self.monitored_state.last_exit_reference_time is None:
			return False
		else :
			return self.monitored_state.elapsed_since_last_exit >= self.duration


class StateEntryCountCondition(MonitoredStateCondition):
	"""Condition basée sur le nombre d'entrées dans l'état.

	L'objet stocke une référence initiale du compteur d'entrées du
	``MonitoredState`` au moment de l'association. La condition devient
	vraie quand la différence entre le compteur courant et la référence
	est supérieure ou égale à ``expected_count``.

	Args:
		expected_count (int): Nombre d'entrées attendues depuis la
			référence.
		monitored_state (MonitoredState | None): État surveillé optionnel.
		invert (bool): Inversion optionnelle de la condition.
	"""
	def __init__(self:Self, expected_count:int, monitored_state:MonitoredState | None = None, invert:bool = False):
		super().__init__(monitored_state, invert)
		self.__expected_count:int = expected_count
		self.__reference_count:int = 0

		if monitored_state:
			self._update_from_setting_new_monitored_state(monitored_state)

	@property
	def expected_count(self) -> int:
		"""Retourne le nombre attendu d'entrées depuis la référence.

		Returns:
			int: Nombre d'entrées attendu.
		"""
		return self.__expected_count
	
	@override
	def _update_from_setting_new_monitored_state(self, monitored_state:MonitoredState) -> None:
		"""Met à jour la référence de compteur lors d'une nouvelle
		association de MonitoredState.

		Args:
			monitored_state (MonitoredState): État surveillé fourni.
		"""
		self.__reference_count = monitored_state.entry_count if monitored_state else 0
	
	@override 
	def _compare(self) -> bool:
		"""Compare le nombre d'entrées depuis la référence.

		Returns:
			bool: True si la différence de compte est >= ``expected_count``.
		"""
		if self.monitored_state is None:
			return False
		current_diff = self.monitored_state.entry_count - self.__reference_count
		return current_diff >= self.__expected_count



class StateValueCondition(MonitoredStateCondition):
	"""Condition qui compare la valeur personnalisée de l'état.

	La condition est vraie si ``monitored_state.custom_value`` est égal à
	``expected_value``.

	Args:
		expected_value (Any): La valeur attendue pour la comparaison.
		monitored_state (MonitoredState | None): État surveillé optionnel.
		invert (bool): Inversion optionnelle de la condition.
	"""
	def __init__(self:Self, expected_value:Any = None, monitored_state:MonitoredState | None = None, invert:bool = False):
		super().__init__(monitored_state, invert)

		self.expected_value:Any = expected_value 
		"""Initialise une condition de comparaison de valeur.

		Args:
			expected_value (Any): La valeur attendue pour la comparaison.
			monitored_state (MonitoredState | None): État surveillé optionnel.
			invert (bool): Inversion optionnelle de la condition.
		"""
		
	@override 
	def _compare(self) -> bool:
		"""Compare la valeur personnalisée de l'état au `expected_value`.

		Returns:
			bool: True si les valeurs sont égales, False sinon.
		"""
		if self.monitored_state is None:
			return False
		return self.monitored_state.custom_value == self.expected_value