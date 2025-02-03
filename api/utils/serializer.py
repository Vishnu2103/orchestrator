import base64
from typing import Any
import json

def serialize_output(obj: Any) -> Any:
    """Serialize output to JSON-compatible format
    
    Handles:
    - bytes (converts to base64)
    - sets (converts to list)
    - custom objects (uses __dict__)
    """
    if isinstance(obj, bytes):
        return {
            "_type": "bytes",
            "data": base64.b64encode(obj).decode('utf-8')
        }
    elif isinstance(obj, set):
        return list(obj)
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable") 