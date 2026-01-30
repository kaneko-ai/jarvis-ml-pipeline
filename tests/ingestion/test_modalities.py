from jarvis_core.ingestion.modalities import TableArtifact, FigureArtifact, ModalityType


def test_table_artifact():
    table = TableArtifact(
        artifact_id="t1",
        doc_id="d1",
        content="| Header | Value |\n|---|---|\n| A | 1 |",
        page_number=5,
    )

    assert table.modality == ModalityType.TABLE
    data = table.to_dict()
    assert data["artifact_id"] == "t1"
    assert "Header" in data["content"]
    assert data["modality"] == "table"


def test_figure_artifact():
    fig = FigureArtifact(
        artifact_id="f1",
        doc_id="d1",
        content="Figure 1: System Architecture",
        image_path="/tmp/fig1.png",
        page_number=10,
    )

    assert fig.modality == ModalityType.FIGURE
    data = fig.to_dict()
    assert data["image_path"] == "/tmp/fig1.png"
    assert data["modality"] == "figure"