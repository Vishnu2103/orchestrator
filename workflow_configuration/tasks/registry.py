import logging
from typing import Dict, Type
from freshflow.models.task_handler import TaskHandler

logger = logging.getLogger(__name__)

class TaskHandlerRegistry:
    _handlers: Dict[str, Type[TaskHandler]] = {}

    @classmethod
    def register(cls, identifier: str):
        """Decorator to register task handlers"""
        def wrapper(handler_class: Type[TaskHandler]):
            cls._handlers[identifier] = handler_class
            logger.info(f"Registered task handler for: {identifier}")
            return handler_class
        return wrapper

    @classmethod
    def get_handler(cls, identifier: str) -> Type[TaskHandler]:
        """Get handler by identifier"""
        if identifier not in cls._handlers:
            raise ValueError(f"No handler registered for identifier: {identifier}")
        return cls._handlers[identifier]
    
    @classmethod
    def get_all_handlers(cls) -> Dict[str, Type[TaskHandler]]:
        """Get all registered handlers"""
        return cls._handlers.copy()