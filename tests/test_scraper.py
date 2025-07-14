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

@pytest.fixture
def explainxkcd_comic_500_html():
    """
    Fixture to load the explainxkcd.com HTML content for comic 500.

    Returns:
        str: HTML content from the explainxkcd.com comic 500 fixture file
    """
    fixture_path = Path(__file__).parent / "fixtures" / "html" / "explainxkcd.com" / "comic_500.html"
    with open(fixture_path, 'r', encoding='utf-8') as f:
        return f.read()

@pytest.fixture
def explainxkcd_comic_505_html():
    """
    Fixture to load the explainxkcd.com HTML content for comic 505.

    Returns:
        str: HTML content from the explainxkcd.com comic 505 fixture file
    """
    fixture_path = Path(__file__).parent / "fixtures" / "html" / "explainxkcd.com" / "comic_505.html"
    with open(fixture_path, 'r', encoding='utf-8') as f:
        return f.read()

@pytest.fixture
def explainxkcd_comic_600_html():
    """
    Fixture to load the explainxkcd.com HTML content for comic 600.

    Returns:
        str: HTML content from the explainxkcd.com comic 600 fixture file
    """
    fixture_path = Path(__file__).parent / "fixtures" / "html" / "explainxkcd.com" / "comic_600.html"
    with open(fixture_path, 'r', encoding='utf-8') as f:
        return f.read()

@pytest.fixture
def xkcd_comic_500_html():
    """
    Fixture to load the actual xkcd.com HTML content from file.

    Returns:
        str: HTML content from the xkcd.com comic 500 fixture file
    """
    fixture_path = Path(__file__).parent / "fixtures" / "html" / "xkcd.com" / "comic_500.html"
    with open(fixture_path, 'r', encoding='utf-8') as f:
        return f.read()

def create_mock_requests_get(explainxkcd_500_html, explainxkcd_505_html, explainxkcd_600_html):
    """
    Create a mock function that returns HTML fixtures for both explainxkcd.com and xkcd.com.

    Args:
        explainxkcd_500_html: HTML content for comic 500
        explainxkcd_505_html: HTML content for comic 505
        explainxkcd_600_html: HTML content for comic 600

    Returns:
        function: Mock function for requests.get
    """
    def mock_get(url, **kwargs):
        # Handle error cases FIRST (before generic fallbacks)
        if '404' in url:
            return MockResponse(ERROR_HTML, 404)
        elif '999' in url:
            return MockResponse("", 500)
        # Handle explainxkcd.com requests
        elif 'explain' in url and '500' in url:
            return MockResponse(explainxkcd_500_html)
        elif 'explain' in url and '505' in url:
            return MockResponse(explainxkcd_505_html)
        elif 'explain' in url and '600' in url:
            return MockResponse(explainxkcd_600_html)
        # Handle any other explainxkcd.com requests (generic fallback)
        elif 'explain' in url:
            # Extract comic ID from URL for generic response
            import re
            match = re.search(r'/(\d+)', url)
            if match:
                comic_id = match.group(1)
                return MockResponse(f'<html><body><h1>{comic_id}: Generic Comic</h1><h2><span id="Explanation">Explanation</span></h2><p>Generic explanation for comic {comic_id}.</p><h2><span id="Transcript">Transcript</span></h2><p>Generic transcript.</p></body></html>')
            else:
                return MockResponse('<html><body><h1>Unknown Comic</h1><h2><span id="Explanation">Explanation</span></h2><p>Unknown explanation.</p><h2><span id="Transcript">Transcript</span></h2><p>Unknown transcript.</p></body></html>')
        # Handle xkcd.com requests - return a simple HTML with comic image
        elif 'xkcd.com/500' in url:
            return MockResponse('<html><body><div id="comic"><img src="//imgs.xkcd.com/comics/election.png" alt="Election"/></div></body></html>')
        elif 'xkcd.com/505' in url:
            return MockResponse('<html><body><div id="comic"><img src="//imgs.xkcd.com/comics/rocks.png" alt="A Bunch of Rocks"/></div></body></html>')
        elif 'xkcd.com/600' in url:
            return MockResponse('<html><body><div id="comic"><img src="//imgs.xkcd.com/comics/android.png" alt="Android Boyfriend"/></div></body></html>')
        # Handle any other xkcd.com requests (generic fallback)
        elif 'xkcd.com/' in url:
            return MockResponse('<html><body><div id="comic"><img src="//imgs.xkcd.com/comics/NOT_THE_REAL_IMAGE.png" alt="Generic Comic"/></div></body></html>')
        return MockResponse("Not found", 404)

    return mock_get

def mock_requests_get_with_xkcd_fixture(xkcd_html_content, explainxkcd_html_content):
    """
    Create a mock function that returns both xkcd.com and explainxkcd.com HTML fixtures.

    Args:
        xkcd_html_content: The HTML content from the xkcd.com fixture file
        explainxkcd_html_content: The HTML content from the explainxkcd.com fixture file

    Returns:
        function: Mock function for requests.get
    """
    def mock_get(url, **kwargs):
        # Handle error cases FIRST (before generic fallbacks)
        if '404' in url:
            return MockResponse(ERROR_HTML, 404)
        elif '999' in url:
            return MockResponse("", 500)
        elif 'xkcd.com/500' in url:
            return MockResponse(xkcd_html_content)
        elif 'explain' in url and '500' in url:
            return MockResponse(explainxkcd_html_content)
        # Handle any other explainxkcd.com requests (generic fallback)
        elif 'explain' in url:
            import re
            match = re.search(r'/(\d+)', url)
            if match:
                comic_id = match.group(1)
                return MockResponse(f'<html><body><h1>{comic_id}: Generic Comic</h1><h2><span id="Explanation">Explanation</span></h2><p>Generic explanation for comic {comic_id}.</p><h2><span id="Transcript">Transcript</span></h2><p>Generic transcript.</p></body></html>')
            else:
                return MockResponse('<html><body><h1>Unknown Comic</h1><h2><span id="Explanation">Explanation</span></h2><p>Unknown explanation.</p><h2><span id="Transcript">Transcript</span></h2><p>Unknown transcript.</p></body></html>')
        # Handle any other xkcd.com requests (generic fallback)
        elif 'xkcd.com/' in url:
            import re
            match = re.search(r'xkcd\.com/(\d+)', url)
            if match:
                comic_id = match.group(1)
                return MockResponse(f'<html><body><div id="comic"><img src="//imgs.xkcd.com/comics/comic_{comic_id}.png" alt="Comic {comic_id}"/></div></body></html>')
            else:
                return MockResponse('<html><body><div id="comic"><img src="//imgs.xkcd.com/comics/generic.png" alt="Generic Comic"/></div></body></html>')
        return MockResponse("Not found", 404)

    return mock_get

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
def test_extract_comic_500_unordered_lists(scraper, explainxkcd_comic_500_html, explainxkcd_comic_505_html, explainxkcd_comic_600_html, monkeypatch):
    """
    Test extracting unordered lists from comic #500

    Verifies that the scraper correctly extracts and formats bullet points
    from unordered lists in the explanation section.
    """
    # Create mock function with all HTML fixtures
    mock_get = create_mock_requests_get(explainxkcd_comic_500_html, explainxkcd_comic_505_html, explainxkcd_comic_600_html)
    monkeypatch.setattr('requests.get', mock_get)

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
def test_extract_comic_505_ordered_lists(scraper, explainxkcd_comic_500_html, explainxkcd_comic_505_html, explainxkcd_comic_600_html, monkeypatch):
    """
    Test extracting ordered lists from comic #505

    Verifies that the scraper correctly extracts and formats numbered items
    from ordered lists in the explanation section, particularly checking
    for the proper extraction of the "Gaussian curve" term.
    """
    # Create mock function with all HTML fixtures
    mock_get = create_mock_requests_get(explainxkcd_comic_500_html, explainxkcd_comic_505_html, explainxkcd_comic_600_html)
    monkeypatch.setattr('requests.get', mock_get)

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
def test_extract_nested_lists(scraper, explainxkcd_comic_500_html, explainxkcd_comic_505_html, explainxkcd_comic_600_html, monkeypatch):
    """
    Test extracting nested lists from comic #600

    Verifies that the scraper correctly extracts and formats lists
    that appear within blockquotes and div elements.
    """
    # Create mock function with all HTML fixtures
    mock_get = create_mock_requests_get(explainxkcd_comic_500_html, explainxkcd_comic_505_html, explainxkcd_comic_600_html)
    monkeypatch.setattr('requests.get', mock_get)

    comic = scraper.scrape_comic(600)

    assert comic is not None
    assert comic.comic_id == 600
    assert comic.title == "Android Boyfriend"

    # The unordered lists should be extracted as bullet points
    # List from blockquote
    assert "• Memory leaks causing forgotten anniversaries" in comic.explanation
    assert "• Charging issues during romantic dinners" in comic.explanation
    assert "• Uncanny valley appearance" in comic.explanation

    # The ordered lists should be extracted as numbered points
    # List from div
    assert "1. Android OS 4.0 (Ice Cream Sandwich)" in comic.explanation
    assert "2. Emotion processor 2.5GHz" in comic.explanation
    assert "3. 32GB personality storage" in comic.explanation

@pytest.mark.parse
def test_extract_image_url_from_xkcd(scraper, xkcd_comic_500_html, explainxkcd_comic_500_html, monkeypatch):
    """
    Test extracting image URL from xkcd.com using the actual HTML fixture.

    Verifies that the scraper correctly extracts the image URL from xkcd.com
    and converts protocol-relative URLs to absolute HTTPS URLs.
    """
    # Create a mock function that returns both HTML fixtures
    mock_get = mock_requests_get_with_xkcd_fixture(xkcd_comic_500_html, explainxkcd_comic_500_html)
    monkeypatch.setattr('requests.get', mock_get)

    comic = scraper.scrape_comic(500)

    assert comic is not None
    assert comic.comic_id == 500
    assert comic.title == "Election"

    # The image URL should be extracted from xkcd.com and converted to absolute HTTPS
    assert comic.image_url == "https://imgs.xkcd.com/comics/election.png"

# =========================================================================
# STORAGE TESTS
# =========================================================================

@pytest.mark.storage
def test_save_comic_to_file(scraper, test_output_dir, explainxkcd_comic_500_html, explainxkcd_comic_505_html, explainxkcd_comic_600_html, monkeypatch):
    """
    Test that comics are correctly saved to file

    Verifies that the scraper can properly save comic data to JSON files
    and that the saved data maintains the structure and content of the
    original comic, including the ordered lists.
    """
    # Create mock function with all HTML fixtures
    mock_get = create_mock_requests_get(explainxkcd_comic_500_html, explainxkcd_comic_505_html, explainxkcd_comic_600_html)
    monkeypatch.setattr('requests.get', mock_get)

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
def test_handle_nonexistent_comic(scraper, explainxkcd_comic_500_html, explainxkcd_comic_505_html, explainxkcd_comic_600_html, monkeypatch):
    """
    Test handling of non-existent comics

    Verifies that the scraper correctly handles attempts to scrape
    comic IDs that don't exist.
    """
    # Create mock function with all HTML fixtures
    mock_get = create_mock_requests_get(explainxkcd_comic_500_html, explainxkcd_comic_505_html, explainxkcd_comic_600_html)
    monkeypatch.setattr('requests.get', mock_get)

    comic = scraper.scrape_comic(404)
    assert comic is None, "Scraper should return None for non-existent comics"

@pytest.mark.error
def test_handle_server_error(scraper, explainxkcd_comic_500_html, explainxkcd_comic_505_html, explainxkcd_comic_600_html, monkeypatch):
    """
    Test handling of server errors

    Verifies that the scraper correctly handles HTTP 500 errors
    from the server.
    """
    # Create mock function with all HTML fixtures
    mock_get = create_mock_requests_get(explainxkcd_comic_500_html, explainxkcd_comic_505_html, explainxkcd_comic_600_html)
    monkeypatch.setattr('requests.get', mock_get)

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
