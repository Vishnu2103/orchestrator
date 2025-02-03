import os
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

@dataclass
class ModuleConfig:
    module_id: str
    identifier: str
    user_config: Dict[str, Any]

class OpenAIHandler:
    def __init__(self, config: ModuleConfig):
        self.config = config
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=api_key)
        logger.info(f"Initialized OpenAI client with model: {config.user_config['model']}")
        
        self.system_prompt = config.user_config.get('system_prompt', 
            """You are a helpful AI assistant. Your task is to answer questions based on the provided context.
            If the context doesn't contain sufficient information to answer the question, say so.
            Always maintain a professional and helpful tone.""")

    def generate_response(self, query: str, contexts: List[Dict]) -> str:
        """Generate a response using OpenAI"""
        try:
            start_time = time.time()
            
            # Format context for the prompt
            formatted_contexts = "\n\n".join([
                f"Context (relevance score: {context['score']:.2f}):\n{context['text']}"
                for context in contexts
            ])
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"""Question: {query}

Available Context:
{formatted_contexts}

Please provide a response based on the above context."""}
            ]
            
            # Get completion from OpenAI
            response = self.client.chat.completions.create(
                model=self.config.user_config['model'],
                messages=messages,
                temperature=self.config.user_config.get('temperature', 0.7),
                max_tokens=self.config.user_config.get('max_tokens', 500)
            )
            
            answer = response.choices[0].message.content
            
            completion_time = time.time() - start_time
            logger.info(f"Generated response in {completion_time:.2f} seconds")
            
            return answer
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {str(e)}")
            raise 