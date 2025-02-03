import logging
from typing import Dict, List, Optional, Callable
from queue import Queue
from threading import Lock
import json

logger = logging.getLogger(__name__)

class EventBus:
    """Manages real-time event distribution"""
    
    def __init__(self):
        """Initialize event bus"""
        self._subscribers: Dict[str, List[Queue]] = {}
        self._lock = Lock()
    
    def subscribe(self, workflow_id: str) -> Queue:
        """Subscribe to workflow events
        
        Returns:
            Queue that will receive workflow events
        """
        queue = Queue()
        
        with self._lock:
            if workflow_id not in self._subscribers:
                self._subscribers[workflow_id] = []
            self._subscribers[workflow_id].append(queue)
            
        logger.info(f"New subscriber added for workflow {workflow_id}")
        return queue
    
    def unsubscribe(self, workflow_id: str, queue: Queue) -> None:
        """Unsubscribe from workflow events"""
        with self._lock:
            if workflow_id in self._subscribers:
                try:
                    self._subscribers[workflow_id].remove(queue)
                    if not self._subscribers[workflow_id]:
                        del self._subscribers[workflow_id]
                    logger.info(f"Subscriber removed from workflow {workflow_id}")
                except ValueError:
                    pass
    
    def publish(self, workflow_id: str, event: Dict) -> None:
        """Publish event to workflow subscribers"""
        with self._lock:
            if workflow_id not in self._subscribers:
                return
                
            # Add timestamp to event if not present
            if "timestamp" not in event:
                from datetime import datetime
                event["timestamp"] = datetime.utcnow().isoformat()
            
            dead_queues = []
            for queue in self._subscribers[workflow_id]:
                try:
                    queue.put_nowait(event)
                except:
                    dead_queues.append(queue)
            
            # Clean up dead queues
            for queue in dead_queues:
                try:
                    self._subscribers[workflow_id].remove(queue)
                except ValueError:
                    pass
            
            if dead_queues:
                logger.warning(f"Removed {len(dead_queues)} dead queues for workflow {workflow_id}")
            
            logger.debug(f"Published event to {len(self._subscribers[workflow_id])} subscribers for workflow {workflow_id}")
    
    def get_subscriber_count(self, workflow_id: str) -> int:
        """Get number of subscribers for a workflow"""
        with self._lock:
            return len(self._subscribers.get(workflow_id, [])) 