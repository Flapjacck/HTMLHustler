# WLU Academic Calendar Scraper
# Test script for verifying scraper functionality

import unittest
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scraper import WLUScraper
from src.data_handler import DataHandler


class TestWLUScraper(unittest.TestCase):
    """Test cases for the WLU scraper."""
    
    def setUp(self):
        """Set up test environment."""
        self.scraper = WLUScraper()
        self.main_url = "https://academic-calendar.wlu.ca/program.php?cal=1&d=3114&p=7090&s=1152&y=92"
    
    def test_course_code_pattern(self):
        """Test the course code pattern regex."""
        pattern = self.scraper.course_code_pattern
        
        # Should match
        self.assertTrue(pattern.match("CP104"))
        self.assertTrue(pattern.match("MA121"))
        self.assertTrue(pattern.match("BU111"))
        
        # Should not match
        self.assertFalse(bool(pattern.match("CP10")))  # Too short
        self.assertFalse(bool(pattern.match("CPP104")))  # Too many letters
        self.assertFalse(bool(pattern.match("C1234")))  # Wrong format
    
    def test_get_course_links(self):
        """Test getting course links from the main page."""
        # This is more of an integration test that requires internet connection
        links = self.scraper.get_course_links(self.main_url)
        
        # We should get some links
        self.assertTrue(len(links) > 0)
        
        # Each link should be a valid URL
        for link in links:
            self.assertTrue(link.startswith("https://academic-calendar.wlu.ca/"))
    
    def test_get_course_details(self):
        """Test getting course details from a course page."""
        # This is more of an integration test that requires internet connection
        # First get some course links
        links = self.scraper.get_course_links(self.main_url)
        
        if links:
            # Test the first link
            course_data = self.scraper.get_course_details(links[0])
            
            # Verify we got data back
            self.assertIsNotNone(course_data)
            
            # Check that important fields are present
            self.assertIn('code', course_data)
            self.assertIn('title', course_data)
            self.assertIn('description', course_data)


if __name__ == "__main__":
    unittest.main()