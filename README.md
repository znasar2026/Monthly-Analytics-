# Monthly AI Analytics Bot

An automated analytics bot that reads your CSV/Excel data, sends it to Claude, and saves a Markdown report every month.

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set your API key
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. Add your data files
Drop any `.csv` or `.xlsx` files into the `./data/` folder.

### 4. Run manually
```bash
# Current month
python analytics_bot.py

# Specific month
python analytics_bot.py --month 2025-04

# Custom directories
python analytics_bot.py --data-dir ./my_data --reports-dir ./my_reports
```

Reports are saved to `./reports/analytics_report_YYYY-MM.md`.

---

## Automate monthly with GitHub Actions

1. Push this project to a GitHub repo
2. Add your API key as a repo secret: **Settings → Secrets → `ANTHROPIC_API_KEY`**
3. The workflow in `.github/workflows/monthly_analytics.yml` runs automatically on the 1st of each month at 08:00 UTC
4. Reports are saved as GitHub Actions artifacts (90-day retention) and optionally committed back to the repo

You can also trigger it manually from the **Actions** tab.

---

## Automate with cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add this line — runs at 08:00 on the 1st of every month
0 8 1 * * cd /path/to/analytics_bot && ANTHROPIC_API_KEY=sk-ant-... python analytics_bot.py >> /var/log/analytics_bot.log 2>&1
```

---

## Customizing the analysis

Edit the `SYSTEM_PROMPT` in `analytics_bot.py` to change what Claude focuses on. For example:

```python
SYSTEM_PROMPT = """You are a financial analyst. Focus on:
- Revenue trends month-over-month
- Customer acquisition cost
- Churn rate and retention
..."""
```

## Project structure

```
analytics_bot/
├── analytics_bot.py          # Main script
├── requirements.txt
├── data/                     # ← put your CSV/Excel files here
│   └── sales_2025.csv
├── reports/                  # ← reports saved here
│   └── analytics_report_2025-05.md
└── .github/
    └── workflows/
        └── monthly_analytics.yml
```
