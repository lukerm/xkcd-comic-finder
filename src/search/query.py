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
Weaviate client for retrieving XKCD comic data.
"""

import logging
from typing import Dict, List
import weaviate.classes.query as wq

from ..database.weaviate_client import XKCDWeaviateClient


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def search_comics(
        client: XKCDWeaviateClient,
        query: str,
        limit: int = 5,
        alpha: float = 1,
        do_rag: bool = False,
        max_id: int = None,
) -> List[Dict]:
    """
    Search for comics in Weaviate using semantic search.

    Args:
        client: the bespoke XKCD client for connecting to weaviate DB
        query: Query string to search for
        limit: Maximum number of results to return
        alpha: float, the strength of semantics in the hybrid search
        do_rag: bool, whether to make generative output
        max_id: int, optionally specify a maximum comic ID

    Returns:
        List of dictionaries containing found comics
    """
    try:
        logger.info(f"Searching for comics with query: '{query}'")

        # Get the collection
        collection = client.client.collections.get("XKCDComic")

        # Build the query
        query_kwargs = {
            "query": query,
            "alpha": alpha,
            "limit": limit,
            "return_properties": ["comic_id", "title", "image_url", "explanation", "transcript"],
        }

        # Add generative search if requested
        if do_rag:
            single_prompt = ("Explain this XKCD comic in exactly than two sentences: {title}."
                             f"Then explain in one more sentence how it relates to: {query}."
                             "Make it funny / light-hearted."
                             "Here is a long description to use as context: {explanation}."
                             )
            query_kwargs["return_metadata"] = wq.MetadataQuery(score=True)
            query_kwargs["generative"] = wq.Generative(single_prompt=single_prompt)

        # Add where filter if max_id is specified
        if max_id:
            query_kwargs["where"] = wq.Filter.by_property("comic_id").less_than(max_id)

        # Execute the hybrid search
        response = collection.query.hybrid(**query_kwargs)

        # Convert results to the expected format
        comics = []
        for obj in response.objects:
            comic = obj.properties.copy()

            # Add generative response if available
            if do_rag and obj.generated:
                comic['_additional'] = {
                    'generate': {
                        'singleResult': obj.generated,
                        'error': None
                    }
                }

            comics.append(comic)

        logger.info(f"Found {len(comics)} comics matching query")
        return comics

    except Exception as e:
        logger.error(f"Error searching comics: {str(e)}")
        return []

def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='XKCD Search With Weaviate')
    parser.add_argument('--query', type=str, required=True, help='Search for comics with the given query')
    parser.add_argument('--do-rag', action="store_true", help='Whether or not to add a generative summary of the comic.')
    parser.add_argument('--limit', type=int, default=3, help='Limit number of search results (default: 3)')
    parser.add_argument('--alpha', type=float, default=0.5, help='alpha value to determine weight of semantics in hybrid search (note: 1 => fully semantic)')
    parser.add_argument('--weaviate-host', type=str, default='localhost', help='Host of Weaviate instance (default: localhost)')
    parser.add_argument('--weaviate-port', type=int, default=8080, help='Port of Weaviate instance (default: 8080)')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout for requests in seconds (default: 30)')
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        return

    client = None
    try:
        client = XKCDWeaviateClient(
            weaviate_host=args.weaviate_host,
            weaviate_port=args.weaviate_port,
            timeout=args.timeout
        )

        print(f"Searching for comics with query: '{args.query}'")
        results = search_comics(client=client, query=args.query, limit=args.limit, alpha=args.alpha, do_rag=args.do_rag)

        if results:
            print(f"Found {len(results)} results:")
            for i, comic in enumerate(results, 1):
                print(f"\n{i}. Comic #{comic.get('comic_id', 'Unknown')}: {comic.get('title', 'Unknown Title')}")
                explanation = None
                if args.do_rag:
                    generate_response = comic['_additional']['generate']
                    explanation = generate_response.get('singleResult', comic.get('explanation'))
                    if generate_response.get('error'):  # can be None itself
                        logger.error(generate_response['error'])
                elif comic.get('explanation'):
                    explanation = comic['explanation'][:200] + "..." if len(comic['explanation']) > 200 else comic['explanation']
                print(f"   Explanation: {explanation}")
        else:
            print("No results found.")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"❌ Error: {str(e)}")
    finally:
        if client:
            client.close()


if __name__ == '__main__':
    main()