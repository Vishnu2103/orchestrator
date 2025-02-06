from typing import Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)

class StateManager:
    """Manages task outputs and state during workflow execution"""
    
    def __init__(self):
        """Initialize state manager"""
        self.task_outputs: Dict[str, Dict[str, Any]] = {}
        self.task_errors: Dict[str, str] = {}
    
    def set_task_output(self, task_ref: str, output: Dict[str, Any]) -> None:
        """Store task output"""
        logger.info(f"Setting output for task {task_ref}: {output}")
        self.task_outputs[task_ref] = output
    
    def set_task_error(self, task_ref: str, error: str) -> None:
        """Store task error"""
        logger.error(f"Setting error for task {task_ref}: {error}")
        self.task_errors[task_ref] = error
    
    def get_task_output(self, task_ref: str) -> Optional[Dict[str, Any]]:
        """Get task output"""
        return self.task_outputs.get(task_ref)
    
    def get_task_error(self, task_ref: str) -> Optional[str]:
        """Get task error"""
        return self.task_errors.get(task_ref)
    
    def resolve_value(self, value: Any) -> Any:
        """Resolve a value, replacing any task references with actual values"""
        logger.info(f"Resolving value: {value}")
        if not isinstance(value, str):
            return value
            
        if not value.startswith('${'):
            return value
            
        # Extract task reference and output path
        # Format: ${task_ref.output.key}
        match = re.match(r'\${([^.}]+)\.output\.([^}]+)}', value)
        if not match:
            return value
        logger.info(f"Match: {match}")
            
        task_ref, output_key = match.groups()
        logger.info(f"Task ref: {task_ref} Output key: {output_key}")
        
        # Get task output
        task_output = self.get_task_output(task_ref)
        if task_output is None:
            raise ValueError(f"No output found for task {task_ref}")
            
        # Get value from output dictionary
        logger.debug(f"Task output: {task_output} Expected key: {output_key}" )
        if 'output' not in task_output:
            raise ValueError(f"No output dictionary found in task {task_ref} result")
            
        output_dict = task_output['output']
        if output_key not in output_dict:
            raise ValueError(f"Key {output_key} not found in output of task {task_ref}")
            
        logger.debug(f"Resolved {value} to {output_dict[output_key]}")
        return output_dict[output_key]
    
    def resolve_inputs(self, input_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve all input parameters, replacing task references with actual values"""
        resolved = {}
        
        # First resolve the module_id and identifier
        resolved['module_id'] = input_parameters.get('module_id')
        resolved['identifier'] = input_parameters.get('identifier')
        
        # Then resolve user_config
        user_config = input_parameters.get('user_config', {})
        resolved_config = {}
        
        for key, value in user_config.items():
            if isinstance(value, dict):
                # Handle nested dictionaries
                resolved_config[key] = {
                    k: self.resolve_value(v) 
                    for k, v in value.items()
                }
            elif isinstance(value, list):
                # Handle lists
                resolved_config[key] = [
                    self.resolve_value(item) 
                    for item in value
                ]
            else:
                # Handle direct values
                resolved_config[key] = self.resolve_value(value)
        
        resolved['user_config'] = resolved_config
        
        # Finally resolve any top-level parameters that aren't in user_config
        for key, value in input_parameters.items():
            if key not in ['module_id', 'identifier', 'user_config']:
                resolved[key] = self.resolve_value(value)
        
        logger.debug(f"Resolved inputs: {resolved}")
        return resolved
    
    def clear(self) -> None:
        """Clear all state"""
        self.task_outputs.clear()
        self.task_errors.clear()