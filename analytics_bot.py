"""
Monthly Analytics Bot — powered by Claude API
Reads CSV/Excel files, generates an AI analysis, saves a Markdown report.
"""

import os
import json
import glob
import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd
import anthropic

# ── Config ────────────────────────────────────────────────────────────────────

DATA_DIR = "./data"           # folder containing your CSV/Excel files
REPORTS_DIR = "./reports"     # where monthly reports are saved
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096

# How many rows to send to Claude (keeps costs predictable)
SAMPLE_ROWS = 200

# ── Data loading ──────────────────────────────────────────────────────────────

def load_data(data_dir: str) -> dict[str, pd.DataFrame]:
    """Load all CSV and Excel files from data_dir into a dict of DataFrames."""
    frames = {}
    patterns = ["*.csv", "*.xlsx", "*.xls"]
    for pattern in patterns:
        for path in glob.glob(os.path.join(data_dir, pattern)):
            name = Path(path).stem
            try:
                df = pd.read_csv(path) if path.endswith(".csv") else pd.read_excel(path)
                frames[name] = df
                print(f"  ✓ Loaded '{name}' — {len(df):,} rows × {len(df.columns)} cols")
            except Exception as e:
                print(f"  ✗ Skipped '{path}': {e}")
    return frames


def summarize_dataframes(frames: dict[str, pd.DataFrame]) -> str:
    """Build a compact text summary of each DataFrame to send to Claude."""
    parts = []
    for name, df in frames.items():
        # Basic shape + dtypes
        info = [f"## Dataset: {name}"]
        info.append(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
        info.append(f"Columns: {', '.join(df.columns.tolist())}")

        # Numeric summary
        numeric = df.select_dtypes(include="number")
        if not numeric.empty:
            desc = numeric.describe().round(2).to_string()
            info.append(f"\nNumeric summary:\n{desc}")

        # Categorical summary (top values for object cols)
        cats = df.select_dtypes(include="object")
        for col in cats.columns[:5]:   # limit to first 5 categorical cols
            top = df[col].value_counts().head(5).to_dict()
            info.append(f"\nTop values in '{col}': {json.dumps(top)}")

        # Date range detection
        for col in df.columns:
            if "date" in col.lower() or "time" in col.lower():
                try:
                    parsed = pd.to_datetime(df[col], errors="coerce").dropna()
                    if not parsed.empty:
                        info.append(f"\nDate range in '{col}': {parsed.min().date()} → {parsed.max().date()}")
                except Exception:
                    pass

        # Sample rows
        sample = df.head(SAMPLE_ROWS).to_csv(index=False)
        info.append(f"\nFirst {min(SAMPLE_ROWS, len(df))} rows (CSV):\n{sample}")
        parts.append("\n".join(info))

    return "\n\n---\n\n".join(parts)


# ── Claude analysis ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a senior data analyst. You receive monthly datasets and produce 
a clear, actionable analytics report in Markdown. Your report must include:

1. **Executive summary** (3–5 bullet points of the most important findings)
2. **Key metrics** — headline numbers the reader should care about
3. **Trends & patterns** — what's going up, down, or changing
4. **Anomalies & outliers** — anything surprising or worth investigating
5. **Recommendations** — 3–5 concrete next steps based on the data
6. **Data quality notes** — missing values, inconsistencies, or caveats

Be specific. Reference actual numbers from the data. Avoid vague statements.
Format everything as clean Markdown with headers, bullet points, and tables where helpful."""


def run_analysis(summary: str, month_label: str) -> str:
    """Send data summary to Claude and return the analysis text."""
    client = anthropic.Anthropic()   # reads ANTHROPIC_API_KEY from env

    user_message = f"""Please analyze the following datasets for the monthly report ({month_label}).

{summary}

Produce a comprehensive Markdown analytics report following the structure in your instructions."""

    print(f"\n  Sending data to Claude ({MODEL})...")
    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    return message.content[0].text


# ── Report saving ─────────────────────────────────────────────────────────────

def save_report(analysis: str, reports_dir: str, month_label: str) -> str:
    """Wrap the analysis in a report shell and save it."""
    os.makedirs(reports_dir, exist_ok=True)
    filename = f"analytics_report_{month_label}.md"
    filepath = os.path.join(reports_dir, filename)

    header = f"""# Monthly Analytics Report
**Period:** {month_label}  
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Model:** {MODEL}

---

"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(header + analysis)

    return filepath


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Monthly AI Analytics Bot")
    parser.add_argument("--data-dir", default=DATA_DIR, help="Folder with CSV/Excel files")
    parser.add_argument("--reports-dir", default=REPORTS_DIR, help="Folder to save reports")
    parser.add_argument("--month", default=datetime.now().strftime("%Y-%m"),
                        help="Month label (default: current month, e.g. 2025-05)")
    args = parser.parse_args()

    print(f"\n{'='*50}")
    print(f"  Monthly Analytics Bot — {args.month}")
    print(f"{'='*50}\n")

    # 1. Load data
    print(f"Loading data from '{args.data_dir}'...")
    frames = load_data(args.data_dir)
    if not frames:
        print("No data files found. Add CSV/Excel files to the data directory.")
        return

    # 2. Summarize for Claude
    print("\nBuilding data summary...")
    summary = summarize_dataframes(frames)

    # 3. Run AI analysis
    analysis = run_analysis(summary, args.month)

    # 4. Save report
    report_path = save_report(analysis, args.reports_dir, args.month)
    print(f"\n  ✓ Report saved: {report_path}")
    print(f"\n{'='*50}\n")


if __name__ == "__main__":
    main()
