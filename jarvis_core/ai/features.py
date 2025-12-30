"""JARVIS AI Features Module - Phase 2 Features (12-20)"""
import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import Counter


# ============================================
# 12. RELATED PAPERS FINDER
# ============================================
class RelatedPapersFinder:
    """Find related papers using keyword similarity."""
    
    def __init__(self, papers: List[Dict] = None):
        self.papers = papers or []
    
    def find_related(self, paper: Dict, top_n: int = 5) -> List[Dict]:
        """Find related papers by keyword overlap.
        
        Args:
            paper: Source paper
            top_n: Number of results
            
        Returns:
            List of related papers with scores
        """
        source_keywords = self._extract_keywords(paper.get("title", "") + " " + paper.get("abstract", ""))
        
        results = []
        for p in self.papers:
            if p.get("pmid") == paper.get("pmid"):
                continue
            
            p_keywords = self._extract_keywords(p.get("title", "") + " " + p.get("abstract", ""))
            score = len(source_keywords & p_keywords) / max(len(source_keywords | p_keywords), 1)
            
            if score > 0:
                results.append({**p, "similarity_score": round(score * 100, 2)})
        
        return sorted(results, key=lambda x: x["similarity_score"], reverse=True)[:top_n]
    
    def _extract_keywords(self, text: str) -> set:
        """Extract keywords from text."""
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        stopwords = {'this', 'that', 'with', 'from', 'have', 'were', 'been', 'their', 'which', 'about', 'these', 'other'}
        return set(w for w in words if w not in stopwords)


# ============================================
# 13. Q&A SYSTEM
# ============================================
class PaperQA:
    """Simple Q&A system for papers."""
    
    def __init__(self):
        self.context = ""
    
    def set_context(self, paper: Dict):
        """Set paper context for Q&A."""
        self.context = f"""
Title: {paper.get('title', '')}
Authors: {paper.get('authors', '')}
Abstract: {paper.get('abstract', '')}
Journal: {paper.get('journal', '')}
Year: {paper.get('year', '')}
"""
    
    def answer(self, question: str) -> str:
        """Answer a question about the paper.
        
        Args:
            question: User question
            
        Returns:
            Answer string
        """
        q_lower = question.lower()
        
        # Simple rule-based QA
        if "author" in q_lower or "who wrote" in q_lower:
            match = re.search(r'Authors: (.+)', self.context)
            return f"The authors are: {match.group(1)}" if match else "Authors not found."
        
        if "year" in q_lower or "when" in q_lower or "published" in q_lower:
            match = re.search(r'Year: (\d+)', self.context)
            return f"Published in {match.group(1)}" if match else "Publication year not found."
        
        if "journal" in q_lower or "where" in q_lower:
            match = re.search(r'Journal: (.+)', self.context)
            return f"Published in {match.group(1)}" if match else "Journal not found."
        
        if "about" in q_lower or "topic" in q_lower or "summary" in q_lower:
            match = re.search(r'Abstract: (.+?)(?:\n|$)', self.context, re.DOTALL)
            abstract = match.group(1)[:200] if match else "No abstract available"
            return f"This paper is about: {abstract}..."
        
        return "I can answer questions about authors, publication year, journal, and topic. Try asking 'Who wrote this?' or 'What is this about?'"


# ============================================
# 14. TRANSLATION
# ============================================
class PaperTranslator:
    """Simple translation support using dictionary lookup."""
    
    # Basic medical terms JP-EN dictionary
    TRANSLATIONS = {
        'en_to_ja': {
            'treatment': '治療',
            'patient': '患者',
            'disease': '疾患',
            'clinical': '臨床',
            'study': '研究',
            'cancer': 'がん',
            'therapy': '療法',
            'drug': '薬物',
            'cell': '細胞',
            'gene': '遺伝子',
            'protein': 'タンパク質',
            'diagnosis': '診断',
            'symptom': '症状',
            'outcome': '結果',
            'method': '方法',
            'analysis': '解析',
            'model': 'モデル',
            'machine learning': '機械学習',
            'artificial intelligence': '人工知能',
            'deep learning': '深層学習'
        }
    }
    
    def translate_keywords(self, text: str, target_lang: str = 'ja') -> Dict[str, str]:
        """Translate keywords in text.
        
        Args:
            text: Source text
            target_lang: Target language code
            
        Returns:
            Dictionary of translations found
        """
        translations = {}
        text_lower = text.lower()
        
        if target_lang == 'ja':
            for en, ja in self.TRANSLATIONS['en_to_ja'].items():
                if en in text_lower:
                    translations[en] = ja
        
        return translations
    
    def add_translations(self, text: str) -> str:
        """Add parenthetical translations to text.
        
        Args:
            text: Source text
            
        Returns:
            Text with translations added
        """
        translations = self.translate_keywords(text)
        result = text
        
        for en, ja in translations.items():
            pattern = re.compile(re.escape(en), re.IGNORECASE)
            result = pattern.sub(f"{en} ({ja})", result, count=1)
        
        return result


# ============================================
# 15. AUTO-TAGGING
# ============================================
class AutoTagger:
    """Automatically tag papers based on content."""
    
    TAG_RULES = {
        'AI': ['machine learning', 'deep learning', 'neural network', 'AI', 'artificial intelligence', 'algorithm', 'model'],
        'Clinical': ['clinical', 'patient', 'trial', 'treatment', 'therapy', 'diagnosis', 'hospital'],
        'Genomics': ['gene', 'genome', 'DNA', 'RNA', 'sequencing', 'mutation', 'CRISPR', 'genetic'],
        'COVID-19': ['COVID', 'coronavirus', 'SARS-CoV-2', 'pandemic', 'vaccine'],
        'Cancer': ['cancer', 'tumor', 'oncology', 'carcinoma', 'metastasis', 'chemotherapy'],
        'Neuroscience': ['brain', 'neural', 'neuron', 'cognitive', 'neurological'],
        'Drug Discovery': ['drug', 'pharmaceutical', 'compound', 'molecule', 'target'],
        'Immunology': ['immune', 'antibody', 'immunotherapy', 'T-cell', 'inflammation']
    }
    
    def get_tags(self, text: str) -> List[str]:
        """Get tags for text.
        
        Args:
            text: Paper title/abstract
            
        Returns:
            List of applicable tags
        """
        tags = []
        text_lower = text.lower()
        
        for tag, keywords in self.TAG_RULES.items():
            if any(kw.lower() in text_lower for kw in keywords):
                tags.append(tag)
        
        return tags if tags else ['General']
    
    def tag_paper(self, paper: Dict) -> Dict:
        """Add tags to paper.
        
        Args:
            paper: Paper dictionary
            
        Returns:
            Paper with tags added
        """
        text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
        paper['tags'] = self.get_tags(text)
        return paper


# ============================================
# 17. SIMILARITY SCORE
# ============================================
class SimilarityCalculator:
    """Calculate similarity between papers."""
    
    def jaccard_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score 0-1
        """
        words1 = set(re.findall(r'\b\w{3,}\b', text1.lower()))
        words2 = set(re.findall(r'\b\w{3,}\b', text2.lower()))
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0
    
    def compare_papers(self, paper1: Dict, paper2: Dict) -> Dict:
        """Compare two papers.
        
        Args:
            paper1: First paper
            paper2: Second paper
            
        Returns:
            Comparison result
        """
        text1 = f"{paper1.get('title', '')} {paper1.get('abstract', '')}"
        text2 = f"{paper2.get('title', '')} {paper2.get('abstract', '')}"
        
        similarity = self.jaccard_similarity(text1, text2)
        
        return {
            "paper1": paper1.get("title", "Unknown")[:50],
            "paper2": paper2.get("title", "Unknown")[:50],
            "similarity_score": round(similarity * 100, 2),
            "similarity_level": "High" if similarity > 0.3 else "Medium" if similarity > 0.15 else "Low"
        }


# ============================================
# 18. KEYWORD EXTRACTION
# ============================================
class KeywordExtractor:
    """Extract keywords from text using TF-IDF-like scoring."""
    
    STOPWORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
        'those', 'it', 'its', 'they', 'them', 'their', 'we', 'our', 'you',
        'your', 'which', 'who', 'whom', 'what', 'when', 'where', 'why', 'how',
        'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some',
        'such', 'than', 'very', 'just', 'also', 'only', 'into', 'through',
        'during', 'before', 'after', 'above', 'below', 'between', 'under',
        'again', 'further', 'then', 'once', 'here', 'there', 'about', 'being',
        'having', 'using', 'used', 'based', 'results', 'study', 'studies',
        'analysis', 'method', 'methods', 'data', 'paper', 'research'
    }
    
    def extract(self, text: str, top_n: int = 10) -> List[Tuple[str, int]]:
        """Extract top keywords.
        
        Args:
            text: Source text
            top_n: Number of keywords
            
        Returns:
            List of (keyword, count) tuples
        """
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        filtered = [w for w in words if w not in self.STOPWORDS]
        
        counter = Counter(filtered)
        first_positions = {}
        for index, word in enumerate(filtered):
            if word not in first_positions:
                first_positions[word] = index

        sorted_keywords = sorted(
            counter.items(),
            key=lambda item: (-item[1], first_positions[item[0]], item[0])
        )
        return sorted_keywords[:top_n]
    
    def extract_phrases(self, text: str, top_n: int = 5) -> List[str]:
        """Extract key phrases (bigrams).
        
        Args:
            text: Source text
            top_n: Number of phrases
            
        Returns:
            List of key phrases
        """
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        filtered = [w for w in words if w not in self.STOPWORDS]
        
        bigrams = [f"{filtered[i]} {filtered[i+1]}" for i in range(len(filtered)-1)]
        counter = Counter(bigrams)
        
        return [phrase for phrase, _ in counter.most_common(top_n)]


# ============================================
# 19. SENTIMENT ANALYSIS
# ============================================
class SentimentAnalyzer:
    """Simple sentiment analysis for research papers."""
    
    POSITIVE_WORDS = {
        'significant', 'improved', 'effective', 'successful', 'promising',
        'novel', 'innovative', 'breakthrough', 'advancement', 'better',
        'enhanced', 'excellent', 'optimal', 'remarkable', 'substantial',
        'important', 'valuable', 'beneficial', 'positive', 'strong'
    }
    
    NEGATIVE_WORDS = {
        'failed', 'limited', 'insufficient', 'poor', 'weak', 'negative',
        'worse', 'declined', 'decreased', 'problematic', 'challenging',
        'difficult', 'complicated', 'unclear', 'uncertain', 'controversial'
    }
    
    def analyze(self, text: str) -> Dict:
        """Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment analysis result
        """
        words = set(re.findall(r'\b\w+\b', text.lower()))
        
        positive_count = len(words & self.POSITIVE_WORDS)
        negative_count = len(words & self.NEGATIVE_WORDS)
        
        total = positive_count + negative_count
        if total == 0:
            sentiment = "Neutral"
            score = 0.5
        else:
            score = positive_count / total
            if score > 0.6:
                sentiment = "Positive"
            elif score < 0.4:
                sentiment = "Negative"
            else:
                sentiment = "Mixed"
        
        return {
            "sentiment": sentiment,
            "score": round(score, 2),
            "positive_indicators": positive_count,
            "negative_indicators": negative_count
        }


# ============================================
# 20. CITATION GENERATOR
# ============================================
class CitationGenerator:
    """Generate citations in various formats."""
    
    def generate(self, paper: Dict, format: str = 'apa') -> str:
        """Generate citation.
        
        Args:
            paper: Paper dictionary
            format: Citation format (apa, mla, bibtex, chicago)
            
        Returns:
            Formatted citation string
        """
        title = paper.get('title', 'Unknown Title')
        authors = paper.get('authors', 'Unknown Authors')
        year = paper.get('year', 'n.d.')
        journal = paper.get('journal', 'Unknown Journal')
        doi = paper.get('doi', '')
        pmid = paper.get('pmid', '')
        
        if format == 'apa':
            citation = f"{authors} ({year}). {title}. {journal}."
            if doi:
                citation += f" https://doi.org/{doi}"
            return citation
        
        elif format == 'mla':
            return f'{authors}. "{title}." {journal}, {year}.'
        
        elif format == 'bibtex':
            key = re.sub(r'[^a-zA-Z0-9]', '', authors.split(',')[0].split()[0] if authors else 'unknown') + str(year)
            return f"""@article{{{key},
  title={{{title}}},
  author={{{authors}}},
  journal={{{journal}}},
  year={{{year}}},
  pmid={{{pmid}}}
}}"""
        
        elif format == 'chicago':
            return f"{authors}. \"{title}.\" {journal} ({year})."
        
        return f"{authors}. {title}. {journal}, {year}."
    
    def generate_all(self, paper: Dict) -> Dict[str, str]:
        """Generate citations in all formats.
        
        Args:
            paper: Paper dictionary
            
        Returns:
            Dictionary of format -> citation
        """
        return {
            'apa': self.generate(paper, 'apa'),
            'mla': self.generate(paper, 'mla'),
            'bibtex': self.generate(paper, 'bibtex'),
            'chicago': self.generate(paper, 'chicago')
        }


# ============================================
# FACTORY FUNCTIONS
# ============================================

def get_auto_tagger() -> AutoTagger:
    """Get auto tagger instance."""
    return AutoTagger()

def get_keyword_extractor() -> KeywordExtractor:
    """Get keyword extractor instance."""
    return KeywordExtractor()

def get_citation_generator() -> CitationGenerator:
    """Get citation generator instance."""
    return CitationGenerator()

def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get sentiment analyzer instance."""
    return SentimentAnalyzer()


if __name__ == "__main__":
    # Demo
    paper = {
        "title": "Deep learning approaches for COVID-19 treatment prediction",
        "authors": "Smith J, Johnson A, Williams B",
        "year": 2024,
        "journal": "Nature Medicine",
        "abstract": "This significant study presents a novel machine learning model for predicting treatment outcomes in COVID-19 patients with promising results.",
        "pmid": "39123456"
    }
    
    print("=== Auto-Tagging ===")
    tagger = AutoTagger()
    print(f"Tags: {tagger.get_tags(paper['title'] + ' ' + paper['abstract'])}")
    
    print("\n=== Keyword Extraction ===")
    extractor = KeywordExtractor()
    keywords = extractor.extract(paper['title'] + ' ' + paper['abstract'], 5)
    print(f"Keywords: {keywords}")
    
    print("\n=== Sentiment Analysis ===")
    analyzer = SentimentAnalyzer()
    sentiment = analyzer.analyze(paper['abstract'])
    print(f"Sentiment: {sentiment}")
    
    print("\n=== Citation Generation ===")
    generator = CitationGenerator()
    print(f"APA: {generator.generate(paper, 'apa')}")
    print(f"BibTeX:\n{generator.generate(paper, 'bibtex')}")
