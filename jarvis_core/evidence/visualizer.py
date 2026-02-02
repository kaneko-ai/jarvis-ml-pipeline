"""Evidence Visualizer.

Generates Mermaid charts for evidence grading visualization.
Per JARVIS_COMPLETION_INSTRUCTION Task 2.1.2
"""

from __future__ import annotations

from jarvis_core.evidence.schema import EvidenceGrade


class EvidenceVisualizer:
    """Visualization utilities for evidence classification."""
    
    @staticmethod
    def get_confidence_color(confidence: float) -> str:
        """Get color based on confidence level."""
        if confidence >= 0.8:
            return "green"
        if confidence >= 0.5:
            return "orange"
        return "red"

    @staticmethod
    def generate_html_badge(grade: EvidenceGrade) -> str:
        """Generate an HTML badge for evidence level with confidence tooltip."""
        color = EvidenceVisualizer.get_confidence_color(grade.confidence)
        return (
            f'<span class="badge badge-{color}" title="Confidence: {grade.confidence:.0%}">'
            f'{grade.level.value}</span>'
        )

    def draw_ascii_bar(self, confidence: float, width: int = 20) -> str:
        """Draw an ASCII progress bar for confidence."""
        filled = int(confidence * width)
        return "[" + "=" * filled + " " * (width - filled) + "]"
    def generate_confidence_chart(self, grades: list[EvidenceGrade]) -> str:
        """Generate Mermaid pie chart of evidence level distribution.

        Args:
            grades: List of EvidenceGrade objects

        Returns:
            Mermaid pie chart string
        """
        level_counts: dict[str, int] = {}
        for grade in grades:
            level = grade.level.value
            level_counts[level] = level_counts.get(level, 0) + 1

        mermaid = "pie title Evidence Level Distribution\n"
        for level, count in level_counts.items():
            mermaid += f'    "{level}" : {count}\n'

        return mermaid

    def generate_confidence_bar(self, grade: EvidenceGrade) -> str:
        """Generate Mermaid bar chart for level probabilities.

        Args:
            grade: Single EvidenceGrade with level_probabilities

        Returns:
            Mermaid xychart string
        """
        # Extract probabilities if available
        probs = getattr(grade, "level_probabilities", None)
        if not probs:
            # Create default based on confidence
            probs = {grade.level.value: grade.confidence}

        mermaid = "xychart-beta\n"
        mermaid += '    title "Level Probabilities"\n'
        keys_list = ['"' + str(k) + '"' for k in probs.keys()]
        mermaid += "    x-axis [" + ", ".join(keys_list) + "]\n"
        mermaid += '    y-axis "Probability" 0 --> 1\n'
        vals_list = [str(v) for v in probs.values()]
        mermaid += "    bar [" + ", ".join(vals_list) + "]\n"

        return mermaid

    def generate_summary_table(self, grades: list[EvidenceGrade]) -> str:
        """Generate markdown table summarizing grades.

        Args:
            grades: List of EvidenceGrade objects

        Returns:
            Markdown table string
        """
        table = "| Level | Confidence | Study Type | Method |\n"
        table += "|-------|------------|------------|--------|\n"

        for grade in grades:
            level = grade.level.value if grade.level else "N/A"
            conf = f"{grade.confidence:.0%}" if grade.confidence else "N/A"
            study = grade.study_type.value if grade.study_type else "N/A"
            method = grade.classifier_source if grade.classifier_source else "N/A"
            table += f"| {level} | {conf} | {study} | {method} |\n"

        return table
