# Weekly PM Content Generator

An automated system that finds new product management and engineering content from top sources, analyzes trends using Claude AI, and generates high-quality weekly digests.

## 🚀 Features

- **Multi-Source Scraping**: Aggregates content from:
  - Hacker News top stories
  - Mind the Product
  - SVPG (Silicon Valley Product Group)
  - Lenny's Newsletter
  - Product Plan Blog
  - And more...

- **AI-Powered Analysis**: Uses Claude AI (Sonnet 4.5) to:
  - Identify key trends and themes
  - Generate actionable insights
  - Create professional weekly digests
  - Provide curated recommendations

- **Automated Weekly Delivery**: GitHub Actions workflow runs every Monday at 9 AM UTC

- **Professional Output**: Generates well-structured markdown documents with:
  - Executive summaries
  - Key trends analysis
  - Featured insights with takeaways
  - Curated reading recommendations
  - Action items for PM/engineering teams

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

Edit `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=your_actual_api_key_here
```

### 4. Set Up GitHub Secrets (for automation)

For the weekly GitHub Actions workflow to work:

1. Go to your repository settings
2. Navigate to **Secrets and variables** → **Actions**
3. Add a new repository secret:
   - Name: `ANTHROPIC_API_KEY`
   - Value: Your Anthropic API key

## 🏃 Usage

### Run Manually

```bash
python main.py
```

This will:
1. Scrape latest content from all configured sources
2. Analyze trends using Claude AI
3. Generate a comprehensive weekly digest
4. Save output to the `output/` directory

### Run Automatically (GitHub Actions)

The workflow is configured to run every Monday at 9 AM UTC. You can also:

- **Trigger manually**: Go to Actions → Weekly Content Generation → Run workflow
- **Modify schedule**: Edit `.github/workflows/weekly-content-generation.yml`

## 📁 Output Structure

Generated files are saved in the `output/` directory:

```
output/
├── weekly_digest_2025-11-17.md       # Main weekly digest
└── source_articles_2025-11-18.json   # Source articles (JSON)
```

### Sample Output

Each weekly digest includes:

```markdown
# Weekly Product & Engineering Digest
## Week of November 17, 2025

## Executive Summary
[2-3 sentence overview]

## Key Trends This Week
- Trend 1: [Explanation]
- Trend 2: [Explanation]
...

## Featured Insights
[Detailed insights with actionable takeaways]

## Recommended Reading
1. Article title - Brief description
...

## Action Items
- [ ] Action item 1
- [ ] Action item 2
...
```

## ⚙️ Configuration

### Modify Content Sources

Edit `main.py` in the `ContentScraper` class to add/remove sources:

```python
self.sources = {
    'rss_feeds': [
        'https://your-favorite-pm-blog.com/feed/',
        # Add more RSS feeds here
    ],
}
```

### Adjust Collection Period

Change the `days_back` parameter in `main.py`:

```python
scraper.fetch_rss_content(days_back=7)  # Default is 7 days
```

### Customize Content Generation

Modify the prompts in the `ContentGenerator` class to adjust:
- Tone and style
- Content structure
- Focus areas
- Output length

## 🔧 Troubleshooting

### Error: "ANTHROPIC_API_KEY environment variable not set"

Make sure you've created a `.env` file with your API key, or set the environment variable:

```bash
export ANTHROPIC_API_KEY=your_key_here
python main.py
```

### No articles collected

- Check your internet connection
- Some RSS feeds may be temporarily unavailable
- The Hacker News API may have rate limits

### GitHub Actions workflow not running

- Verify the `ANTHROPIC_API_KEY` secret is set in repository settings
- Check Actions are enabled for your repository
- Review workflow logs in the Actions tab

## 📊 Cost Considerations

- **API Costs**: The script uses Claude AI API which incurs costs based on tokens
- **Typical weekly run**: ~10,000-20,000 tokens (~$0.30-$0.60 per week)
- **Optimization tip**: Reduce the number of articles analyzed by adjusting limits in `main.py`

## 🤝 Contributing

Contributions are welcome! Some ideas:

- Add more content sources (Reddit, Product Hunt API, etc.)
- Implement email delivery
- Add support for different content formats (PDF, HTML)
- Create a web interface for browsing past digests
- Add sentiment analysis
- Implement topic clustering

## 📝 License

MIT License - feel free to use and modify as needed.

## 🙏 Acknowledgments

- Content sources: Hacker News, Mind the Product, SVPG, Lenny Rachitsky, and others
- Powered by [Anthropic Claude AI](https://www.anthropic.com/)

---

**Generated with ❤️ for the PM and Engineering community**
