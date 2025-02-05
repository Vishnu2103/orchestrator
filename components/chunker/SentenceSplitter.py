import logging
import re
from typing import List

logger = logging.getLogger(__name__)


class SentenceSplitter:
    def __init__(self, chunk_size: int = 500):
        self.chunk_size = chunk_size

    def split_text(self, content: str) -> List[str]:
        try:
            logger.info(f"Sentence Splitter triggered {self.chunk_size}")
            # Use regex to split the content by sentences, ensuring that we keep punctuation
            sentences = re.split(r'(?<=[.!?]) +', content)  # Split on sentences

            chunks = []
            current_chunk = []

            # Group sentences into chunks
            for sentence in sentences:
                if sum(len(s) for s in current_chunk) + len(sentence) <= self.chunk_size:
                    current_chunk.append(sentence)
                else:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = [sentence]

            # Add the last chunk if exists
            if current_chunk:
                chunks.append(" ".join(current_chunk))

            return chunks

        except Exception as e:
            logger.error(f"Error during document chunking: {str(e)}")
            raise
