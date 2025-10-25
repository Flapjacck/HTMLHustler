#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Data handler for the WLU academic calendar scraper.
"""

import json
import csv
import os
from datetime import datetime


class DataHandler:
    """A class to handle storage and formatting of scraped data."""
    
    def __init__(self):
        """Initialize the data handler with output directory."""
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def save_data(self, courses):
        """
        Save the scraped course data in multiple formats.
        
        Args:
            courses (list): List of dictionaries containing course data
        """
        # Create a timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON
        self._save_json(courses, timestamp)
        
        # Save as CSV
        self._save_csv(courses, timestamp)
        
        print(f"Data saved to {self.output_dir}")
    
    def _save_json(self, courses, timestamp):
        """Save data as a JSON file."""
        filename = os.path.join(self.output_dir, f'wlu_courses_{timestamp}.json')
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(courses, f, indent=4, ensure_ascii=False)
        
        print(f"JSON data saved to {filename}")
    
    def _save_csv(self, courses, timestamp):
        """Save data as a CSV file."""
        filename = os.path.join(self.output_dir, f'wlu_courses_{timestamp}.csv')
        
        # Determine all possible fields across all courses
        fieldnames = ['code', 'title', 'url', 'description', 'hours', 'prerequisites', 'exclusions']
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            for course in courses:
                # Extract the main fields that match our fieldnames
                row = {field: course.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        print(f"CSV data saved to {filename}")
    
    def _format_additional_info(self, additional_info):
        """Format additional info as a readable string."""
        if not additional_info:
            return ""
        
        formatted_info = []
        for info in additional_info:
            label = info.get('label', '').replace('cal_', '').capitalize()
            content = info.get('content', '')
            formatted_info.append(f"{label}: {content}")
        
        return "\n".join(formatted_info)