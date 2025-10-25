#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test to see if BeautifulSoup is finding the CSS links
"""

import requests
from bs4 import BeautifulSoup

url = "https://ox-fleetcare.com/"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

response = requests.get(url, headers=headers, timeout=15)
soup = BeautifulSoup(response.text, 'html.parser')

print("Testing link finding with different methods:\n")

# Method 1: find_all('link', rel='stylesheet')
links1 = soup.find_all('link', rel='stylesheet')
print(f"Method 1 - rel='stylesheet': {len(links1)} links")

# Method 2: find_all('link') then check rel
links2 = soup.find_all('link')
stylesheet_links = [l for l in links2 if l.get('rel') and 'stylesheet' in l.get('rel')]
print(f"Method 2 - manual check: {len(stylesheet_links)} links")

# Show first 3 link tags
print(f"\nFirst 3 <link> tags found:")
for i, link in enumerate(links2[:3], 1):
    print(f"{i}. rel={link.get('rel')}, href={link.get('href', 'NO HREF')[:60]}")

# Test with first stylesheet link
if stylesheet_links:
    print(f"\nFirst stylesheet link:")
    print(f"  rel attribute: {stylesheet_links[0].get('rel')}")
    print(f"  rel type: {type(stylesheet_links[0].get('rel'))}")
    print(f"  href: {stylesheet_links[0].get('href')}")
