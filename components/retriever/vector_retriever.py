import os
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
import time
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import numpy as np
from elasticsearch.connection import create_ssl_context
import ssl
from opensearchpy import OpenSearch

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

        if self.config.user_config['search'] == 'pinecone':
            self._initialize_pinecone()
        elif self.config.user_config['search'] == 'opensearch':
            self._initialize_opensearch()
        else:
            raise ValueError(f"Unsupported database: {self.config.user_config['database']}")

        # Initialize embedding model
        # self.model = SentenceTransformer(config.user_config['model'])
        # logger.info(f"Loaded embedding model: {config.user_config['model']}")

        # Initialize Pinecone
        # api_key = os.getenv('PINECONE_API_KEY')
        # if not api_key:
        #     raise ValueError("PINECONE_API_KEY environment variable not set")
        #
        # pc = Pinecone(api_key=api_key)
        # self.index = pc.Index(config.user_config['index_name'])
        # logger.info(f"Connected to Pinecone index: {config.user_config['index_name']}")

    def _initialize_pinecone(self):
        logger.info(f"Initializing Pinecone vector store with index: {self.config.user_config['index_name']}")

        # Initialize Pinecone with API key
        api_key = os.getenv('PINECONE_API_KEY')
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable not set")

        pc = Pinecone(api_key=api_key)
        logger.info("Successfully initialized Pinecone client")

        logger.info(f"Connecting to index: {self.config.user_config['index_name']} {api_key}")
        # Get the index
        self.store = pc.Index(self.config.user_config['index_name'])
        logger.info(f"Successfully connected to index: {self.config.user_config['index_name']}")

    def _initialize_opensearch(self):
        logger.info(f"Initializing AWS OpenSearch with index: {self.config.user_config['index_name']}")
        try:
            self.store = None
            logger.info(f"Initializing AWS OpenSearch with index: {self.config.user_config['index_name']}")
            es_host = os.getenv('ES_HOST')
            dev_mode = os.getenv('DEV_MODE')
            if dev_mode:
                ssl_context = create_ssl_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                self.store = OpenSearch(
                    [es_host],
                    http_auth=("admin", "admin"),
                    verify_certs=False,
                    ssl_context=ssl_context,
                )
            else:
                self.store = OpenSearch([es_host], http_auth=())
            self.store.cluster.health()
            logger.info("Successfully initialized OpenSearch client")
        except Exception as e:
            logger.error(f"Error initializing OpenSearch client: {str(e)}")
            raise
        logger.info("Successfully initialized OpenSearch client")
        return self.store

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

            if self.config.user_config['search'] == 'pinecone':
                contexts = self.search_pinecone(query_embedding, top_k)
            elif self.config.user_config['search'] == 'opensearch':
                contexts = self.search_opensearch(query_embedding, top_k)
            else:
                raise ValueError(f"Unsupported database: {self.config.user_config['database']}")

            query_time = time.time() - start_time
            logger.info(f"Retrieved {len(contexts)} contexts in {query_time:.2f} seconds")

            return contexts

        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            raise

    def search_pinecone(self, query_embedding: np.ndarray, top_k: int) -> List[Dict]:
        results = self.store.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=self.config.user_config['namespace'],
            include_metadata=True
        )

        contexts = []
        for match in results.matches:
            contexts.append({
                'text': match.metadata['text'],
                'score': match.score
            })

        return contexts

    def search_opensearch(self, query_embedding: np.ndarray, top_k: int) -> List[Dict]:
        query = {
            "size": top_k,
            "query": {
                "bool": {
                    "must": [
                        {
                            "knn": {
                                "vector": {
                                    "vector": query_embedding,
                                    "k": top_k
                                }
                            }
                        },
                        {
                            "term": {
                                "namespace": self.config.user_config['namespace']
                            }
                        }
                    ]
                }
            }
        }

        logger.info(f"Executing OpenSearch query: {query}")
        response = self.store.search(
            index=self.config.user_config['index_name'],
            body=query
        )

        logger.info(response)

        contexts = []
        for hit in response['hits']['hits']:
            contexts.append({
                'text': hit['_source']['text'],
                'score': hit['_score']
            })

        return contexts
