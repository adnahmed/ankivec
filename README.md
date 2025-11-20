# AnkiVec - Vector Search for Anki

This anki addon creates vector embeddings for your cards, allowing you to search using natural language queries rather than keywords.

## Features

- **Vector Embeddings**: Generate embeddings for all cards using local Ollama models
- **Semantic Search**: Find cards by meaning, not just keywords
- **Fast Local Processing**: Uses lightweight embedding models (nomic-embed-text by default)
- **Persistent Storage**: ChromaDB stores embeddings for quick retrieval

## How to Use It

When you restart Anki after installing the add-on, a vector-database will be initialized for your deck. This process may take a few minute- you should see a loading dialog with a progress bar. From this point on, any changes to your deck will be automatically indexed.

To search the vector database, use the form "vec: [your query here]" in Anki's usual search bar. You can combine keyword searches with vector searches by putting the "vec" section at the end of the query: e.g. "keyword1 keyword2 vec: [natural language description]". 

## Prerequisites

1. **Anki** (version 2.1.45+)
2. **Ollama** installed and running locally

### Install Ollama

Download from [ollama.ai](https://ollama.ai) and install.

Pull the embedding model:
```bash
ollama pull nomic-embed-text
```
