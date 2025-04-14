#!/usr/bin/env python
"""
Web Scraper that converts website content to JSON
Using: requests, BeautifulSoup4, html5lib, fake-useragent, ratelimit
"""
import json
import time
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from ratelimit import limits, sleep_and_retry

class WebScraper:
    def __init__(self, base_url=None):
        """Initialize the scraper with optional base URL"""
        self.ua = UserAgent()
        self.base_url = base_url
        self.session = requests.Session()
        
    def _get_headers(self):
        """Generate random user agent headers to avoid detection"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    @sleep_and_retry
    @limits(calls=5, period=10)  # 5 requests per 10 seconds
    def fetch_page(self, url, params=None):
        """
        Fetch a webpage with rate limiting
        Returns the response object
        """
        full_url = url if url.startswith('http') else f"{self.base_url}/{url.lstrip('/')}"
        
        try:
            response = self.session.get(
                full_url,
                headers=self._get_headers(),
                params=params,
                timeout=30
            )
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {full_url}: {e}")
            return None
    
    def parse_to_json(self, response, parser_function=None):
        """
        Parse the response content using the provided parser function
        Returns data in JSON format
        """
        if not response or response.status_code != 200:
            return json.dumps({"error": "Failed to fetch page"})
        
        soup = BeautifulSoup(response.text, 'html5lib')
        
        # Use the provided parser function or fallback to the default parser
        if parser_function:
            data = parser_function(soup)
        else:
            data = self.default_parser(soup, response.url)
            
        return json.dumps(data, indent=2)
    
    def default_parser(self, soup, url):
        """
        Default parser that attempts to extract content from any website
        by targeting common HTML structures
        """
        # Get page title
        title = soup.title.text.strip() if soup.title else "No title found"
        
        # Try to find the main content area
        main_content = soup.find(['main', 'article', 'div[role="main"]', '#content', '.content'])
        
        # Extract all headings
        headings = []
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            text = heading.get_text().strip()
            if text and len(text) > 5:  # Filter out empty or very short headings
                headings.append(text)
        
        # Extract all paragraphs of meaningful length
        paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if text and len(text) > 30:  # Only paragraphs with meaningful content
                paragraphs.append(text)
        
        # Extract all links
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text().strip()
            if href and not href.startswith('#') and not href.startswith('javascript:'):
                # Make relative URLs absolute
                if not href.startswith('http'):
                    if href.startswith('/'):
                        base_url = '/'.join(url.split('/')[:3])  # Extract domain
                        href = base_url + href
                    else:
                        href = url.rstrip('/') + '/' + href
                
                links.append({
                    "text": text if text else "No text",
                    "url": href
                })
        
        # Try to find articles or post items
        articles = []
        
        # Method 1: Look for article tags
        article_elements = soup.find_all('article')
        
        # Method 2: Look for common article containers
        if not article_elements:
            article_elements = soup.select('.post, .article, .news-item, .item, .card')
        
        # Method 3: Look for lists of items with similar structure
        if not article_elements:
            # Find parent elements that contain multiple similar structured children
            for parent in soup.find_all(['div', 'ul', 'section']):
                children = parent.find_all(['div', 'li'], recursive=False)
                if len(children) >= 3:  # At least 3 similar items
                    # Check if these children have similar structure
                    headings_count = sum(1 for c in children if c.find(['h1', 'h2', 'h3', 'h4']))
                    links_count = sum(1 for c in children if c.find('a'))
                    
                    if headings_count >= len(children) * 0.7 or links_count >= len(children) * 0.7:
                        article_elements = children
                        break
        
        # Process found article elements
        for article in article_elements:
            # Try different selectors for title
            title_elem = article.find(['h1', 'h2', 'h3', 'h4', '.title', '.headline', 'a'])
            
            # Try different selectors for summary
            summary_elem = article.find(['p', '.summary', '.excerpt', '.description'])
            
            # Try to find a link
            link_elem = None
            if title_elem and title_elem.name == 'a':
                link_elem = title_elem
            else:
                link_elem = article.find('a')
            
            if title_elem:
                article_data = {
                    'title': title_elem.get_text().strip(),
                    'summary': summary_elem.get_text().strip() if summary_elem else '',
                    'link': link_elem['href'] if link_elem and 'href' in link_elem.attrs else '',
                }
                articles.append(article_data)
        
        # Try to extract metadata
        meta_data = {}
        for meta in soup.find_all('meta'):
            if 'name' in meta.attrs and 'content' in meta.attrs:
                meta_data[meta['name']] = meta['content']
            elif 'property' in meta.attrs and 'content' in meta.attrs:
                meta_data[meta['property']] = meta['content']
        
        return {
            'title': title,
            'url': url,
            'articles': articles,
            'headings': headings,
            'paragraphs': paragraphs[:10],  # Limit to first 10 paragraphs
            'links': links[:20],  # Limit to first 20 links
            'meta': meta_data,
            'total_articles': len(articles),
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def scrape_to_json(self, url, parser_function=None, params=None, output_file=None):
        """
        Scrape a website and convert the results to JSON
        
        Args:
            url: URL to scrape
            parser_function: Function that takes a BeautifulSoup object and returns dictionary data
                            (if None, uses the default parser)
            params: Optional query parameters
            output_file: Optional file path to save the JSON output
            
        Returns:
            JSON string
        """
        print(f"Scraping: {url}")
        response = self.fetch_page(url, params)
        json_data = self.parse_to_json(response, parser_function)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_data)
            print(f"Data saved to {output_file}")
                
        return json_data

# Example usage
if __name__ == "__main__":
    import sys
    
    # Get URL from command line or use default
    url = sys.argv[1] if len(sys.argv) > 1 else "https://news.ycombinator.com/"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "news_data.json"
    
    print(f"Scraping {url} and saving to {output_file}")
    
    # Initialize scraper
    scraper = WebScraper()
    
    # Scrape and convert to JSON using the default parser
    json_data = scraper.scrape_to_json(
        url,
        output_file=output_file
    )
    
    # Print a preview
    parsed_data = json.loads(json_data)
    print(f"\nTitle: {parsed_data['title']}")
    print(f"Total articles found: {parsed_data['total_articles']}")
    print(f"Total headings found: {len(parsed_data['headings'])}")
    print(f"Total paragraphs found: {len(parsed_data['paragraphs'])}")
    
    if parsed_data['articles']:
        print("\nFirst article:")
        print(f"- Title: {parsed_data['articles'][0]['title']}")
        if parsed_data['articles'][0]['summary']:
            print(f"- Summary: {parsed_data['articles'][0]['summary'][:100]}...")
    
    print("\nData saved successfully!")