import os
import requests
import browser_cookie3
import argparse
from typing import List, Dict
from bs4 import BeautifulSoup

GRAPHQL_URL = "https://leetcode.com/graphql"

SUPPORTED_BROWSERS = {
    "chrome": browser_cookie3.chrome,
    "firefox": browser_cookie3.firefox,
    "brave": browser_cookie3.brave,
    "edge": browser_cookie3.edge,
    "opera": browser_cookie3.opera
}

def get_session_cookie(browser: str) -> str:
    if browser not in SUPPORTED_BROWSERS:
        raise ValueError(f"Unsupported browser '{browser}'. Choose from: {', '.join(SUPPORTED_BROWSERS)}")
    cookies = SUPPORTED_BROWSERS[browser]()
    for cookie in cookies:
        if cookie.name == 'LEETCODE_SESSION':
            return cookie.value
    raise Exception(f"LEETCODE_SESSION cookie not found in {browser}. Make sure you're logged into LeetCode.")

def graphql_request(query: str, variables: dict, session_token: str) -> dict:
    headers = {
        'Content-Type': 'application/json',
        'Referer': 'https://leetcode.com/problemset/all/',
        'Cookie': f'LEETCODE_SESSION={session_token};'
    }
    payload = {
        "query": query,
        "variables": variables
    }
    response = requests.post(GRAPHQL_URL, json=payload, headers=headers)
    if not response.ok:
        print("GraphQL error:", response.text)
        response.raise_for_status()
    return response.json()

def get_solved_problem_slugs(session_token: str) -> List[str]:
    slugs = set()
    offset = 0
    limit = 20

    while True:
        query = """
        query mySubmissions($offset: Int!, $limit: Int!) {
          submissionList(offset: $offset, limit: $limit) {
            submissions {
              titleSlug
              statusDisplay
            }
            hasNext
          }
        }
        """
        variables = {"offset": offset, "limit": limit}
        data = graphql_request(query, variables, session_token)

        submissions = data["data"]["submissionList"]["submissions"]
        for sub in submissions:
            if sub["statusDisplay"] == "Accepted":
                slugs.add(sub["titleSlug"])

        if not data["data"]["submissionList"]["hasNext"]:
            break

        offset += limit

    return list(slugs)

def get_problem_data(slug: str, session_token: str) -> Dict:
    query = """
    query questionData($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        title
        content
        codeSnippets {
          lang
          code
        }
      }
    }
    """
    variables = {"titleSlug": slug}
    data = graphql_request(query, variables, session_token)
    return data["data"]["question"]

import html2text

def html_to_markdown(html: str) -> str:
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.body_width = 0  # Do not wrap lines
    return h.handle(html)


def save_problem(problem_data: Dict, base_dir: str):
    slug = problem_data["title"].replace(" ", "_")
    target_dir = os.path.join(base_dir, slug)
    os.makedirs(target_dir, exist_ok=True)

    markdown = html_to_markdown(problem_data['content'] or "No description available.")

    with open(os.path.join(target_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(f"# {problem_data['title']}\n\n")
        f.write(markdown)

    for snippet in problem_data.get("codeSnippets", []):
        if snippet["lang"] == "Python3":
            with open(os.path.join(target_dir, "solution.py"), "w", encoding="utf-8") as f:
                f.write(snippet["code"])
            break

def main():
    parser = argparse.ArgumentParser(description="Download accepted LeetCode submissions.")
    parser.add_argument("--username", required=True, help="Your LeetCode username")
    parser.add_argument("--output", default="leetcode", help="Directory to save problems")
    parser.add_argument("--browser", default="chrome", choices=SUPPORTED_BROWSERS.keys(), help="Browser to load cookies from")
    parser.add_argument("--sync", action="store_true", help="Only download new problems not yet in the output folder")

    args = parser.parse_args()

    session_token = get_session_cookie(args.browser)
    print("Fetching solved problem slugs...")
    slugs = get_solved_problem_slugs(session_token)
    print(f"Found {len(slugs)} solved problems.")

    if args.sync:
        existing = set(os.listdir(args.output)) if os.path.exists(args.output) else set()
        slugs = [slug for slug in slugs if slug.replace("-", "_") not in existing]
        print(f"{len(slugs)} new problems to download (sync mode).")

    for slug in slugs:
        print(f"Processing {slug}...")
        problem_data = get_problem_data(slug, session_token)
        save_problem(problem_data, args.output)

    print("Done.")

if __name__ == "__main__":
    main()
