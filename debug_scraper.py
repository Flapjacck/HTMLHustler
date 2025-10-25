#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug script to investigate the ox-fleetcare.com website structure
"""

import requests
from bs4 import BeautifulSoup

url = "https://ox-fleetcare.com/"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

print(f"🔍 Investigating: {url}\n")

try:
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    
    print(f"✓ Successfully connected (Status: {response.status_code})")
    print(f"✓ Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
    print(f"✓ Content-Length: {len(response.text)} bytes\n")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Check for CSS files
    css_links = soup.find_all('link', rel='stylesheet')
    print(f"📄 Found {len(css_links)} CSS files:")
    for i, link in enumerate(css_links[:10], 1):
        href = link.get('href', 'No href')
        print(f"  {i}. {href}")
    if len(css_links) > 10:
        print(f"  ... and {len(css_links) - 10} more")
    
    # Check for style tags
    style_tags = soup.find_all('style')
    print(f"\n📄 Found {len(style_tags)} inline <style> tags")
    
    # Check for images
    images = soup.find_all('img')
    print(f"\n🖼️  Found {len(images)} <img> tags:")
    for i, img in enumerate(images[:10], 1):
        src = img.get('src') or img.get('data-src', 'No src')
        print(f"  {i}. {src}")
    if len(images) > 10:
        print(f"  ... and {len(images) - 10} more")
    
    # Check for JavaScript files
    scripts = soup.find_all('script', src=True)
    print(f"\n📜 Found {len(scripts)} external JavaScript files:")
    for i, script in enumerate(scripts[:10], 1):
        src = script.get('src', 'No src')
        print(f"  {i}. {src}")
    if len(scripts) > 10:
        print(f"  ... and {len(scripts) - 10} more")
    
    # Check for internal links
    links = soup.find_all('a', href=True)
    print(f"\n🔗 Found {len(links)} <a> tags with href")
    
    # Check if page uses frameworks
    html_text = response.text.lower()
    frameworks = []
    if 'react' in html_text:
        frameworks.append('React')
    if 'vue' in html_text:
        frameworks.append('Vue')
    if 'angular' in html_text:
        frameworks.append('Angular')
    if 'next' in html_text or '_next' in html_text:
        frameworks.append('Next.js')
    if 'gatsby' in html_text:
        frameworks.append('Gatsby')
    
    if frameworks:
        print(f"\n⚠️  Possible frameworks detected: {', '.join(frameworks)}")
        print("   (This site may load content dynamically with JavaScript)")
    
    # Save first 2000 chars of HTML for inspection
    print(f"\n📝 First 2000 characters of HTML:")
    print("=" * 60)
    print(response.text[:2000])
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Error: {e}")
