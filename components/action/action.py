import os
import logging
import requests
from typing import List, Dict, Any
from dataclasses import dataclass
import time
from dotenv import load_dotenv
import re

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class ModuleConfig:
    module_id: str
    identifier: str
    user_config: Dict[str, Any]


class ActionHandler:
    def __init__(self, config: ModuleConfig):
        self.config = config
        self.pattern = re.compile(r'\s+', re.IGNORECASE)

    def make_api_call(self, url: str, request: Dict, headers: Dict) -> Dict:
        """Make an API call with the given URL, request body, and headers"""
        try:
            start_time = time.time()
            response = requests.post(url, json=request, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            completion_time = time.time() - start_time
            logger.info(f"API call to {url} completed in {completion_time:.2f} seconds")
            return response_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making API call to {url}: {str(e)}")
            raise

    def process_requests(self):
        """Process each request based on the action specified"""
        for req in self.config.user_config['requests']:
            name = req.get('name')
            url = req.get('url')
            headers = req.get('headers', {})
            body = req.get('body', {})
            action = req.get('action')

            logger.info(f"Processing request: {name} with action: {action}")

            normalized_name = self.pattern.sub('', name).lower()
            normalized_action = self.pattern.sub('', action).lower()
            logger.info(f"Normalized name: {normalized_name}, normalized action: {normalized_action}")
            if normalized_name == normalized_action:
                response = self.make_api_call(url, body, headers)
                logger.info(f"Response for {name}: {response}")
            else:
                logger.warning(f"Unknown action: {action} for request: {name}")
