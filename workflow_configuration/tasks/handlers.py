import json
import logging
import re
from typing import Dict, Any

from components.action.action import ActionHandler
from components.chunker.LineChunker import LineChunker
from components.chunker.SentenceSplitter import SentenceSplitter
from components.language_component.detect_language import DetectLanguage, TranslateLanguage
from freshflow.models.task_handler import TaskHandler
from components.downloader import S3Downloader
from components.chunker import DocumentChunker
from components.preprocessor import DocumentPreprocessor
from components.embedder import EmbeddingsGenerator
from components.vector_store import VectorStore
from dataclasses import dataclass
import numpy as np
from .registry import TaskHandlerRegistry
from components.input import TextInput
from components.retriever import VectorRetriever
from components.assistant import OpenAIHandler

logger = logging.getLogger(__name__)


@dataclass
class ModuleConfig:
    module_id: str
    identifier: str
    user_config: Dict[str, Any]


@TaskHandlerRegistry.register('s3_downloader')
class DownloadTaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'download_001'),
                identifier='s3_downloader',
                user_config=task_input.get('user_config', {})
            )

            downloader = S3Downloader(config)
            content = downloader.download_file()

            return {
                'status': 'COMPLETED',
                'output': {
                    'content': content
                }
            }
        except Exception as e:
            logger.error(f"Download task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }


@TaskHandlerRegistry.register('recursive_chunker')
class ChunkTaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'process_001'),
                identifier='document_processor',
                user_config=task_input.get('user_config', {})
            )

            config.user_config['splitting_strategy'] = 'text_splitter'
            # Get content from user_config's input_content reference
            content = task_input.get('user_config', {}).get('input_content')
            if not content:
                raise ValueError("No content provided for chunking")

            chunker = DocumentChunker(config)
            chunks = chunker.chunk_document(content)

            return {
                'status': 'COMPLETED',
                'output': {
                    'chunks': chunks
                }
            }
        except Exception as e:
            logger.error(f"Chunk task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }


@TaskHandlerRegistry.register('line_chunker')
class ChunkTaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'process_001'),
                identifier='document_processor',
                user_config=task_input.get('user_config', {})
            )

            config.user_config['splitting_strategy'] = 'line_chunker'
            # Get content from user_config's input_content reference
            content = task_input.get('user_config', {}).get('input_content')
            if not content:
                raise ValueError("No content provided for chunking")

            chunker = DocumentChunker(config)
            chunks = chunker.chunk_document(content)

            return {
                'status': 'COMPLETED',
                'output': {
                    'chunks': chunks
                }
            }
        except Exception as e:
            logger.error(f"Chunk task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }


@TaskHandlerRegistry.register('sentence_splitter')
class ChunkTaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'process_001'),
                identifier='document_processor',
                user_config=task_input.get('user_config', {})
            )

            config.user_config['splitting_strategy'] = 'sentence_splitter'
            # Get content from user_config's input_content reference
            content = task_input.get('user_config', {}).get('input_content')
            if not content:
                raise ValueError("No content provided for chunking")

            chunker = DocumentChunker(config)
            chunks = chunker.chunk_document(content)

            return {
                'status': 'COMPLETED',
                'output': {
                    'chunks': chunks
                }
            }
        except Exception as e:
            logger.error(f"Chunk task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }


@TaskHandlerRegistry.register('document_preprocessor')
class PreprocessTaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'process_002'),
                identifier='document_preprocessor',
                user_config=task_input.get('user_config', {})
            )

            # Get chunks from user_config's input_chunks reference
            chunks = task_input.get('user_config', {}).get('input_chunks')
            if not chunks:
                raise ValueError("No chunks provided for preprocessing")

            preprocessor = DocumentPreprocessor(config)
            processed_chunks = preprocessor.preprocess(chunks)

            return {
                'status': 'COMPLETED',
                'output': {
                    'processed_chunks': processed_chunks
                }
            }
        except Exception as e:
            logger.error(f"Preprocess task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }


@TaskHandlerRegistry.register('embeddings_generator')
class EmbeddingTaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'embed_001'),
                identifier='embeddings_generator',
                user_config=task_input.get('user_config', {})
            )

            # Get chunks from user_config's input_text reference
            chunks = task_input.get('user_config', {}).get('input_text')
            if not chunks:
                raise ValueError("No processed chunks provided for embedding")

            embedder = EmbeddingsGenerator(config)
            embeddings = embedder.generate_embeddings(chunks)

            # Convert numpy arrays to lists for JSON serialization
            if config.user_config['model'] == 'all-minilm-l6-v2':
                embeddings_list = [emb.tolist() for emb in embeddings]
            else:
                embeddings_list = embeddings

            logger.debug(f"Generated {embeddings_list} embeddings")

            return {
                'status': 'COMPLETED',
                'output': {
                    'embeddings': embeddings_list,
                    'chunks': chunks
                }
            }
        except Exception as e:
            logger.error(f"Embedding task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }


@TaskHandlerRegistry.register('minilm_embeddings_generator')
class EmbeddingTaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'embed_001'),
                identifier='embeddings_generator',
                user_config=task_input.get('user_config', {})
            )
            config.user_config['model'] = 'all-minilm-l6-v2'

            # Get chunks from user_config's input_text reference
            chunks = task_input.get('user_config', {}).get('input_text')
            if not chunks:
                raise ValueError("No processed chunks provided for embedding")

            embedder = EmbeddingsGenerator(config)
            embeddings = embedder.generate_embeddings(chunks)

            # Convert numpy arrays to lists for JSON serialization
            if config.user_config['model'] == 'all-minilm-l6-v2':
                embeddings_list = [emb.tolist() for emb in embeddings]
            else:
                embeddings_list = embeddings

            logger.debug(f"Generated {embeddings_list} embeddings")

            return {
                'status': 'COMPLETED',
                'output': {
                    'embeddings': embeddings_list,
                    'chunks': chunks
                }
            }
        except Exception as e:
            logger.error(f"Embedding task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }


@TaskHandlerRegistry.register('labse-sentence_embeddings_generator')
class EmbeddingTaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'embed_001'),
                identifier='embeddings_generator',
                user_config=task_input.get('user_config', {})
            )

            config.user_config['model'] = 'labse-sentence-embedding'
            # Get chunks from user_config's input_text reference
            chunks = task_input.get('user_config', {}).get('input_text')
            if not chunks:
                raise ValueError("No processed chunks provided for embedding")

            embedder = EmbeddingsGenerator(config)
            embeddings = embedder.generate_embeddings(chunks)

            # Convert numpy arrays to lists for JSON serialization
            if config.user_config['model'] == 'all-minilm-l6-v2':
                embeddings_list = [emb.tolist() for emb in embeddings]
            else:
                embeddings_list = embeddings

            logger.debug(f"Generated {embeddings_list} embeddings")

            return {
                'status': 'COMPLETED',
                'output': {
                    'embeddings': embeddings_list,
                    'chunks': chunks
                }
            }
        except Exception as e:
            logger.error(f"Embedding task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }


@TaskHandlerRegistry.register('bge-m3_embeddings_generator')
class EmbeddingTaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'embed_001'),
                identifier='embeddings_generator',
                user_config=task_input.get('user_config', {})
            )

            config.user_config['model'] = 'bge-m3'
            # Get chunks from user_config's input_text reference
            chunks = task_input.get('user_config', {}).get('input_text')
            if not chunks:
                raise ValueError("No processed chunks provided for embedding")

            embedder = EmbeddingsGenerator(config)
            embeddings = embedder.generate_embeddings(chunks)

            # Convert numpy arrays to lists for JSON serialization
            if config.user_config['model'] == 'all-minilm-l6-v2':
                embeddings_list = [emb.tolist() for emb in embeddings]
            else:
                embeddings_list = embeddings

            logger.debug(f"Generated {embeddings_list} embeddings")

            return {
                'status': 'COMPLETED',
                'output': {
                    'embeddings': embeddings_list,
                    'chunks': chunks
                }
            }
        except Exception as e:
            logger.error(f"Embedding task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }


@TaskHandlerRegistry.register('openai_embeddings_generator')
class EmbeddingTaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'embed_001'),
                identifier='embeddings_generator',
                user_config=task_input.get('user_config', {})
            )

            config.user_config['model'] = 'text-embedding-3-large'
            # Get chunks from user_config's input_text reference
            chunks = task_input.get('user_config', {}).get('input_text')
            if not chunks:
                raise ValueError("No processed chunks provided for embedding")

            embedder = EmbeddingsGenerator(config)
            embeddings = embedder.generate_embeddings(chunks)

            # Convert numpy arrays to lists for JSON serialization
            if config.user_config['model'] == 'all-minilm-l6-v2':
                embeddings_list = [emb.tolist() for emb in embeddings]
            else:
                embeddings_list = embeddings

            logger.debug(f"Generated {embeddings_list} embeddings")

            return {
                'status': 'COMPLETED',
                'output': {
                    'embeddings': embeddings_list,
                    'chunks': chunks
                }
            }
        except Exception as e:
            logger.error(f"Embedding task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }


@TaskHandlerRegistry.register('pincecone')
class VectorStoreTaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'store_001'),
                identifier='vector_store',
                user_config=task_input.get('user_config', {})
            )

            config.user_config['database'] = 'pinecone'
            # Get inputs from user_config references
            embeddings = task_input.get('user_config', {}).get('input_vectors')
            chunks = task_input.get('user_config', {}).get('input_chunks')

            if not embeddings or not chunks:
                raise ValueError("Missing embeddings or chunks for vector storage")

            # Convert lists back to numpy arrays
            embeddings_arrays = [np.array(emb) for emb in embeddings]

            vector_store = VectorStore(config)
            vector_store.store_vectors(embeddings_arrays, chunks)

            return {
                'status': 'COMPLETED',
                'output': {
                    'message': 'Vectors stored successfully'
                }
            }
        except Exception as e:
            logger.error(f"Vector store task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }


@TaskHandlerRegistry.register('opensearch')
class VectorStoreTaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'store_001'),
                identifier='vector_store',
                user_config=task_input.get('user_config', {})
            )

            config.user_config['database'] = 'opensearch'
            # Get inputs from user_config references
            embeddings = task_input.get('user_config', {}).get('input_vectors')
            chunks = task_input.get('user_config', {}).get('input_chunks')

            if not embeddings or not chunks:
                raise ValueError("Missing embeddings or chunks for vector storage")

            # Convert lists back to numpy arrays
            embeddings_arrays = [np.array(emb) for emb in embeddings]

            vector_store = VectorStore(config)
            vector_store.store_vectors(embeddings_arrays, chunks)

            return {
                'status': 'COMPLETED',
                'output': {
                    'message': 'Vectors stored successfully'
                }
            }
        except Exception as e:
            logger.error(f"Vector store task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }


@TaskHandlerRegistry.register('user_input')
class UserInputTaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'input_001'),
                identifier='user_input',
                user_config=task_input.get('user_config', {})
            )

            input_handler = TextInput(config)
            result = input_handler.get_input()

            return {
                'status': 'COMPLETED',
                'output': {
                   "input": result
                }
            }
        except Exception as e:
            logger.error(f"User input task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }


@TaskHandlerRegistry.register('vector_retriever')
class VectorRetrieverTaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'retriever_001'),
                identifier='vector_retriever',
                user_config=task_input.get('user_config', {})
            )

            # Get query from user_config's input_query reference
            query = task_input.get('user_config', {}).get('input_query')
            logger.info(f"Retrieving context for query: {query}")
            if not query:
                raise ValueError("No query provided for vector retrieval")

            retriever = VectorRetriever(config)
            contexts = retriever.get_relevant_context(query)

            return {
                'status': 'COMPLETED',
                'output': {
                    'contexts': contexts
                }
            }
        except Exception as e:
            logger.error(f"Vector retrieval task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }


@TaskHandlerRegistry.register('openai_handler')
class OpenAITaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'openai_001'),
                identifier='openai_handler',
                user_config=task_input.get('user_config', {})
            )

            config.user_config['platform'] = 'openai'
            # Get inputs from user_config references
            query = task_input.get('user_config', {}).get('input_query')
            contexts = task_input.get('user_config', {}).get('input_contexts')
            logger.info(f"Query: {query}, Contexts: {contexts}")
            if not query:
                raise ValueError("Missing query or contexts for OpenAI handler")

            handler = OpenAIHandler(config)
            response = handler.generate_response(query, contexts)
            logger.info(f"Generated openai_handler response: {response}")
            return {
                'status': 'COMPLETED',
                'output': {
                    'response': response
                }
            }
        except Exception as e:
            logger.error(f"OpenAI task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }


@TaskHandlerRegistry.register('deepseek_handler')
class OpenAITaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'openai_001'),
                identifier='openai_handler',
                user_config=task_input.get('user_config', {})
            )

            config.user_config['platform'] = 'deepseek'
            # Get inputs from user_config references
            query = task_input.get('user_config', {}).get('input_query')
            contexts = task_input.get('user_config', {}).get('input_contexts')
            logger.info(f"Query: {query}, Contexts: {contexts}")
            if not query:
                raise ValueError("Missing query for OpenAI handler")

            handler = OpenAIHandler(config)
            response = handler.generate_response(query, contexts)
            logger.info(f"Generated openai_handler response: {response}")
            return {
                'status': 'COMPLETED',
                'output': {
                    'response': response
                }
            }
        except Exception as e:
            logger.error(f"OpenAI task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }


@TaskHandlerRegistry.register('gemini_handler')
class OpenAITaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'openai_001'),
                identifier='openai_handler',
                user_config=task_input.get('user_config', {})
            )

            config.user_config['platform'] = 'gemini'
            # Get inputs from user_config references
            query = task_input.get('user_config', {}).get('input_query')
            contexts = task_input.get('user_config', {}).get('input_contexts')
            logger.info(f"Query: {query}, Contexts: {contexts}")
            if not query:
                raise ValueError("Missing query or contexts for OpenAI handler")

            handler = OpenAIHandler(config)
            response = handler.generate_response(query, contexts)
            logger.info(f"Generated openai_handler response: {response}")
            return {
                'status': 'COMPLETED',
                'output': {
                    'response': response
                }
            }
        except Exception as e:
            logger.error(f"OpenAI task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }


@TaskHandlerRegistry.register('claude_handler')
class OpenAITaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'openai_001'),
                identifier='openai_handler',
                user_config=task_input.get('user_config', {})
            )

            config.user_config['platform'] = 'claude'
            # Get inputs from user_config references
            query = task_input.get('user_config', {}).get('input_query')
            contexts = task_input.get('user_config', {}).get('input_contexts')
            logger.info(f"Query: {query}, Contexts: {contexts}")
            if not query:
                raise ValueError("Missing query or contexts for OpenAI handler")

            handler = OpenAIHandler(config)
            response = handler.generate_response(query, contexts)
            logger.info(f"Generated openai_handler response: {response}")
            return {
                'status': 'COMPLETED',
                'output': {
                    'response': response
                }
            }
        except Exception as e:
            logger.error(f"OpenAI task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }


@TaskHandlerRegistry.register('openrouter_handler')
class OpenAITaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'openai_001'),
                identifier='openai_handler',
                user_config=task_input.get('user_config', {})
            )

            config.user_config['platform'] = 'openrouter'
            # Get inputs from user_config references
            query = task_input.get('user_config', {}).get('input_query')
            contexts = task_input.get('user_config', {}).get('input_contexts')
            logger.info(f"Query: {query}, Contexts: {contexts}")
            if not query:
                raise ValueError("Missing query or contexts for OpenAI handler")

            handler = OpenAIHandler(config)
            response = handler.generate_response(query, contexts)
            logger.info(f"Generated openai_handler response: {response}")
            return {
                'status': 'COMPLETED',
                'output': {
                    'response': response
                }
            }
        except Exception as e:
            logger.error(f"OpenAI task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }


@TaskHandlerRegistry.register('detect_language')
class DetectLanguageTaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'detect_language_001'),
                identifier='detect_language',
                user_config=task_input.get('user_config', {})
            )

            # Get texts from user_config's input_texts reference
            texts = task_input.get('user_config', {}).get('input_query')
            logger.info(f"Detectinggg language for texts: {texts}")
            if not texts:
                raise ValueError("No texts provided for language detection")

            detector = DetectLanguage(config)
            detected_language = detector.detect_language([texts])
            logger.info(f"Detected language: {detected_language}")
            return {
                'status': 'COMPLETED',
                'output': {
                    'detected_language': detected_language
                }
            }
        except Exception as e:
            logger.error(f"Language detection task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }


@TaskHandlerRegistry.register('translate_language')
class TranslateLanguageTaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'translate_language_001'),
                identifier='translate_language',
                user_config=task_input.get('user_config', {})
            )

            # Get texts, source_language, and target_language from user_config references
            texts = task_input.get('user_config', {}).get('input_contexts')
            target_language = task_input.get('user_config', {}).get('input_query')
            logger.info(f"Translating {texts} to {target_language}")
            if not texts or not target_language:
                raise ValueError("Missing texts, source language, or target language for translation")

            translator = TranslateLanguage(config)
            translated_text = translator.translate_language([texts], target_language)

            return {
                'status': 'COMPLETED',
                'output': {
                    'translated_text': translated_text
                }
            }
        except Exception as e:
            logger.error(f"Translation task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }


@TaskHandlerRegistry.register('action_handler')
class ActionTaskHandler(TaskHandler):
    def execute(self, task_input: Dict) -> Dict:
        try:
            config = ModuleConfig(
                module_id=task_input.get('module_id', 'execute_action_001'),
                identifier='action_handler',
                user_config=task_input.get('user_config', {})
            )

            # Get texts from user_config's input_texts reference
            json_string = task_input.get('user_config', {}).get('input_contexts')
            query = task_input.get('user_config', {}).get('input_query')
            if not json_string:
                raise ValueError("No requests provided for Action Handler")

            intent = re.search(r'["\']intent["\']:\s*["\']([^"\']*)["\']', json_string)
            actionId = re.search(r'["\']actionId["\']:\s*["\']([^"\']*)["\']', json_string)
            if actionId:
                actionId = actionId.group(1)
            else:
                print("actionId not found")

            if intent:
                intent = intent.group(1)
            else:
                print("intent not found")

            logger.info(f"Executing action: {actionId} {query}")
            action = ActionHandler(config)
            action_results = action.process_requests(intent, actionId, query)
            logger.info(f"Action Handler: {action_results}")
            return {
                'status': 'COMPLETED',
                'output': {
                    'action_response': action_results
                }
            }
        except Exception as e:
            logger.error(f"Action Handler task failed: {str(e)}")
            return {
                'status': 'FAILED',
                'output': {
                    'error': str(e)
                }
            }