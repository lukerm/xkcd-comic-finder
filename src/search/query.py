#!/usr/bin/env python3
"""
Weaviate client for retrieving XKCD comic data.
"""

import logging
from typing import Dict, List

from ..database.weaviate_client import XKCDWeaviateClient


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def search_comics(
        client: XKCDWeaviateClient,
        query: str,
        limit: int = 5,
        alpha: float = 1,
        do_rag: bool = False,
) -> List[Dict]:
    """
    Search for comics in Weaviate using semantic search.

    Args:
        client: the bespoke XKCD client for connecting to weaviate DB
        query: Query string to search for
        limit: Maximum number of results to return
        alpha: float, the strength of semantics in the hybrid search
        do_rag: bool, whether to make generative output

    Returns:
        List of dictionaries containing found comics
    """
    try:
        logger.info(f"Searching for comics with query: '{query}'")

        query_builder = (
            client.client.query
            .get("XKCDComic", ["comic_id", "title", "image_url", "explanation", "transcript"])
            .with_hybrid(query=query, alpha=alpha)
        )
        if do_rag:
            single_prompt = ("Explain this XKCD comic in exactly than two sentences: {title}."
                             f"Then explain in one more sentence how it relates to: {query}."
                             "Make it funny / light-hearted."
                             "Here is a long description to use as context: {explanation}."
                             )
            query_builder = query_builder.with_generate(single_prompt=single_prompt)

        # Add a hard limit
        query_builder = query_builder.with_limit(limit)
        results = query_builder.do()


        # Extract comics from result
        comics = results.get("data", {}).get("Get", {}).get("XKCDComic", [])
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
    parser.add_argument('--limit', type=int, default=3, help='Limit number of search results (default: 5)')
    parser.add_argument('--alpha', type=float, default=0.5, help='alpha value to determine weight of semantics in hybrid search (note: 1 => fully semantic)')
    parser.add_argument('--weaviate-url', type=str, default='http://localhost:8080', help='URL of Weaviate instance (default: http://localhost:8080)')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout for requests in seconds (default: 30)')
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        return

    try:
        client = XKCDWeaviateClient(
            weaviate_url=args.weaviate_url,
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
        sys.exit(1)


if __name__ == '__main__':
    main()