from __future__ import annotations
from typing import Self, Any, override
from abc import ABC, abstractmethod
from condition import Condition
from state_machine_utilities import MonitoredState

class MonitoredStateCondition(Condition, ABC):
	def __init__(self: Self, monitored_state: MonitoredState | None = None, invert: bool = False):
		super().__init__(invert)
		self.__monitored_state : MonitoredState | None = monitored_state
	
	@property
	def monitored_state(self):
		return self.__monitored_state
	
	def _update_from_setting_new_monitored_state(self, monitored_state: MonitoredState | None):
		pass
        
		

class DelayStateCondition(MonitoredStateCondition):
	def __init__(self:Self, duration:float, monitored_state:MonitoredState | None = None, invert:bool = False):
		super().__init__(monitored_state, invert)
		self.__duration : float = duration

	@property
	def duration(self):
		return self.__duration


class DelaySinceEnteredCondition(DelayStateCondition):
	def __init__(self:Self, duration:float, monitored_state:MonitoredState | None = None, invert:bool = False):
		super().__init__(duration, monitored_state, invert)

	@override
	def _compare(self):
		return super()._compare()


class DelaySinceExitedCondition(DelayStateCondition):
	def __init__(self:Self, duration:float, monitored_state:MonitoredState | None = None, invert:bool = False):
		super().__init__(duration, monitored_state, invert)

	@override
	def _compare(self):
		return super()._compare()



class StateEntryCountCondition(MonitoredStateCondition):
	def __init__(self:Self, expected_count:int, monitored_state:MonitoredState | None = None, invert:bool = False):
		super().__init__(monitored_state, invert)
		self.__expected_count:int = expected_count
		self.__reference_count:int = 0

	@property
	def expected_count(self):
		return self.__expected_count
	
	@override
	def _update_from_setting_new_monitored_state(self, monitored_state):
		return super()._update_from_setting_new_monitored_state()
	
	@override 
	def _compare(self):
		return super()._compare()


class StateValueCondition(MonitoredStateCondition):
	def __init__(self:Self, expected_value:Any = None, monitored_state:MonitoredState | None = None, invert:bool = False):
		super().__init__(monitored_state, invert)

		self.expected_value:Any = expected_value 
		
	@override 
	def _compare(self):
		return super()._compare()