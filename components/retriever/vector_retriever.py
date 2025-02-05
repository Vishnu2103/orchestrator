import os
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
import time
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

from components.embedder import EmbeddingsGenerator

load_dotenv()
logger = logging.getLogger(__name__)

@dataclass
class ModuleConfig:
    module_id: str
    identifier: str
    user_config: Dict[str, Any]

class VectorRetriever:
    def __init__(self, config: ModuleConfig):
        self.config = config
        logger.info(f"Initializing vector retriever")
        
        # Initialize embedding model
        # self.model = SentenceTransformer(config.user_config['model'])
        # logger.info(f"Loaded embedding model: {config.user_config['model']}")
        
        # Initialize Pinecone
        api_key = os.getenv('PINECONE_API_KEY')
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable not set")
        
        pc = Pinecone(api_key=api_key)
        self.index = pc.Index(config.user_config['index_name'])
        logger.info(f"Connected to Pinecone index: {config.user_config['index_name']}")

    def get_relevant_context(self, query: str, top_k: int = 3) -> List[Dict]:
        """Retrieve relevant context based on the query"""
        start_time = time.time()
        
        try:
            # Generate query embedding
            embedder = EmbeddingsGenerator(self.config)
            query_embedding = embedder.generate_embeddings([query])[0]
            logger.info(f"Generated query embedding")

            if self.config.user_config['model'] == 'all-minilm-l6-v2':
                query_embedding = query_embedding.tolist()

            # Search in Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                namespace=self.config.user_config['namespace'],
                include_metadata=True
            )
            
            # Format results
            contexts = []
            for match in results.matches:
                contexts.append({
                    'text': match.metadata['text'],
                    'score': match.score
                })
            
            query_time = time.time() - start_time
            logger.info(f"Retrieved {len(contexts)} contexts in {query_time:.2f} seconds")
            
            return contexts
            
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            raise 