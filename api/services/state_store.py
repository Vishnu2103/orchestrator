import json
import logging
from typing import Dict, Optional
import redis
from datetime import datetime
from ..utils.serializer import serialize_output

logger = logging.getLogger(__name__)

class StateStore:
    """Manages workflow state using Redis"""

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_password = os.getenv("REDIS_PASSWORD", None)
    def __init__(self, redis_url):
        """Initialize state store with Redis connection"""
        try:
            self.redis = redis.Redis.from_url(
                            redis_url,
                            password=redis_password,
                            decode_responses=True
                        )
            logger.info("Connected to Redis successfully")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def initialize_workflow(self, workflow_id: str, config: Dict) -> None:
        """Initialize workflow state with module information"""
        initial_state = {
            "workflow_id": workflow_id,
            "status": "INITIALIZING",
            "start_time": datetime.utcnow().isoformat(),
            "modules": {
                module_id: {
                    "status": "WAITING",
                    "start_time": None,
                    "end_time": None,
                    "brief_output": None,
                    "detailed_output": None
                }
                for module_id in config.get("modules", {}).keys()
            },
            "summary": {
                "total_modules": len(config.get("modules", {})),
                "completed_modules": 0,
                "failed_modules": 0
            }
        }
        
        self._set_workflow_state(workflow_id, initial_state)
        logger.info(f"Initialized workflow state for {workflow_id}")
    
    def update_workflow_status(self, workflow_id: str, status: str, error: Optional[Dict] = None) -> None:
        """Update overall workflow status"""
        state = self._get_workflow_state(workflow_id)
        if not state:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        state["status"] = status
        if status in ["COMPLETED", "FAILED"]:
            state["end_time"] = datetime.utcnow().isoformat()
        
        if error:
            state["error"] = error
        
        self._set_workflow_state(workflow_id, state)
        logger.info(f"Updated workflow {workflow_id} status to {status}")
    
    def update_module_status(
        self,
        workflow_id: str,
        module_id: str,
        status: str,
        brief_output: Optional[Dict] = None,
        detailed_output: Optional[Dict] = None
    ) -> None:
        """Update module status and outputs"""
        state = self._get_workflow_state(workflow_id)
        if not state:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        if module_id not in state["modules"]:
            raise ValueError(f"Module {module_id} not found in workflow {workflow_id}")
        
        module_state = state["modules"][module_id]
        module_state["status"] = status
        
        if status == "IN_PROGRESS" and not module_state["start_time"]:
            module_state["start_time"] = datetime.utcnow().isoformat()
        elif status in ["COMPLETED", "FAILED"]:
            module_state["end_time"] = datetime.utcnow().isoformat()
        
        if brief_output is not None:
            module_state["brief_output"] = brief_output
        if detailed_output is not None:
            module_state["detailed_output"] = detailed_output
        
        # Update summary
        if status == "COMPLETED":
            state["summary"]["completed_modules"] += 1
        elif status == "FAILED":
            state["summary"]["failed_modules"] += 1
        
        self._set_workflow_state(workflow_id, state)
        logger.info(f"Updated module {module_id} status to {status} in workflow {workflow_id}")
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Get current workflow status"""
        return self._get_workflow_state(workflow_id)
    
    def _get_workflow_state(self, workflow_id: str) -> Optional[Dict]:
        """Get workflow state from Redis"""
        state_json = self.redis.get(f"workflow:{workflow_id}")
        return json.loads(state_json) if state_json else None
    
    def _set_workflow_state(self, workflow_id: str, state: Dict) -> None:
        """Set workflow state in Redis"""
        # Serialize any non-JSON serializable objects
        serialized_state = json.loads(
            json.dumps(state, default=serialize_output)
        )
        self.redis.set(f"workflow:{workflow_id}", json.dumps(serialized_state)) 