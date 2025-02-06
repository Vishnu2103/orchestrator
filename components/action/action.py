import os
import logging
import requests
from typing import List, Dict, Any
from dataclasses import dataclass
import time
from dotenv import load_dotenv


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

    def make_canvas_api_call(self, url: str, headers: Dict) -> Dict:
        """Make a GET API call to the canvas URL with the given headers"""
        try:
            start_time = time.time()
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            completion_time = time.time() - start_time
            logger.info(f"Canvas API call to {url} completed in {completion_time:.2f} seconds")
            return response_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making canvas API call to {url}: {str(e)}")
            raise

    def poll_workflow_status(self, workflow_id: str, headers: Dict) -> Dict:
        """Poll the workflow status until it is COMPLETED"""
        status_url = f"http://localhost:8000/api/workflow/{workflow_id}/status"
        while True:
            try:
                response = requests.get(status_url, headers=headers)
                response.raise_for_status()
                status_data = response.json()
                logger.info(f"Workflow status: {status_data}")
                if status_data.get("status") == "COMPLETED" or status_data.get("status") == "FAILED":
                    return status_data
                time.sleep(5)  # Wait for 5 seconds before polling again
            except requests.exceptions.RequestException as e:
                logger.error(f"Error polling workflow status: {str(e)}")
                raise

    def process_requests(self, intent: str, actionId: str):
        """Process each request based on the action specified"""
        response = None
        for req in self.config.user_config['requests']:
            name = req.get('name')

            if actionId is not None and name.lower() == actionId.lower() and req.get('type') == 'api':
                url = req.get('url')
                headers = req.get('headers', {})
                body = req.get('body', {})
                response = self.make_api_call(url, body, headers)
                logger.info(f"Response for {name}: {response}")
                return response
            elif intent == "SEARCH" and req.get('type') == 'canvas':
                canvas_id = req.get('id')
                url = f'https://freddy-ml-pipeline-test.cxbu.staging.freddyproject.com/api/v1/canvas/{canvas_id}'
                headers = req.get('headers', {"account-id": "1"})
                response = self.make_canvas_api_call(url, headers)
                logger.info(f"Canvas response for {name}: {response}")
                mock_response = {
                    "canvas_name": "qa_retrieval_pipeline",
                    "modules": {
                        "user_input": {
                            "identifier": "user_input",
                            "user_config": {
                                "query": "உலகில் மிகவும் வளர்ந்த நாடு எது?"
                            }
                        },
                        "vector_retriever": {
                            "identifier": "vector_retriever",
                            "user_config": {
                                "search": "opensearch",
                                "type": "semantic",
                                "model": "text-embedding-3-large",
                                "index_name": "hackathonindex3072",
                                "namespace": "pdf_docs",
                                "top_k": 3,
                                "input_query": {
                                    "module_id": "user_input",
                                    "output_key": "query"
                                }
                            }
                        },
                        "openai_handler": {
                            "identifier": "openai_handler",
                            "user_config": {
                                "model": "gpt-4o",
                                "temperature": 0.7,
                                "max_tokens": 4200,
                                "system_prompt": "You are a helpful AI assistant specialized in answering questions about Freshflow's documentation. Your task is to provide accurate, concise answers based on the provided context. If the context doesn't contain sufficient information to answer the question, clearly state that. Always maintain a professional and helpful tone.",
                                "input_query": {
                                    "module_id": "user_input",
                                    "output_key": "query"
                                },
                                "input_contexts": {
                                    "module_id": "vector_retriever",
                                    "output_key": "contexts"
                                }
                            }
                        },
                        "detect_language": {
                            "identifier": "detect_language",
                            "user_config": {
                                "platform": "azure",
                                "input_query": {
                                    "module_id": "user_input",
                                    "output_key": "query"
                                }
                            }
                        },
                        "translate_language": {
                            "identifier": "translate_language",
                            "user_config": {
                                "platform": "azure",
                                "input_query": {
                                    "module_id": "detect_language",
                                    "output_key": "detected_language"
                                },
                                "input_contexts": {
                                    "module_id": "openai_handler",
                                    "output_key": "response"
                                }
                            }
                        }
                    }
                }
                url = "http://localhost:8000/api/workflow"
                result = self.make_api_call(url, mock_response, headers)
                logger.info(f"Workflow response for {name}: {result}")
                response = self.poll_workflow_status(result.get('workflow_id'), headers)
                logger.info(f"Workflow status for {name}: {response}")
                return response
        return response
