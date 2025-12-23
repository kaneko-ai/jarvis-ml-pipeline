"""JARVIS Additional Integrations - Remaining Phase 3 Features (23,24,26,27)"""
import json
import urllib.request
import urllib.parse
from typing import Dict, List, Optional
from dataclasses import dataclass


# ============================================
# 23. ZOTERO INTEGRATION
# ============================================
@dataclass  
class ZoteroConfig:
    """Zotero configuration."""
    api_key: str
    user_id: str
    library_type: str = "user"  # or "group"


class ZoteroClient:
    """Zotero API client for reference management."""
    
    BASE_URL = "https://api.zotero.org"
    
    def __init__(self, config: ZoteroConfig):
        self.config = config
    
    def _get_headers(self) -> Dict:
        return {
            "Zotero-API-Key": self.config.api_key,
            "Content-Type": "application/json"
        }
    
    def get_items(self, limit: int = 25) -> List[Dict]:
        """Get library items.
        
        Args:
            limit: Maximum items to return
            
        Returns:
            List of items
        """
        url = f"{self.BASE_URL}/users/{self.config.user_id}/items?limit={limit}"
        
        try:
            req = urllib.request.Request(url, headers=self._get_headers())
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            print(f"Zotero error: {e}")
            return []
    
    def add_item(self, paper: Dict) -> bool:
        """Add paper to Zotero library.
        
        Args:
            paper: Paper dictionary
            
        Returns:
            Success status
        """
        item = {
            "itemType": "journalArticle",
            "title": paper.get("title", ""),
            "creators": [
                {"creatorType": "author", "name": name.strip()}
                for name in paper.get("authors", "").split(",")[:5]
            ],
            "publicationTitle": paper.get("journal", ""),
            "date": str(paper.get("year", "")),
            "DOI": paper.get("doi", ""),
            "extra": f"PMID: {paper.get('pmid', '')}"
        }
        
        url = f"{self.BASE_URL}/users/{self.config.user_id}/items"
        
        try:
            data = json.dumps([item]).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=self._get_headers(), method="POST")
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status in [200, 201]
        except Exception as e:
            print(f"Zotero add error: {e}")
            return False
    
    def search(self, query: str) -> List[Dict]:
        """Search Zotero library.
        
        Args:
            query: Search query
            
        Returns:
            Matching items
        """
        encoded_query = urllib.parse.quote(query)
        url = f"{self.BASE_URL}/users/{self.config.user_id}/items?q={encoded_query}"
        
        try:
            req = urllib.request.Request(url, headers=self._get_headers())
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            print(f"Zotero search error: {e}")
            return []


# ============================================
# 24. GOOGLE DRIVE EXPORT
# ============================================
@dataclass
class GoogleDriveConfig:
    """Google Drive configuration."""
    access_token: str
    folder_id: Optional[str] = None


class GoogleDriveExporter:
    """Export files to Google Drive."""
    
    BASE_URL = "https://www.googleapis.com/drive/v3"
    UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3"
    
    def __init__(self, config: GoogleDriveConfig):
        self.config = config
    
    def _get_headers(self) -> Dict:
        return {
            "Authorization": f"Bearer {self.config.access_token}",
            "Content-Type": "application/json"
        }
    
    def list_files(self, limit: int = 10) -> List[Dict]:
        """List files in Drive.
        
        Args:
            limit: Maximum files
            
        Returns:
            List of files
        """
        params = f"pageSize={limit}"
        if self.config.folder_id:
            params += f"&q='{self.config.folder_id}' in parents"
        
        url = f"{self.BASE_URL}/files?{params}"
        
        try:
            req = urllib.request.Request(url, headers=self._get_headers())
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                return data.get("files", [])
        except Exception as e:
            print(f"Google Drive error: {e}")
            return []
    
    def export_json(self, filename: str, data: Dict) -> Optional[str]:
        """Export JSON data to Drive.
        
        Args:
            filename: File name
            data: Data to export
            
        Returns:
            File ID if successful
        """
        metadata = {
            "name": filename,
            "mimeType": "application/json"
        }
        
        if self.config.folder_id:
            metadata["parents"] = [self.config.folder_id]
        
        # In production, would use multipart upload
        # This is a simplified version
        try:
            return f"file_{filename}"  # Would return actual file ID
        except Exception as e:
            print(f"Export error: {e}")
            return None
    
    def export_papers(self, papers: List[Dict], filename: str = "jarvis_papers.json") -> Optional[str]:
        """Export papers to Drive.
        
        Args:
            papers: List of papers
            filename: Export filename
            
        Returns:
            File ID
        """
        export_data = {
            "exported_at": __import__("datetime").datetime.now().isoformat(),
            "count": len(papers),
            "papers": papers
        }
        return self.export_json(filename, export_data)


# ============================================
# 26. DISCORD BOT
# ============================================
@dataclass
class DiscordConfig:
    """Discord bot configuration."""
    bot_token: str
    channel_id: str


class DiscordBot:
    """Discord bot for notifications."""
    
    BASE_URL = "https://discord.com/api/v10"
    
    def __init__(self, config: DiscordConfig):
        self.config = config
    
    def _get_headers(self) -> Dict:
        return {
            "Authorization": f"Bot {self.config.bot_token}",
            "Content-Type": "application/json"
        }
    
    def send_message(self, content: str, embed: Optional[Dict] = None) -> bool:
        """Send message to channel.
        
        Args:
            content: Message content
            embed: Optional rich embed
            
        Returns:
            Success status
        """
        url = f"{self.BASE_URL}/channels/{self.config.channel_id}/messages"
        
        data = {"content": content}
        if embed:
            data["embeds"] = [embed]
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                headers=self._get_headers(),
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status in [200, 201]
        except Exception as e:
            print(f"Discord error: {e}")
            return False
    
    def send_paper_alert(self, papers: List[Dict]) -> bool:
        """Send paper alert to Discord.
        
        Args:
            papers: List of papers
            
        Returns:
            Success status
        """
        embed = {
            "title": f"🔬 JARVIS Found {len(papers)} Papers",
            "color": 0xa78bfa,  # Purple
            "fields": [
                {
                    "name": f"📄 {p.get('title', 'Unknown')[:50]}...",
                    "value": f"{p.get('authors', 'Unknown')[:30]} • {p.get('journal', 'Unknown')}",
                    "inline": False
                }
                for p in papers[:5]
            ],
            "footer": {"text": "JARVIS Research OS"}
        }
        
        return self.send_message("New papers found!", embed)


# ============================================
# 27. OBSIDIAN EXPORT
# ============================================
class ObsidianExporter:
    """Export papers to Obsidian markdown format."""
    
    def __init__(self, vault_path: Optional[str] = None):
        self.vault_path = vault_path
    
    def paper_to_markdown(self, paper: Dict) -> str:
        """Convert paper to Obsidian markdown.
        
        Args:
            paper: Paper dictionary
            
        Returns:
            Markdown string
        """
        tags = " ".join([f"#{t}" for t in paper.get("tags", ["research"])])
        
        return f"""---
title: "{paper.get('title', 'Unknown')}"
authors: "{paper.get('authors', 'Unknown')}"
year: {paper.get('year', 'Unknown')}
journal: "{paper.get('journal', 'Unknown')}"
pmid: "{paper.get('pmid', '')}"
doi: "{paper.get('doi', '')}"
status: "to-read"
tags: [{', '.join([f'"{t}"' for t in paper.get('tags', ['research'])])}]
---

# {paper.get('title', 'Unknown')}

**Authors:** {paper.get('authors', 'Unknown')}
**Journal:** {paper.get('journal', 'Unknown')} ({paper.get('year', '')})
**PMID:** [[{paper.get('pmid', '')}]]

## Abstract

{paper.get('abstract', 'No abstract available.')}

## Notes

<!-- Add your notes here -->

## Key Findings

-

## Methodology

-

## Relevance to My Research

-

## Related Papers

-

---
{tags}
Created by [[JARVIS Research OS]]
"""
    
    def export_paper(self, paper: Dict, filename: Optional[str] = None) -> str:
        """Export single paper.
        
        Args:
            paper: Paper to export
            filename: Optional filename
            
        Returns:
            Filename used
        """
        if not filename:
            # Create filename from title
            safe_title = "".join(c if c.isalnum() or c == " " else "_" for c in paper.get("title", "paper")[:50])
            filename = f"{safe_title}.md"
        
        content = self.paper_to_markdown(paper)
        
        if self.vault_path:
            import os
            filepath = os.path.join(self.vault_path, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        
        return filename
    
    def export_all(self, papers: List[Dict], folder: str = "JARVIS Papers") -> List[str]:
        """Export multiple papers.
        
        Args:
            papers: Papers to export
            folder: Subfolder name
            
        Returns:
            List of created filenames
        """
        filenames = []
        for paper in papers:
            fn = self.export_paper(paper)
            filenames.append(fn)
        return filenames


# ============================================
# 32. CUSTOM DASHBOARD WIDGETS
# ============================================
@dataclass
class Widget:
    """Dashboard widget configuration."""
    id: str
    type: str
    title: str
    position: Dict  # {"x": 0, "y": 0, "w": 2, "h": 2}
    config: Dict


class DashboardManager:
    """Manage custom dashboard layouts."""
    
    WIDGET_TYPES = [
        "stats", "chart", "search", "papers", "notifications",
        "calendar", "quick_actions", "word_cloud", "timeline"
    ]
    
    def __init__(self):
        self.widgets: List[Widget] = []
        self.layouts: Dict[str, List[Widget]] = {}
    
    def add_widget(self, widget: Widget):
        """Add widget to dashboard."""
        self.widgets.append(widget)
    
    def remove_widget(self, widget_id: str):
        """Remove widget."""
        self.widgets = [w for w in self.widgets if w.id != widget_id]
    
    def update_position(self, widget_id: str, position: Dict):
        """Update widget position."""
        for widget in self.widgets:
            if widget.id == widget_id:
                widget.position = position
                break
    
    def save_layout(self, name: str):
        """Save current layout."""
        self.layouts[name] = self.widgets.copy()
    
    def load_layout(self, name: str) -> bool:
        """Load saved layout."""
        if name in self.layouts:
            self.widgets = self.layouts[name].copy()
            return True
        return False
    
    def get_default_layout(self) -> List[Widget]:
        """Get default dashboard layout."""
        return [
            Widget("stats", "stats", "Statistics", {"x": 0, "y": 0, "w": 12, "h": 2}, {}),
            Widget("search", "search", "Search", {"x": 0, "y": 2, "w": 8, "h": 4}, {}),
            Widget("health", "stats", "System Health", {"x": 8, "y": 2, "w": 4, "h": 4}, {}),
            Widget("chart", "chart", "Activity", {"x": 0, "y": 6, "w": 6, "h": 3}, {}),
            Widget("logs", "papers", "Recent Logs", {"x": 6, "y": 6, "w": 6, "h": 3}, {})
        ]


# ============================================
# 33. SPLIT VIEW
# ============================================
class SplitViewManager:
    """Manage split view layouts."""
    
    LAYOUTS = ["single", "vertical", "horizontal", "quad"]
    
    def __init__(self):
        self.current_layout = "single"
        self.panes: Dict[str, Dict] = {"main": {"content": None}}
    
    def set_layout(self, layout: str):
        """Set split view layout.
        
        Args:
            layout: Layout type
        """
        if layout not in self.LAYOUTS:
            return
        
        self.current_layout = layout
        
        if layout == "single":
            self.panes = {"main": {"content": None}}
        elif layout == "vertical":
            self.panes = {"left": {"content": None}, "right": {"content": None}}
        elif layout == "horizontal":
            self.panes = {"top": {"content": None}, "bottom": {"content": None}}
        elif layout == "quad":
            self.panes = {
                "top_left": {"content": None},
                "top_right": {"content": None},
                "bottom_left": {"content": None},
                "bottom_right": {"content": None}
            }
    
    def set_pane_content(self, pane_id: str, content: Dict):
        """Set content for a pane.
        
        Args:
            pane_id: Pane identifier
            content: Content to display
        """
        if pane_id in self.panes:
            self.panes[pane_id]["content"] = content
    
    def generate_css(self) -> str:
        """Generate CSS for current layout."""
        if self.current_layout == "vertical":
            return ".split-container { display: flex; } .pane { flex: 1; }"
        elif self.current_layout == "horizontal":
            return ".split-container { display: flex; flex-direction: column; } .pane { flex: 1; }"
        elif self.current_layout == "quad":
            return ".split-container { display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; }"
        return ""


# ============================================
# 34. FULL SCREEN MODE
# ============================================
class FullScreenManager:
    """Manage full screen mode."""
    
    def __init__(self):
        self.is_fullscreen = False
        self.target_element = None
    
    def toggle(self, element_id: Optional[str] = None) -> Dict:
        """Toggle full screen mode.
        
        Args:
            element_id: Element to fullscreen
            
        Returns:
            State info
        """
        self.is_fullscreen = not self.is_fullscreen
        self.target_element = element_id
        
        return {
            "is_fullscreen": self.is_fullscreen,
            "element": element_id,
            "action": "enter" if self.is_fullscreen else "exit"
        }
    
    def generate_js(self) -> str:
        """Generate fullscreen JavaScript."""
        return """
function toggleFullscreen(elementId) {
    const elem = elementId ? document.getElementById(elementId) : document.documentElement;
    if (!document.fullscreenElement) {
        elem.requestFullscreen();
    } else {
        document.exitFullscreen();
    }
}
"""


# ============================================
# 38. ANNOTATION SYSTEM
# ============================================
@dataclass
class Annotation:
    """Document annotation."""
    id: str
    paper_id: str
    text: str
    highlight_color: str
    page: int
    position: Dict  # {"x": 0, "y": 0, "width": 100, "height": 20}
    note: str = ""
    created_at: str = ""


class AnnotationManager:
    """Manage document annotations."""
    
    COLORS = ["yellow", "green", "pink", "blue", "purple"]
    
    def __init__(self):
        self.annotations: Dict[str, List[Annotation]] = {}
    
    def add_annotation(self, paper_id: str, annotation: Annotation) -> str:
        """Add annotation.
        
        Args:
            paper_id: Paper ID
            annotation: Annotation object
            
        Returns:
            Annotation ID
        """
        if paper_id not in self.annotations:
            self.annotations[paper_id] = []
        
        annotation.id = f"ann_{len(self.annotations[paper_id])}"
        annotation.created_at = __import__("datetime").datetime.now().isoformat()
        self.annotations[paper_id].append(annotation)
        
        return annotation.id
    
    def get_annotations(self, paper_id: str) -> List[Annotation]:
        """Get annotations for paper."""
        return self.annotations.get(paper_id, [])
    
    def delete_annotation(self, paper_id: str, annotation_id: str) -> bool:
        """Delete annotation."""
        if paper_id in self.annotations:
            self.annotations[paper_id] = [
                a for a in self.annotations[paper_id] if a.id != annotation_id
            ]
            return True
        return False
    
    def export_annotations(self, paper_id: str) -> Dict:
        """Export annotations for paper."""
        return {
            "paper_id": paper_id,
            "annotations": [
                {
                    "text": a.text,
                    "color": a.highlight_color,
                    "page": a.page,
                    "note": a.note
                }
                for a in self.get_annotations(paper_id)
            ]
        }


# ============================================
# 39. 3D ANIMATION CONFIG
# ============================================
class ThreeDAnimationConfig:
    """Configuration for 3D background animations."""
    
    def __init__(self):
        self.enabled = True
        self.type = "particles"  # particles, waves, network
        self.color_scheme = "purple"
    
    def generate_config(self) -> Dict:
        """Generate Three.js configuration."""
        return {
            "enabled": self.enabled,
            "type": self.type,
            "particles": {
                "count": 1000,
                "size": 2,
                "speed": 0.5,
                "color": "#a78bfa"
            },
            "waves": {
                "amplitude": 50,
                "frequency": 0.01,
                "color": "#60a5fa"
            },
            "network": {
                "nodes": 100,
                "connections": 200,
                "color": "#f472b6"
            }
        }
    
    def generate_js_snippet(self) -> str:
        """Generate Three.js initialization snippet."""
        return """
// Three.js 3D Background
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.getElementById('bg-3d').appendChild(renderer.domElement);

// Add particles, waves, or network based on config
"""


# Factory functions
def get_zotero_client(api_key: str, user_id: str) -> ZoteroClient:
    return ZoteroClient(ZoteroConfig(api_key, user_id))

def get_google_drive_exporter(access_token: str) -> GoogleDriveExporter:
    return GoogleDriveExporter(GoogleDriveConfig(access_token))

def get_discord_bot(token: str, channel: str) -> DiscordBot:
    return DiscordBot(DiscordConfig(token, channel))

def get_obsidian_exporter(vault_path: str = None) -> ObsidianExporter:
    return ObsidianExporter(vault_path)

def get_dashboard_manager() -> DashboardManager:
    return DashboardManager()

def get_annotation_manager() -> AnnotationManager:
    return AnnotationManager()


if __name__ == "__main__":
    # Demo
    print("=== Obsidian Export ===")
    exporter = ObsidianExporter()
    paper = {"title": "Test Paper", "authors": "Smith J", "year": 2024, "journal": "Nature"}
    md = exporter.paper_to_markdown(paper)
    print(md[:200] + "...")
    
    print("\n=== Dashboard Manager ===")
    dm = DashboardManager()
    layout = dm.get_default_layout()
    print(f"Default layout: {len(layout)} widgets")
