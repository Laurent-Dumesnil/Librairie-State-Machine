from __future__ import annotations
from typing import Self
from abc import ABC, abstractmethod
from condition import Condition, MonitoredState



class MonitoredStateCondition(ABC, Condition):
	def __init__(self: Self, monitored_state: MonitoredState | None = None, invert: bool = False):
	    super().__init__(invert)
		self.__monitored_state : MonitoredState | None = monitored_state
	
    @property
	def monitored_state(self):
		return self.__monitored_state
	
    def _update_from_setting_new_monitored_state(monitored_state: MonitoredState | None):
	    pass
        
		
		



class DelayStateCondition(ABC, MonitoredStateCondition):
	pass



class DelaySinceEnteredCondition():
	pass



class DelaySinceExitedCondition():
	pass