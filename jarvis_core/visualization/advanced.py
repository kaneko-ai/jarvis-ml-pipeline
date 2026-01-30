"""JARVIS Advanced Visualization Module - Remaining Phase 1 Features (4,5,8,9)"""


# ============================================
# 4. SANKEY DIAGRAM DATA GENERATOR
# ============================================
class SankeyGenerator:
    """Generate data for Sankey diagrams (citation flow)."""

    def generate_citation_flow(self, papers: list[dict]) -> dict:
        """Generate citation flow data.

        Args:
            papers: List of papers with citations

        Returns:
            Sankey diagram data structure
        """
        nodes = []
        links = []
        node_map = {}

        for i, paper in enumerate(papers):
            node_id = f"paper_{i}"
            nodes.append({"id": node_id, "name": paper.get("title", "Unknown")[:40] + "..."})
            node_map[paper.get("pmid", str(i))] = node_id

        # Generate sample links
        for i, paper in enumerate(papers):
            refs = paper.get("references", [])[:3]
            for ref_pmid in refs:
                if ref_pmid in node_map:
                    links.append({"source": f"paper_{i}", "target": node_map[ref_pmid], "value": 1})

        return {"nodes": nodes, "links": links}

    def generate_topic_flow(self, categories: dict[str, list[str]]) -> dict:
        """Generate topic flow data.

        Args:
            categories: Dict of category -> papers

        Returns:
            Sankey diagram data
        """
        nodes = []
        links = []

        # Add category nodes
        for cat in categories:
            nodes.append({"id": cat, "name": cat})

        # Add year nodes
        years = ["2022", "2023", "2024"]
        for year in years:
            nodes.append({"id": year, "name": year})

        # Generate links
        for cat, papers in categories.items():
            for year in years:
                links.append(
                    {
                        "source": year,
                        "target": cat,
                        "value": len([p for p in papers if str(p.get("year")) == year]),
                    }
                )

        return {"nodes": nodes, "links": links}


# ============================================
# 5. FORCE GRAPH (Author Network)
# ============================================
class ForceGraphGenerator:
    """Generate data for force-directed graphs."""

    def generate_author_network(self, papers: list[dict]) -> dict:
        """Generate author collaboration network.

        Args:
            papers: List of papers

        Returns:
            Force graph data structure
        """
        nodes = {}
        links = []

        for paper in papers:
            authors = paper.get("authors", "").split(", ")

            # Add author nodes
            for author in authors:
                if author and author not in nodes:
                    nodes[author] = {
                        "id": author,
                        "name": author,
                        "papers": 0,
                        "group": hash(author.split()[0]) % 5,  # Color group
                    }
                if author:
                    nodes[author]["papers"] += 1

            # Add collaboration links
            for i, a1 in enumerate(authors):
                for a2 in authors[i + 1 :]:
                    if a1 and a2:
                        links.append({"source": a1, "target": a2, "value": 1})

        return {"nodes": list(nodes.values()), "links": links}

    def generate_citation_network(self, papers: list[dict]) -> dict:
        """Generate paper citation network.

        Args:
            papers: List of papers

        Returns:
            Force graph data
        """
        nodes = []
        links = []

        for paper in papers:
            nodes.append(
                {
                    "id": paper.get("pmid", ""),
                    "name": paper.get("title", "")[:30],
                    "citations": paper.get("citation_count", 0),
                    "group": 0,
                }
            )

        # Add citation links (if available)
        for paper in papers:
            for ref in paper.get("references", []):
                links.append({"source": paper.get("pmid"), "target": ref, "value": 1})

        return {"nodes": nodes, "links": links}


# ============================================
# 8. BUBBLE CHART DATA
# ============================================
class BubbleChartGenerator:
    """Generate bubble chart data for impact analysis."""

    def generate_impact_chart(self, papers: list[dict]) -> list[dict]:
        """Generate impact factor bubble chart data.

        Args:
            papers: List of papers

        Returns:
            List of bubble data points
        """
        return [
            {
                "id": paper.get("pmid", str(i)),
                "title": paper.get("title", "")[:30],
                "x": paper.get("year", 2024),
                "y": paper.get("citation_count", 0),
                "r": min(paper.get("citation_count", 1) / 10 + 5, 50),  # Radius
                "category": paper.get("category", "General"),
            }
            for i, paper in enumerate(papers)
        ]

    def generate_author_impact(self, authors: list[dict]) -> list[dict]:
        """Generate author impact bubble chart.

        Args:
            authors: List of author stats

        Returns:
            Bubble chart data
        """
        return [
            {
                "id": author.get("name"),
                "name": author.get("name"),
                "x": author.get("h_index", 0),
                "y": author.get("total_citations", 0),
                "r": author.get("paper_count", 1) * 2 + 5,
            }
            for author in authors
        ]


# ============================================
# 9. TREEMAP DATA
# ============================================
class TreemapGenerator:
    """Generate treemap data for hierarchical visualization."""

    def generate_category_treemap(self, papers: list[dict]) -> dict:
        """Generate category treemap.

        Args:
            papers: List of papers

        Returns:
            Treemap data structure
        """
        categories = {}

        for paper in papers:
            cat = paper.get("category", "General")
            subcat = paper.get("subcategory", "Other")

            if cat not in categories:
                categories[cat] = {"name": cat, "children": {}}

            if subcat not in categories[cat]["children"]:
                categories[cat]["children"][subcat] = {"name": subcat, "value": 0}

            categories[cat]["children"][subcat]["value"] += 1

        return {
            "name": "Research Topics",
            "children": [
                {"name": cat, "children": list(data["children"].values())}
                for cat, data in categories.items()
            ],
        }

    def generate_journal_treemap(self, papers: list[dict]) -> dict:
        """Generate journal distribution treemap.

        Args:
            papers: List of papers

        Returns:
            Treemap data
        """
        journals = {}

        for paper in papers:
            journal = paper.get("journal", "Unknown")
            if journal not in journals:
                journals[journal] = 0
            journals[journal] += 1

        return {
            "name": "Journals",
            "children": [
                {"name": j, "value": c} for j, c in sorted(journals.items(), key=lambda x: -x[1])
            ],
        }


# ============================================
# 16. TREND PREDICTION
# ============================================
class TrendPredictor:
    """Simple trend prediction for research topics."""

    def __init__(self):
        self.historical_data = {}

    def add_data(self, topic: str, year: int, count: int):
        """Add historical data point."""
        if topic not in self.historical_data:
            self.historical_data[topic] = {}
        self.historical_data[topic][year] = count

    def predict_trend(self, topic: str, years_ahead: int = 2) -> dict:
        """Predict future trend using linear regression.

        Args:
            topic: Topic name
            years_ahead: Years to predict

        Returns:
            Prediction result
        """
        if topic not in self.historical_data:
            return {"error": "No data for topic"}

        data = self.historical_data[topic]
        years = sorted(data.keys())

        if len(years) < 2:
            return {"error": "Insufficient data"}

        # Simple linear regression
        n = len(years)
        x_mean = sum(years) / n
        y_values = [data[y] for y in years]
        y_mean = sum(y_values) / n

        numerator = sum((years[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
        denominator = sum((years[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator

        intercept = y_mean - slope * x_mean

        # Predict future years
        predictions = {}
        last_year = max(years)
        for i in range(1, years_ahead + 1):
            future_year = last_year + i
            predictions[future_year] = max(0, int(slope * future_year + intercept))

        return {
            "topic": topic,
            "historical": data,
            "predictions": predictions,
            "trend": "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable",
            "growth_rate": round(slope / y_mean * 100, 2) if y_mean > 0 else 0,
        }

    def get_hot_topics(self, top_n: int = 5) -> list[dict]:
        """Get hottest trending topics.

        Args:
            top_n: Number of topics to return

        Returns:
            List of trending topics
        """
        trends = []
        for topic in self.historical_data:
            pred = self.predict_trend(topic)
            if "error" not in pred:
                trends.append(
                    {"topic": topic, "growth_rate": pred["growth_rate"], "trend": pred["trend"]}
                )

        return sorted(trends, key=lambda x: x["growth_rate"], reverse=True)[:top_n]


# Factory functions
def get_sankey_generator() -> SankeyGenerator:
    return SankeyGenerator()


def get_force_graph_generator() -> ForceGraphGenerator:
    return ForceGraphGenerator()


def get_bubble_chart_generator() -> BubbleChartGenerator:
    return BubbleChartGenerator()


def get_treemap_generator() -> TreemapGenerator:
    return TreemapGenerator()


def get_trend_predictor() -> TrendPredictor:
    return TrendPredictor()


if __name__ == "__main__":
    # Demo
    papers = [
        {
            "pmid": "1",
            "title": "Machine Learning in Healthcare",
            "authors": "Smith J, Johnson A",
            "year": 2024,
            "category": "AI",
        },
        {
            "pmid": "2",
            "title": "Deep Learning for Drug Discovery",
            "authors": "Johnson A, Williams B",
            "year": 2024,
            "category": "AI",
        },
        {
            "pmid": "3",
            "title": "CRISPR Gene Editing",
            "authors": "Williams B, Brown C",
            "year": 2023,
            "category": "Genomics",
        },
    ]

    print("=== Force Graph (Author Network) ===")
    fg = ForceGraphGenerator()
    network = fg.generate_author_network(papers)
    print(f"Nodes: {len(network['nodes'])}, Links: {len(network['links'])}")

    print("\n=== Treemap ===")
    tm = TreemapGenerator()
    treemap = tm.generate_category_treemap(papers)
    print(f"Categories: {len(treemap['children'])}")

    print("\n=== Trend Prediction ===")
    tp = TrendPredictor()
    tp.add_data("AI", 2020, 100)
    tp.add_data("AI", 2021, 150)
    tp.add_data("AI", 2022, 200)
    tp.add_data("AI", 2023, 280)
    tp.add_data("AI", 2024, 350)
    prediction = tp.predict_trend("AI")
    print(f"AI Trend: {prediction['trend']}, Growth: {prediction['growth_rate']}%")