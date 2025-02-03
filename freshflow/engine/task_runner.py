from typing import Dict, Any
import logging
from workflow_configuration.tasks.registry import TaskHandlerRegistry
from workflow_configuration.tasks import handlers  # Import handlers to register them
from ..models.task import Task
from ..models.task_handler import TaskHandler

logger = logging.getLogger(__name__)

class TaskExecutionError(Exception):
    """Raised when task execution fails"""
    pass

class TaskRunner:
    """Handles task execution using registered handlers"""
    
    def __init__(self):
        """Initialize task runner"""
        self.registry = TaskHandlerRegistry()
    
    def execute_task(self, task: Task, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task with given inputs
        
        Args:
            task: Task to execute
            input_data: Resolved input parameters
            
        Returns:
            Dict containing task output
            
        Raises:
            TaskExecutionError: If task execution fails
        """
        try:
            # Get handler for task type
            # Extract identifier from task name (e.g., 's3_downloader_task' -> 's3_downloader')
            handler_name = task.name.replace('_task', '')
            
            # Get handler class from registry
            try:
                handler_class = self.registry.get_handler(handler_name)
            except ValueError as e:
                # Try alternate handler name formats
                alternate_name = handler_name.replace('_', '')
                try:
                    handler_class = self.registry.get_handler(alternate_name)
                except ValueError:
                    # Try with task input parameters identifier
                    if 'identifier' in task.input_parameters:
                        try:
                            handler_class = self.registry.get_handler(
                                task.input_parameters['identifier']
                            )
                        except ValueError:
                            raise TaskExecutionError(
                                f"No handler found for task type: {handler_name}"
                            ) from e
            
            if not handler_class:
                raise TaskExecutionError(f"No handler found for task type: {handler_name}")
            
            # Instantiate handler
            handler: TaskHandler = handler_class()
            
            logger.info(f"Executing task {task.reference_name} with handler {handler_name}")
            logger.debug(f"Task inputs: {input_data}")
            
            # Execute task
            result = handler.execute(input_data)
            
            # Validate result
            if not isinstance(result, dict):
                raise TaskExecutionError(
                    f"Task {task.reference_name} returned invalid result type: {type(result)}"
                )
            
            if 'status' not in result:
                raise TaskExecutionError(
                    f"Task {task.reference_name} result missing required 'status' field"
                )
            
            if result['status'] == 'FAILED':
                error_msg = result.get('output', {}).get('error', 'Unknown error')
                raise TaskExecutionError(
                    f"Task {task.reference_name} failed: {error_msg}"
                )
            
            logger.info(f"Task {task.reference_name} completed successfully")
            logger.debug(f"Task output: {result}")
            
            return result
            
        except Exception as e:
            error_msg = f"Task {task.reference_name} execution failed: {str(e)}"
            logger.error(error_msg)
            raise TaskExecutionError(error_msg) from e
    
    def validate_handler_exists(self, task_name: str) -> bool:
        """Check if handler exists for task type"""
        try:
            # Try different handler name formats
            handler_name = task_name.replace('_task', '')
            try:
                return self.registry.get_handler(handler_name) is not None
            except ValueError:
                alternate_name = handler_name.replace('_', '')
                try:
                    return self.registry.get_handler(alternate_name) is not None
                except ValueError:
                    return False
        except Exception:
            return False