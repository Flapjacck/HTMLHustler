#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scraper class for the WLU academic calendar.
"""

import re
import requests
from bs4 import BeautifulSoup


class WLUScraper:
    """A class to scrape the WLU academic calendar."""
    
    def __init__(self):
        """Initialize the scraper with headers for requests."""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Regular expression for course codes (e.g., CP104, MA121)
        self.course_code_pattern = re.compile(r'[A-Z]{2}\d{3}')
    
    def get_course_links(self, url):
        """
        Extract all course links from the main program page.
        
        Args:
            url (str): URL of the main program page
            
        Returns:
            list: List of URLs to individual course pages
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find all links that could be course links
            all_links = soup.find_all('a', href=True)
            
            course_links = []
            base_url = "https://academic-calendar.wlu.ca/"
            
            for link in all_links:
                # Check if the link text matches our course code pattern
                if self.course_code_pattern.match(link.text.strip()):
                    # Construct the full URL
                    course_url = base_url + link['href']
                    course_links.append(course_url)
            
            return course_links
            
        except Exception as e:
            print(f"Error getting course links: {e}")
            return []
    
    def get_course_details(self, url):
        """
        Extract detailed information from an individual course page.
        
        Args:
            url (str): URL of the course page
            
        Returns:
            dict: Course information including code, title, description, etc.
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Initialize course data dictionary
            course_data = {
                'url': url,
                'code': '',
                'title': '',
                'description': '',
                'hours': '',
                'prerequisites': '',
                'exclusions': '',
                'additional_info': []
            }
            
            # Extract the course code and title
            course_title_element = soup.find('h1')
            if course_title_element:
                title_text = course_title_element.text.strip()
                # Parse course code and title
                match = self.course_code_pattern.search(title_text)
                if match:
                    course_data['code'] = match.group(0)
                    # Title is everything after the course code
                    course_data['title'] = title_text[match.end():].strip()
            
            # Extract the course description
            description_element = soup.find('div', class_='cal_description')
            if description_element:
                course_data['description'] = description_element.text.strip()
            
            # Extract hours
            hours_element = soup.find('div', class_='cal_hours')
            if hours_element:
                course_data['hours'] = hours_element.text.strip()
            
            # Extract prerequisites
            prereq_element = soup.find('div', class_='cal_prerequisite')
            if prereq_element:
                course_data['prerequisites'] = prereq_element.text.strip()
            
            # Extract exclusions
            exclusions_element = soup.find('div', class_='cal_exclusion')
            if exclusions_element:
                course_data['exclusions'] = exclusions_element.text.strip()
            
            # Extract any additional information (may vary by course)
            additional_info_elements = soup.find_all('div', class_=lambda c: c and c.startswith('cal_') and c not in [
                'cal_description', 'cal_hours', 'cal_prerequisite', 'cal_exclusion'
            ])
            for element in additional_info_elements:
                course_data['additional_info'].append({
                    'label': element.get('class', [''])[0],
                    'content': element.text.strip()
                })
            
            return course_data
            
        except Exception as e:
            print(f"Error getting course details for {url}: {e}")
            return None