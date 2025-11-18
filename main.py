#!/usr/bin/env python3
"""
Weekly Product & Engineering Content Generator
Scrapes latest PM/engineering content and generates high-quality articles using Claude AI
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import atoma
import requests
from anthropic import Anthropic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContentScraper:
    """Scrapes content from various PM and engineering sources"""

    def __init__(self):
        self.sources = {
            'rss_feeds': [
                'https://news.ycombinator.com/rss',
                'https://www.productplan.com/blog/feed/',
                'https://www.mindtheproduct.com/feed/',
                'https://www.svpg.com/feed/',
                'https://www.lennysnewsletter.com/feed',
            ],
            'hacker_news_api': 'https://hacker-news.firebaseio.com/v0',
        }

    def fetch_rss_content(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch content from RSS feeds"""
        articles = []
        cutoff_date = datetime.now() - timedelta(days=days_back)

        for feed_url in self.sources['rss_feeds']:
            try:
                logger.info(f"Fetching RSS feed: {feed_url}")
                response = requests.get(feed_url, timeout=10)
                response.raise_for_status()

                # Parse with atoma (supports both RSS and Atom)
                feed = atoma.parse_rss_bytes(response.content) if b'<rss' in response.content else atoma.parse_atom_bytes(response.content)

                feed_title = feed.title if hasattr(feed, 'title') else feed_url
                items = feed.items if hasattr(feed, 'items') else feed.entries

                for entry in items[:10]:  # Get latest 10 from each feed
                    pub_date = entry.pub_date if hasattr(entry, 'pub_date') else (entry.published if hasattr(entry, 'published') else None)

                    # Only include recent articles
                    if pub_date and pub_date.replace(tzinfo=None) < cutoff_date:
                        continue

                    # Get summary/description
                    summary = ''
                    if hasattr(entry, 'description') and entry.description:
                        summary = entry.description[:500]
                    elif hasattr(entry, 'summary') and entry.summary:
                        summary = entry.summary.value[:500] if hasattr(entry.summary, 'value') else str(entry.summary)[:500]

                    articles.append({
                        'title': entry.title if hasattr(entry, 'title') else 'No title',
                        'link': entry.link if hasattr(entry, 'link') else (entry.links[0].href if hasattr(entry, 'links') and entry.links else ''),
                        'summary': summary,
                        'source': feed_title,
                        'published': pub_date.isoformat() if pub_date else None
                    })
            except Exception as e:
                logger.error(f"Error fetching RSS feed {feed_url}: {e}")

        return articles

    def fetch_hackernews_top_stories(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Fetch top stories from Hacker News"""
        articles = []

        try:
            logger.info("Fetching Hacker News top stories")
            response = requests.get(f"{self.sources['hacker_news_api']}/topstories.json", timeout=10)
            story_ids = response.json()[:limit]

            for story_id in story_ids[:20]:  # Get top 20
                try:
                    story_response = requests.get(
                        f"{self.sources['hacker_news_api']}/item/{story_id}.json",
                        timeout=5
                    )
                    story = story_response.json()

                    if story and story.get('type') == 'story':
                        articles.append({
                            'title': story.get('title', 'No title'),
                            'link': story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                            'summary': story.get('text', '')[:500] if story.get('text') else '',
                            'source': 'Hacker News',
                            'score': story.get('score', 0),
                            'published': datetime.fromtimestamp(story.get('time', 0)).isoformat()
                        })
                except Exception as e:
                    logger.error(f"Error fetching HN story {story_id}: {e}")

        except Exception as e:
            logger.error(f"Error fetching Hacker News stories: {e}")

        return articles

    def get_all_content(self) -> List[Dict[str, Any]]:
        """Aggregate content from all sources"""
        all_content = []

        # Fetch from RSS feeds
        all_content.extend(self.fetch_rss_content())

        # Fetch from Hacker News
        all_content.extend(self.fetch_hackernews_top_stories())

        logger.info(f"Total articles collected: {len(all_content)}")
        return all_content


class ContentGenerator:
    """Generates high-quality content using Claude AI"""

    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5-20250929"

    def analyze_trends(self, articles: List[Dict[str, Any]]) -> str:
        """Analyze articles to identify key trends"""
        # Prepare content summary for Claude
        content_summary = self._prepare_content_summary(articles)

        prompt = f"""You are a senior product manager and engineering leader analyzing the latest industry trends.

Below is a collection of recent articles, blog posts, and discussions from the product management and engineering community:

{content_summary}

Please analyze these articles and:
1. Identify the top 3-5 key themes and trends
2. Highlight important insights for product and engineering teams
3. Note any emerging technologies or methodologies
4. Identify common challenges or discussions

Provide a concise analysis (300-400 words) that would be valuable for PMs and engineering leaders."""

        try:
            logger.info("Analyzing trends with Claude AI")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return "Error analyzing trends"

    def generate_weekly_content(self, articles: List[Dict[str, Any]], trends_analysis: str) -> Dict[str, str]:
        """Generate comprehensive weekly content"""

        content_summary = self._prepare_content_summary(articles[:20])  # Use top 20

        prompt = f"""You are a content creator for product and engineering professionals. Based on the latest industry content and trends, create a high-quality weekly digest.

TRENDS ANALYSIS:
{trends_analysis}

RECENT CONTENT:
{content_summary}

Please create a comprehensive weekly digest with the following sections:

1. **Executive Summary** (2-3 sentences)
2. **Key Trends This Week** (3-5 bullet points with brief explanations)
3. **Featured Insights** (2-3 detailed insights with actionable takeaways)
4. **Recommended Reading** (5-7 curated articles with brief descriptions)
5. **Action Items** (3-5 concrete actions for PM/engineering teams)

Make the content:
- Professional and insightful
- Actionable and practical
- Well-structured and easy to scan
- Focused on value for busy PMs and engineers

Write in markdown format."""

        try:
            logger.info("Generating weekly content with Claude AI")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            return {
                'main_content': content,
                'trends_analysis': trends_analysis,
                'articles_count': len(articles)
            }
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return {
                'main_content': "Error generating content",
                'trends_analysis': trends_analysis,
                'articles_count': len(articles)
            }

    def _prepare_content_summary(self, articles: List[Dict[str, Any]]) -> str:
        """Prepare a formatted summary of articles for the prompt"""
        summary_parts = []

        for i, article in enumerate(articles[:30], 1):  # Limit to 30 for token efficiency
            article_text = f"{i}. **{article['title']}**\n"
            article_text += f"   Source: {article['source']}\n"
            if article.get('summary'):
                article_text += f"   Summary: {article['summary']}\n"
            if article.get('link'):
                article_text += f"   Link: {article['link']}\n"
            summary_parts.append(article_text)

        return "\n".join(summary_parts)


class OutputManager:
    """Manages output formatting and file storage"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def save_weekly_digest(self, content: Dict[str, str]) -> str:
        """Save the weekly digest to a markdown file"""
        # Generate filename with date
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        filename = f"weekly_digest_{week_start.strftime('%Y-%m-%d')}.md"
        filepath = os.path.join(self.output_dir, filename)

        # Format the complete document
        document = f"""# Weekly Product & Engineering Digest
## Week of {week_start.strftime('%B %d, %Y')}

Generated on {today.strftime('%Y-%m-%d at %H:%M UTC')}

---

{content['main_content']}

---

## About This Digest

This digest was automatically generated by analyzing {content['articles_count']} articles from leading product management and engineering sources including Hacker News, Mind the Product, SVPG, Lenny's Newsletter, and more.

**Trends Analysis:**
{content['trends_analysis']}

---

*Generated with Claude AI*
"""

        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(document)

        logger.info(f"Weekly digest saved to: {filepath}")
        return filepath

    def save_source_articles(self, articles: List[Dict[str, Any]]) -> str:
        """Save source articles to JSON for reference"""
        today = datetime.now()
        filename = f"source_articles_{today.strftime('%Y-%m-%d')}.json"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, default=str)

        logger.info(f"Source articles saved to: {filepath}")
        return filepath


def main():
    """Main execution function"""
    logger.info("Starting Weekly Content Generator")

    # Check for API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    try:
        # Step 1: Scrape content
        logger.info("Step 1: Scraping content from sources")
        scraper = ContentScraper()
        articles = scraper.get_all_content()

        if not articles:
            logger.error("No articles collected")
            sys.exit(1)

        # Step 2: Analyze trends
        logger.info("Step 2: Analyzing trends")
        generator = ContentGenerator(api_key)
        trends = generator.analyze_trends(articles)

        # Step 3: Generate content
        logger.info("Step 3: Generating weekly digest")
        content = generator.generate_weekly_content(articles, trends)

        # Step 4: Save output
        logger.info("Step 4: Saving output")
        output_manager = OutputManager()
        digest_path = output_manager.save_weekly_digest(content)
        articles_path = output_manager.save_source_articles(articles)

        logger.info("=" * 50)
        logger.info("Content generation completed successfully!")
        logger.info(f"Weekly digest: {digest_path}")
        logger.info(f"Source articles: {articles_path}")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
