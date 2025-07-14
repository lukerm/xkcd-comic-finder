#!/usr/bin/env python3
#  Copyright (C) 2025 lukerm of www.zl-labs.tech
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""
Weaviate client for storing XKCD comic data.
"""
import logging
from typing import Dict, List

import weaviate
import weaviate.classes as wvc
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.init import AdditionalConfig, Timeout

from ..utils_data_models import Comic

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class XKCDWeaviateClient:
    """Client for interacting with Weaviate database for XKCD comics."""

    def __init__(
        self,
        weaviate_host: str = "localhost",
        weaviate_port: int = 8080,
        batch_size: int = 100,
        timeout: int = 300,
    ):
        """
        Initialize the Weaviate client.

        Args:
            weaviate_host: Host of the Weaviate instance
            weaviate_port: Port of the Weaviate instance
            batch_size: Number of objects to batch when importing
            timeout: Timeout for requests to Weaviate in seconds
        """
        self.weaviate_host = weaviate_host
        self.weaviate_port = weaviate_port
        self.batch_size = batch_size
        self.timeout = timeout
        self.client = self._connect()

    def _connect(self):
        """Connect to Weaviate."""
        try:
            logger.info(f"Connecting to Weaviate at {self.weaviate_host}:{self.weaviate_port}")

            # Connect to local Weaviate instance
            client = weaviate.connect_to_local(
                host=self.weaviate_host,
                port=self.weaviate_port,
                additional_config=wvc.init.AdditionalConfig(
                    timeout=wvc.init.Timeout(init=self.timeout)
                )
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
            # Check if the collection already exists
            if self.client.collections.exists("XKCDComic"):
                logger.info("Schema for XKCDComic already exists")
                return

            # Create the collection with properties
            self.client.collections.create(
                name="XKCDComic",
                description="An XKCD comic with explanation and transcript",
                vectorizer_config=Configure.Vectorizer.text2vec_openai(
                    model="text-embedding-3-small"
                ),
                generative_config=Configure.Generative.openai(
                    model="gpt-3.5-turbo"
                ),
                properties=[
                    Property(
                        name="comic_id",
                        description="ID of the comic",
                        data_type=DataType.INT,
                    ),
                    Property(
                        name="title",
                        description="Title of the comic",
                        data_type=DataType.TEXT,
                        skip_vectorization=True,
                    ),
                    Property(
                        name="image_url",
                        description="URL of the comic image",
                        data_type=DataType.TEXT,
                        skip_vectorization=True,
                    ),
                    Property(
                        name="explanation",
                        description="Explanation of the comic",
                        data_type=DataType.TEXT,
                        skip_vectorization=False,
                    ),
                    Property(
                        name="transcript",
                        description="Transcript of the comic",
                        data_type=DataType.TEXT,
                        skip_vectorization=False,
                    ),
                ],
            )

            logger.info("Created collection for XKCDComic")

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

            # Get the collection
            collection = self.client.collections.get("XKCDComic")

            # Import comics in batches
            with collection.batch.dynamic() as batch:
                for k, comic in enumerate(comics):
                    if k > 0 and k % 100 == 0:
                        logger.info(f'Importing {k} / {len(comics)}')

                    # Convert Comic object to dictionary
                    data_object = {
                        "comic_id": comic.comic_id,
                        "title": comic.title,
                        "image_url": comic.image_url or "",
                        "explanation": comic.explanation,
                        "transcript": comic.transcript,
                    }

                    # Add data object to batch
                    batch.add_object(
                        properties=data_object,
                        uuid=weaviate.util.generate_uuid5(str(comic.comic_id)),
                    )

            logger.info(f"Successfully imported {len(comics)} comics into Weaviate")

        except Exception as e:
            logger.error(f"Error importing comics: {str(e)}")
            raise

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
                # Get collections
                collections = self.client.collections.list_all()
                info["schema_classes"] = list(collections)

                # Get comic count if XKCDComic collection exists
                if "XKCDComic" in info["schema_classes"]:
                    try:
                        collection = self.client.collections.get("XKCDComic")
                        result = collection.aggregate.over_all(total_count=True)
                        info["comic_count"] = result.total_count
                    except:
                        pass

            return info

        except Exception as e:
            logger.error(f"Error getting database info: {str(e)}")
            return {"ready": False, "error": str(e)}

    def __del__(self):
        """Close the connection when the object is destroyed."""
        if hasattr(self, 'client') and self.client:
            self.client.close()


def main():
    """Main function for command-line usage."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='XKCD Weaviate Client - Test and manage Weaviate database connection')
    parser.add_argument('--weaviate-host', type=str, default='localhost',
                       help='Host of Weaviate instance (default: localhost)')
    parser.add_argument('--weaviate-port', type=int, default=8080,
                       help='Port of Weaviate instance (default: 8080)')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Timeout for requests in seconds (default: 30)')
    parser.add_argument('--test-connection', action='store_true',
                       help='Test connection to Weaviate')
    parser.add_argument('--create-schema', action='store_true',
                       help='Create the XKCDComic schema')
    args = parser.parse_args()

    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return

    try:
        client = XKCDWeaviateClient(
            weaviate_host=args.weaviate_host,
            weaviate_port=args.weaviate_port,
            timeout=args.timeout
        )

        if args.test_connection:
            logger.info(f"Testing connection to Weaviate at {args.weaviate_host}:{args.weaviate_port}...")
            success = client.test_connection()
            if success:
                logger.info("✅ Connection test successful!")
                logger.info(f"Getting database information from {args.weaviate_host}:{args.weaviate_port}...")
                info = client.get_database_info()

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

        else:
            parser.print_help()

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
