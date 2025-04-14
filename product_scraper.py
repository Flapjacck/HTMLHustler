#!/usr/bin/env python
"""
Product Catalog Scraper
A specialized web scraper that extracts product information from an e-commerce site
and converts it to structured JSON.
"""
import json
import argparse
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from ratelimit import limits, sleep_and_retry

class ProductScraper:
    def __init__(self):
        """Initialize the product scraper"""
        self.ua = UserAgent()
        self.session = requests.Session()
        
    def _get_headers(self):
        """Generate random user agent headers to avoid detection"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    
    @sleep_and_retry
    @limits(calls=3, period=10)  # 3 requests per 10 seconds - be polite
    def fetch_page(self, url):
        """Fetch a webpage with rate limiting"""
        try:
            response = self.session.get(
                url,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def scrape_products(self, url, product_selector, max_pages=1):
        """
        Scrape product listings from the given URL
        
        Args:
            url: Starting URL for product catalog
            product_selector: CSS selector to find product elements
            max_pages: Maximum number of pages to scrape (pagination)
            
        Returns:
            List of product data dictionaries
        """
        all_products = []
        current_url = url
        
        for page in range(1, max_pages + 1):
            print(f"Scraping page {page} of {max_pages}: {current_url}")
            
            response = self.fetch_page(current_url)
            if not response or response.status_code != 200:
                break
                
            soup = BeautifulSoup(response.text, 'html5lib')
            
            # Extract products on current page
            products_on_page = self._extract_products(soup, product_selector)
            all_products.extend(products_on_page)
            
            # Find next page link - adjust selector based on target site
            next_page = soup.select_one('a.next-page')
            if not next_page or not next_page.get('href'):
                break
                
            # Update URL for next page
            current_url = urljoin(url, next_page['href'])
            
        return all_products
    
    def _extract_products(self, soup, product_selector):
        """Extract product information from the page"""
        products = []
        
        # Find all product elements using the provided selector
        for product_elem in soup.select(product_selector):
            # Customize these selectors based on the website structure
            name_elem = product_elem.select_one('.product-name, h3, .title')
            price_elem = product_elem.select_one('.price, .product-price')
            image_elem = product_elem.select_one('img')
            link_elem = product_elem.select_one('a')
            
            if name_elem:
                product = {
                    'name': name_elem.text.strip(),
                    'price': price_elem.text.strip() if price_elem else 'N/A',
                    'image': image_elem['src'] if image_elem and 'src' in image_elem.attrs else '',
                    'link': link_elem['href'] if link_elem and 'href' in link_elem.attrs else '',
                    # Add more fields as needed
                }
                products.append(product)
                
        return products
    
    def save_to_json(self, data, output_file):
        """Save the scraped data to a JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'products': data,
                'count': len(data)
            }, f, indent=2)
            
        print(f"Saved {len(data)} products to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Scrape product information from a website')
    parser.add_argument('url', help='URL of the product catalog to scrape')
    parser.add_argument('--selector', default='.product, .product-item, .item', 
                      help='CSS selector for product elements')
    parser.add_argument('--output', default='products.json',
                      help='Output JSON file')
    parser.add_argument('--pages', type=int, default=1,
                      help='Maximum number of pages to scrape')
    args = parser.parse_args()
    
    scraper = ProductScraper()
    products = scraper.scrape_products(args.url, args.selector, args.pages)
    scraper.save_to_json(products, args.output)

if __name__ == "__main__":
    main()