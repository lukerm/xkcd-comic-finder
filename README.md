# XKCD Comic Finder

_A project for finding XKCD comics with semantic search and RAG._

Read the full details on the ZL Labs [website](https://zl-labs.tech/post/2025-06-27-xkcd-rag/).

[![Main Image](/image/tsne_visualization.png)](/image/tsne_visualization.png)


## Setup

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Local Weaviate instance
- AWS credentials (S3-read enabled)

### Installation

1. Clone the repository.
   ```
   git clone https://github.com/lukerm/xkcd-comic-finder.git
   cd xkcd-comic-finder
   ```

2. Install dependencies.
   From the project root, run:
   ```
   pip install .
   ```
   or for running the tests / visualization:
   ```
   pip install -e .[test,tsne]
   ```

3. Set up your OpenAI API key.
   
   Copy the example environment file and add your OpenAI API key:
   ```
   cp .env.example .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```
   
   Ensure your environment variable is in the shell session:
   ```
   export $(cat .env | xargs)
   ```

4. Set up Weaviate.
   
   The easiest way is to get a weaviate endpoint running is to use `docker compose`:
   ```
   docker compose up -d
   ```
   
   Test the connection with:
   ```
   export PYTHONPATH=. 
   python -m src.database.weaviate_client --test-connection
   ```

5. Schema.

   Create the schema defining the collection for storing the Comic data:
   ```commandline
   python -m src.database.weaviate_client --create-schema
   ```

   



## Usage

### Getting the Comic Data

_This was originally a scraper, but now points to an open S3 bucket mirroring the data. You'll need to set up AWS credentials first for download. 
See [here](https://zl-labs.tech/post/2025-06-27-xkcd-rag/#xkcd-dataset) for more details._

Get comics by range and save them to JSON files (iterates backwards from the starting ID):

```bash
python -m src.scraper.run_scraper range --start-id 42 --num-comics 10 --output-dir data/comics --min-delay 1.0 --max-delay 3.0 
```

Get comics by specific IDs:

```bash
python -m src.scraper.run_scraper scrape ids --comic-ids 200 307 404 500 --output-dir data/comics
```

### Populating the Database

Populate the database with:

```bash
export PYTHONPATH=.
python -m src.database.populate_db --comics-dir data/comics scrape --start-id 42 --num-comics 10
python -m src.database.populate_db --comics-dir data/comics scrape --comic-ids 200 307 404 500
```
In this case, the program will either scrape/download the specified comics or load them from `--comics-dir` if available there.

Instead, you can populate from previously downloaded files: _every_ comic-related JSON files in `--comics-dir`:

```bash
python -m src.database.populate_db --comics-dir data/comics load
```

### Querying Comics

Search for comics using natural language queries:

```bash
export PYTHONPATH=.
python -m src.search.query --query barrel --limit 3 --do-rag
```

The only required flag is `--query` for your search time. Other options include:

- `--limit`: Maximum number of results to return (default: 5)
- `--alpha`: Strength of the semantic part of the hybrid search (default: 0.5)
- `--weaviate-url`: URL of Weaviate instance (default: http://localhost:8080)
- `--timeout`: Timeout for Weaviate requests in seconds (default: 300)

## Data Format

Comics are saved as JSON files in the following format:

```json
{
  "comic_id": 605,
  "title": "Extrapolating",
  "image_url": "https://imgs.xkcd.com/comics/extrapolating.png",
  "explanation": "This comic is a joke about the incorrect application of linear extrapolation...",
  "transcript": "My Hobby: Extrapolating..."
}
```


If you like this project, please hit the ⭐ button!

This project was a great learning experience for me, and I hope that you find it interesting too. If you have any questions, 
please don't hesitate to get in touch via the [contact](https://zl-labs.tech/contact/) page on ZL Labs website.