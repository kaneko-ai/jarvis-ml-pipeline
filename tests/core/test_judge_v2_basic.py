from jarvis_core.eval.judge_v2 import (
    FormJudge,
    SemanticJudge,
    IntegratedJudge,
    JudgeType,
)


class TestFormJudge:
    def test_judge_pass(self):
        judge = FormJudge()
        answer = "This is a valid answer."
        citations = [{"paper_id": "P1", "locator": {"section": "Results"}}]
        res = judge.judge(answer, citations)
        assert res.passed is True
        assert res.score == 1.0
        assert res.judge_type == JudgeType.FORM

    def test_judge_fail_no_citations(self):
        judge = FormJudge()
        res = judge.judge("Answer", [])
        assert res.passed is False
        assert any(i["check"] == "citation_exists" for i in res.issues)

    def test_judge_fail_missing_fields(self):
        judge = FormJudge()
        citations = [{"id_only": "P1"}]  # missing 'paper_id'
        res = judge.judge("Answer", citations)
        assert res.passed is False
        assert any(i["check"] == "citation_structure" for i in res.issues)

    def test_judge_fail_empty_answer(self):
        judge = FormJudge()
        res = judge.judge("", [{"paper_id": "P1", "locator": {"section": "S"}}])
        assert res.passed is False
        assert any(i["check"] == "answer_exists" for i in res.issues)


class TestSemanticJudge:
    def test_judge_pass(self):
        judge = SemanticJudge()
        answer = "The protein EGFR expression is high."
        citations = [{"evidence_text": "EGFR expression levels."}]
        res = judge.judge(answer, citations)
        assert res.passed is True
        assert res.score > 0.5

    def test_judge_fail_relevance(self):
        judge = SemanticJudge()
        answer = "climate warming"
        citations = [{"evidence_text": "mitochondria synthesis"}]
        res = judge.judge(answer, citations)
        # 1. Relevance: 0 (fail)
        # 2. Length: 1 (pass)
        # Total: 1/2 = 0.5.
        assert res.score == 0.5
        assert any(i["check"] == "answer_citation_relevance" for i in res.issues)

    def test_judge_with_claims(self):
        judge = SemanticJudge()
        answer = "Higher expression of EGFR."
        citations = []
        claims = [{"claim_text": "EGFR expression"}]
        res = judge.judge(answer, citations, claims)
        assert res.score == 1.0  # Length, Relevance (pass because no citations), Claim consistency
        assert res.passed is True

    def test_judge_fail_length(self):
        judge = SemanticJudge()
        res = judge.judge("Short", [])
        assert res.score == 0.5  # Relevance (pass because no citations), Length (fail)
        assert res.passed is True  # 0.5 is pass threshold


class TestIntegratedJudge:
    def test_integrated_judge(self):
        ij = IntegratedJudge()
        answer = "Valid answer with citations."
        citations = [{"paper_id": "P1", "locator": {"section": "X"}, "evidence_text": "citations"}]
        results = ij.judge(answer, citations)
        assert results["form"].passed is True
        assert results["semantic"].passed is True
        assert ij.overall_passed(answer, citations) is True

    def test_overall_fail(self):
        ij = IntegratedJudge()
        # Form fails (no citations)
        assert ij.overall_passed("Answer", []) is False