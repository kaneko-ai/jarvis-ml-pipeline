"""JARVIS Integrations Module - Phase 3 Features (21-30)"""

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime


# ============================================
# 21. SLACK INTEGRATION
# ============================================
@dataclass
class SlackConfig:
    """Slack configuration."""

    webhook_url: str
    channel: str = "#jarvis-alerts"
    username: str = "JARVIS Bot"
    icon_emoji: str = ":robot_face:"


class SlackNotifier:
    """Send notifications to Slack."""

    def __init__(self, config: SlackConfig):
        self.config = config

    def send_message(self, text: str, attachments: list[dict] | None = None) -> bool:
        """Send a message to Slack.

        Args:
            text: Message text
            attachments: Optional rich attachments

        Returns:
            True if successful
        """
        payload = {
            "text": text,
            "username": self.config.username,
            "icon_emoji": self.config.icon_emoji,
            "channel": self.config.channel,
        }

        if attachments:
            payload["attachments"] = attachments

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.config.webhook_url, data=data, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(
                req, timeout=10
            ) as response:  # nosec B310: trusted Slack webhook URL
                return response.status == 200
        except Exception as e:
            print(f"Slack error: {e}")
            return False

    def send_paper_alert(self, papers: list[dict]) -> bool:
        """Send paper alert to Slack.

        Args:
            papers: List of paper dictionaries

        Returns:
            True if successful
        """
        if not papers:
            return False

        attachments = [
            {
                "color": "#a78bfa",
                "title": f"📄 {p.get('title', 'Unknown')}",
                "text": f"{p.get('authors', 'Unknown')} • {p.get('journal', 'Unknown')}",
                "footer": f"PMID: {p.get('pmid', 'N/A')}",
                "ts": int(datetime.now().timestamp()),
            }
            for p in papers[:5]
        ]

        return self.send_message(f"🔬 JARVIS found {len(papers)} new papers!", attachments)


# ============================================
# 22. NOTION INTEGRATION
# ============================================
@dataclass
class NotionConfig:
    """Notion configuration."""

    api_key: str
    database_id: str


class NotionSync:
    """Sync data with Notion."""

    BASE_URL = "https://api.notion.com/v1"

    def __init__(self, config: NotionConfig):
        self.config = config

    def _make_request(
        self, endpoint: str, method: str = "GET", data: dict | None = None
    ) -> dict | None:
        """Make Notion API request."""
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

        try:
            req = urllib.request.Request(url, headers=headers, method=method)
            if data:
                req.data = json.dumps(data).encode("utf-8")

            with urllib.request.urlopen(
                req, timeout=10
            ) as response:  # nosec B310: trusted Notion API
                return json.loads(response.read().decode())
        except Exception as e:
            print(f"Notion error: {e}")
            return None

    def add_paper(self, paper: dict) -> bool:
        """Add a paper to Notion database.

        Args:
            paper: Paper dictionary

        Returns:
            True if successful
        """
        data = {
            "parent": {"database_id": self.config.database_id},
            "properties": {
                "Title": {"title": [{"text": {"content": paper.get("title", "")}}]},
                "PMID": {"rich_text": [{"text": {"content": paper.get("pmid", "")}}]},
                "Authors": {"rich_text": [{"text": {"content": paper.get("authors", "")}}]},
                "Journal": {"select": {"name": paper.get("journal", "Unknown")}},
                "Year": {"number": int(paper.get("year", 2024))},
                "Status": {"select": {"name": "To Read"}},
            },
        }

        result = self._make_request("pages", method="POST", data=data)
        return result is not None


# ============================================
# 28. ORCID INTEGRATION
# ============================================
class ORCIDClient:
    """ORCID API client for author profiles."""

    BASE_URL = "https://pub.orcid.org/v3.0"

    def get_author(self, orcid_id: str) -> dict | None:
        """Get author profile by ORCID ID.

        Args:
            orcid_id: ORCID identifier (e.g., 0000-0001-2345-6789)

        Returns:
            Author profile dictionary
        """
        url = f"{self.BASE_URL}/{orcid_id}/person"
        headers = {"Accept": "application/json"}

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(
                req, timeout=10
            ) as response:  # nosec B310: trusted ORCID API
                data = json.loads(response.read().decode())
                return {
                    "orcid": orcid_id,
                    "name": data.get("name", {}).get("given-names", {}).get("value", ""),
                    "family_name": data.get("name", {}).get("family-name", {}).get("value", ""),
                    "biography": data.get("biography", {}).get("content", ""),
                }
        except Exception as e:
            print(f"ORCID error: {e}")
            return None


# ============================================
# 29. ARXIV INTEGRATION
# ============================================
class ArXivClient:
    """arXiv API client for preprints."""

    BASE_URL = "http://export.arxiv.org/api/query"

    def search(self, query: str, max_results: int = 10) -> list[dict]:
        """Search arXiv for papers.

        Args:
            query: Search query
            max_results: Maximum results

        Returns:
            List of paper dictionaries
        """
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"

        try:
            with urllib.request.urlopen(
                url, timeout=10
            ) as response:  # nosec B310: trusted arXiv API URL
                # Parse XML response (simplified)
                content = response.read().decode()
                # In real implementation, use xml.etree.ElementTree
                return self._parse_response(content)
        except Exception as e:
            print(f"arXiv error: {e}")
            return []

    def _parse_response(self, xml_content: str) -> list[dict]:
        """Parse arXiv XML response (simplified)."""
        # Simplified parsing - in production use proper XML parser
        import re

        papers = []
        entries = re.findall(r"<entry>(.*?)</entry>", xml_content, re.DOTALL)

        for entry in entries[:10]:
            title_match = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
            id_match = re.search(r"<id>(.*?)</id>", entry)
            summary_match = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)

            papers.append(
                {
                    "title": title_match.group(1).strip() if title_match else "Unknown",
                    "arxiv_id": id_match.group(1).split("/")[-1] if id_match else "",
                    "abstract": summary_match.group(1).strip()[:200] if summary_match else "",
                    "source": "arXiv",
                }
            )

        return papers


# ============================================
# 30. SEMANTIC SCHOLAR INTEGRATION
# ============================================
class SemanticScholarClient:
    """Semantic Scholar API client."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """Search Semantic Scholar.

        Args:
            query: Search query
            limit: Result limit

        Returns:
            List of paper dictionaries
        """
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,authors,year,citationCount,abstract",
        }

        url = f"{self.BASE_URL}/paper/search?{urllib.parse.urlencode(params)}"
        headers = {"Accept": "application/json"}

        if self.api_key:
            headers["x-api-key"] = self.api_key

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(
                req, timeout=10
            ) as response:  # nosec B310: trusted Semantic Scholar API
                data = json.loads(response.read().decode())
                return [
                    {
                        "paper_id": p.get("paperId", ""),
                        "title": p.get("title", ""),
                        "authors": ", ".join([a.get("name", "") for a in p.get("authors", [])[:3]]),
                        "year": p.get("year"),
                        "citations": p.get("citationCount", 0),
                        "abstract": p.get("abstract", "")[:200] if p.get("abstract") else "",
                    }
                    for p in data.get("data", [])
                ]
        except Exception as e:
            print(f"Semantic Scholar error: {e}")
            return []

    def get_paper(self, paper_id: str) -> dict | None:
        """Get paper details by ID.

        Args:
            paper_id: Semantic Scholar paper ID

        Returns:
            Paper details dictionary
        """
        url = f"{self.BASE_URL}/paper/{paper_id}?fields=title,authors,year,abstract,citationCount,references"

        try:
            with urllib.request.urlopen(
                url, timeout=10
            ) as response:  # nosec B310: trusted Semantic Scholar API
                return json.loads(response.read().decode())
        except Exception as e:
            print(f"Semantic Scholar error: {e}")
            return None


# ============================================
# 25. GITHUB ISSUES INTEGRATION
# ============================================
class GitHubIssueCreator:
    """Create GitHub issues from papers."""

    def __init__(self, token: str, owner: str, repo: str):
        self.token = token
        self.owner = owner
        self.repo = repo

    def create_issue(self, title: str, body: str, labels: list[str] | None = None) -> str | None:
        """Create a GitHub issue.

        Args:
            title: Issue title
            body: Issue body
            labels: Optional labels

        Returns:
            Issue URL if successful
        """
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/issues"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

        data = {"title": title, "body": body}
        if labels:
            data["labels"] = labels

        try:
            req = urllib.request.Request(
                url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST"
            )
            with urllib.request.urlopen(
                req, timeout=10
            ) as response:  # nosec B310: trusted GitHub API
                result = json.loads(response.read().decode())
                return result.get("html_url")
        except Exception as e:
            print(f"GitHub error: {e}")
            return None

    def create_paper_issue(self, paper: dict) -> str | None:
        """Create issue from paper.

        Args:
            paper: Paper dictionary

        Returns:
            Issue URL
        """
        title = f"📄 Review: {paper.get('title', 'Unknown Paper')}"
        body = f"""## Paper Details

**Title:** {paper.get('title', 'N/A')}
**Authors:** {paper.get('authors', 'N/A')}
**Year:** {paper.get('year', 'N/A')}
**PMID:** {paper.get('pmid', 'N/A')}

## Abstract
{paper.get('abstract', 'No abstract available.')}

---
*Created by JARVIS Research OS*
"""
        return self.create_issue(title, body, labels=["paper", "review"])


# ============================================
# FACTORY FUNCTIONS
# ============================================


def get_slack_notifier(webhook_url: str, channel: str = "#jarvis") -> SlackNotifier:
    """Get Slack notifier instance."""
    return SlackNotifier(SlackConfig(webhook_url=webhook_url, channel=channel))


def get_arxiv_client() -> ArXivClient:
    """Get arXiv client instance."""
    return ArXivClient()


def get_semantic_scholar_client(api_key: str | None = None) -> SemanticScholarClient:
    """Get Semantic Scholar client instance."""
    return SemanticScholarClient(api_key)


if __name__ == "__main__":
    # Demo
    print("Testing arXiv client...")
    arxiv = ArXivClient()
    papers = arxiv.search("machine learning", max_results=3)
    for p in papers:
        print(f"  - {p['title'][:60]}...")

    print("\nTesting Semantic Scholar client...")
    ss = SemanticScholarClient()
    papers = ss.search("COVID-19 treatment", limit=3)
    for p in papers:
        print(f"  - {p['title'][:60]}... ({p['citations']} citations)")
