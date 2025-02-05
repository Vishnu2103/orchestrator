import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from langchain.text_splitter import RecursiveCharacterTextSplitter
import time

from components.chunker.LineChunker import LineChunker
from components.chunker.SentenceSplitter import SentenceSplitter

logger = logging.getLogger(__name__)


@dataclass
class ModuleConfig:
    module_id: str
    identifier: str
    user_config: Dict[str, Any]


class DocumentChunker:
    def __init__(self, config: ModuleConfig):
        self.config = config
        logger.info(f"Initializing document chunker with chunk size: {config.user_config['chunk_size']}, "
                    f"overlap: {config.user_config['chunk_overlap']}")
        self.splitting_strategy = config.user_config['splitting_strategy']
        if self.splitting_strategy == 'text_splitter':
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=config.user_config['chunk_size'],
                chunk_overlap=config.user_config['chunk_overlap']
            )
        elif self.splitting_strategy == 'line_chunker':
            self.splitter = LineChunker()
        elif self.splitting_strategy == 'sentence_splitter':
            self.splitter = SentenceSplitter()
        else:
            raise ValueError(f"Unsupported splitting strategy: {self.splitting_strategy}")

    def chunk_document(self, content: bytes) -> List[str]:
        start_time = time.time()
        try:
            text = content.decode('utf-8')
            chunks = self.splitter.split_text(text)

            process_time = time.time() - start_time
            logger.info(f"Document chunking completed in {process_time:.2f} seconds")
            logger.info(f"Generated {len(chunks)} chunks")
            logger.info(f"Average chunk size: {sum(len(chunk) for chunk in chunks) / len(chunks):.0f} characters")

            return chunks
        except Exception as e:
            logger.error(f"Error during document chunking: {str(e)}")
            raise
