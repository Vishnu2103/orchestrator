from typing import Dict, Any, Optional, List
import logging
import time
from ..models.workflow import WorkflowDefinition
from ..utils.state_manager import StateManager
from .task_runner import TaskRunner, TaskExecutionError

logger = logging.getLogger(__name__)

class WorkflowExecutionError(Exception):
    """Raised when workflow execution fails"""
    pass

class WorkflowEngine:
    """Executes workflows using local task runners"""
    
    def __init__(self):
        """Initialize workflow engine"""
        self.task_runner = TaskRunner()
        self.state_manager = StateManager()
        self.observers = []
    
    def add_observer(self, observer):
        """Add an observer to the workflow execution"""
        self.observers.append(observer)
    
    def execute(self, workflow_def: WorkflowDefinition, observer=None) -> Dict[str, Any]:
        """Execute workflow
        
        Args:
            workflow_def: Workflow definition to execute
            observer: Optional observer to notify of execution events
            
        Returns:
            Dict containing workflow outputs
        """
        if observer:
            self.add_observer(observer)
            
        try:
            # Execute each task in order
            for task in workflow_def.tasks:
                try:
                    # Notify observers of task start
                    for obs in self.observers:
                        obs.on_module_start(task.reference_name)
                    
                    # Resolve input parameters
                    inputs = self.state_manager.resolve_inputs(task.input_parameters)
                    
                    # Execute task
                    result = self.task_runner.execute_task(task, inputs)
                    
                    # Store output
                    self.state_manager.set_task_output(task.reference_name, result)
                    
                    # Notify observers of task completion
                    for obs in self.observers:
                        obs.on_module_complete(task.reference_name, result)
                        
                except Exception as e:
                    # Handle task failure
                    error_msg = f"Task {task.reference_name} failed: {str(e)}"
                    logger.error(error_msg)
                    
                    # Store error
                    self.state_manager.set_task_error(task.reference_name, str(e))
                    
                    # Notify observers of task failure
                    for obs in self.observers:
                        obs.on_module_error(task.reference_name, str(e))
                    
                    raise TaskExecutionError(error_msg) from e
            
            # Get final outputs
            outputs = {}
            for output_key, output_ref in workflow_def.outputs.items():
                try:
                    outputs[output_key] = self.state_manager.resolve_value(output_ref)
                except Exception as e:
                    logger.error(f"Failed to resolve output {output_key}: {e}")
                    raise WorkflowExecutionError(f"Failed to resolve output {output_key}") from e
            
            return outputs
            
        except Exception as e:
            raise WorkflowExecutionError(str(e)) from e
        finally:
            # Clear observers
            self.observers.clear()
    
    def get_task_outputs(self) -> Dict[str, Dict[str, Any]]:
        """Get all task outputs"""
        return self.state_manager.task_outputs
    
    def get_task_errors(self) -> Dict[str, str]:
        """Get all task errors"""
        return self.state_manager.task_errors