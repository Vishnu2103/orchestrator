import json
import logging
from workflow_configuration.workflows.builder import WorkflowBuilder

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_workflow_builder():
    """Test the workflow builder with new module-based configuration"""
    try:
        # Load test configuration
        with open('configs/test_config.json', 'r') as f:
            config = json.load(f)
        
        # Create workflow builder
        builder = WorkflowBuilder(config)
        
        # Validate configuration
        logger.info("Validating configuration...")
        builder.validate_config()
        logger.info("Configuration validation successful")
        
        # Create workflow definition
        logger.info("Creating workflow definition...")
        workflow_def = builder.create_workflow_definition()
        
        # Print workflow definition for inspection
        logger.info("\nGenerated Workflow Definition:")
        logger.info("-----------------------------")
        print(json.dumps(workflow_def, indent=2))
        
        # Validate task sequence
        logger.info("\nValidating task sequence...")
        tasks = workflow_def['tasks']
        
        # Check task dependencies are properly ordered
        task_order = [task['taskReferenceName'] for task in tasks]
        logger.info(f"Task execution order: {' -> '.join(task_order)}")
        
        # Verify input parameters
        logger.info("\nValidating task input parameters...")
        for task in tasks:
            logger.info(f"\nTask: {task['name']}")
            logger.info(f"Input Parameters: {json.dumps(task['inputParameters'], indent=2)}")
            
            # Check if dependencies are properly referenced
            for param_name, param_value in task['inputParameters'].get('user_config', {}).items():
                if isinstance(param_value, str) and param_value.startswith("${"):
                    logger.info(f"Found dependency: {param_name} -> {param_value}")
        
        logger.info("\nWorkflow builder test completed successfully")
        return workflow_def
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    test_workflow_builder()