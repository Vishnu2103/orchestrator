from typing import Dict, Any
from dataclasses import dataclass, field

@dataclass
class Task:
    """Represents a task in a workflow"""
    name: str
    task_reference_name: str = field(metadata={"alias": "taskReferenceName"})
    type: str
    input_parameters: Dict[str, Any] = field(metadata={"alias": "inputParameters"})
    
    def __init__(self, name: str, taskReferenceName: str, type: str, inputParameters: Dict[str, Any]):
        """Initialize task with backward compatibility for camelCase parameters"""
        self.name = name
        self.task_reference_name = taskReferenceName
        self.type = type
        self.input_parameters = inputParameters
    
    @property
    def taskReferenceName(self) -> str:
        """Backward compatibility for camelCase task reference name"""
        return self.task_reference_name
    
    @property
    def reference_name(self) -> str:
        """Get the task reference name"""
        return self.task_reference_name
    
    @property
    def inputParameters(self) -> Dict[str, Any]:
        """Backward compatibility for camelCase input parameters"""
        return self.input_parameters
    
    def extract_dependencies(self) -> list[str]:
        """Extract task dependencies from input parameters"""
        dependencies = []
        for param in self.input_parameters.values():
            if isinstance(param, str) and param.startswith('${'):
                # Extract task reference from ${task_ref.output.key}
                task_ref = param[2:param.find('.', 2)]
                dependencies.append(task_ref)
        return dependencies