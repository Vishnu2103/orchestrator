import json
import logging
from workflow_configuration.workflows.builder import WorkflowBuilder
from freshflow.engine.workflow_engine import WorkflowEngine, WorkflowExecutionError
from freshflow.models.workflow import WorkflowDefinition

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def serialize_output(obj):
    """Custom JSON serializer to handle bytes"""
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

def main():
    try:
        # Load module configuration
        logger.info("Loading configuration...")
        with open('configs/test_config.json', 'r') as f:
            config = json.load(f)
        
        # Convert to Conductor format using existing WorkflowBuilder
        logger.info("Converting configuration to workflow definition...")
        workflow_builder = WorkflowBuilder(config)
        conductor_workflow = workflow_builder.create_workflow_definition()
        
        # Create WorkflowDefinition from conductor workflow
        workflow_def = WorkflowDefinition(conductor_workflow)
        
        # Execute with freshflow
        logger.info("Initializing workflow engine...")
        engine = WorkflowEngine()
        
        logger.info("Starting workflow execution...")
        try:
            result = engine.execute(workflow_def)
            logger.info("Workflow completed successfully")
            logger.info(f"Result: {json.dumps(result, indent=2, default=serialize_output)}")
            
            # Print task outputs for inspection
            logger.info("\nTask Outputs:")
            for task_ref, output in engine.get_task_outputs().items():
                logger.info(f"\n{task_ref}:")
                logger.info(json.dumps(output, indent=2, default=serialize_output))
            
        except WorkflowExecutionError as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            
            # Print task errors if any
            errors = engine.get_task_errors()
            if errors:
                logger.error("\nTask Errors:")
                for task_ref, error in errors.items():
                    logger.error(f"{task_ref}: {error}")
            
            raise
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()