# Weekly PM Content Generator

An automated system that finds new product management and engineering content from top sources, analyzes trends using Claude AI, and generates high-quality weekly digests in multiple formats.

## 🚀 Features

### Multi-Source Content Aggregation
Automatically scrapes content from 10+ sources:
- **Hacker News** - Top stories and discussions
- **Medium** - Product Management & Engineering Management tags
- **Dev.to** - Productivity and Career content
- **Lenny's Newsletter** - PM insights from Lenny Rachitsky
- **SVPG** - Silicon Valley Product Group blog
- **Reddit** - r/ProductManagement, r/programming, r/SaaS, r/startups (when available)
- **Product Hunt** - Latest product launches

### Advanced Reliability Features
- **Exponential Backoff Retry** - Automatic retry with 1s, 2s, 4s delays
- **Proper User-Agent Headers** - Avoid 403 errors
- **Session Management** - Persistent connections with retry strategies
- **Graceful Failure Handling** - Continues even if some sources fail

### AI-Powered Content Generation
Uses Claude Sonnet 4.5 to generate:
- **Trend Analysis** - Identifies key themes and emerging topics
- **Multiple Digest Styles**:
  - `comprehensive` - Full weekly digest with all sections
  - `executive` - Strategic brief for senior leaders
  - `technical` - Deep-dive for engineering teams
  - `learning` - Growth-focused for skill development
- **Key Quote Extraction** - Highlights powerful insights
- **Discussion Questions** - Team meeting prompts
- **Curated Recommendations** - Filtered, relevant reading

### Multi-Format Output
Generates content in 5+ formats:
- **Markdown** (.md) - Full digest with all features
- **HTML** (.html) - Styled web version
- **LinkedIn** (.txt) - Optimized post format
- **Twitter** (.txt) - Thread format with breaks
- **Slack** (.txt) - Team-ready markdown

## 📋 Prerequisites

- Python 3.11 or higher
- Anthropic API key ([Get one here](https://console.anthropic.com/))
- GitHub repository (for automated weekly runs)

## 🛠️ Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd dailypmcontentgenerator
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and configure:

```
ANTHROPIC_API_KEY=your_actual_api_key_here
DIGEST_STYLE=comprehensive  # Options: comprehensive, executive, technical, learning
```

### 4. Set Up GitHub Secrets (for automation)

For the weekly GitHub Actions workflow to work:

1. Go to your repository settings
2. Navigate to **Secrets and variables** → **Actions**
3. Add repository secrets:
   - Name: `ANTHROPIC_API_KEY`
   - Value: Your Anthropic API key
   - Optional: `DIGEST_STYLE` (default: comprehensive)

## 🏃 Usage

### Run Manually

```bash
python main.py
```

This will:
1. Scrape latest content from all configured sources (60-100 articles)
2. Analyze trends using Claude AI
3. Generate a digest in your chosen style
4. Extract key quotes and create discussion questions
5. Save output in 5 formats to the `output/` directory

### Run with Different Styles

```bash
# Executive brief for leaders
DIGEST_STYLE=executive python main.py

# Technical deep-dive for engineers
DIGEST_STYLE=technical python main.py

# Learning-focused for growth
DIGEST_STYLE=learning python main.py
```

### Run Automatically (GitHub Actions)

The workflow is configured to run every Monday at 9 AM UTC. You can also:

- **Trigger manually**: Go to Actions → Weekly Content Generation → Run workflow
- **Modify schedule**: Edit `.github/workflows/weekly-content-generation.yml`
- **Change style**: Add `DIGEST_STYLE` secret in repository settings

## 📁 Output Structure

Generated files are saved in the `output/` directory:

```
output/
├── weekly_digest_2025-11-17.md           # Main markdown digest
├── weekly_digest_2025-11-17.html         # HTML version (styled)
├── weekly_digest_2025-11-17_linkedin.txt # LinkedIn post
├── weekly_digest_2025-11-17_twitter.txt  # Twitter thread
├── weekly_digest_2025-11-17_slack.txt    # Slack message
└── source_articles_2025-11-18.json       # Source data (JSON)
```

### Sample Output Structure

**Comprehensive Style:**
```markdown
# Weekly Product & Engineering Digest
## Week of November 17, 2025

## Executive Summary
[2-3 sentence overview]

## Key Trends This Week
- Trend 1: [Explanation]
- Trend 2: [Explanation]

## Featured Insights
[Detailed insights with actionable takeaways]

## Recommended Reading
1. Article title - Brief description

## Action Items
- [ ] Action item 1

## Key Quotes
> "Quote" - Source

## Discussion Questions for Your Team
1. Question 1...
```

**Executive Style:**
```markdown
# TL;DR
[100-word strategic overview]

# Strategic Implications
- Business impact 1
- Market movement 2

# Recommended Actions
1. Strategic action

# Market Watch
[Competitive intelligence]
```

**Technical Style:**
```markdown
# Engineering Highlights
[Key technical developments]

# Architecture & Design Patterns
[Emerging patterns]

# Tools & Technologies
[New tools and frameworks]

# Engineering Leadership
[Team building insights]
```

**Learning Style:**
```markdown
# What We're Learning This Week
[Key lessons from community]

# Skill Spotlight
[Skill to develop and why]

# Case Studies & War Stories
[Real-world examples]

# Reflection Questions
[Questions to apply learnings]
```

## ⚙️ Configuration

### Modify Content Sources

Edit `main.py` in the `ContentScraper.__init__` method:

```python
self.sources = {
    'rss_feeds': [
        'https://your-favorite-pm-blog.com/feed/',
        'https://medium.com/feed/tag/your-topic',
        # Add more RSS feeds here
    ],
}
```

### Adjust Collection Period

Change the `days_back` parameter in `main.py`:

```python
scraper.fetch_rss_content(days_back=7)  # Default is 7 days
```

### Customize Digest Styles

Modify the prompt methods in the `ContentGenerator` class:
- `_get_comprehensive_prompt()` - Full digest
- `_get_executive_prompt()` - Leadership brief
- `_get_technical_prompt()` - Engineering focus
- `_get_learning_prompt()` - Growth oriented

### Add Custom Subreddits

```python
reddit_articles = scraper.fetch_reddit_posts(
    subreddits=['YourSubreddit', 'AnotherOne'],
    limit=15
)
```

## 🎨 Output Formats Explained

### Markdown (.md)
- Complete digest with all sections
- Discussion questions and key quotes
- Best for: Documentation, archiving, GitHub

### HTML (.html)
- Styled web version with CSS
- Professional appearance
- Best for: Email, web publishing, sharing

### LinkedIn (.txt)
- 3000 character limit respected
- Hashtags included
- Engagement question
- Best for: Professional networking, thought leadership

### Twitter (.txt)
- Thread format with clear breaks
- Character-optimized tweets
- CTA in final tweet
- Best for: Social media engagement, viral reach

### Slack (.txt)
- Slack markdown formatting
- Truncated for channel messages
- Link to full version
- Best for: Team sharing, internal communications

## 🔧 Troubleshooting

### Error: "ANTHROPIC_API_KEY environment variable not set"

Make sure you've created a `.env` file with your API key, or set the environment variable:

```bash
export ANTHROPIC_API_KEY=your_key_here
python main.py
```

### Some sources return 403 errors

This is expected - some sites (like Reddit) have restricted their public APIs. The system gracefully handles failures and continues with available sources.

### No articles collected from certain feeds

- Check your internet connection
- Some RSS feeds may be temporarily unavailable
- The system will log warnings but continue
- Try running again later

### GitHub Actions workflow not running

- Verify the `ANTHROPIC_API_KEY` secret is set in repository settings
- Check Actions are enabled for your repository
- Review workflow logs in the Actions tab

### Output format missing

All formats are generated automatically. If one is missing:
- Check file permissions in the `output/` directory
- Review logs for specific error messages
- Ensure disk space is available

## 📊 Performance & Cost

### Collection Performance
- **Sources**: 10+ configured sources
- **Articles**: 60-100 articles per run
- **Time**: ~2-3 minutes per run
- **Retry Logic**: 3 attempts with exponential backoff

### API Costs (Claude AI)
- **Trend Analysis**: ~1,500 tokens (~$0.02)
- **Content Generation**: ~8,000 tokens (~$0.10)
- **Quote Extraction**: ~800 tokens (~$0.01)
- **Discussion Questions**: ~600 tokens (~$0.01)
- **Total per week**: ~$0.15-$0.20

### Optimization Tips
- Reduce number of articles: Adjust limits in `main.py`
- Use `executive` style for shorter content
- Disable quote extraction if not needed
- Adjust `days_back` to reduce article count

## 🤝 Contributing

Contributions are welcome! Enhancement ideas:

### Content Sources
- [ ] RSS feed deduplication
- [ ] Content quality scoring
- [ ] Topic clustering
- [ ] Sentiment analysis

### Output Formats
- [ ] PDF generation with styling
- [ ] Notion page format
- [ ] Email HTML templates
- [ ] Newsletter platform integration (Substack, Beehiiv)

### AI Features
- [ ] Multi-language support
- [ ] Custom prompt templates
- [ ] Personalized recommendations
- [ ] Historical trend tracking

### Infrastructure
- [ ] SQLite database for history
- [ ] Web dashboard for browsing
- [ ] Search functionality
- [ ] Analytics and metrics

## 🆕 What's New

### v2.0 - Enhanced Edition
- ✅ **4 Digest Styles** - Comprehensive, Executive, Technical, Learning
- ✅ **5 Output Formats** - Markdown, HTML, LinkedIn, Twitter, Slack
- ✅ **Retry Logic** - Exponential backoff for reliability
- ✅ **New Sources** - Medium, Dev.to, Reddit support
- ✅ **AI Quote Extraction** - Highlights key insights
- ✅ **Discussion Questions** - Team engagement prompts
- ✅ **Better Error Handling** - Graceful failure recovery

### v1.0 - Initial Release
- ✅ Hacker News integration
- ✅ RSS feed scraping
- ✅ Claude AI content generation
- ✅ GitHub Actions automation
- ✅ Markdown output

## 📝 License

MIT License - feel free to use and modify as needed.

## 🙏 Acknowledgments

- Content sources: Hacker News, Medium, Dev.to, Mind the Product, SVPG, Lenny Rachitsky, and others
- Powered by [Anthropic Claude AI](https://www.anthropic.com/)
- Built with Python, atoma, and requests

---

**Generated with ❤️ for the PM and Engineering community**

**Questions or feedback?** Open an issue or contribute to the project!
