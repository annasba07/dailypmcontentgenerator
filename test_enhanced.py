#!/usr/bin/env python3
"""Test script to verify enhanced features"""

import sys
import logging
from main import ContentScraper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_scraper():
    """Test the enhanced content scraper with new sources"""
    logger.info("Testing enhanced content scraper...")

    try:
        scraper = ContentScraper()

        # Test Hacker News
        logger.info("\n=== Testing Hacker News (with retry logic) ===")
        hn_articles = scraper.fetch_hackernews_top_stories(limit=5)
        logger.info(f"✓ Fetched {len(hn_articles)} Hacker News articles")
        if hn_articles:
            logger.info(f"  Sample: {hn_articles[0]['title'][:60]}...")

        # Test RSS feeds (including Medium, Dev.to)
        logger.info("\n=== Testing Enhanced RSS Feeds ===")
        rss_articles = scraper.fetch_rss_content(days_back=30)
        logger.info(f"✓ Fetched {len(rss_articles)} RSS articles")
        if rss_articles:
            sources = set(a['source'] for a in rss_articles)
            logger.info(f"  Sources: {', '.join(list(sources)[:5])}")

        # Test Reddit
        logger.info("\n=== Testing Reddit Integration ===")
        reddit_articles = scraper.fetch_reddit_posts(limit=5)
        logger.info(f"✓ Fetched {len(reddit_articles)} Reddit posts")
        if reddit_articles:
            logger.info(f"  Sample: {reddit_articles[0]['title'][:60]}...")
            logger.info(f"  Comments: {reddit_articles[0].get('comments', 0)}")

        # Test Product Hunt
        logger.info("\n=== Testing Product Hunt ===")
        ph_articles = scraper.fetch_producthunt_posts()
        logger.info(f"✓ Fetched {len(ph_articles)} Product Hunt posts")
        if ph_articles:
            logger.info(f"  Sample: {ph_articles[0]['title'][:60]}...")

        # Get all content
        logger.info("\n=== Getting All Content ===")
        all_articles = scraper.get_all_content()
        logger.info(f"✓ Total articles collected: {len(all_articles)}")

        # Show source distribution
        if all_articles:
            sources_count = {}
            for article in all_articles:
                source = article['source']
                sources_count[source] = sources_count.get(source, 0) + 1

            logger.info("\n📊 Source Distribution:")
            for source, count in sorted(sources_count.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  {source}: {count} articles")

        if len(all_articles) > 0:
            logger.info("\n✅ Enhanced scraper test PASSED!")
            return True
        else:
            logger.error("\n❌ No articles were collected")
            return False

    except Exception as e:
        logger.error(f"\n❌ Enhanced scraper test FAILED: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_enhanced_scraper()
    sys.exit(0 if success else 1)
