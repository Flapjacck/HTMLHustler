#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Main script to run the WLU academic calendar scraper.
"""

import time
from scraper import WLUScraper
from data_handler import DataHandler


def main():
    """Main function to run the scraper."""
    # URL for the main program page
    main_url = "https://academic-calendar.wlu.ca/program.php?cal=1&d=3114&p=7090&s=1152&y=92"
    
    # Initialize the scraper
    scraper = WLUScraper()
    
    # Initialize data handler
    data_handler = DataHandler()
    
    print("Starting to scrape WLU academic calendar...")
    
    # Get all course links from the main page
    course_links = scraper.get_course_links(main_url)
    print(f"Found {len(course_links)} course links")
    
    # Extract data from each course page
    all_courses = []
    for i, link in enumerate(course_links):
        print(f"Scraping course {i+1}/{len(course_links)}: {link}")
        course_data = scraper.get_course_details(link)
        if course_data:
            all_courses.append(course_data)
            # Be nice to the server with a small delay
            time.sleep(1)
    
    # Save the data
    if all_courses:
        data_handler.save_data(all_courses)
        print(f"Successfully scraped {len(all_courses)} courses")
    else:
        print("No courses were found or scraped")


if __name__ == "__main__":
    main()