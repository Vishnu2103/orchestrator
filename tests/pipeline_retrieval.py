# # config.py
# import os
# import json
# import time
# from dataclasses import dataclass
# from typing import List, Dict, Any, Optional
# import logging
# from datetime import datetime
# from dotenv import load_dotenv

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
# class RetrievalConfig:
#     canvas_id: str
#     canvas_config: List[ModuleConfig]

#     @classmethod
#     def from_dict(cls, config_dict: Dict) -> 'RetrievalConfig':
#         logger.info(f"Loading retrieval configuration with ID: {config_dict['canvas_id']}")
#         canvas_config = [
#             ModuleConfig(**module_config)
#             for module_config in config_dict['canvas_config']
#         ]
#         return cls(
#             canvas_id=config_dict['canvas_id'],
#             canvas_config=canvas_config
#         )

# # vector_store.py
# from pinecone import Pinecone
# from sentence_transformers import SentenceTransformer
# import numpy as np

# class VectorRetriever:
#     def __init__(self, config: ModuleConfig):
#         self.config = config
#         logger.info(f"Initializing vector retriever")
        
#         # Initialize embedding model
#         self.model = SentenceTransformer(config.user_config['model'])
#         logger.info(f"Loaded embedding model: {config.user_config['model']}")
        
#         # Initialize Pinecone
#         api_key = os.getenv('PINECONE_API_KEY')
#         if not api_key:
#             raise ValueError("PINECONE_API_KEY environment variable not set")
        
#         pc = Pinecone(api_key=api_key)
#         self.index = pc.Index(config.user_config['index_name'])
#         logger.info(f"Connected to Pinecone index: {config.user_config['index_name']}")

#     def get_relevant_context(self, query: str, top_k: int = 3) -> List[Dict]:
#         """Retrieve relevant context based on the query"""
#         start_time = time.time()
        
#         # Generate query embedding
#         query_embedding = self.model.encode(query)
#         logger.info(f"Generated query embedding")
        
#         # Search in Pinecone
#         results = self.index.query(
#             vector=query_embedding.tolist(),
#             top_k=top_k,
#             namespace=self.config.user_config['namespace'],
#             include_metadata=True
#         )
        
#         # Format results
#         contexts = []
#         for match in results.matches:
#             contexts.append({
#                 'text': match.metadata['text'],
#                 'score': match.score
#             })
        
#         query_time = time.time() - start_time
#         logger.info(f"Retrieved {len(contexts)} contexts in {query_time:.2f} seconds")
        
#         return contexts

# # openai_handler.py
# from openai import OpenAI

# class OpenAIHandler:
#     def __init__(self, config: ModuleConfig):
#         self.config = config
#         api_key = os.getenv('OPENAI_API_KEY')
#         if not api_key:
#             raise ValueError("OPENAI_API_KEY environment variable not set")
        
#         self.client = OpenAI(api_key=api_key)
#         logger.info(f"Initialized OpenAI client with model: {config.user_config['model']}")
        
#         self.system_prompt = config.user_config.get('system_prompt', 
#             """You are a helpful AI assistant. Your task is to answer questions based on the provided context.
#             If the context doesn't contain sufficient information to answer the question, say so.
#             Always maintain a professional and helpful tone.""")

#     def generate_response(self, query: str, contexts: List[Dict]) -> str:
#         """Generate a response using OpenAI"""
#         try:
#             start_time = time.time()
            
#             # Format context for the prompt
#             formatted_contexts = "\n\n".join([
#                 f"Context (relevance score: {context['score']:.2f}):\n{context['text']}"
#                 for context in contexts
#             ])
            
#             messages = [
#                 {"role": "system", "content": self.system_prompt},
#                 {"role": "user", "content": f"""Question: {query}

# Available Context:
# {formatted_contexts}

# Please provide a response based on the above context."""}
#             ]
            
#             # Get completion from OpenAI
#             response = self.client.chat.completions.create(
#                 model=self.config.user_config['model'],
#                 messages=messages,
#                 temperature=self.config.user_config.get('temperature', 0.7),
#                 max_tokens=self.config.user_config.get('max_tokens', 500)
#             )
            
#             answer = response.choices[0].message.content
            
#             completion_time = time.time() - start_time
#             logger.info(f"Generated response in {completion_time:.2f} seconds")
            
#             return answer
            
#         except Exception as e:
#             logger.error(f"Error generating OpenAI response: {str(e)}")
#             raise

# # retrieval_pipeline.py
# class RetrievalPipeline:
#     def __init__(self, vector_retriever: VectorRetriever, openai_handler: OpenAIHandler):
#         self.vector_retriever = vector_retriever
#         self.openai_handler = openai_handler

#     def process_query(self, query: str) -> str:
#         """Process a query through the full pipeline"""
#         try:
#             # Get relevant contexts
#             contexts = self.vector_retriever.get_relevant_context(query)
            
#             # Generate response
#             response = self.openai_handler.generate_response(query, contexts)
            
#             return response
            
#         except Exception as e:
#             logger.error(f"Error processing query: {str(e)}")
#             raise

# # main.py
# def main():
#     start_time = time.time()
#     logger.info("Starting document processing pipeline")
    
#     try:
#         # Load configuration
#         with open('config_retrieval.json', 'r') as f:
#             config = json.load(f)

#         # Initialize pipeline
#         logger.info("Initializing retrieval pipeline")
#         retrieval_config = RetrievalConfig.from_dict(config)
        
#         vector_retriever = VectorRetriever(
#             next(m for m in retrieval_config.canvas_config if m.identifier == 'vector_retriever')
#         )
        
#         openai_handler = OpenAIHandler(
#             next(m for m in retrieval_config.canvas_config if m.identifier == 'openai_handler')
#         )
        
#         pipeline = RetrievalPipeline(vector_retriever, openai_handler)
        
#         # Interactive query loop
#         print("\nDocument Q&A System")
#         print("Type 'exit' to quit\n")
        
#         while True:
#             query = input("\nEnter your question: ").strip()
            
#             if query.lower() == 'exit':
#                 break
                
#             try:
#                 logger.info(f"Processing query: {query}")
#                 response = pipeline.process_query(query)
#                 print("\nResponse:", response)
                
#             except Exception as e:
#                 logger.error(f"Error: {str(e)}")
#                 print("\nAn error occurred. Please try again.")
                
#     except Exception as e:
#         logger.error(f"Pipeline initialization failed: {str(e)}")
#         raise

# if __name__ == "__main__":
#     main()