import logging
from typing import Dict, List, Set
from collections import defaultdict

logger = logging.getLogger(__name__)

class WorkflowBuilder:
    def __init__(self, config: Dict):
        """Initialize workflow builder with module-based config format
        
        Args:
            config: Dictionary containing:
                - canvas_name: Name of the workflow
                - modules: Dictionary of module configurations
        """
        self.workflow_name = config.get('canvas_name', 'default_workflow')
        self.modules = config.get('modules', {})
        self.tasks = []
        self._build_task_graph()

    def _resolve_dependencies(self) -> Dict[str, Set[str]]:
        """Build dependency graph from module input configurations"""
        dependencies = defaultdict(set)
        
        for module_id, module in self.modules.items():
            logger.info(f"Resolving dependencies for module: {module_id}")
            # Check user_config for dependencies
            for param_name, param_value in module.get('user_config', {}).items():
                if isinstance(param_value, dict) and 'module_id' in param_value:
                    # This parameter depends on another module's output
                    dep_module_id = param_value['module_id']
                    dependencies[module_id].add(dep_module_id)
                    logger.info(f"  Found dependency: {module_id} -> {dep_module_id}")
        
        return dependencies

    def _build_task_graph(self):
        """Build task graph from module dependencies"""
        # Get dependencies
        dependencies = self._resolve_dependencies()
        logger.info("Dependency graph:")
        for module_id, deps in dependencies.items():
            logger.info(f"{module_id} depends on: {deps}")
        
        # Calculate in-degrees for topological sort
        in_degree = defaultdict(int)
        for module_id in self.modules:
            for dep in dependencies[module_id]:
                in_degree[dep] += 1
        
        logger.info("Initial in-degrees:")
        for module_id, degree in in_degree.items():
            logger.info(f"{module_id}: {degree}")
        
        # Find starting nodes (no dependencies)
        queue = []
        for module_id in self.modules:
            if not dependencies[module_id]:
                queue.append(module_id)
                logger.info(f"Adding start node: {module_id}")
        
        if not queue:
            raise ValueError("No starting nodes found - possible circular dependency")
        
        processed = []
        while queue:
            current_id = queue.pop(0)
            current_module = self.modules[current_id]
            processed.append(current_id)
            logger.info(f"Processing node: {current_id}")
            
            # Find modules that depend on the current module
            for module_id in self.modules:
                if current_id in dependencies[module_id]:
                    dependencies[module_id].remove(current_id)
                    logger.info(f"Removed dependency {current_id} from {module_id}")
                    if not dependencies[module_id]:  # All dependencies processed
                        queue.append(module_id)
                        logger.info(f"Adding to queue: {module_id}")
        
        if len(processed) != len(self.modules):
            unprocessed = set(self.modules.keys()) - set(processed)
            logger.error(f"Unprocessed modules: {unprocessed}")
            remaining_deps = {k: v for k, v in dependencies.items() if v}
            logger.error(f"Remaining dependencies: {remaining_deps}")
            raise ValueError("Circular dependency detected in module graph")
        
        # Create final task list in processed order
        self.tasks = [
            {'id': module_id, 'config': self.modules[module_id]}
            for module_id in processed
        ]
        
        logger.info("Final task order:")
        for task in self.tasks:
            logger.info(f"  {task['id']}")

    def _resolve_input_parameters(self, module_id: str, module_config: Dict) -> Dict:
        """Resolve input parameters with dependencies"""
        input_params = {
            'identifier': module_config['identifier'],
            'user_config': {}
        }
        
        for param_name, param_value in module_config.get('user_config', {}).items():
            if isinstance(param_value, dict) and 'module_id' in param_value:
                # This is a reference to another module's output
                dep_module = param_value['module_id']
                output_key = param_value['output_key']
                input_params['user_config'][param_name] = f"${{{dep_module}.output.{output_key}}}"
            else:
                # This is a direct configuration value
                input_params['user_config'][param_name] = param_value
        
        return input_params

    def create_workflow_definition(self) -> Dict:
        """Create workflow definition from module configuration"""
        tasks = []
        
        for task in self.tasks:
            module_id = task['id']
            module_config = task['config']
            
            # Use camelCase for compatibility with Task model
            task_def = {
                "name": f"{module_config['identifier']}_task",
                "taskReferenceName": module_id,
                "type": "SIMPLE",
                "inputParameters": self._resolve_input_parameters(module_id, module_config)
            }
            
            tasks.append(task_def)
            logger.info(f"Added task: {task_def['name']}")
        
        workflow_def = {
            "name": self.workflow_name,
            "version": 1,
            "tasks": tasks,
            "outputParameters": {
                "workflow_output": "${" + tasks[-1]['taskReferenceName'] + ".output}"
            },
            "failureWorkflow": "cleanup_workflow",
            "schemaVersion": 2
        }
        
        return workflow_def

    def validate_config(self) -> bool:
        """Validate the module configuration"""
        try:
            if not self.modules:
                raise ValueError("No modules defined in configuration")
            
            # Validate each module
            for module_id, module in self.modules.items():
                # Check required fields
                if not all(k in module for k in ['identifier', 'user_config']):
                    raise ValueError(f"Module {module_id} missing required fields")
                
                # Validate dependencies in user_config
                for param_name, param_value in module.get('user_config', {}).items():
                    if isinstance(param_value, dict) and 'module_id' in param_value:
                        dep_module_id = param_value['module_id']
                        if dep_module_id not in self.modules:
                            raise ValueError(
                                f"Module {module_id} depends on non-existent module {dep_module_id}"
                            )
                        if 'output_key' not in param_value:
                            raise ValueError(
                                f"Module {module_id} dependency missing output_key"
                            )
            
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            raise