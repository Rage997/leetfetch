# leetfetch

**leetfetch** is a command-line Python tool to fetch and organize all your LeetCode submissions and problem descriptions locally.

## Features

- Fetches all submissions using browser session cookies (no password or API token required)
- Filters to include only accepted submissions (default) or all submissions
- Groups submissions by problem and programming language
- Supports all LeetCode languages (e.g., Python, C++, Java, etc.)
- Allows downloading only specific languages with `--languages`, or all with `--all-languages`
- Creates a Markdown README index with problem links, difficulty, and summary
- Sync mode to only download newly solved problems

## Requirements

- Python 3
- Must be logged into LeetCode in your selected browser (for cookie access)
- Supported browsers: Chrome, Firefox, Brave, Edge, Opera

## Installation

Clone the repository:

```bash
git clone https://github.com/Rage997/leetfetch.git
cd leetfetch
```

Install required Python packages:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python3 main.py [options]
```

### Options:

- `--browser chrome|firefox|brave|edge|opera` (default: chrome)
- `--output <path>` (default: `leetcode`)
- `--sync` → Only download new problems
- `--only-accepted/--no-only-accepted` → Include only accepted submissions (default: True)
- `--languages lang1 lang2` → List of languages to include (default: python3)
- `--all-languages` → Include all supported languages

### Examples:

```bash
# Download all accepted Python3 submissions using Chrome cookies
python3 main.py --languages python3

# Download all submissions in all languages using Firefox
python3 main.py --no-only-accepted --browser firefox --all-languages

# Sync and download only newly accepted C++ and Python submissions
python3 main.py --sync --languages cpp python3
```

## Output Structure

```
leetcode/
├── problem-1/
│   ├── README.md
│   ├── solutiontemplate.py
│   └── submissions/
│       └── python3/
│           └── 123456789_Accepted.py
├── problem-2/
│   └── ...
└── README.md  # Summary index
```
