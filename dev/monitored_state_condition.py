from __future__ import annotations
from typing import Self, Any, override
from abc import ABC, abstractmethod
from condition import Condition
from state_machine_utilities import MonitoredState

class MonitoredStateCondition(Condition, ABC):
	def __init__(self: Self, monitored_state: MonitoredState | None = None, invert: bool = False):
		super().__init__(invert)
		self.monitored_state : MonitoredState | None = monitored_state
	
	@property
	def monitored_state(self) -> MonitoredState | None:
		return self.__monitored_state
	
	@monitored_state.setter
	def monitored_state(self, value:MonitoredState | None) -> None:
		if not isinstance(value, MonitoredState):
			raise ValueError("value must be a MonitoredState")
		self.__monitored_state = value
		self._update_from_setting_new_monitored_state(value)
	
	def _update_from_setting_new_monitored_state(self, monitored_state: MonitoredState | None):
		pass
        
class DelayStateCondition(MonitoredStateCondition):
	def __init__(self:Self, duration:float, monitored_state:MonitoredState | None = None, invert:bool = False):
		super().__init__(monitored_state, invert)
		self.__duration : float = duration

	@property
	def duration(self) -> float:
		return self.__duration


class DelaySinceEnteredCondition(DelayStateCondition):
	def __init__(self:Self, duration:float, monitored_state:MonitoredState | None = None, invert:bool = False):
		super().__init__(duration, monitored_state, invert)

	@override
	def _compare(self) -> bool:
		if self.monitored_state is None or self.monitored_state.last_entry_reference_time is None:
			return False
		else :
			return self.monitored_state.elapsed_since_last_entry >= self.duration


class DelaySinceExitedCondition(DelayStateCondition):
	def __init__(self:Self, duration:float, monitored_state:MonitoredState | None = None, invert:bool = False):
		super().__init__(duration, monitored_state, invert)

	@override
	def _compare(self) -> bool:
		if self.monitored_state is None or self.monitored_state.last_exit_reference_time is None:
			return False
		else :
			return self.monitored_state.elapsed_since_last_exit >= self.duration


class StateEntryCountCondition(MonitoredStateCondition):
	def __init__(self:Self, expected_count:int, monitored_state:MonitoredState | None = None, invert:bool = False):
		super().__init__(monitored_state, invert)
		self.__expected_count:int = expected_count
		self.__reference_count:int = 0

		if monitored_state:
			self._update_from_setting_new_monitored_state(monitored_state)

	@property
	def expected_count(self) -> int:
		return self.__expected_count
	
	@override
	def _update_from_setting_new_monitored_state(self, monitored_state:MonitoredState) -> None:
		self.__reference_count = monitored_state.entry_count if monitored_state else 0
	
	@override 
	def _compare(self) -> bool:
		if self.monitored_state is None:
			return False
		current_diff = self.monitored_state.entry_count - self.__reference_count
		return current_diff >= self.__expected_count



class StateValueCondition(MonitoredStateCondition):
	def __init__(self:Self, expected_value:Any = None, monitored_state:MonitoredState | None = None, invert:bool = False):
		super().__init__(monitored_state, invert)

		self.expected_value:Any = expected_value 
		
	@override 
	def _compare(self) -> bool:
		if self.monitored_state is None:
			return False
		return self.monitored_state.custom_value == self.expected_value