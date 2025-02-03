import logging
import re
from typing import List, Dict, Any
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

@dataclass
class ModuleConfig:
    module_id: str
    identifier: str
    user_config: Dict[str, Any]

class DocumentPreprocessor:
    def __init__(self, config: ModuleConfig):
        self.config = config
        self.stop_words = set(config.user_config['stop_words'])
        logger.info(f"Initializing document preprocessor with {len(self.stop_words)} stop words")

    def preprocess(self, chunks: List[str]) -> List[str]:
        start_time = time.time()
        logger.info(f"Starting preprocessing of {len(chunks)} chunks")
        
        try:
            processed_chunks = []
            for i, chunk in enumerate(chunks, 1):
                processed = chunk
                for stop_word in self.stop_words:
                    processed = processed.replace(stop_word, ' ')
                processed = re.sub(r'\s+', ' ', processed).strip()
                processed_chunks.append(processed)
                
                if i % 100 == 0:
                    logger.debug(f"Processed {i}/{len(chunks)} chunks")

            process_time = time.time() - start_time
            logger.info(f"Preprocessing completed in {process_time:.2f} seconds")
            
            # Calculate reduction in size
            original_size = sum(len(chunk) for chunk in chunks)
            processed_size = sum(len(chunk) for chunk in processed_chunks)
            reduction_percent = ((original_size - processed_size) / original_size) * 100
            logger.info(f"Text reduction: {reduction_percent:.1f}%")
            
            return processed_chunks
            
        except Exception as e:
            logger.error(f"Error during preprocessing: {str(e)}")
            raise 