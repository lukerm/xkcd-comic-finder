#!/usr/bin/env python3
"""
Weaviate client for storing and retrieving XKCD comic data.
"""
import logging
from typing import Dict, List

import weaviate
from weaviate import Client
from weaviate.util import generate_uuid5

from ..utils_data_models import Comic

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class XKCDWeaviateClient:
    """Client for interacting with Weaviate database for XKCD comics."""
    
    def __init__(
        self,
        weaviate_url: str = "http://localhost:8080",
        batch_size: int = 100,
        timeout: int = 300,
    ):
        """
        Initialize the Weaviate client.
        
        Args:
            weaviate_url: URL of the Weaviate instance
            batch_size: Number of objects to batch when importing
            timeout: Timeout for requests to Weaviate in seconds
        """
        self.weaviate_url = weaviate_url
        self.batch_size = batch_size
        self.timeout = timeout
        self.client = self._connect()
        
    def _connect(self) -> Client:
        """Connect to Weaviate."""
        try:
            logger.info(f"Connecting to Weaviate at {self.weaviate_url}")
            client = weaviate.Client(
                url=self.weaviate_url,
                timeout_config=(self.timeout, self.timeout)
            )
            if not client.is_ready():
                raise ConnectionError("Weaviate is not ready")
            logger.info("Connected to Weaviate successfully")
            return client
        except Exception as e:
            logger.error(f"Error connecting to Weaviate: {str(e)}")
            raise
    
    def create_schema(self) -> None:
        """Create the schema for XKCD comics in Weaviate."""
        try:
            # Check if the schema already exists
            schema = self.client.schema.get()
            class_names = [c["class"] for c in schema["classes"]] if "classes" in schema else []
            
            if "XKCDComic" in class_names:
                logger.info("Schema for XKCDComic already exists")
                return
            
            # Define schema for XKCD comics
            comic_class = {
                "class": "XKCDComic",
                "description": "An XKCD comic with explanation and transcript",
                "vectorizer": "text2vec-openai",
                "moduleConfig": {
                    "text2vec-openai": {
                        "model": "text-embedding-3-small",
                        "modelVersion": "003",
                        "type": "text"
                    }
                },
                "properties": [
                    {
                        "name": "comic_id",
                        "description": "ID of the comic",
                        "dataType": ["int"],
                    },
                    {
                        "name": "title",
                        "description": "Title of the comic",
                        "dataType": ["text"],
                        "moduleConfig": {
                            "text2vec-openai": {
                                "skip": True,
                                "vectorizePropertyName": False,
                            }
                        },
                    },
                    {
                        "name": "image_url",
                        "description": "URL of the comic image",
                        "dataType": ["text"],
                        "moduleConfig": {
                            "text2vec-openai": {
                                "skip": True,
                                "vectorizePropertyName": False,
                            }
                        },
                    },
                    {
                        "name": "explanation",
                        "description": "Explanation of the comic",
                        "dataType": ["text"],
                        "moduleConfig": {
                            "text2vec-openai": {
                                "skip": False,
                                "vectorizePropertyName": False,
                            }
                        },
                    },
                    {
                        "name": "transcript",
                        "description": "Transcript of the comic",
                        "dataType": ["text"],
                        "moduleConfig": {
                            "text2vec-openai": {
                                "skip": False,
                                "vectorizePropertyName": False,
                            }
                        },
                    },
                ],
            }
            
            # Create the schema in Weaviate
            self.client.schema.create_class(comic_class)
            logger.info("Created schema for XKCDComic")
            
        except Exception as e:
            logger.error(f"Error creating schema: {str(e)}")
            raise
    
    def import_comics(self, comics: List[Comic]) -> None:
        """
        Import comics into Weaviate.
        
        Args:
            comics: List of Comic objects to import
        """
        try:
            logger.info(f"Importing {len(comics)} comics into Weaviate")
            
            # Make sure schema exists
            self.create_schema()
            
            # Create a batch process
            with self.client.batch as batch:
                batch.batch_size = self.batch_size
                
                # Add comics to batch
                for k, comic in enumerate(comics):
                    if k > 0 and k % 100 == 0:
                        logger.info(f'Importing {k} / {len(comics)}')

                    # Generate a deterministic UUID based on comic ID
                    uuid = generate_uuid5(str(comic.comic_id))
                    
                    # Convert Comic object to dictionary
                    data_object = {
                        "comic_id": comic.comic_id,
                        "title": comic.title,
                        "image_url": comic.image_url or "",
                        "explanation": comic.explanation,
                        "transcript": comic.transcript,
                    }
                    
                    # Add data object to batch
                    batch.add_data_object(
                        data_object=data_object,
                        class_name="XKCDComic",
                        uuid=uuid,
                    )
            
            logger.info(f"Successfully imported {len(comics)} comics into Weaviate")
            
        except Exception as e:
            logger.error(f"Error importing comics: {str(e)}")
            raise
    
    def search_comics(
        self,
        query: str,
        limit: int = 5,
        with_vector: bool = False
    ) -> List[Dict]:
        """
        Search for comics in Weaviate using semantic search.
        
        Args:
            query: Query string to search for
            limit: Maximum number of results to return
            with_vector: Whether to include vector representation in results
            
        Returns:
            List of dictionaries containing found comics
        """
        try:
            logger.info(f"Searching for comics with query: '{query}'")
            
            result = (
                self.client.query
                .get("XKCDComic", ["comic_id", "title", "image_url", "explanation", "transcript"])
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .do()
            )
            
            # Extract comics from result
            comics = result.get("data", {}).get("Get", {}).get("XKCDComic", [])
            
            logger.info(f"Found {len(comics)} comics matching query")
            
            return comics
            
        except Exception as e:
            logger.error(f"Error searching comics: {str(e)}")
            return []
    
    def test_connection(self) -> bool:
        """
        Test the connection to Weaviate.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Check if Weaviate is ready
            if not self.client.is_ready():
                logger.error("Weaviate is not ready")
                return False

            return True
            
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def get_database_info(self) -> dict:
        """
        Get information about the Weaviate database.
        
        Returns:
            Dictionary containing database information
        """
        try:
            info = {
                "ready": False,
                "schema_classes": [],
                "comic_count": 0,
                "version": None
            }
            
            # Check if ready
            info["ready"] = self.client.is_ready()
            
            if info["ready"]:
                # Get schema
                schema = self.client.schema.get()
                info["schema_classes"] = [c["class"] for c in schema.get("classes", [])]
                
                # Get version info
                try:
                    meta = self.client.cluster.get_nodes_status()
                    if meta and len(meta) > 0:
                        info["version"] = meta[0].get("version", "Unknown")
                except:
                    pass
                
                # Get comic count if XKCDComic class exists
                if "XKCDComic" in info["schema_classes"]:
                    try:
                        result = self.client.query.aggregate("XKCDComic").with_meta_count().do()
                        info["comic_count"] = result.get("data", {}).get("Aggregate", {}).get("XKCDComic", [{}])[0].get("meta", {}).get("count", 0)
                    except:
                        pass
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting database info: {str(e)}")
            return {"ready": False, "error": str(e)}


def main():
    """Main function for command-line usage."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='XKCD Weaviate Client - Test and manage Weaviate database connection')
    parser.add_argument('--weaviate-url', type=str, default='http://localhost:8080', 
                       help='URL of Weaviate instance (default: http://localhost:8080)')
    parser.add_argument('--timeout', type=int, default=30, 
                       help='Timeout for requests in seconds (default: 30)')
    parser.add_argument('--test-connection', action='store_true', 
                       help='Test connection to Weaviate')
    parser.add_argument('--create-schema', action='store_true', 
                       help='Create the XKCDComic schema')
    parser.add_argument('--search', type=str, 
                       help='Search for comics with the given query')
    parser.add_argument('--limit', type=int, default=5, 
                       help='Limit number of search results (default: 5)')
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    try:
        # Create client
        client = XKCDWeaviateClient(
            weaviate_url=args.weaviate_url,
            timeout=args.timeout
        )
        
        if args.test_connection:
            logger.info(f"Testing connection to Weaviate at {args.weaviate_url}...")
            success = client.test_connection()
            if success:
                logger.info("✅ Connection test successful!")
                logger.info(f"Getting database information from {args.weaviate_url}...")
                info = client.get_database_info()

                if info.get('version'):
                    logger.info(f"Version: {info['version']}")
                logger.info(f"Schema classes: {', '.join(info['schema_classes']) if info['schema_classes'] else 'None'}")
                logger.info(f"XKCDComic count: {info['comic_count']}")
                sys.exit(0)
            else:
                logger.info("❌ Connection test failed!")
                sys.exit(1)
        
        elif args.create_schema:
            print("Creating XKCDComic schema...")
            client.create_schema()
            print("✅ Schema created successfully!")
        
        elif args.search:
            print(f"Searching for comics with query: '{args.search}'")
            results = client.search_comics(args.search, limit=args.limit)
            
            if results:
                print(f"Found {len(results)} results:")
                for i, comic in enumerate(results, 1):
                    print(f"\n{i}. Comic #{comic.get('comic_id', 'Unknown')}: {comic.get('title', 'Unknown Title')}")
                    if comic.get('explanation'):
                        explanation = comic['explanation'][:200] + "..." if len(comic['explanation']) > 200 else comic['explanation']
                        print(f"   Explanation: {explanation}")
            else:
                print("No results found.")
        
        else:
            parser.print_help()
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
