import logging
from typing import List, Dict, Any
from dataclasses import dataclass
import numpy as np
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
        self.config = config
        logger.info(f"Loading embedding model: {config.user_config['model']}")
        self.model = SentenceTransformer(config.user_config['model'])
        self.batch_size = config.user_config['batch_size']
        logger.info(f"Batch size set to: {self.batch_size}")

    def generate_embeddings(self, chunks: List[str]) -> List[np.ndarray]:
        start_time = time.time()
        logger.info(f"Starting embedding generation for {len(chunks)} chunks")
        
        try:
            embeddings = []
            total_batches = (len(chunks) + self.batch_size - 1) // self.batch_size
            
            for i in range(0, len(chunks), self.batch_size):
                batch_start_time = time.time()
                batch = chunks[i:i + self.batch_size]
                batch_embeddings = self.model.encode(batch)
                embeddings.extend(batch_embeddings)
                
                batch_time = time.time() - batch_start_time
                batch_num = (i // self.batch_size) + 1
                logger.info(f"Processed batch {batch_num}/{total_batches} in {batch_time:.2f} seconds")

            total_time = time.time() - start_time
            logger.info(f"Embedding generation completed in {total_time:.2f} seconds")
            logger.info(f"Average time per chunk: {total_time/len(chunks):.3f} seconds")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise 