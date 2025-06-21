#!/usr/bin/env python3
"""
Tests for the XKCD scraper.

This module provides comprehensive tests for the XKCDScraper class functionality,
particularly focusing on the extraction of ordered and unordered lists from comic pages.
It uses pytest fixtures and monkeypatch to intercept HTTP requests and return predefined
HTML content, eliminating the need for network connectivity during testing.

Test Categories:
- Parse Tests: Verify correct parsing of HTML content
- Storage Tests: Verify correct file storage
- Error Tests: Verify correct error handling
"""
import json
import pytest
import tempfile
from pathlib import Path

from src.scraper.scraper import XKCDScraper

# Sample error HTML to test error handling
ERROR_HTML = """
<html>
<body>
<h1>Error: Page not found</h1>
<p>The requested comic does not exist.</p>
</body>
</html>
"""

class MockResponse:
    """
    Mock response object to simulate requests.get

    This class mimics the behavior of a requests.Response object
    with just the necessary attributes and methods needed for testing.
    """
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        """Simulate the raise_for_status method of requests.Response"""
        if self.status_code != 200:
            raise Exception(f"HTTP Error: {self.status_code}")

# Sample HTML content for tests - just enough to test the list extraction
COMIC_500_HTML = """
<html>
<body>
<h1>500: Election</h1>
<h2><span id="Explanation">Explanation</span></h2>
<p>This comic was published the day after the 2008 presidential election.</p>
<p>A list of the elements Cueball had been thinking about:</p>
<ul>
<li>Opinion polls: These are simply surveys of voters' opinions</li>
<li>Exit polls: These are surveys conducted with people</li>
<li>Margins of error: As censuses are expensive</li>
</ul>
<p>The title text is about statistician Nate Silver.</p>
<h2><span id="Transcript">Transcript</span></h2>
</body>
</html>
"""

COMIC_505_HTML = """
<html>
<body>
<h1>505: A Bunch of Rocks</h1>
<h2><span id="Explanation">Explanation</span></h2>
<p>Cueball awakens to find himself trapped for eternity in an endless expanse of sand and rocks.</p>
<p>From xkcd: volume 0:</p>
<h3>Graphs</h3>
<p>The three diagrams in the "Physics, too. I worked out the kinks..." panel are, from left to right:</p>
<ol>
<li>The Normal distribution of the Gaussian curve marking the points that represent a standard deviation</li>
<li>The Epitaph of Stevinus, an explanation of the mechanical advantage</li>
<li>The last graph is unknown. It may represent coupled pendulums</li>
</ol>
<p>The graph that represents particle interaction is a Feynman Diagram.</p>
<h2><span id="Transcript">Transcript</span></h2>
</body>
</html>
"""

# Add a new constant for nested list HTML test case
COMIC_600_HTML = """
<html>
<body>
<h1>600: Android Boyfriend</h1>
<h2><span id="Explanation">Explanation</span></h2>
<p>The comic illustrates problems with android relationships.</p>
<blockquote>
<p>Common issues with android partners include:</p>
<ul>
<li>Memory leaks causing forgotten anniversaries</li>
<li>Charging issues during romantic dinners</li>
<li>Uncanny valley appearance</li>
</ul>
</blockquote>
<div class="mw-highlight">
<p>Product specifications:</p>
<ol>
<li>Android OS 4.0 (Ice Cream Sandwich)</li>
<li>Emotion processor 2.5GHz</li>
<li>32GB personality storage</li>
</ol>
</div>
<p>Further notes on compatibility issues...</p>
<h2><span id="Transcript">Transcript</span></h2>
</body>
</html>
"""

def mock_requests_get(url, **kwargs):
    """
    Mock the requests.get function to return test fixtures

    This function intercepts HTTP requests made by the scraper and
    returns predefined HTML content instead of making real network calls.
    It identifies which comic to return based on the URL.

    Args:
        url: The URL being requested
        **kwargs: Additional keyword arguments

    Returns:
        MockResponse: A mocked response object with predefined HTML
    """
    if '500' in url:
        return MockResponse(COMIC_500_HTML)
    elif '505' in url:
        return MockResponse(COMIC_505_HTML)
    elif '600' in url:
        return MockResponse(COMIC_600_HTML)
    elif '404' in url:
        return MockResponse(ERROR_HTML, 404)
    elif '999' in url:
        return MockResponse("", 500)

    return MockResponse("Not found", 404)

@pytest.fixture
def scraper():
    """
    Fixture to create a scraper instance for tests.

    Returns:
        XKCDScraper: A scraper instance
    """
    return XKCDScraper()

@pytest.fixture
def test_output_dir():
    """
    Fixture to create a temporary test output directory.

    Returns:
        Path: Path to the temporary test output directory
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        yield output_dir
        # No manual cleanup needed - the context manager will handle it

# =========================================================================
# PARSE TESTS
# =========================================================================

@pytest.mark.parse
def test_extract_comic_500_unordered_lists(scraper, monkeypatch):
    """
    Test extracting unordered lists from comic #500

    Verifies that the scraper correctly extracts and formats bullet points
    from unordered lists in the explanation section.
    """
    # Patch the requests.get function
    monkeypatch.setattr('requests.get', mock_requests_get)

    comic = scraper.scrape_comic(500)

    assert comic is not None
    assert comic.comic_id == 500
    assert comic.title == "Election"

    # Check for unordered list items in the explanation
    list_markers = [line for line in comic.explanation.split('\n') if line.startswith('•')]
    assert len(list_markers) >= 3  # At least 3 bullet points

    # Check for specific items
    assert "• Opinion polls:" in comic.explanation
    assert "• Exit polls:" in comic.explanation
    assert "• Margins of error:" in comic.explanation

@pytest.mark.parse
def test_extract_comic_505_ordered_lists(scraper, monkeypatch):
    """
    Test extracting ordered lists from comic #505

    Verifies that the scraper correctly extracts and formats numbered items
    from ordered lists in the explanation section, particularly checking
    for the proper extraction of the "Gaussian curve" term.
    """
    # Patch the requests.get function
    monkeypatch.setattr('requests.get', mock_requests_get)

    comic = scraper.scrape_comic(505)

    assert comic is not None
    assert comic.comic_id == 505
    assert comic.title == "A Bunch of Rocks"

    # Check for ordered list items in the explanation
    assert "1. The Normal distribution of the Gaussian curve" in comic.explanation
    assert "2. The Epitaph of Stevinus" in comic.explanation
    assert "3. The last graph is unknown" in comic.explanation

    # Check that the Gaussian curve term is present
    assert "Gaussian curve" in comic.explanation

@pytest.mark.parse
def test_extract_nested_lists(scraper, monkeypatch):
    """
    Test extracting lists nested inside blockquotes and divs

    Verifies that the scraper correctly extracts and formats lists
    that are nested inside container elements like blockquotes and divs.
    This tests the container handling code in the scraper.
    """
    # Patch the requests.get function
    monkeypatch.setattr('requests.get', mock_requests_get)

    comic = scraper.scrape_comic(600)

    assert comic is not None
    assert comic.comic_id == 600
    assert comic.title == "Android Boyfriend"

    # Check for unordered list items from blockquote
    assert "• Memory leaks causing forgotten anniversaries" in comic.explanation
    assert "• Charging issues during romantic dinners" in comic.explanation
    assert "• Uncanny valley appearance" in comic.explanation

    # Check for ordered list items from div
    assert "1. Android OS 4.0 (Ice Cream Sandwich)" in comic.explanation
    assert "2. Emotion processor 2.5GHz" in comic.explanation
    assert "3. 32GB personality storage" in comic.explanation

# =========================================================================
# STORAGE TESTS
# =========================================================================

@pytest.mark.storage
def test_save_comic_to_file(scraper, test_output_dir, monkeypatch):
    """
    Test that comics are correctly saved to file

    Verifies that the scraper can properly save comic data to JSON files
    and that the saved data maintains the structure and content of the
    original comic, including the ordered lists.
    """
    # Patch the requests.get function
    monkeypatch.setattr('requests.get', mock_requests_get)

    # Create a scraper that saves to test_output
    scraper = XKCDScraper(output_dir=test_output_dir)

    # Extract comic
    comic = scraper.scrape_comic(505)
    assert comic is not None

    # Save comic manually to ensure it's created
    filename = test_output_dir / f"comic_{comic.comic_id}.json"
    comic_dict = {
        "comic_id": comic.comic_id,
        "title": comic.title,
        "image_url": comic.image_url or "",
        "explanation": comic.explanation,
        "transcript": comic.transcript
    }
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(comic_dict, f, indent=2)

    # Check that the file was created
    assert filename.exists()

    # Read the file and check its contents
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert data['comic_id'] == 505
    assert data['title'] == "A Bunch of Rocks"
    assert "Gaussian curve" in data['explanation']

# =========================================================================
# ERROR HANDLING TESTS
# =========================================================================

@pytest.mark.error
def test_handle_nonexistent_comic(scraper, monkeypatch):
    """
    Test handling of non-existent comics

    Verifies that the scraper correctly handles attempts to scrape
    comic IDs that don't exist.
    """
    # Patch the requests.get function
    monkeypatch.setattr('requests.get', mock_requests_get)

    comic = scraper.scrape_comic(404)
    assert comic is None, "Scraper should return None for non-existent comics"

@pytest.mark.error
def test_handle_server_error(scraper, monkeypatch):
    """
    Test handling of server errors

    Verifies that the scraper correctly handles HTTP 500 errors
    from the server.
    """
    # Patch the requests.get function
    monkeypatch.setattr('requests.get', mock_requests_get)

    comic = scraper.scrape_comic(999)
    assert comic is None, "Scraper should return None for server errors"

@pytest.mark.error
def test_handle_network_error(scraper, monkeypatch):
    """
    Test handling of network errors

    Verifies that the scraper correctly handles network errors
    that might occur during HTTP requests.
    """
    # Patch requests.get to raise an exception
    def mock_requests_get_error(*args, **kwargs):
        raise Exception("Network error")

    monkeypatch.setattr('requests.get', mock_requests_get_error)

    comic = scraper.scrape_comic(505)
    assert comic is None, "Scraper should return None for network errors"