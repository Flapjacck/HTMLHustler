# WLU Academic Calendar Scraper
# Created: September 16, 2025

This project is a web scraper designed to extract course data from Wilfrid Laurier University's academic calendar.

## Features
- Extracts course listings from the main program page
- Scrapes detailed information from individual course pages
- Identifies courses by their course code pattern (e.g., XX123)
- Stores data in a structured format

## Setup
1. Ensure Python 3.7+ is installed
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `.\venv\Scripts\activate` (May require setting execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`)
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

## Usage
Run the main script:
```
python src/main.py
```

## Structure
- `src/main.py` - Main execution script
- `src/scraper.py` - Contains the WLUScraper class with core functionality
- `src/data_handler.py` - Handles storage and formatting of scraped data