import logging
import os
import requests
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ModuleConfig:
    module_id: str
    identifier: str
    user_config: Dict[str, Any]


class DetectLanguage:
    def __init__(self, config: ModuleConfig):
        self.config = config
        self.api_url = f"https://freddy-ai-platform.cxbu.staging.freddyproject.com/v1/freshcaller/freddy-ai-services/detect-languages?platform={self.config.user_config['platform']}"
        self.headers = {
            'Authorization': os.getenv('AUTHORIZATION'),
            'Freddy-Ai-Platform-Authorization': os.getenv('FREDDY_AI_PLATFORM_AUTHORIZATION'),
            'Content-Type': 'application/json'
        }

    def detect_language(self, texts: List[str]) -> str:
        logger.info(f"Detecting languages for {len(texts)} texts")
        response = requests.post(
            self.api_url,
            headers=self.headers,
            json={'texts': texts}
        )
        logger.info(f"detect_language Response: {self.headers} {texts}")
        if response.status_code == 200:
            return response.json()[0]['detected_language']
        else:
            raise ValueError(f"Error from language detection API: {response.status_code} {response.text}")


class TranslateLanguage:
    def __init__(self, config: ModuleConfig):
        self.config = config
        self.api_url = f"https://freddy-ai-platform.cxbu.staging.freddyproject.com/v1/freshcaller/freddy-ai-services/translations?platform={self.config.user_config['platform']}"
        self.headers = {
            'Authorization': os.getenv('AUTHORIZATION'),
            'Freddy-Ai-Platform-Authorization': os.getenv('FREDDY_AI_PLATFORM_AUTHORIZATION'),
            'Content-Type': 'application/json'
        }

    def translate_language(self, texts: List[str],target_language: str) -> List[str]:
        logger.info(f"Translating {len(texts)} texts from to {target_language}")
        response = requests.post(
            self.api_url,
            headers=self.headers,
            json={
                'texts': texts,
                'target_language': target_language
            }
        )
        logger.info(f"detect_language Response: {self.headers} {texts} {target_language}")
        if response.status_code == 200:
            return response.json()[0]['translated_text']
        else:
            raise ValueError(f"Error from translation API: {response.status_code} {response.text}")
