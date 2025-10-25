#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick runner script for the Website Cloner.
"""

from src.website_cloner import WebsiteCloner


def main():
    """Run the website cloner for ox-fleetcare.com"""
    
    print("=" * 60)
    print("   WEBSITE CLONER - HTMLHustler")
    print("=" * 60)
    
    # Target website
    target_url = "https://ox-fleetcare.com/"
    
    print(f"\n🎯 Target: {target_url}")
    
    # Initialize the cloner
    cloner = WebsiteCloner(target_url, output_dir="output")
    
    # Scrape the full site
    # Parameters you can adjust:
    # - max_pages: Maximum number of pages to scrape (default: 50)
    # - delay: Delay between requests in seconds (default: 1.5)
    #   Higher delay is more polite to the server
    
    cloner.scrape_full_site(max_pages=50, delay=1.5)
    
    print("\n" + "=" * 60)
    print("   All files saved to: ./output/")
    print("=" * 60)
    print("\n📁 Directory structure:")
    print("   output/")
    print("   ├── images/      - All images from the site")
    print("   ├── css/         - All CSS files")
    print("   ├── js/          - All JavaScript files")
    print("   ├── html/        - All HTML pages")
    print("   ├── fonts/       - All font files")
    print("   └── scrape_summary.json - Summary of the scrape")
    print("\n")


if __name__ == "__main__":
    main()
