#!/usr/bin/env python3
"""
Update README with recently pushed GitHub repositories.
Uses /users/{user}/repos?sort=pushed — reliable, no latency, no weird event types.
"""

import argparse
import os
import re
from datetime import datetime, timezone
from typing import Optional

import requests


SECTION_HEADER = "## 📊 Recent Activity"


def get_recent_repos(
    username: str,
    token: Optional[str],
    limit: int = 6,
) -> list[dict]:
    """
    Fetch public repos sorted by last push, return simplified dicts.
    Excludes forks and archived repos (configurable).
    """
    headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"https://api.github.com/users/{username}/repos"
    params = {"sort": "pushed", "direction": "desc", "per_page": 30, "type": "public"}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        repos = response.json()
    except requests.exceptions.RequestException as exc:
        print(f"Error fetching repos: {exc}")
        return []

    results = []
    for repo in repos:
        if repo.get("fork") or repo.get("archived"):
            continue
        pushed_raw = repo.get("pushed_at") or ""
        try:
            dt = datetime.fromisoformat(pushed_raw.replace("Z", "+00:00"))
            pushed = dt.strftime("%b %Y")
        except ValueError:
            pushed = pushed_raw[:7]

        results.append({
            "name": repo["name"],
            "url": repo["html_url"],
            "description": repo.get("description") or "",
            "pushed": pushed,
        })
        if len(results) >= limit:
            break

    return results


def build_section(repos: list[dict]) -> str:
    """Render repos as a Markdown table."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        SECTION_HEADER,
        "",
        f"*Auto-updated {now}*",
        "",
        "| Repository | Description | Last push |",
        "|---|---|---|",
    ]
    for r in repos:
        desc = r["description"].replace("|", "\\|")[:80]
        lines.append(f"| [{r['name']}]({r['url']}) | {desc} | {r['pushed']} |")

    if not repos:
        lines.append("| — | No public repositories found | — |")

    return "\n".join(lines)


def update_readme(file_path: str, repos: list[dict]) -> bool:
    """Replace the Recent Activity section in-place."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    new_section = build_section(repos)

    # Replace existing section (everything up to the next ## heading or EOF)
    pattern = rf"({re.escape(SECTION_HEADER)}\n)(.*?)(?=\n## |\Z)"

    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(
            pattern,
            new_section + "\n\n",
            content,
            flags=re.DOTALL,
        )
    else:
        # Insert before Contact section, or append
        contact_pattern = r"(## 📫 Contact)"
        if re.search(contact_pattern, content):
            new_content = re.sub(
                contact_pattern,
                f"{new_section}\n\n---\n\n\\1",
                content,
            )
        else:
            new_content = content.rstrip() + f"\n\n{new_section}\n"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ Updated {file_path} with {len(repos)} repos")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Update README Recent Activity from GitHub repos API"
    )
    parser.add_argument("--user", required=True, help="GitHub username")
    parser.add_argument("--file", required=True, help="Path to README.md")
    parser.add_argument("--limit", type=int, default=6, help="Max repos to show")
    args = parser.parse_args()

    token = os.getenv("GITHUB_TOKEN")
    print(f"Fetching recent repos for @{args.user}...")
    repos = get_recent_repos(args.user, token, args.limit)
    print(f"Found {len(repos)} repos")
    update_readme(args.file, repos)


if __name__ == "__main__":
    main()
