#!/usr/bin/env python3
"""Test script to verify content scraping works"""

import sys
import logging
from main import ContentScraper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_scraper():
    """Test the content scraper"""
    logger.info("Testing content scraper...")

    try:
        scraper = ContentScraper()

        # Test Hacker News scraping
        logger.info("\n=== Testing Hacker News ===")
        hn_articles = scraper.fetch_hackernews_top_stories(limit=5)
        logger.info(f"✓ Fetched {len(hn_articles)} Hacker News articles")
        if hn_articles:
            logger.info(f"  Sample: {hn_articles[0]['title'][:60]}...")

        # Test RSS feed scraping
        logger.info("\n=== Testing RSS Feeds ===")
        rss_articles = scraper.fetch_rss_content(days_back=30)
        logger.info(f"✓ Fetched {len(rss_articles)} RSS articles")
        if rss_articles:
            logger.info(f"  Sample: {rss_articles[0]['title'][:60]}...")

        # Get all content
        logger.info("\n=== Getting All Content ===")
        all_articles = scraper.get_all_content()
        logger.info(f"✓ Total articles collected: {len(all_articles)}")

        if len(all_articles) > 0:
            logger.info("\n✅ Content scraper test PASSED!")
            logger.info(f"\nSample articles:")
            for i, article in enumerate(all_articles[:3], 1):
                logger.info(f"\n{i}. {article['title']}")
                logger.info(f"   Source: {article['source']}")
                logger.info(f"   Link: {article['link'][:50]}...")
            return True
        else:
            logger.error("\n❌ No articles were collected")
            return False

    except Exception as e:
        logger.error(f"\n❌ Content scraper test FAILED: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_scraper()
    sys.exit(0 if success else 1)
