# JARVIS 300 Features - Complete Guide

## 概要

JARVISには300の機能が実装されています。このガイドでは、全機能の使用方法を説明します。

---

## 🧬 Phase 1: AI Co-Scientist (101-120)

### 仮説生成

```python
from jarvis_core.scientist import HypothesisGenerator

hg = HypothesisGenerator()
hypotheses = hg.generate_hypotheses("cancer immunotherapy", n=5)

for h in hypotheses:
    print(f"{h['id']}: {h['text']}")
    print(f"  Confidence: {h['confidence']}")
```

### 研究質問分解

```python
from jarvis_core.scientist import ResearchQuestionDecomposer

rqd = ResearchQuestionDecomposer()
result = rqd.decompose("What is the mechanism of drug resistance?")
print(f"Sub-questions: {len(result['sub_questions'])}")
```

### 実験設計

```python
from jarvis_core.scientist import ExperimentDesignerPro

designer = ExperimentDesignerPro()
design = designer.design_experiment("Treatment improves outcome")
print(f"Sample size: {design['design']['total_n']}")
```

---

## 🔬 Phase 2: Protein & Biomolecule (121-140)

### AlphaFold構造取得

```python
from jarvis_core.protein import AlphaFoldIntegration

af = AlphaFoldIntegration()
urls = af.get_structure_url("P12345")
print(f"View: {urls['viewer_url']}")
```

### 結合予測

```python
from jarvis_core.protein import BindingAffinityPredictor

bp = BindingAffinityPredictor()
result = bp.predict_binding("MVLSPADKTN", "CCO")
print(f"Kd: {result['predicted_kd_M']}")
```

### ADMET予測

```python
from jarvis_core.protein import ADMETPredictor

admet = ADMETPredictor()
result = admet.predict("CCO")
print(f"Lipinski violations: {result['lipinski_violations']}")
```

---

## 🤖 Phase 3: Self-Driving Lab (141-160)

### 機器制御

```python
from jarvis_core.lab import LabEquipmentController

lec = LabEquipmentController()
lec.register_equipment(LabEquipment("eq1", "Centrifuge", "centrifuge"))
lec.send_command("eq1", "spin", {"rpm": 5000})
```

### OpenTronsプロトコル

```python
from jarvis_core.lab import RoboticArmIntegration

robot = RoboticArmIntegration()
protocol = robot.generate_protocol([
    {"action": "transfer", "source": "A1", "dest": "B1", "volume": 100}
])
```

---

## 🌐 Phase 4-5: Browser & MCP (161-200)

### MCPサーバー管理

```python
from jarvis_core.lab import MCPServerManager

mcp = MCPServerManager()
mcp.register_server("pubmed", "http://localhost:8080", ["search"])
```

---

## 📊 Phase 6: Advanced Analytics (201-220)

### メタ分析

```python
from jarvis_core.advanced import MetaAnalysisBot

ma = MetaAnalysisBot()
result = ma.run_meta_analysis([
    {"effect_size": 0.5, "sample_size": 100},
    {"effect_size": 0.6, "sample_size": 150}
])
print(f"Pooled effect: {result['pooled_effect_size']}")
```

---

## 🔒 Phase 8: Security (241-260)

### HIPAAチェック

```python
from jarvis_core.advanced import HIPAAComplianceChecker

checker = HIPAAComplianceChecker()
result = checker.check("Patient SSN: 123-45-6789")
print(f"Compliant: {result['compliant']}")
```

---

## 🏢 Phase 10: Enterprise (281-300)

### チームワークスペース

```python
from jarvis_core.advanced import TeamWorkspace

tw = TeamWorkspace()
ws = tw.create_workspace("Research Team", ["alice", "bob"])
```

---

## パイプライン使用方法

```bash
# GitHub Actionsから実行
gh workflow run research-pipelines.yml \
  -f pipeline=hypothesis \
  -f topic="cancer treatment"
```

---

## リンク

- **GitHub**: https://github.com/kaneko-ai/jarvis-ml-pipeline
- **Dashboard**: https://kaneko-ai.github.io/jarvis-ml-pipeline/
