import os
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
import numpy as np
from pinecone import Pinecone
import time
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

@dataclass
class ModuleConfig:
    module_id: str
    identifier: str
    user_config: Dict[str, Any]

class VectorStore:
    def __init__(self, config: ModuleConfig):
        self.config = config
        logger.info(f"Initializing Pinecone vector store with index: {config.user_config['index_name']}")
        
        # Initialize Pinecone with API key
        api_key = os.getenv('PINECONE_API_KEY')
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable not set")
        
        pc = Pinecone(api_key=api_key)
        logger.info("Successfully initialized Pinecone client")
        
        # Get the index
        self.index = pc.Index(config.user_config['index_name'])
        logger.info(f"Successfully connected to index: {config.user_config['index_name']}")

    def store_vectors(self, vectors: List[np.ndarray], chunks: List[str]):
        start_time = time.time()
        logger.info(f"Preparing to store {len(vectors)} vectors")
        
        try:
            vectors_with_ids = [
                (f"doc_{i}", vector.tolist(), {"text": chunk})
                for i, (vector, chunk) in enumerate(zip(vectors, chunks))
            ]
            
            # Store vectors in batches of 100
            batch_size = 100
            total_batches = (len(vectors_with_ids) + batch_size - 1) // batch_size
            
            for i in range(0, len(vectors_with_ids), batch_size):
                batch_start = time.time()
                batch = vectors_with_ids[i:i + batch_size]
                self.index.upsert(
                    vectors=batch,
                    namespace=self.config.user_config['namespace']
                )
                batch_time = time.time() - batch_start
                batch_num = (i // batch_size) + 1
                logger.info(f"Stored batch {batch_num}/{total_batches} in {batch_time:.2f} seconds")

            total_time = time.time() - start_time
            logger.info(f"Vector storage completed in {total_time:.2f} seconds")
            logger.info(f"Successfully stored {len(vectors)} vectors in namespace: {self.config.user_config['namespace']}")
            
        except Exception as e:
            logger.error(f"Error storing vectors: {str(e)}")
            raise 