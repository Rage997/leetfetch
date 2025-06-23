import os
import requests
import browser_cookie3
import argparse
from typing import List, Dict
import html2text

GRAPHQL_URL = "https://leetcode.com/graphql"

SUPPORTED_BROWSERS = {
    "chrome": browser_cookie3.chrome,
    "firefox": browser_cookie3.firefox,
    "brave": browser_cookie3.brave,
    "edge": browser_cookie3.edge,
    "opera": browser_cookie3.opera
}

EXT_MAP = {"python": "py", "python3": "py", "cpp": "cpp"}

def get_session_cookie(browser: str) -> str:
    if browser not in SUPPORTED_BROWSERS:
        raise ValueError(f"Unsupported browser '{browser}'. Choose from: {', '.join(SUPPORTED_BROWSERS)}")
    cookies = SUPPORTED_BROWSERS[browser]()
    for c in cookies:
        if c.name == 'LEETCODE_SESSION':
            return c.value
    raise RuntimeError(f"LEETCODE_SESSION cookie not found in {browser}.")

def graphql_request(query: str, variables: dict, session_token: str) -> dict:
    r = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables},
        headers={
            "Content-Type": "application/json",
            "Cookie": f"LEETCODE_SESSION={session_token};",
            "Referer": "https://leetcode.com/problemset/all/"
        }
    )
    if not r.ok:
        print("GraphQL error:", r.text)
        r.raise_for_status()
    return r.json()

def get_all_submissions(session_token: str) -> List[Dict]:
    subs = []
    offset = 0
    limit = 20

    while True:
        data = graphql_request(
            """
            query subs($offset: Int!, $limit: Int!) {
              submissionList(offset: $offset, limit: $limit) {
                submissions {
                  id titleSlug lang statusDisplay timestamp
                }
                hasNext
              }
            }
            """,
            {"offset": offset, "limit": limit},
            session_token
        )
        s = data["data"]["submissionList"]
        subs.extend(s["submissions"])
        if not s["hasNext"]:
            break
        offset += limit
    return subs

def get_submission_code(submission_id: int, session_token: str) -> str:
    data = graphql_request(
        """
        query details($submissionId: Int!) {
          submissionDetails(submissionId: $submissionId) {
            code
          }
        }
        """,
        {"submissionId": submission_id},
        session_token
    )
    return data["data"]["submissionDetails"]["code"]

def html_to_md(html: str) -> str:
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.body_width = 0
    return h.handle(html)

def get_problem_data(slug, session_token):
    q = """
    query q($slug: String!) {
      question(titleSlug: $slug) {
        title content difficulty codeSnippets { lang code }
      }
    }"""
    return graphql_request(q, {"slug": slug}, session_token)["data"]["question"]

def save_problem(slug: str, problem_data: dict, submissions: List[dict], base_dir: str, session_token: str):
    title = problem_data["title"]
    problem_dir = os.path.join(base_dir, slug)
    os.makedirs(os.path.join(problem_dir, "submissions"), exist_ok=True)

    with open(os.path.join(problem_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n{html_to_md(problem_data.get('content',''))}")

    for snippet in problem_data.get("codeSnippets", []):
        if snippet["lang"] == "Python3":
            p = os.path.join(problem_dir, "solutiontemplate.py")
            with open(p, "w", encoding="utf-8") as f:
                f.write(snippet["code"])
            break

    for sub in submissions:
        lang = sub["lang"].lower()
        ext = EXT_MAP.get(lang, lang)
        lang_dir = os.path.join(problem_dir, "submissions", lang)
        os.makedirs(lang_dir, exist_ok=True)

        code = get_submission_code(int(sub["id"]), session_token)
        timestamp = sub["timestamp"]
        status = sub["statusDisplay"].replace(" ", "_")
        filename = f"{timestamp}_{status}.{ext}"
        path = os.path.join(lang_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)

def write_root_readme(output: str, summary: List[Dict]):
    summary_path = os.path.join(output, "README.md")
    total = len(summary)
    count = {"Easy": 0, "Medium": 0, "Hard": 0}
    for item in summary:
        count[item["difficulty"]] += 1

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("""leetcode
========
""")
        f.write(f"#### Total solved: {total} (Easy: {count['Easy']} Medium: {count['Medium']} Hard: {count['Hard']})\n")
        f.write("My Python solutions of [leetcode](https://leetcode.com/problemset/all/)\n\n")
        f.write("| No | Title | Source Code | Difficulty |\n")
        f.write("|----|-------|-------------|------------|\n")
        for i, item in enumerate(sorted(summary, key=lambda x: x["title"])):
            slug = item["slug"]
            title = item["title"]
            diff = item["difficulty"]
            url = f"./{slug}"
            f.write(f"| {i+1} | {title} | [Python]({url}) | {diff} |\n")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--browser", default="chrome", choices=SUPPORTED_BROWSERS)
    p.add_argument("--output", default="leetcode")
    p.add_argument("--sync", action="store_true")
    p.add_argument("--only-accepted", action=argparse.BooleanOptionalAction, default=True,
                   help="Only include accepted submissions (default: True)")
    args = p.parse_args()

    token = get_session_cookie(args.browser)
    all_subs = get_all_submissions(token)
    by_slug = {}

    for s in all_subs:
        if args.only_accepted and s["statusDisplay"] != "Accepted":
            continue
        by_slug.setdefault(s["titleSlug"], []).append(s)

    slugs = list(by_slug.keys())
    if args.sync and os.path.exists(args.output):
        existing = set(os.listdir(args.output))
        slugs = [s for s in slugs if s not in existing]
    print(f"Processing {len(slugs)} problems…")

    total_submissions_written = 0
    total_problems = len(slugs)
    summary = []

    for slug in slugs:
        try:
            pd = get_problem_data(slug, token)
            subs = by_slug[slug]
            save_problem(slug, pd, subs, args.output, token)
            total_submissions_written += len(subs)
            summary.append({"slug": slug, "title": pd["title"], "difficulty": pd["difficulty"]})
        except Exception as e:
            print(f"❌ {slug}: {e}")

    write_root_readme(args.output, summary)

    print(f"\n✅ Finished. {total_problems} problems saved.")
    print(f"📝 Total submissions downloaded: {total_submissions_written}")

if __name__ == "__main__":
    main()
