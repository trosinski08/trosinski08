#!/usr/bin/env python3
"""
Update README with recent GitHub activity
Fetches recent activity from GitHub API and updates README file
"""

import argparse
import os
import re
from datetime import datetime
from typing import Optional

import requests


def get_recent_activity(username: str, token: Optional[str], limit: int = 5) -> list[str]:
    """
    Fetch recent GitHub activity for a user
    
    Args:
        username: GitHub username
        token: GitHub API token (optional, for higher rate limits)
        limit: Number of recent events to fetch
    
    Returns:
        List of formatted activity strings
    """
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"token {token}"
    
    # Fetch user events
    url = f"https://api.github.com/users/{username}/events/public"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        events = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching GitHub activity: {e}")
        return []
    
    activities = []
    
    for event in events[:limit]:
        event_type = event.get("type", "")
        repo_name = event.get("repo", {}).get("name", "")
        created_at = event.get("created_at", "")
        payload = event.get("payload", {})
        
        # Format timestamp
        try:
            date_obj = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            formatted_date = date_obj.strftime("%b %d, %Y")
        except:
            formatted_date = created_at
        
        # Build activity description
        if event_type == "PushEvent":
            commits = payload.get("commits", [])
            commit_count = len(commits)
            activity = f"- **Pushed {commit_count} commit(s)** to [{repo_name}](https://github.com/{repo_name}) on {formatted_date}"
        
        elif event_type == "CreateEvent":
            ref_type = payload.get("ref_type", "repository")
            ref = payload.get("ref", "")
            if ref_type == "repository":
                activity = f"- **Created repository** [{repo_name}](https://github.com/{repo_name}) on {formatted_date}"
            else:
                activity = f"- **Created {ref_type}** `{ref}` in [{repo_name}](https://github.com/{repo_name}) on {formatted_date}"
        
        elif event_type == "PullRequestEvent":
            action = payload.get("action", "")
            pr = payload.get("pull_request", {})
            pr_number = pr.get("number", "")
            pr_title = pr.get("title", "")
            activity = f"- **{action.title()} Pull Request** #{pr_number} - {pr_title} in [{repo_name}](https://github.com/{repo_name}) on {formatted_date}"
        
        elif event_type == "IssuesEvent":
            action = payload.get("action", "")
            issue = payload.get("issue", {})
            issue_number = issue.get("number", "")
            issue_title = issue.get("title", "")
            activity = f"- **{action.title()} Issue** #{issue_number} - {issue_title} in [{repo_name}](https://github.com/{repo_name}) on {formatted_date}"
        
        elif event_type == "ForkEvent":
            activity = f"- **Forked** [{repo_name}](https://github.com/{repo_name}) on {formatted_date}"
        
        elif event_type == "WatchEvent":
            activity = f"- **Starred** [{repo_name}](https://github.com/{repo_name}) on {formatted_date}"
        
        elif event_type == "PullRequestReviewEvent":
            action = payload.get("action", "")
            pr = payload.get("pull_request", {})
            pr_number = pr.get("number", "")
            activity = f"- **Reviewed Pull Request** #{pr_number} in [{repo_name}](https://github.com/{repo_name}) on {formatted_date}"
        
        else:
            activity = f"- **{event_type}** on [{repo_name}](https://github.com/{repo_name}) on {formatted_date}"
        
        activities.append(activity)
    
    return activities


def update_readme(file_path: str, activities: list[str]) -> bool:
    """
    Update README file with recent activity section
    
    Args:
        file_path: Path to README file
        activities: List of activity strings
    
    Returns:
        True if file was updated, False otherwise
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Build activity section
    activity_section = "## 📊 Recent Activity\n\n"
    if activities:
        activity_section += "\n".join(activities)
    else:
        activity_section += "No recent public activity to display."
    
    # Pattern to find and replace recent activity section
    pattern = r"(## 📊 Recent Activity\n\n)(.*?)(?=\n## |\Z)"
    
    if re.search(pattern, content, re.DOTALL):
        # Replace existing section
        new_content = re.sub(
            pattern,
            activity_section + "\n\n",
            content,
            flags=re.DOTALL
        )
    else:
        # Add new section before Contact section or at the end
        contact_pattern = r"(## 📫 Contact)"
        if re.search(contact_pattern, content):
            new_content = re.sub(
                contact_pattern,
                f"{activity_section}\n\n---\n\n\\1",
                content
            )
        else:
            new_content = content.rstrip() + f"\n\n{activity_section}\n"
    
    # Write updated content
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print(f"✅ Updated {file_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Update README with recent GitHub activity")
    parser.add_argument("--user", required=True, help="GitHub username")
    parser.add_argument("--file", required=True, help="Path to README file to update")
    parser.add_argument("--limit", type=int, default=5, help="Number of recent activities to show")
    
    args = parser.parse_args()
    
    # Get GitHub token from environment
    token = os.getenv("GITHUB_TOKEN")
    
    print(f"Fetching recent activity for @{args.user}...")
    activities = get_recent_activity(args.user, token, args.limit)
    
    if activities:
        print(f"Found {len(activities)} recent activities")
    else:
        print("No recent activities found")
    
    # Update README
    update_readme(args.file, activities)


if __name__ == "__main__":
    main()
