import os
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
import numpy as np
from pinecone import Pinecone
import time
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from elasticsearch.connection import create_ssl_context
import ssl
from opensearchpy import OpenSearch
from urllib.parse import urlparse

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
        if self.config.user_config['database'] == 'pinecone':
            logger.info(f"Initializing Pinecone vector store with index: {config.user_config['index_name']}")

            # Initialize Pinecone with API key
            api_key = os.getenv('PINECONE_API_KEY')
            if not api_key:
                raise ValueError("PINECONE_API_KEY environment variable not set")

            pc = Pinecone(api_key=api_key)
            logger.info("Successfully initialized Pinecone client")

            # Get the index
            self.store = pc.Index(config.user_config['index_name'])
            logger.info(f"Successfully connected to index: {config.user_config['index_name']}")
            self.store_vectors_func = self.store_vectors_pinecone
        elif self.config.user_config['database'] == 'opensearch':
            try:
                self.store = None
                logger.info(f"Initializing AWS OpenSearch with index: {config.user_config['index_name']}")
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
                    parsed_url = urlparse(es_host)
                    self.store = OpenSearch(
                        [
                            {
                                "host": parsed_url.hostname,
                                "port": parsed_url.port or 443,
                                "scheme": parsed_url.scheme,
                            }
                        ]
                    )
                self.store.cluster.health()
                logger.info("Successfully initialized OpenSearch client")
                self.store_vectors_func = self.store_vectors_os
            except Exception as e:
                logger.error(f"Error initializing OpenSearch client: {str(e)}")
                raise
        else:
            raise ValueError(f"Unsupported database: {self.config.user_config['database']}")

    def store_vectors(self, vectors: List[np.ndarray], chunks: List[str]):
        self.store_vectors_func(vectors, chunks)

    def store_vectors_pinecone(self, vectors: List[np.ndarray], chunks: List[str]):
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
                self.store.upsert(
                    vectors=batch,
                    namespace=self.config.user_config['namespace']
                )
                batch_time = time.time() - batch_start
                batch_num = (i // batch_size) + 1
                logger.info(f"Stored batch {batch_num}/{total_batches} in {batch_time:.2f} seconds")

            total_time = time.time() - start_time
            logger.info(f"Vector storage completed in {total_time:.2f} seconds")
            logger.info(
                f"Successfully stored {len(vectors)} vectors in namespace: {self.config.user_config['namespace']}")

        except Exception as e:
            logger.error(f"Error storing vectors: {str(e)}")
            raise

    def store_vectors_os(self, vectors: List[np.ndarray], chunks: List[str]):
        start_time = time.time()
        logger.info(f"Preparing to store {len(vectors)} vectors in OpenSearch")

        try:
            for i, (vector, chunk) in enumerate(zip(vectors, chunks)):
                doc = {
                    'vector': vector.tolist(),
                    'text': chunk,
                    'namespace': self.config.user_config['namespace']
                }
                self.store.index(
                    index=self.config.user_config['index_name'],
                    id=f"doc_{i}",
                    body=doc
                )
                logger.info(f"Stored document {i} in OpenSearch")

            total_time = time.time() - start_time
            logger.info(f"Vector storage in OpenSearch completed in {total_time:.2f} seconds")
            logger.info(f"Successfully stored {len(vectors)} vectors in index: {self.config.user_config['index_name']}")

        except Exception as e:
            logger.error(f"Error storing vectors in OpenSearch: {str(e)}")
            raise
