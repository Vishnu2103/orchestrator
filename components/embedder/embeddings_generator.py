import logging
import os
from typing import List, Dict, Any
from dataclasses import dataclass
import numpy as np
import requests
from sentence_transformers import SentenceTransformer
import time

logger = logging.getLogger(__name__)


@dataclass
class ModuleConfig:
    module_id: str
    identifier: str
    user_config: Dict[str, Any]


class EmbeddingsGenerator:
    def __init__(self, config: ModuleConfig):
        try:
            self.config = config
            logger.info(f"Loading embedding model: {config.user_config['model']}")
            self.batch_size = config.user_config.get('batch_size', 1)
            self.user_config = config.user_config
            logger.info(f"Batch size set to: {self.batch_size}")
            self.model_handlers = {
                'all-minilm-l6-v2': self._encode_with_all_minilm_l6_v2,
                'labse-sentence-embedding': self._encode_with_labse,
                'bge-m3': self._encode_with_bgem3,
                'text-embedding-3-large': self._encode_with_openai
            }
        except Exception as e:
            logger.error(f"Error initializing EmbeddingsGenerator: {str(e)}")
            raise

    def _encode_with_all_minilm_l6_v2(self, batch: List[str]) -> List[np.ndarray]:
        self.model = SentenceTransformer(self.user_config['model'])
        return self.model.encode(batch)

    def _encode_with_labse(self, batch: List[str]) -> List[np.ndarray]:
        logger.info(f"Encoding {batch} texts with LaBSE")
        response = requests.post(
            'https://fd-freddy-serv.cxbu.staging.freddyproject.com/embedding/api/v1/1/embed-labse',
            headers={'Content-Type': 'application/json'},
            json={'texts': batch, 'normalize': True}
        )
        if response.status_code == 200:
            return response.json()['embeddings']
        else:
            raise ValueError(f"Error from embedding API: {response.status_code} {response.text}")

    def _encode_with_openai(self, batch: List[str]) -> List[np.ndarray]:
        logger.info(f"Encoding {batch} texts with OpenAI")
        response = requests.post(
            'https://platforms-eastus-ai-stage07.openai.azure.com/openai/deployments/text-embedding-3-large-1/embeddings?api-version=2024-02-01',
            headers={
                'Content-Type': 'application/json',
                'api-key': os.getenv('AZURE_KEY')
            },
            json={'input': batch}
        )
        if response.status_code == 200:
            embeddings = [item['embedding'] for item in response.json()['data']]
            return embeddings
        else:
            raise ValueError(f"Error from embedding API: {response.status_code} {response.text}")

    def _encode_with_bgem3(self, batch: List[str]) -> List[np.ndarray]:
        response = requests.post(
            'https://fd-freddy-serv-prod.freddybot.com/similar-tickets-handler/embed',
            headers={
                'Content-Type': 'application/json',
                'product': 'freshdesk'
            },
            json={'tickets': batch}
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Error from embedding API: {response.status_code} {response.text}")

    def generate_embeddings(self, chunks: List[str]) -> List[np.ndarray]:
        start_time = time.time()
        logger.info(f"Starting embedding generation for {len(chunks)} chunks")

        try:
            embeddings = []
            total_batches = (len(chunks) + self.batch_size - 1) // self.batch_size

            for i in range(0, len(chunks), self.batch_size):
                batch_start_time = time.time()
                batch = chunks[i:i + self.batch_size]

                model_type = self.config.user_config['model']
                if model_type in self.model_handlers:
                    batch_embeddings = self.model_handlers[model_type](batch)
                else:
                    raise ValueError(f"Unsupported model: {model_type}")
                embeddings.extend(batch_embeddings)

                batch_time = time.time() - batch_start_time
                batch_num = (i // self.batch_size) + 1
                logger.info(f"Processed batch {batch_num}/{total_batches} in {batch_time:.2f} seconds")

            total_time = time.time() - start_time
            logger.info(f"Embedding generation completed in {total_time:.2f} seconds")
            logger.info(f"Average time per chunk: {total_time / len(chunks):.3f} seconds")
            return embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
