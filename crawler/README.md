# Web Crawler

This is a Python-based web crawler that can continuously scrape websites and update your website's content.

## Features

- Automated web scraping
- Scheduled crawling (runs every hour by default)
- Data storage in JSON format
- Error handling and logging
- User-agent headers to avoid blocking

## Setup

1. Install Python 3.7 or higher
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Open `crawler.py` and modify the `websites` dictionary in the `main()` function to include the URLs you want to crawl:
   ```python
   websites = {
       'https://example.com': 'example_data.json',
       # Add more websites as needed
   }
   ```

2. Customize the `parse_content()` method in the `WebCrawler` class to extract the specific data you need from each website.

## Usage

Run the crawler:
```bash
python crawler.py
```

The crawler will:
1. Create a `data` directory if it doesn't exist
2. Crawl the specified websites
3. Save the scraped data in JSON format
4. Continue running and update the data every hour

## Data Structure

The scraped data is saved in JSON format with the following structure:
```json
{
  "title": "Page Title",
  "links": ["url1", "url2", ...],
  "text_content": "Page content",
  "timestamp": "2024-03-28T10:00:00.000000"
}
```

## Customization

You can modify the following aspects of the crawler:

1. Crawling frequency: Change the schedule in `main()`
2. Data structure: Modify the `parse_content()` method
3. Error handling: Adjust the error handling in `fetch_page()`
4. Storage format: Modify the `save_data()` method

## Notes

- Make sure to respect the websites' robots.txt files and terms of service
- Add appropriate delays between requests if needed
- Consider implementing rate limiting for large-scale crawling 