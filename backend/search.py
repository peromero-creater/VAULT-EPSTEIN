import os
from opensearchpy import OpenSearch
from sentence_transformers import SentenceTransformer
from typing import List, Dict

OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://opensearch:9200")
INDEX_NAME = "pages"

# Load embedding model
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
except:
    print("Warning: SentenceTransformer model not loaded. Semantic search will be unavailable.")
    model = None

client = OpenSearch(
    hosts=[OPENSEARCH_URL],
    http_compress=True,
    use_ssl=False,
    verify_certs=False,
    ssl_assert_hostname=False,
    ssl_show_warn=False,
)

def create_index():
    settings = {
        "settings": {
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 100
            }
        },
        "mappings": {
            "properties": {
                "text": {"type": "text"},
                "page_id": {"type": "integer"},
                "document_id": {"type": "integer"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": 384,
                    "method": {
                        "name": "hnsw",
                        "space_type": "l2",
                        "engine": "nmslib"
                    }
                },
                "metadata": {
                    "properties": {
                        "country_codes": {"type": "keyword"},
                        "person_names": {"type": "keyword"},
                        "year": {"type": "integer"}
                    }
                }
            }
        }
    }
    if not client.indices.exists(index=INDEX_NAME):
        client.indices.create(INDEX_NAME, body=settings)

def index_page(page_id: int, document_id: int, text: str, country_codes: List[str], person_names: List[str]):
    embedding = model.encode(text).tolist() if model else [0.0] * 384
    
    doc = {
        "text": text,
        "page_id": page_id,
        "document_id": document_id,
        "embedding": embedding,
        "metadata": {
            "country_codes": country_codes,
            "person_names": person_names
        }
    }
    client.index(index=INDEX_NAME, body=doc, id=str(page_id), refresh=True)

def search_pages(query: str, filters: Dict = None, limit: int = 10):
    # Hybrid search (simplified: just keyword search for now, 
    # but structure is ready for vector)
    
    query_body = {
        "size": limit,
        "query": {
            "bool": {
                "must": [
                    {"match": {"text": query}}
                ]
            }
        }
    }
    
    if filters:
        if "countries" in filters:
            query_body["query"]["bool"]["filter"] = [
                {"terms": {"metadata.country_codes": filters["countries"]}}
            ]
            
    response = client.search(body=query_body, index=INDEX_NAME)
    return response['hits']['hits']
