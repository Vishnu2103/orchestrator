import logging
from typing import Dict, Optional
from uuid import uuid4
from threading import Thread
from queue import Queue

from freshflow.engine import WorkflowEngine
from freshflow.models.workflow import WorkflowDefinition
from workflow_configuration.workflows.builder import WorkflowBuilder
from .state_store import StateStore
from .event_bus import EventBus
from .workflow_observer import WorkflowObserver

logger = logging.getLogger(__name__)

class WorkflowManager:
    """Manages workflow execution and state"""
    
    def __init__(self, state_store: StateStore, event_bus: EventBus):
        """Initialize workflow manager
        
        Args:
            state_store: StateStore instance for persisting state
            event_bus: EventBus instance for real-time updates
        """
        self.state_store = state_store
        self.event_bus = event_bus
        self.engine = WorkflowEngine()
        logger.info("Initialized workflow manager")
    
    def create_workflow(self, config: Dict) -> str:
        """Create and start workflow execution
        
        Args:
            config: Workflow configuration
            
        Returns:
            str: Workflow ID
        """
        try:
            # Generate workflow ID
            workflow_id = str(uuid4())
            
            # Initialize workflow state
            self.state_store.initialize_workflow(workflow_id, config)
            
            # Create observer
            observer = WorkflowObserver(
                workflow_id,
                self.state_store,
                self.event_bus
            )
            
            # Start execution in background thread
            thread = Thread(
                target=self._execute_workflow,
                args=(workflow_id, config, observer)
            )
            thread.daemon = True
            thread.start()
            
            logger.info(f"Started workflow {workflow_id}")
            return workflow_id
            
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            raise
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Get current workflow status"""
        try:
            return self.state_store.get_workflow_status(workflow_id)
        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            raise
    
    def stream_events(self, workflow_id: str) -> Queue:
        """Subscribe to workflow events
        
        Returns:
            Queue that will receive workflow events
        """
        try:
            return self.event_bus.subscribe(workflow_id)
        except Exception as e:
            logger.error(f"Failed to subscribe to workflow events: {e}")
            raise
    
    def _execute_workflow(self, workflow_id: str, config: Dict, observer: WorkflowObserver) -> None:
        """Execute workflow in background thread"""
        try:
            # Update workflow status
            self.state_store.update_workflow_status(workflow_id, "IN_PROGRESS")
            
            # Create workflow builder and build definition
            builder = WorkflowBuilder(config)
            
            # Validate configuration
            builder.validate_config()
            
            # Create workflow definition
            workflow_def = WorkflowDefinition(builder.create_workflow_definition())
            
            # Execute workflow
            self.engine.execute(workflow_def, observer=observer)
            
            # Handle successful completion
            observer.on_workflow_complete()
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            observer.on_workflow_error(str(e)) 