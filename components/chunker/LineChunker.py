import logging

from typing import List

logger = logging.getLogger(__name__)


class LineChunker:
    def __init__(self, chunk_size: int = 500):
        self.chunk_size = chunk_size

    def split_text(self, content_str: str) -> List[str]:
        try:
            # Decode bytes to string
            logger.info(f"LineChunker Triggered {self.chunk_size}")
            # Split content by lines
            lines = content_str.splitlines()
            chunks = []
            current_chunk = []

            # Group lines into chunks
            for line in lines:
                if sum(len(l) for l in current_chunk) + len(line) <= self.chunk_size:
                    current_chunk.append(line)
                else:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = [line]

            # Add the last chunk if exists
            if current_chunk:
                chunks.append("\n".join(current_chunk))

            return chunks

        except Exception as e:
            logger.error(f"Error during document chunking: {str(e)}")
            raise
