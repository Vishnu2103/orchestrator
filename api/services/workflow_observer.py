import logging
from typing import Dict, Optional
from .state_store import StateStore
from .event_bus import EventBus

logger = logging.getLogger(__name__)

class WorkflowObserver:
    """Observes workflow execution and updates state/events"""
    
    def __init__(self, workflow_id: str, state_store: StateStore, event_bus: EventBus):
        """Initialize workflow observer
        
        Args:
            workflow_id: ID of workflow being observed
            state_store: StateStore instance for persisting state
            event_bus: EventBus instance for real-time updates
        """
        self.workflow_id = workflow_id
        self.state_store = state_store
        self.event_bus = event_bus
        logger.info(f"Initialized observer for workflow {workflow_id}")
    
    def on_module_start(self, module_id: str) -> None:
        """Called when module execution starts"""
        try:
            brief_output = {
                "message": f"Starting module {module_id}"
            }
            
            self.state_store.update_module_status(
                self.workflow_id,
                module_id,
                "IN_PROGRESS",
                brief_output=brief_output
            )
            
            self.event_bus.publish(
                self.workflow_id,
                {
                    "type": "module_update",
                    "module_id": module_id,
                    "status": "IN_PROGRESS",
                    "brief_output": brief_output
                }
            )
            
            logger.info(f"Module {module_id} started in workflow {self.workflow_id}")
            
        except Exception as e:
            logger.error(f"Error handling module start for {module_id}: {e}")
    
    def on_module_complete(self, module_id: str, output: Dict) -> None:
        """Called when module execution completes successfully"""
        try:
            # Create brief output from full output
            brief_output = self._create_brief_output(module_id, output)
            
            self.state_store.update_module_status(
                self.workflow_id,
                module_id,
                "COMPLETED",
                brief_output=brief_output,
                detailed_output=output
            )
            
            self.event_bus.publish(
                self.workflow_id,
                {
                    "type": "module_update",
                    "module_id": module_id,
                    "status": "COMPLETED",
                    "brief_output": brief_output
                }
            )
            
            logger.info(f"Module {module_id} completed in workflow {self.workflow_id}")
            
        except Exception as e:
            logger.error(f"Error handling module completion for {module_id}: {e}")
    
    def on_module_error(self, module_id: str, error: str) -> None:
        """Called when module execution fails"""
        try:
            brief_output = {
                "message": "Module execution failed",
                "error": str(error)
            }
            
            detailed_output = {
                "error": str(error),
                "type": "module_error"
            }
            
            self.state_store.update_module_status(
                self.workflow_id,
                module_id,
                "FAILED",
                brief_output=brief_output,
                detailed_output=detailed_output
            )
            
            self.event_bus.publish(
                self.workflow_id,
                {
                    "type": "module_update",
                    "module_id": module_id,
                    "status": "FAILED",
                    "brief_output": brief_output
                }
            )
            
            logger.error(f"Module {module_id} failed in workflow {self.workflow_id}: {error}")
            
        except Exception as e:
            logger.error(f"Error handling module error for {module_id}: {e}")
    
    def on_workflow_complete(self) -> None:
        """Called when workflow execution completes successfully"""
        try:
            self.state_store.update_workflow_status(
                self.workflow_id,
                "COMPLETED"
            )
            
            # Get final state for event
            final_state = self.state_store.get_workflow_status(self.workflow_id)
            
            self.event_bus.publish(
                self.workflow_id,
                {
                    "type": "workflow_update",
                    "status": "COMPLETED",
                    "summary": final_state["summary"]
                }
            )
            
            logger.info(f"Workflow {self.workflow_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error handling workflow completion: {e}")
    
    def on_workflow_error(self, error: str) -> None:
        """Called when workflow execution fails"""
        try:
            error_details = {
                "message": str(error),
                "type": "workflow_error"
            }
            
            self.state_store.update_workflow_status(
                self.workflow_id,
                "FAILED",
                error=error_details
            )
            
            self.event_bus.publish(
                self.workflow_id,
                {
                    "type": "workflow_update",
                    "status": "FAILED",
                    "error": error_details
                }
            )
            
            logger.error(f"Workflow {self.workflow_id} failed: {error}")
            
        except Exception as e:
            logger.error(f"Error handling workflow error: {e}")
    
    def _create_brief_output(self, module_id: str, output: Dict) -> Dict:
        """Create brief output from detailed output"""
        # Default brief output
        brief = {
            "message": f"Module {module_id} completed successfully"
        }
        
        # Add key metrics based on module type
        if "content_length" in output:
            brief["size"] = output["content_length"]
        if "total_chunks" in output:
            brief["chunks"] = output["total_chunks"]
        if "total_tokens" in output:
            brief["tokens"] = output["total_tokens"]
        if "embeddings" in output:
            brief["embeddings_count"] = len(output["embeddings"])
            
        return brief 