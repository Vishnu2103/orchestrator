# # config.py
# import json
# from dataclasses import dataclass
# from typing import List, Dict, Any
# import time
# import logging
# # downloader.py
# import boto3
# from botocore import UNSIGNED
# from botocore.client import Config
# # vector_store.py
# import os

# from dotenv import load_dotenv
# from pinecone import Pinecone
# from typing import List
# import numpy as np


# # preprocessor.py
# import re
# from typing import List

# # embedder.py
# from sentence_transformers import SentenceTransformer
# import numpy as np
# from typing import List

# # chunker.py
# from langchain.text_splitter import RecursiveCharacterTextSplitter

# load_dotenv()

# # Set up logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S'
# )
# logger = logging.getLogger(__name__)

# @dataclass
# class ModuleConfig:
#     module_id: str
#     identifier: str
#     user_config: Dict[str, Any]

# @dataclass
# class CanvasConfig:
#     canvas_id: str
#     canvas_config: List[ModuleConfig]

#     @classmethod
#     def from_dict(cls, config_dict: Dict) -> 'CanvasConfig':
#         logger.info(f"Loading canvas configuration with ID: {config_dict['canvas_id']}")
#         canvas_config = [
#             ModuleConfig(**module_config)
#             for module_config in config_dict['canvas_config']
#         ]
#         logger.info(f"Loaded {len(canvas_config)} module configurations")
#         return cls(
#             canvas_id=config_dict['canvas_id'],
#             canvas_config=canvas_config
#         )

# class S3Downloader:
#     def __init__(self, config: ModuleConfig):
#         self.config = config
#         logger.info(f"Initializing S3 downloader with access type: {config.user_config['access']}")
#         self.s3_client = boto3.client(
#             's3',
#             config=Config(signature_version=UNSIGNED) if config.user_config['access'] == 'public' else None
#         )

#     def download_file(self) -> bytes:
#         start_time = time.time()
#         bucket, key = self._parse_s3_uri(self.config.user_config['s3_link'])
#         logger.info(f"Downloading file from bucket: {bucket}, key: {key}")
        
#         try:
#             response = self.s3_client.get_object(Bucket=bucket, Key=key)
#             content = response['Body'].read()
#             download_time = time.time() - start_time
#             content_size_mb = len(content) / (1024 * 1024)
            
#             logger.info(f"Download completed in {download_time:.2f} seconds")
#             logger.info(f"File size: {content_size_mb:.2f} MB")
#             return content
#         except Exception as e:
#             logger.error(f"Error downloading file: {str(e)}")
#             raise

#     def _parse_s3_uri(self, uri: str) -> tuple:
#         path = uri.replace('s3://', '')
#         bucket, *key_parts = path.split('/')
#         return bucket, '/'.join(key_parts)

# class DocumentChunker:
#     def __init__(self, config: ModuleConfig):
#         self.config = config
#         logger.info(f"Initializing document chunker with chunk size: {config.user_config['chunk_size']}, "
#                    f"overlap: {config.user_config['chunk_overlap']}")
#         self.text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=config.user_config['chunk_size'],
#             chunk_overlap=config.user_config['chunk_overlap']
#         )

#     def chunk_document(self, content: bytes) -> List[str]:
#         start_time = time.time()
#         text = content.decode('utf-8')
#         chunks = self.text_splitter.split_text(text)
        
#         process_time = time.time() - start_time
#         logger.info(f"Document chunking completed in {process_time:.2f} seconds")
#         logger.info(f"Generated {len(chunks)} chunks")
#         logger.info(f"Average chunk size: {sum(len(chunk) for chunk in chunks)/len(chunks):.0f} characters")
        
#         return chunks

# class DocumentPreprocessor:
#     def __init__(self, config: ModuleConfig):
#         self.config = config
#         self.stop_words = set(config.user_config['stop_words'])
#         logger.info(f"Initializing document preprocessor with {len(self.stop_words)} stop words")

#     def preprocess(self, chunks: List[str]) -> List[str]:
#         start_time = time.time()
#         logger.info(f"Starting preprocessing of {len(chunks)} chunks")
        
#         processed_chunks = []
#         for i, chunk in enumerate(chunks, 1):
#             processed = chunk
#             for stop_word in self.stop_words:
#                 processed = processed.replace(stop_word, ' ')
#             processed = re.sub(r'\s+', ' ', processed).strip()
#             processed_chunks.append(processed)
            
#             if i % 100 == 0:
#                 logger.debug(f"Processed {i}/{len(chunks)} chunks")

#         process_time = time.time() - start_time
#         logger.info(f"Preprocessing completed in {process_time:.2f} seconds")
        
#         # Calculate reduction in size
#         original_size = sum(len(chunk) for chunk in chunks)
#         processed_size = sum(len(chunk) for chunk in processed_chunks)
#         reduction_percent = ((original_size - processed_size) / original_size) * 100
#         logger.info(f"Text reduction: {reduction_percent:.1f}%")
        
#         return processed_chunks

# class EmbeddingsGenerator:
#     def __init__(self, config: ModuleConfig):
#         self.config = config
#         logger.info(f"Loading embedding model: {config.user_config['model']}")
#         self.model = SentenceTransformer(config.user_config['model'])
#         self.batch_size = config.user_config['batch_size']
#         logger.info(f"Batch size set to: {self.batch_size}")

#     def generate_embeddings(self, chunks: List[str]) -> List[np.ndarray]:
#         start_time = time.time()
#         logger.info(f"Starting embedding generation for {len(chunks)} chunks")
        
#         embeddings = []
#         total_batches = (len(chunks) + self.batch_size - 1) // self.batch_size
        
#         for i in range(0, len(chunks), self.batch_size):
#             batch_start_time = time.time()
#             batch = chunks[i:i + self.batch_size]
#             batch_embeddings = self.model.encode(batch)
#             embeddings.extend(batch_embeddings)
            
#             batch_time = time.time() - batch_start_time
#             batch_num = (i // self.batch_size) + 1
#             logger.info(f"Processed batch {batch_num}/{total_batches} in {batch_time:.2f} seconds")

#         total_time = time.time() - start_time
#         logger.info(f"Embedding generation completed in {total_time:.2f} seconds")
#         logger.info(f"Average time per chunk: {total_time/len(chunks):.3f} seconds")
        
#         return embeddings

# class VectorStore:
#     def __init__(self, config: ModuleConfig):
#         self.config = config
#         logger.info(f"Initializing Pinecone vector store with index: {config.user_config['index_name']}")
        
#         # Initialize Pinecone with API key
#         api_key = os.getenv('PINECONE_API_KEY')
#         if not api_key:
#             raise ValueError("PINECONE_API_KEY environment variable not set")
        
#         pc = Pinecone(api_key=api_key)
#         logger.info("Successfully initialized Pinecone client")
        
#         # Get the index
#         self.index = pc.Index(config.user_config['index_name'])
#         logger.info(f"Successfully connected to index: {config.user_config['index_name']}")

#     def store_vectors(self, vectors: List[np.ndarray], chunks: List[str]):
#         start_time = time.time()
#         logger.info(f"Preparing to store {len(vectors)} vectors")
        
#         vectors_with_ids = [
#             (f"doc_{i}", vector.tolist(), {"text": chunk})
#             for i, (vector, chunk) in enumerate(zip(vectors, chunks))
#         ]
        
#         # Store vectors in batches of 100
#         batch_size = 100
#         total_batches = (len(vectors_with_ids) + batch_size - 1) // batch_size
        
#         for i in range(0, len(vectors_with_ids), batch_size):
#             batch_start = time.time()
#             batch = vectors_with_ids[i:i + batch_size]
#             self.index.upsert(
#                 vectors=batch,
#                 namespace=self.config.user_config['namespace']
#             )
#             batch_time = time.time() - batch_start
#             batch_num = (i // batch_size) + 1
#             logger.info(f"Stored batch {batch_num}/{total_batches} in {batch_time:.2f} seconds")

#         total_time = time.time() - start_time
#         logger.info(f"Vector storage completed in {total_time:.2f} seconds")
#         logger.info(f"Successfully stored {len(vectors)} vectors in namespace: {self.config.user_config['namespace']}")

# # main.py
# def main():
#     start_time = time.time()
#     logger.info("Starting document processing pipeline")
    
#     try:
#         # Load configuration
#         with open('config_ingestion.json', 'r') as f:
#             config_dict = json.load(f)
        
#         canvas_config = CanvasConfig.from_dict(config_dict)
#         logger.info(f"Loaded configuration for canvas: {canvas_config.canvas_id}")

#         # Initialize modules
#         logger.info("Initializing pipeline modules")
#         downloader = S3Downloader(
#             next(m for m in canvas_config.canvas_config if m.identifier == 's3_downloader')
#         )
#         chunker = DocumentChunker(
#             next(m for m in canvas_config.canvas_config if m.identifier == 'document_processor')
#         )
#         preprocessor = DocumentPreprocessor(
#             next(m for m in canvas_config.canvas_config if m.identifier == 'document_preprocessor')
#         )
#         embedder = EmbeddingsGenerator(
#             next(m for m in canvas_config.canvas_config if m.identifier == 'embeddings_generator')
#         )
#         vector_store = VectorStore(
#             next(m for m in canvas_config.canvas_config if m.identifier == 'vector_store')
#         )

#         # Execute pipeline
#         logger.info("Starting pipeline execution")
        
#         content = downloader.download_file()
#         logger.info("File download completed")
        
#         chunks = chunker.chunk_document(content)
#         logger.info("Document chunking completed")
        
#         processed_chunks = preprocessor.preprocess(chunks)
#         logger.info("Preprocessing completed")
        
#         embeddings = embedder.generate_embeddings(processed_chunks)
#         logger.info("Embedding generation completed")
        
#         vector_store.store_vectors(embeddings, processed_chunks)
#         logger.info("Vector storage completed")

#         total_time = time.time() - start_time
#         logger.info(f"Pipeline completed successfully in {total_time:.2f} seconds")
        
#     except Exception as e:
#         logger.error(f"Pipeline failed with error: {str(e)}", exc_info=True)
#         raise

# if __name__ == "__main__":
#     main()