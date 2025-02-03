from abc import ABC, abstractmethod
from typing import Dict, Any

class TaskHandler(ABC):
    """Base class for all Freshflow task handlers"""
    
    @abstractmethod
    def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task with given inputs
        
        Args:
            task_input: Dictionary containing task inputs
            
        Returns:
            Dictionary containing:
                - status: 'COMPLETED' or 'FAILED'
                - output: Task output data or error message
        """
        pass