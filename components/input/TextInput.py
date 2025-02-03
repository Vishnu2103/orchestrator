import logging
from typing import Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ModuleConfig:
    module_id: str
    identifier: str
    user_config: Dict[str, Any]

class TextInput:
    def __init__(self, config: ModuleConfig):
        self.config = config
        if 'query' in config.user_config:
            self.query = config.user_config['query']
        else:
            self.prompt = config.user_config.get('prompt', 'Enter your question: ')
        logger.info("Initialized user input handler")

    def get_input(self) -> Dict[str, Any]:
        """Get input from the user"""
        try:
            if self.query:
                query = self.query
            else:
                query = input(self.prompt).strip()
            logger.info(f"Received user query: {query}")
            
            return {
                'query': query,
                'metadata': {
                    'timestamp': None,  # Can be added if needed
                    'source': 'user_input'
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting user input: {str(e)}")
            raise 