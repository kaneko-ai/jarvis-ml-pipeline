import pytest
from jarvis_core.multimodal.scientific import (
    FormulaCalculator,
    TableExtractor,
    ChemicalStructureAnalyzer,
    StatisticalResultParser,
    CodeRepositoryLinker,
    ProteinViewer,
    ProteinStructure,
    FigureAnalyzer,
    MedicalImageAnalyzer,
    ProtocolExtractor,
)

class TestFormulaCalculator:
    def test_evaluate_basic(self):
        calc = FormulaCalculator()
        assert calc.evaluate("1 + 2 * 3", {}) == 7.0
        assert calc.evaluate("(1 + 2) * 3", {}) == 9.0
        assert calc.evaluate("10 / 2 - 1", {}) == 4.0
        assert calc.evaluate("2**3", {}) == 8.0

    def test_evaluate_variables(self):
        calc = FormulaCalculator()
        vars = {"x": 10.0, "y": 5.0}
        assert calc.evaluate("x + y", vars) == 15.0
        assert calc.evaluate("x * y - 2", vars) == 48.0

    def test_evaluate_unary(self):
        calc = FormulaCalculator()
        assert calc.evaluate("-5 + 10", {}) == 5.0

    def test_evaluate_errors(self):
        calc = FormulaCalculator()
        # Unknown variable
        assert calc.evaluate("z + 1", {"x": 1}) is None
        # Unsupported syntax
        assert calc.evaluate("import os", {}) is None
        # Invalid formula
        assert calc.evaluate("1 + +", {}) is None

    def test_parse_latex(self):
        calc = FormulaCalculator()
        res = calc.parse_latex("\\int x dx")
        assert res["type"] == "integral"
        assert "x" in res["variables"]

class TestTableExtractor:
    def test_extract_table(self):
        ext = TableExtractor()
        raw = "Header1 | Header2\nVal1 | Val2\n---\nVal3 | Val4"
        res = ext.extract_table(raw)
        assert res["headers"] == ["Header1", "Header2"]
        assert len(res["rows"]) == 2
        assert res["rows"][0] == ["Val1", "Val2"]

    def test_compare_tables(self):
        ext = TableExtractor()
        t1 = {"headers": ["A", "B"], "rows": [[1, 2]]}
        t2 = {"headers": ["A", "B"], "rows": [[1, 2], [3, 4]]}
        res = ext.compare_tables(t1, t2)
        assert res["same_structure"] is True
        assert res["row_count_diff"] == -1

class TestChemicalStructureAnalyzer:
    def test_parse_smiles(self):
        ana = ChemicalStructureAnalyzer()
        res = ana.parse_smiles("C1=CC=CC=C1") # Benzene
        assert res["atom_count"] == 6
        assert res["ring_count"] == 1
        assert res["is_aromatic"] is True

    def test_similarity(self):
        ana = ChemicalStructureAnalyzer()
        db = [{"name": "Ethanol", "smiles": "CCO"}]
        res = ana.find_similar_compounds("CC", db)
        assert res[0]["similarity"] > 0

class TestStatisticalResultParser:
    def test_parse_p_value(self):
        parser = StatisticalResultParser()
        text = "The effect was significant (p = 0.02, p < 0.001)."
        res = parser.parse(text)
        p_vals = [r["value"] for r in res if r["type"] == "p_value"]
        assert "0.02" in p_vals
        assert "0.001" in p_vals

    def test_parse_ci(self):
        parser = StatisticalResultParser()
        text = "The 95% confidence interval [1.5-2.5]."
        res = parser.parse(text)
        ci = [r for r in res if r["type"] == "confidence_interval"][0]
        assert ci["level"] == "95"
        assert ci["lower"] == "1.5"
        assert ci["upper"] == "2.5"

class TestCodeRepositoryLinker:
    def test_find_github(self):
        linker = CodeRepositoryLinker()
        paper = {"title": "Paper", "abstract": "Code at github.com/user/repo"}
        res = linker.find_repository(paper)
        assert res["platform"] == "github"
        assert res["repo"] == "user/repo"

def test_protein_viewer():
    viewer = ProteinViewer()
    s = ProteinStructure(pdb_id="1ABC", sequence="ACD")
    viewer.add_structure(s)
    info = viewer.get_sequence_info("1ABC")
    assert info["length"] == 3
    assert info["composition"]["A"] == 1
    
    pred = viewer.predict_secondary_structure("AELMVIY")
    assert "H" in pred
    assert "E" in pred

def test_protocol_extractor():
    ext = ProtocolExtractor()
    methods = "Incubate for 10 min. Centrifuge at high speed. Add 5 mL buffer."
    steps = ext.extract(methods)
    assert len(steps) >= 3
    assert steps[0]["duration"] == "10 min"

def test_medical_image_analyzer():
    ana = MedicalImageAnalyzer()
    res = ana.analyze({"modality": "ct"})
    assert res["modality"] == "ct"
    assert len(res["findings"]) > 0

def test_figure_analyzer():
    ana = FigureAnalyzer()
    res = ana.analyze_figure({"type": "bar_chart", "caption": "test"})
    assert res["figure_type"] == "bar_chart"
