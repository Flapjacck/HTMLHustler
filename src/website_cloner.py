#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Website Cloner Scraper
Extracts HTML, CSS, JavaScript, images, and other assets from a website
to enable creating a clone of the site.
"""

import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from pathlib import Path
import json
import time
from typing import Set, Dict, List


class WebsiteCloner:
    """A class to scrape and clone website content including HTML, CSS, images, and scripts."""
    
    def __init__(self, base_url: str, output_dir: str = "output"):
        """
        Initialize the website cloner.
        
        Args:
            base_url (str): The base URL of the website to clone
            output_dir (str): Directory to save all scraped content
        """
        self.base_url = base_url.rstrip('/')
        self.domain = urlparse(base_url).netloc
        self.output_dir = output_dir
        
        # Headers to mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Track downloaded resources
        self.downloaded_images: Set[str] = set()
        self.downloaded_css: Set[str] = set()
        self.downloaded_js: Set[str] = set()
        self.visited_pages: Set[str] = set()
        
        # CSS data storage
        self.all_css_rules: Dict[str, List[str]] = {}
        self.inline_styles: List[str] = []
        
        # Create output directories
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary output directories."""
        directories = [
            self.output_dir,
            os.path.join(self.output_dir, 'images'),
            os.path.join(self.output_dir, 'css'),
            os.path.join(self.output_dir, 'js'),
            os.path.join(self.output_dir, 'html'),
            os.path.join(self.output_dir, 'fonts'),
            os.path.join(self.output_dir, 'assets')
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _is_same_domain(self, url: str) -> bool:
        """Check if URL belongs to the same domain."""
        parsed = urlparse(url)
        # Allow same domain or relative URLs (empty netloc)
        return parsed.netloc == self.domain or parsed.netloc == '' or parsed.netloc == f'www.{self.domain}' or parsed.netloc == self.domain.replace('www.', '')
    
    def _normalize_url(self, url: str, base: str = None) -> str:
        """
        Normalize and make URL absolute.
        
        Args:
            url (str): URL to normalize
            base (str): Base URL for relative URLs
            
        Returns:
            str: Normalized absolute URL
        """
        if not url or url.startswith('data:') or url.startswith('javascript:'):
            return ''
        
        base = base or self.base_url
        absolute_url = urljoin(base, url)
        
        # Remove fragment identifiers
        parsed = urlparse(absolute_url)
        return urlunparse(parsed._replace(fragment=''))
    
    def _get_filename_from_url(self, url: str, prefix: str = '') -> str:
        """Generate a safe filename from URL."""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if not path or path.endswith('/'):
            path = 'index.html'
        
        # Replace slashes and special characters
        filename = path.replace('/', '_').replace('\\', '_')
        
        # Remove query parameters from filename but keep extension
        if '?' in filename:
            filename = filename.split('?')[0]
        
        # Ensure we have an extension
        if '.' not in filename:
            filename += '.html'
        
        return prefix + filename
    
    def download_image(self, img_url: str) -> str:
        """
        Download an image and save it locally.
        
        Args:
            img_url (str): URL of the image
            
        Returns:
            str: Local path to the saved image
        """
        if img_url in self.downloaded_images:
            return self._get_filename_from_url(img_url, 'img_')
        
        try:
            response = requests.get(img_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            filename = self._get_filename_from_url(img_url, 'img_')
            filepath = os.path.join(self.output_dir, 'images', filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            self.downloaded_images.add(img_url)
            print(f"  ✓ Downloaded image: {filename}")
            
            return filename
            
        except Exception as e:
            print(f"  ✗ Error downloading image {img_url}: {e}")
            return ''
    
    def download_css(self, css_url: str) -> str:
        """
        Download a CSS file and save it locally.
        
        Args:
            css_url (str): URL of the CSS file
            
        Returns:
            str: Local path to the saved CSS file
        """
        if css_url in self.downloaded_css:
            return self._get_filename_from_url(css_url, 'style_')
        
        try:
            print(f"  📥 Downloading CSS: {css_url[:80]}...")
            response = requests.get(css_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            filename = self._get_filename_from_url(css_url, 'style_')
            filepath = os.path.join(self.output_dir, 'css', filename)
            
            css_content = response.text
            
            # Download images referenced in CSS
            css_content = self._process_css_urls(css_content, css_url)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(css_content)
            
            # Store CSS rules for analysis
            self.all_css_rules[css_url] = [css_content]
            
            self.downloaded_css.add(css_url)
            print(f"  ✓ Downloaded CSS: {filename}")
            
            return filename
            
        except Exception as e:
            print(f"  ✗ Error downloading CSS {css_url[:80]}: {e}")
            return ''
    
    def _process_css_urls(self, css_content: str, css_url: str) -> str:
        """
        Process URLs in CSS content (images, fonts, etc.) and download them.
        
        Args:
            css_content (str): CSS content
            css_url (str): URL of the CSS file for resolving relative URLs
            
        Returns:
            str: Updated CSS content with local paths
        """
        # Find all url() references in CSS
        url_pattern = r'url\(["\']?([^"\'()]+)["\']?\)'
        
        def replace_url(match):
            url = match.group(1)
            
            # Skip data URLs and already processed URLs
            if url.startswith('data:') or url.startswith('../images/'):
                return match.group(0)
            
            # Make URL absolute
            absolute_url = self._normalize_url(url, css_url)
            
            if not absolute_url:
                return match.group(0)
            
            # Download the resource
            if any(ext in absolute_url.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico']):
                local_filename = self.download_image(absolute_url)
                if local_filename:
                    return f'url(../images/{local_filename})'
            elif any(ext in absolute_url.lower() for ext in ['.woff', '.woff2', '.ttf', '.eot', '.otf']):
                local_filename = self._download_font(absolute_url)
                if local_filename:
                    return f'url(../fonts/{local_filename})'
            
            return match.group(0)
        
        return re.sub(url_pattern, replace_url, css_content)
    
    def _download_font(self, font_url: str) -> str:
        """Download a font file."""
        try:
            response = requests.get(font_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            filename = self._get_filename_from_url(font_url, 'font_')
            filepath = os.path.join(self.output_dir, 'fonts', filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"  ✓ Downloaded font: {filename}")
            return filename
            
        except Exception as e:
            print(f"  ✗ Error downloading font {font_url}: {e}")
            return ''
    
    def download_js(self, js_url: str) -> str:
        """
        Download a JavaScript file and save it locally.
        
        Args:
            js_url (str): URL of the JS file
            
        Returns:
            str: Local path to the saved JS file
        """
        if js_url in self.downloaded_js:
            return self._get_filename_from_url(js_url, 'script_')
        
        try:
            print(f"  📥 Downloading JS: {js_url[:80]}...")
            response = requests.get(js_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            filename = self._get_filename_from_url(js_url, 'script_')
            filepath = os.path.join(self.output_dir, 'js', filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            self.downloaded_js.add(js_url)
            print(f"  ✓ Downloaded JS: {filename}")
            
            return filename
            
        except Exception as e:
            print(f"  ✗ Error downloading JS {js_url[:80]}: {e}")
            return ''
    
    def extract_inline_css(self, soup: BeautifulSoup):
        """Extract all inline CSS from style tags."""
        style_tags = soup.find_all('style')
        
        for style in style_tags:
            if style.string:
                self.inline_styles.append(style.string)
    
    def scrape_page(self, url: str, save_html: bool = True) -> BeautifulSoup:
        """
        Scrape a single page and download all its resources.
        
        Args:
            url (str): URL of the page to scrape
            save_html (bool): Whether to save the HTML file
            
        Returns:
            BeautifulSoup: Parsed HTML content
        """
        if url in self.visited_pages:
            return None
        
        print(f"\n🌐 Scraping page: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            # Debug: Check if content is properly decoded
            print(f"  📊 Response size: {len(response.content)} bytes, Text size: {len(response.text)} chars")
            
            # The response should automatically decompress, but let's ensure it
            # response.text will handle the decompression automatically
            soup = BeautifulSoup(response.content, 'html.parser')
            self.visited_pages.add(url)
            
            # Extract inline CSS
            self.extract_inline_css(soup)
            
            # Download all CSS files
            css_links = soup.find_all('link', rel='stylesheet')
            print(f"  📋 Found {len(css_links)} CSS files to download")
            for link in css_links:
                css_url = link.get('href')
                if css_url:
                    css_url = self._normalize_url(css_url, url)
                    if css_url:  # Download CSS from any domain
                        local_css = self.download_css(css_url)
                        if local_css:
                            link['href'] = f'../css/{local_css}'
            
            # Download all images
            images = soup.find_all('img')
            print(f"  📋 Found {len(images)} images to download")
            for img in images:
                img_url = img.get('src') or img.get('data-src')
                if img_url:
                    img_url = self._normalize_url(img_url, url)
                    if img_url and not img_url.startswith('data:'):
                        local_img = self.download_image(img_url)
                        if local_img:
                            img['src'] = f'../images/{local_img}'
            
            # Download background images from inline styles
            for elem in soup.find_all(style=True):
                style = elem.get('style', '')
                if 'background-image' in style or 'background:' in style:
                    elem['style'] = self._process_css_urls(style, url)
            
            # Download all JavaScript files
            scripts = soup.find_all('script', src=True)
            print(f"  📋 Found {len(scripts)} JS files to download")
            for script in scripts:
                js_url = script.get('src')
                if js_url:
                    js_url = self._normalize_url(js_url, url)
                    if js_url:  # Download JS from any domain
                        local_js = self.download_js(js_url)
                        if local_js:
                            script['src'] = f'../js/{local_js}'
            
            # Download favicon
            for link in soup.find_all('link', rel=lambda x: x and 'icon' in x.lower()):
                icon_url = link.get('href')
                if icon_url:
                    icon_url = self._normalize_url(icon_url, url)
                    if icon_url:
                        local_icon = self.download_image(icon_url)
                        if local_icon:
                            link['href'] = f'../images/{local_icon}'
            
            # Save HTML file
            if save_html:
                filename = self._get_filename_from_url(url, 'page_')
                filepath = os.path.join(self.output_dir, 'html', filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(soup.prettify())
                
                print(f"  ✓ Saved HTML: {filename}")
            
            return soup
            
        except Exception as e:
            print(f"  ✗ Error scraping page {url}: {e}")
            return None
    
    def find_internal_links(self, soup: BeautifulSoup, base_url: str) -> Set[str]:
        """
        Find all internal links on a page.
        
        Args:
            soup (BeautifulSoup): Parsed HTML content
            base_url (str): Base URL of the current page
            
        Returns:
            Set[str]: Set of internal URLs
        """
        internal_links = set()
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            absolute_url = self._normalize_url(href, base_url)
            
            if absolute_url and self._is_same_domain(absolute_url):
                # Filter out non-HTML pages
                if not any(ext in absolute_url.lower() for ext in ['.pdf', '.zip', '.doc', '.xls']):
                    internal_links.add(absolute_url)
        
        return internal_links
    
    def scrape_full_site(self, max_pages: int = 50, delay: float = 1.0):
        """
        Scrape the entire website by following internal links.
        
        Args:
            max_pages (int): Maximum number of pages to scrape
            delay (float): Delay between requests in seconds
        """
        print(f"🚀 Starting full website scrape: {self.base_url}")
        print(f"   Max pages: {max_pages}, Delay: {delay}s\n")
        
        pages_to_visit = {self.base_url}
        
        while pages_to_visit and len(self.visited_pages) < max_pages:
            url = pages_to_visit.pop()
            
            if url in self.visited_pages:
                continue
            
            soup = self.scrape_page(url)
            
            if soup:
                # Find new internal links
                new_links = self.find_internal_links(soup, url)
                pages_to_visit.update(new_links - self.visited_pages)
            
            # Be respectful to the server
            time.sleep(delay)
        
        # Save summary
        self._save_summary()
        
        print(f"\n✅ Scraping complete!")
        print(f"   Pages scraped: {len(self.visited_pages)}")
        print(f"   Images downloaded: {len(self.downloaded_images)}")
        print(f"   CSS files downloaded: {len(self.downloaded_css)}")
        print(f"   JS files downloaded: {len(self.downloaded_js)}")
    
    def _save_summary(self):
        """Save a summary of the scraping session."""
        summary = {
            'base_url': self.base_url,
            'pages_scraped': len(self.visited_pages),
            'visited_pages': list(self.visited_pages),
            'images_downloaded': len(self.downloaded_images),
            'image_urls': list(self.downloaded_images),
            'css_files_downloaded': len(self.downloaded_css),
            'css_urls': list(self.downloaded_css),
            'js_files_downloaded': len(self.downloaded_js),
            'js_urls': list(self.downloaded_js),
            'inline_styles_count': len(self.inline_styles)
        }
        
        filepath = os.path.join(self.output_dir, 'scrape_summary.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n  ✓ Summary saved to: scrape_summary.json")
        
        # Save all inline CSS to a single file
        if self.inline_styles:
            css_filepath = os.path.join(self.output_dir, 'css', 'inline_styles.css')
            with open(css_filepath, 'w', encoding='utf-8') as f:
                f.write('\n\n/* ========================================= */\n\n'.join(self.inline_styles))
            print(f"  ✓ Inline styles saved to: css/inline_styles.css")


def main():
    """Main function to run the website cloner."""
    # Target website
    target_url = "https://ox-fleetcare.com/"
    
    # Initialize the cloner
    cloner = WebsiteCloner(target_url, output_dir="output")
    
    # Scrape the full site
    # Adjust max_pages and delay as needed
    cloner.scrape_full_site(max_pages=50, delay=1.5)


if __name__ == "__main__":
    main()
