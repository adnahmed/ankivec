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

## Configuration

There are three parameters that govern how `AnkiVec` operates, available in the add-on's configuration dialog:

- **model_name**: The name of the Ollama model to use for generating embeddings. The default is "nomic-embed-text", but you can specify any model supported by Ollama (for example, "kronos483/MedEmbed-large-v0.1" for a specialized medical model).
- **search_results_limit**: The maximum number of search results to return. Default is 20.
- **ollama_host**: The URL of the Ollama server. Default is "http://localhost:11434".

## Future Plans

- **Other Platforms**: Currently, only Mac OS is supported. Windows support should be straightforward if I can get my hands on a Windows machine. Linux support is more tricky, as the `uv` binary bundled with Anki will be installed in different places depending on your distribution. I need to investigate how Anki is distributed in different package managers. 

- **Ordering by Relevance**: Currently, Anki's search feature allows you to filter the cards you seen in the Browser, but not to order them by a specific relevance score. Implementing this as an add on might require obscene amounts of monkey patching, but I think it will be worth the effort.

- **Debugging Ollama**: Ollama can be buggy. A small fraction of Anki notes cause Ollama to throw an error when generating embeddings. This is a known issue, and I'm working on figuring out what's going on.
