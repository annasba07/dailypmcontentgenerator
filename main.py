#!/usr/bin/env python3
"""
Weekly Product & Engineering Content Generator
Scrapes latest PM/engineering content and generates high-quality articles using Claude AI
"""

import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import atoma
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from anthropic import Anthropic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContentScraper:
    """Scrapes content from various PM and engineering sources with retry logic"""

    def __init__(self):
        self.sources = {
            'rss_feeds': [
                'https://news.ycombinator.com/rss',
                'https://www.svpg.com/feed/',
                'https://www.lennysnewsletter.com/feed',
                'https://medium.com/feed/tag/product-management',
                'https://medium.com/feed/tag/engineering-management',
                'https://dev.to/feed/tag/productivity',
                'https://dev.to/feed/tag/career',
            ],
            'hacker_news_api': 'https://hacker-news.firebaseio.com/v0',
        }

        # Setup session with retry logic
        self.session = self._create_session_with_retries()

    def _create_session_with_retries(self) -> requests.Session:
        """Create a requests session with automatic retries and proper headers"""
        session = requests.Session()

        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,  # Wait 1, 2, 4 seconds between retries
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set user agent to avoid 403s
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; ContentBot/1.0; +http://example.com/bot)'
        })

        return session

    def _fetch_with_retry(self, url: str, timeout: int = 10) -> Optional[requests.Response]:
        """Fetch URL with exponential backoff retry"""
        max_attempts = 3
        base_delay = 2

        for attempt in range(max_attempts):
            try:
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt < max_attempts - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed for {url}, retrying in {delay}s: {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"All retry attempts failed for {url}: {e}")
                    return None
        return None

    def fetch_rss_content(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch content from RSS feeds"""
        articles = []
        cutoff_date = datetime.now() - timedelta(days=days_back)

        for feed_url in self.sources['rss_feeds']:
            try:
                logger.info(f"Fetching RSS feed: {feed_url}")
                response = self._fetch_with_retry(feed_url)

                if not response:
                    continue

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
            response = self._fetch_with_retry(f"{self.sources['hacker_news_api']}/topstories.json")

            if not response:
                return articles

            story_ids = response.json()[:limit]

            for story_id in story_ids[:20]:  # Get top 20
                try:
                    story_response = self._fetch_with_retry(
                        f"{self.sources['hacker_news_api']}/item/{story_id}.json"
                    )

                    if not story_response:
                        continue

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

    def fetch_reddit_posts(self, subreddits: List[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch top posts from Reddit"""
        if subreddits is None:
            subreddits = ['ProductManagement', 'programming', 'SaaS', 'startups']

        articles = []

        for subreddit in subreddits:
            try:
                logger.info(f"Fetching Reddit r/{subreddit}")
                url = f"https://www.reddit.com/r/{subreddit}/top.json?t=week&limit={limit}"
                response = self._fetch_with_retry(url)

                if not response:
                    continue

                data = response.json()
                posts = data.get('data', {}).get('children', [])

                for post in posts[:limit]:
                    post_data = post.get('data', {})

                    # Skip if it's just a link to an external site with no discussion
                    if post_data.get('num_comments', 0) < 5:
                        continue

                    articles.append({
                        'title': post_data.get('title', 'No title'),
                        'link': f"https://reddit.com{post_data.get('permalink', '')}",
                        'summary': post_data.get('selftext', '')[:500],
                        'source': f"Reddit r/{subreddit}",
                        'score': post_data.get('score', 0),
                        'comments': post_data.get('num_comments', 0),
                        'published': datetime.fromtimestamp(post_data.get('created_utc', 0)).isoformat()
                    })

            except Exception as e:
                logger.error(f"Error fetching Reddit r/{subreddit}: {e}")

        return articles

    def fetch_producthunt_posts(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch popular Product Hunt posts"""
        articles = []

        try:
            logger.info("Fetching Product Hunt posts")
            # Product Hunt doesn't have a public API without auth, but we can use their RSS
            url = "https://www.producthunt.com/feed"
            response = self._fetch_with_retry(url)

            if not response:
                return articles

            feed = atoma.parse_rss_bytes(response.content)
            cutoff_date = datetime.now() - timedelta(days=days_back)

            for entry in feed.items[:15]:
                pub_date = entry.pub_date if hasattr(entry, 'pub_date') else None

                if pub_date and pub_date.replace(tzinfo=None) < cutoff_date:
                    continue

                articles.append({
                    'title': entry.title if hasattr(entry, 'title') else 'No title',
                    'link': entry.link if hasattr(entry, 'link') else '',
                    'summary': entry.description[:500] if hasattr(entry, 'description') else '',
                    'source': 'Product Hunt',
                    'published': pub_date.isoformat() if pub_date else None
                })

        except Exception as e:
            logger.error(f"Error fetching Product Hunt: {e}")

        return articles

    def get_all_content(self) -> List[Dict[str, Any]]:
        """Aggregate content from all sources"""
        all_content = []

        # Fetch from RSS feeds
        all_content.extend(self.fetch_rss_content())

        # Fetch from Hacker News
        all_content.extend(self.fetch_hackernews_top_stories())

        # Fetch from Reddit
        all_content.extend(self.fetch_reddit_posts())

        # Fetch from Product Hunt
        all_content.extend(self.fetch_producthunt_posts())

        logger.info(f"Total articles collected: {len(all_content)}")
        return all_content


class ContentGenerator:
    """Generates high-quality content using Claude AI with multiple styles"""

    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5-20250929"

    def analyze_trends(self, articles: List[Dict[str, Any]]) -> str:
        """Analyze articles to identify key trends"""
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

    def generate_weekly_content(
        self,
        articles: List[Dict[str, Any]],
        trends_analysis: str,
        style: str = "comprehensive"
    ) -> Dict[str, str]:
        """Generate comprehensive weekly content with specified style"""

        content_summary = self._prepare_content_summary(articles[:20])

        # Different prompts for different styles
        style_prompts = {
            "comprehensive": self._get_comprehensive_prompt(content_summary, trends_analysis),
            "executive": self._get_executive_prompt(content_summary, trends_analysis),
            "technical": self._get_technical_prompt(content_summary, trends_analysis),
            "learning": self._get_learning_prompt(content_summary, trends_analysis)
        }

        prompt = style_prompts.get(style, style_prompts["comprehensive"])

        try:
            logger.info(f"Generating {style} weekly content with Claude AI")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )

            main_content = response.content[0].text

            # Generate additional AI features
            key_quotes = self.extract_key_quotes(articles[:10])
            discussion_questions = self.generate_discussion_questions(trends_analysis)

            return {
                'main_content': main_content,
                'trends_analysis': trends_analysis,
                'articles_count': len(articles),
                'key_quotes': key_quotes,
                'discussion_questions': discussion_questions,
                'style': style
            }
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return {
                'main_content': "Error generating content",
                'trends_analysis': trends_analysis,
                'articles_count': len(articles),
                'key_quotes': '',
                'discussion_questions': '',
                'style': style
            }

    def extract_key_quotes(self, articles: List[Dict[str, Any]]) -> str:
        """Extract key quotes from articles using AI"""
        content_summary = self._prepare_content_summary(articles)

        prompt = f"""From the following articles, extract 3-5 powerful, insightful quotes that would resonate with product managers and engineering leaders. Focus on actionable wisdom, unique perspectives, or thought-provoking statements.

{content_summary}

Format as:
> "Quote here" - Source

Only include truly valuable quotes."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error extracting quotes: {e}")
            return ""

    def generate_discussion_questions(self, trends_analysis: str) -> str:
        """Generate thought-provoking discussion questions for teams"""
        prompt = f"""Based on this trends analysis, generate 4-6 thought-provoking discussion questions that product and engineering teams could use in their next team meeting or 1-on-1s.

Trends Analysis:
{trends_analysis}

Make the questions:
- Open-ended and discussion-worthy
- Relevant to current work
- Applicable to various team contexts
- Forward-thinking

Format as numbered list."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return ""

    def _get_comprehensive_prompt(self, content_summary: str, trends_analysis: str) -> str:
        """Comprehensive digest prompt"""
        return f"""You are a content creator for product and engineering professionals. Based on the latest industry content and trends, create a high-quality weekly digest.

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

    def _get_executive_prompt(self, content_summary: str, trends_analysis: str) -> str:
        """Executive-focused brief prompt"""
        return f"""You are creating an executive brief for senior product and engineering leaders.

TRENDS ANALYSIS:
{trends_analysis}

RECENT CONTENT:
{content_summary}

Create a concise executive brief with:

1. **TL;DR** (1 paragraph, max 100 words)
2. **Strategic Implications** (3-4 key points on what this means for the business)
3. **Recommended Actions** (Top 3 strategic actions)
4. **Market Watch** (Competitive or market movements worth noting)

Keep it crisp, strategic, and focused on business impact. Use markdown."""

    def _get_technical_prompt(self, content_summary: str, trends_analysis: str) -> str:
        """Technical deep-dive prompt"""
        return f"""You are creating a technical digest for engineering leaders and senior ICs.

TRENDS ANALYSIS:
{trends_analysis}

RECENT CONTENT:
{content_summary}

Create a technical deep-dive with:

1. **Engineering Highlights** (Key technical developments and discussions)
2. **Architecture & Design Patterns** (Emerging patterns and best practices)
3. **Tools & Technologies** (New tools, frameworks, or techniques gaining traction)
4. **Technical Reads** (Top technical articles worth diving into)
5. **Engineering Leadership** (Insights on team building, culture, processes)

Focus on technical depth and practical applicability. Use markdown."""

    def _get_learning_prompt(self, content_summary: str, trends_analysis: str) -> str:
        """Learning-focused prompt"""
        return f"""You are creating a learning-focused digest for product and engineering professionals who want to grow.

TRENDS ANALYSIS:
{trends_analysis}

RECENT CONTENT:
{content_summary}

Create a learning digest with:

1. **What We're Learning This Week** (Key lessons from the community)
2. **Skill Spotlight** (A skill or area getting attention - why it matters and how to develop it)
3. **Case Studies & War Stories** (Real-world examples and lessons learned)
4. **Learning Resources** (Articles, discussions, talks worth your time)
5. **Reflection Questions** (Questions to help apply these learnings)

Focus on growth, learning, and skill development. Use markdown."""

    def _prepare_content_summary(self, articles: List[Dict[str, Any]]) -> str:
        """Prepare a formatted summary of articles for the prompt"""
        summary_parts = []

        for i, article in enumerate(articles[:30], 1):
            article_text = f"{i}. **{article['title']}**\n"
            article_text += f"   Source: {article['source']}\n"
            if article.get('summary'):
                article_text += f"   Summary: {article['summary']}\n"
            if article.get('link'):
                article_text += f"   Link: {article['link']}\n"
            if article.get('score'):
                article_text += f"   Score: {article['score']}\n"
            if article.get('comments'):
                article_text += f"   Comments: {article['comments']}\n"
            summary_parts.append(article_text)

        return "\n".join(summary_parts)


class OutputManager:
    """Manages output formatting and file storage in multiple formats"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def save_weekly_digest(self, content: Dict[str, str]) -> Dict[str, str]:
        """Save the weekly digest in multiple formats"""
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        base_filename = f"weekly_digest_{week_start.strftime('%Y-%m-%d')}"

        saved_files = {}

        # Save Markdown version
        saved_files['markdown'] = self._save_markdown(content, base_filename, week_start, today)

        # Save HTML version
        saved_files['html'] = self._save_html(content, base_filename, week_start, today)

        # Save LinkedIn format
        saved_files['linkedin'] = self._save_linkedin(content, base_filename)

        # Save Twitter thread
        saved_files['twitter'] = self._save_twitter(content, base_filename)

        # Save Slack format
        saved_files['slack'] = self._save_slack(content, base_filename)

        return saved_files

    def _save_markdown(self, content: Dict[str, str], base_filename: str, week_start: datetime, today: datetime) -> str:
        """Save markdown version"""
        filename = f"{base_filename}.md"
        filepath = os.path.join(self.output_dir, filename)

        document = f"""# Weekly Product & Engineering Digest
## Week of {week_start.strftime('%B %d, %Y')}

Generated on {today.strftime('%Y-%m-%d at %H:%M UTC')}
Style: {content.get('style', 'comprehensive').title()}

---

{content['main_content']}

---

## Key Quotes

{content.get('key_quotes', 'No quotes extracted')}

---

## Discussion Questions for Your Team

{content.get('discussion_questions', 'No questions generated')}

---

## About This Digest

This digest was automatically generated by analyzing {content['articles_count']} articles from leading product management and engineering sources including Hacker News, Reddit, Product Hunt, Mind the Product, SVPG, Lenny's Newsletter, Dev.to, Medium, and more.

**Trends Analysis:**
{content['trends_analysis']}

---

*Generated with Claude AI*
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(document)

        logger.info(f"Markdown digest saved to: {filepath}")
        return filepath

    def _save_html(self, content: Dict[str, str], base_filename: str, week_start: datetime, today: datetime) -> str:
        """Save HTML version"""
        filename = f"{base_filename}.html"
        filepath = os.path.join(self.output_dir, filename)

        # Convert markdown to HTML-ready content (basic conversion)
        html_content = content['main_content'].replace('\n\n', '</p><p>').replace('# ', '<h1>').replace('## ', '<h2>')

        html_document = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly PM & Engineering Digest - {week_start.strftime('%B %d, %Y')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; }}
        .meta {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 30px; }}
        .quote {{
            border-left: 4px solid #3498db;
            padding-left: 20px;
            margin: 20px 0;
            font-style: italic;
            color: #555;
        }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        ul {{ padding-left: 25px; }}
        li {{ margin-bottom: 10px; }}
    </style>
</head>
<body>
    <h1>Weekly Product & Engineering Digest</h1>
    <div class="meta">
        Week of {week_start.strftime('%B %d, %Y')} | Generated on {today.strftime('%Y-%m-%d at %H:%M UTC')}
    </div>

    <div class="content">
        {html_content}
    </div>

    <h2>Key Quotes</h2>
    <div class="quote">
        {content.get('key_quotes', 'No quotes extracted')}
    </div>

    <h2>Discussion Questions</h2>
    <p>{content.get('discussion_questions', 'No questions generated')}</p>

    <div class="footer">
        <p>This digest was automatically generated by analyzing {content['articles_count']} articles from leading sources.</p>
        <p><em>Powered by Claude AI</em></p>
    </div>
</body>
</html>"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_document)

        logger.info(f"HTML digest saved to: {filepath}")
        return filepath

    def _save_linkedin(self, content: Dict[str, str], base_filename: str) -> str:
        """Save LinkedIn-optimized format"""
        filename = f"{base_filename}_linkedin.txt"
        filepath = os.path.join(self.output_dir, filename)

        # Extract first 2-3 key points from main content for LinkedIn
        lines = content['main_content'].split('\n')

        # Find executive summary or first substantive content
        summary_start = 0
        for i, line in enumerate(lines):
            if 'executive summary' in line.lower() or 'tl;dr' in line.lower():
                summary_start = i + 1
                break

        # Get first meaningful paragraph
        summary = []
        for line in lines[summary_start:summary_start+15]:
            if line.strip() and not line.startswith('#'):
                summary.append(line.strip())
            if len(summary) >= 3:
                break

        linkedin_post = f"""📊 Weekly Product & Engineering Insights

{' '.join(summary[:3])}

🔑 Key Takeaways:
{chr(10).join([line for line in lines if line.strip().startswith('-') or line.strip().startswith('•')])[:300]}...

💭 Question for you: What trends are you seeing in your organization?

---
This is from my weekly PM/Engineering digest analyzing {content['articles_count']} articles from top sources.

#ProductManagement #Engineering #Leadership #Tech #Innovation
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(linkedin_post[:3000])  # LinkedIn has character limits

        logger.info(f"LinkedIn post saved to: {filepath}")
        return filepath

    def _save_twitter(self, content: Dict[str, str], base_filename: str) -> str:
        """Save Twitter thread format"""
        filename = f"{base_filename}_twitter.txt"
        filepath = os.path.join(self.output_dir, filename)

        # Create a thread from key points
        lines = content['main_content'].split('\n')

        thread = [
            f"🧵 Weekly PM & Engineering Digest\n\nAnalyzed {content['articles_count']} articles from top sources. Here are the key insights:"
        ]

        # Extract bullet points or key sections
        tweet_count = 1
        current_tweet = ""
        for line in lines:
            if line.strip().startswith('-') or line.strip().startswith('•') or line.strip().startswith('##'):
                if current_tweet and len(current_tweet) > 50:
                    tweet_count += 1
                    thread.append(f"{tweet_count}/ {current_tweet}")
                    current_tweet = ""
                current_tweet = line.strip().lstrip('-•#').strip()
            elif current_tweet and line.strip():
                current_tweet += " " + line.strip()

            if len(current_tweet) > 240:
                tweet_count += 1
                thread.append(f"{tweet_count}/ {current_tweet[:240]}...")
                current_tweet = ""

        # Add final tweet with CTA
        thread.append(f"\n{tweet_count + 1}/ Want the full digest with quotes, discussion questions, and links?\n\nDM me or check the link in bio.\n\n#ProductManagement #Engineering #Tech")

        twitter_thread = "\n\n---TWEET BREAK---\n\n".join(thread)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(twitter_thread)

        logger.info(f"Twitter thread saved to: {filepath}")
        return filepath

    def _save_slack(self, content: Dict[str, str], base_filename: str) -> str:
        """Save Slack-optimized format"""
        filename = f"{base_filename}_slack.txt"
        filepath = os.path.join(self.output_dir, filename)

        # Slack markdown format
        slack_message = f"""*📊 Weekly Product & Engineering Digest*

_{content.get('style', 'comprehensive').title()} Edition_

{content['main_content'][:2000]}

---

*💬 Discussion Questions:*
{content.get('discussion_questions', 'No questions generated')[:500]}

---

_This digest analyzed {content['articles_count']} articles from Hacker News, Reddit, Product Hunt, Medium, Dev.to, and top PM blogs._

:bulb: Full digest available in the team drive.
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(slack_message)

        logger.info(f"Slack message saved to: {filepath}")
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

    # Get style from environment (default: comprehensive)
    style = os.getenv('DIGEST_STYLE', 'comprehensive')
    if style not in ['comprehensive', 'executive', 'technical', 'learning']:
        logger.warning(f"Invalid style '{style}', using 'comprehensive'")
        style = 'comprehensive'

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
        logger.info(f"Step 3: Generating {style} weekly digest")
        content = generator.generate_weekly_content(articles, trends, style=style)

        # Step 4: Save output in multiple formats
        logger.info("Step 4: Saving output in multiple formats")
        output_manager = OutputManager()
        saved_files = output_manager.save_weekly_digest(content)
        articles_path = output_manager.save_source_articles(articles)

        logger.info("=" * 50)
        logger.info("Content generation completed successfully!")
        logger.info(f"Style: {style}")
        for format_name, filepath in saved_files.items():
            logger.info(f"{format_name.title()}: {filepath}")
        logger.info(f"Source articles: {articles_path}")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
