from typing import Dict, List, Optional
from .task import Task

class WorkflowDefinition:
    """Represents a workflow definition"""
    
    def __init__(self, workflow_json: Dict):
        """Initialize workflow from JSON configuration
        
        Args:
            workflow_json: Dictionary containing workflow configuration with fields:
                - name: Workflow name
                - version: (optional) Workflow version
                - tasks: List of task definitions
                - outputParameters: (optional) Output parameter mappings
                - failureWorkflow: (optional) Workflow to execute on failure
                - schemaVersion: (optional) Schema version
        """
        self.name = workflow_json['name']
        self.version = workflow_json.get('version', 1)
        self.tasks = [Task(**task) for task in workflow_json['tasks']]
        self.outputs = workflow_json.get('outputParameters', {})
        self.failure_workflow = workflow_json.get('failureWorkflow')
        self.schema_version = workflow_json.get('schemaVersion', 2)
        
        # Build task lookup for quick access
        self._task_lookup = {task.reference_name: task for task in self.tasks}
    
    def get_task(self, reference_name: str) -> Optional[Task]:
        """Get task by reference name"""
        return self._task_lookup.get(reference_name)
    
    def get_task_dependencies(self) -> Dict[str, List[str]]:
        """Extract task dependencies from all tasks"""
        dependencies = {}
        for task in self.tasks:
            dependencies[task.reference_name] = task.extract_dependencies()
        return dependencies
    
    def get_execution_order(self) -> List[str]:
        """Get topologically sorted task execution order"""
        dependencies = self.get_task_dependencies()
        
        # Calculate in-degrees
        in_degree = {task.reference_name: 0 for task in self.tasks}
        for deps in dependencies.values():
            for dep in deps:
                in_degree[dep] = in_degree.get(dep, 0) + 1
        
        # Find starting tasks (no dependencies)
        queue = [
            task_ref for task_ref, degree in in_degree.items() 
            if degree == 0
        ]
        
        if not queue:
            raise ValueError("No starting tasks found - possible circular dependency")
        
        # Process tasks in order
        execution_order = []
        while queue:
            current = queue.pop(0)
            execution_order.append(current)
            
            # Update in-degrees of dependent tasks
            for task_ref, deps in dependencies.items():
                if current in deps:
                    in_degree[task_ref] -= 1
                    if in_degree[task_ref] == 0:
                        queue.append(task_ref)
        
        if len(execution_order) != len(self.tasks):
            unprocessed = set(task.reference_name for task in self.tasks) - set(execution_order)
            raise ValueError(f"Circular dependency detected. Unprocessed tasks: {unprocessed}")
        
        return execution_order
    
    def validate(self) -> bool:
        """Validate workflow definition"""
        try:
            # Check required fields
            if not self.name or not self.tasks:
                raise ValueError("Workflow missing required fields (name, tasks)")
            
            # Validate task references
            task_refs = set(task.reference_name for task in self.tasks)
            for task in self.tasks:
                for dep in task.extract_dependencies():
                    if dep not in task_refs:
                        raise ValueError(f"Task {task.reference_name} depends on non-existent task {dep}")
            
            # Validate execution order (checks for circular dependencies)
            self.get_execution_order()
            
            return True
            
        except Exception as e:
            raise ValueError(f"Workflow validation failed: {str(e)}")