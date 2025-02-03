# Local Setup


[For Architecture refer] - > /docs/Architecture.md

#### Requirements

- Python > 3.9

### Initial Setup and Starting Server
```python

python -m venv venvfreshflow
python venvfreshflow/source/bin/activate

pip install -r requirements.txt

redis-server (before this install redis locally with -> brew install redis)
python -m api.run
```

### Sample Request for Create/Run a Workflow(Canvas)
```bash
curl --location 'http://localhost:8000/api/workflow' \
--header 'Content-Type: application/json' \
--data '{
    "canvas_name": "ingestion_canvas",
    "modules": {
        "s3_downloader": {
            "identifier": "s3_downloader",
            "user_config": {
                "s3_link": "s3://general-vishnu/facts.txt",
                "access": "public"
            }
        },
        "document_processor": {
            "identifier": "document_processor",
            "user_config": {
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "splitting_strategy": "recursive",
                "input_content": {
                    "module_id": "s3_downloader",
                    "output_key": "content"
                }
            }
        },
        "document_preprocessor": {
            "identifier": "document_preprocessor",
            "user_config": {
                "stop_words": [".", "\n"],
                "input_chunks": {
                    "module_id": "document_processor",
                    "output_key": "chunks"
                }
            }
        },
        "embeddings_generator": {
            "identifier": "embeddings_generator",
            "user_config": {
                "model": "all-minilm-l6-v2",
                "batch_size": 100,
                "dimensions": 1536,
                "input_text": {
                    "module_id": "document_preprocessor",
                    "output_key": "processed_chunks"
                }
            }
        },
        "vector_store": {
            "identifier": "vector_store",
            "user_config": {
                "database": "pinecone",
                "index_name": "documents",
                "metric": "cosine",
                "namespace": "pdf_docs",
                "input_vectors": {
                    "module_id": "embeddings_generator",
                    "output_key": "embeddings"
                },
                "input_chunks": {
                    "module_id": "embeddings_generator",
                    "output_key": "chunks"
                }
            }
        }
    }
}'

```

### To Check Status of the workflow
```bash
curl --location --globoff 'http://localhost:8000/api/workflow/{{workflow_id}}/status'
```

### For streaming workflow updates
```bash
curl --location --globoff 'http://localhost:8000/api/workflow/{{workflow_id}}/stream'
```
