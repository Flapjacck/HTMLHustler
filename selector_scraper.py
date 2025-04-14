#!/usr/bin/env python
"""
Custom Selector Scraper
A flexible web scraper that allows you to extract data using custom CSS selectors
and convert it to JSON.
"""
import json
import argparse
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from ratelimit import limits, sleep_and_retry

class SelectorScraper:
    def __init__(self):
        """Initialize the scraper"""
        self.ua = UserAgent()
        
    @sleep_and_retry
    @limits(calls=3, period=10)  # 3 requests per 10 seconds
    def fetch_page(self, url):
        """Fetch a webpage with rate limiting"""
        headers = {'User-Agent': self.ua.random}
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_data(self, soup, selectors):
        """
        Extract data using provided CSS selectors
        
        Args:
            soup: BeautifulSoup object
            selectors: Dictionary of {field_name: {selector: str, attribute: str or None}}
                       If attribute is None, gets text content, otherwise gets the specified attribute
        
        Returns:
            Dictionary of extracted data
        """
        result = {}
        
        for field, config in selectors.items():
            selector = config['selector']
            attribute = config.get('attribute')
            is_list = config.get('list', False)
            
            if is_list:
                # Extract a list of items
                elements = soup.select(selector)
                if attribute:
                    # Get attribute from each element
                    result[field] = [elem.get(attribute, '') for elem in elements if elem]
                else:
                    # Get text from each element
                    result[field] = [elem.text.strip() for elem in elements if elem]
            else:
                # Extract a single item
                element = soup.select_one(selector)
                if element:
                    if attribute:
                        # Get attribute
                        result[field] = element.get(attribute, '')
                    else:
                        # Get text
                        result[field] = element.text.strip()
                else:
                    result[field] = None
                    
        return result
    
    def scrape_to_json(self, url, selectors, output_file=None):
        """
        Scrape a website and convert the results to JSON
        
        Args:
            url: URL to scrape
            selectors: Dictionary of CSS selectors configuration
            output_file: Optional file path to save the JSON output
            
        Returns:
            JSON string
        """
        response = self.fetch_page(url)
        
        if not response or response.status_code != 200:
            result = {"error": f"Failed to fetch {url}"}
        else:
            soup = BeautifulSoup(response.text, 'html5lib')
            result = self.extract_data(soup, selectors)
            
        # Convert to JSON
        json_data = json.dumps(result, indent=2)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_data)
                print(f"Data saved to {output_file}")
                
        return json_data

def load_selectors_config(config_file):
    """Load selectors configuration from a JSON file"""
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description='Scrape website data using custom CSS selectors')
    parser.add_argument('url', help='URL of the website to scrape')
    parser.add_argument('--config', required=True, help='Path to JSON selectors configuration file')
    parser.add_argument('--output', help='Output JSON file')
    args = parser.parse_args()
    
    # Load selectors configuration
    selectors = load_selectors_config(args.config)
    
    # Scrape the website
    scraper = SelectorScraper()
    json_data = scraper.scrape_to_json(args.url, selectors, args.output)
    
    # Print result if not saving to file
    if not args.output:
        print(json_data)

if __name__ == "__main__":
    main()