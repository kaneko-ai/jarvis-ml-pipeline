"""Coverage boost tests for low-covered compatibility and utility paths."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest


def test_providers_factory_selects_local_and_api(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cover config loading and provider selection branches."""
    from jarvis_core.providers import factory
    from jarvis_core.providers.base import ProviderType

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "runtime:",
                "  llm_provider: local",
                "  embed_provider: api",
                "  local:",
                "    llm:",
                "      model: local-model",
                "      backend: local-backend",
                "  api:",
                "    embed:",
                "      model: api-embed-model",
                "    llm:",
                "      model: api-llm-model",
            ]
        ),
        encoding="utf-8",
    )

    class DummyLocalLLM:
        def __init__(self, config) -> None:
            self.config = config

    class DummyApiLLM:
        def __init__(self, config) -> None:
            self.config = config

    class DummyLocalEmbed:
        def __init__(self, config) -> None:
            self.config = config

    class DummyApiEmbed:
        def __init__(self, config) -> None:
            self.config = config

    monkeypatch.setattr(factory, "LocalLLMProvider", DummyLocalLLM)
    monkeypatch.setattr(factory, "APILLMProvider", DummyApiLLM)
    monkeypatch.setattr(factory, "LocalEmbedProvider", DummyLocalEmbed)
    monkeypatch.setattr(factory, "APIEmbedProvider", DummyApiEmbed)

    runtime = factory.load_runtime_config(str(config_path))
    assert runtime["llm_provider"] == "local"
    assert factory.load_runtime_config(str(tmp_path / "missing.yaml")) == {}

    llm_provider = factory.get_llm_provider(None, str(config_path))
    assert isinstance(llm_provider, DummyLocalLLM)
    assert llm_provider.config.provider_type == ProviderType.LOCAL

    llm_provider_api = factory.get_llm_provider("api", str(config_path))
    assert isinstance(llm_provider_api, DummyApiLLM)
    assert llm_provider_api.config.provider_type == ProviderType.API

    embed_provider = factory.get_embed_provider(None, str(config_path))
    assert isinstance(embed_provider, DummyApiEmbed)
    assert embed_provider.config.provider_type == ProviderType.API

    embed_provider_local = factory.get_embed_provider("local", str(config_path))
    assert isinstance(embed_provider_local, DummyLocalEmbed)
    assert embed_provider_local.config.provider_type == ProviderType.LOCAL


def test_llm_ensemble_strategy_paths() -> None:
    """Cover voting/weighted/best-of-n/consensus and error branches."""
    from jarvis_core.llm.ensemble import EnsembleStrategy, MultiModelEnsemble

    def ok_a(_: str) -> str:
        return "alpha beta"

    def ok_b(_: str) -> str:
        return "alpha gamma"

    def boom(_: str) -> str:
        raise RuntimeError("boom")

    ensemble = MultiModelEnsemble(
        models={"a": ok_a, "b": ok_b, "bad": boom},
        weights={"a": 0.9, "b": 0.5, "bad": 0.3},
    )
    voting = ensemble.generate("prompt", strategy=EnsembleStrategy.VOTING)
    assert voting.final_text in {"alpha beta", "alpha gamma", ""}
    assert len(voting.model_outputs) == 3

    consensus = ensemble.generate("prompt", strategy=EnsembleStrategy.CONSENSUS)
    assert consensus.strategy == EnsembleStrategy.VOTING

    weighted_empty = MultiModelEnsemble(
        models={"empty": lambda _: ""},
        weights={"empty": 1.0},
        strategy=EnsembleStrategy.WEIGHTED,
    ).generate("prompt")
    assert weighted_empty.selected_model is None

    best_empty = MultiModelEnsemble(
        models={"empty": lambda _: ""},
        weights={"empty": 1.0},
        strategy=EnsembleStrategy.BEST_OF_N,
    ).generate("prompt")
    assert best_empty.selected_model is None


def test_pdf_extractor_with_mocked_fitz_and_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cover fitz and fallback extraction paths."""
    import jarvis_core.extraction.pdf_extractor as pdf_mod

    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test")

    class MockPage:
        def __init__(self, text: str) -> None:
            self._text = text

        def get_text(self) -> str:
            return self._text

    class MockDoc:
        metadata = {"title": "Demo Title", "author": "Alice,Bob"}

        def __iter__(self):
            return iter(
                [
                    MockPage("Abstract\nThis is abstract"),
                    MockPage("References\nPMID: 12345\n10.1234/example"),
                ]
            )

        def close(self) -> None:
            return None

    class MockFitz:
        @staticmethod
        def open(_: str) -> MockDoc:
            return MockDoc()

    extractor = pdf_mod.PDFExtractor()
    rich_doc = extractor._extract_with_fitz(str(pdf_path), MockFitz())
    assert rich_doc.title == "Demo Title"
    assert rich_doc.to_dict()["title"] == "Demo Title"
    assert "Abstract" in rich_doc.get_full_text()
    assert any(ref.startswith("PMID:") for ref in rich_doc.references)
    assert any(ref.startswith("DOI:") for ref in rich_doc.references)

    parsed = extractor._parse_sections([(1, "Introduction\nLine 1\nReferences\nPMID: 1")])
    assert len(parsed) >= 1
    assert extractor._detect_section_type("Abstract") == "abstract"
    assert extractor._get_section_type("Unknown Heading") == "other"

    monkeypatch.setattr(pdf_mod, "fitz", None)
    fallback_doc = pdf_mod.PDFExtractor().extract(str(pdf_path))
    assert fallback_doc.title == "sample"
    assert fallback_doc.sections == []


@pytest.mark.asyncio
async def test_terminal_security_from_yaml_and_runtime_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cover YAML loading, allow-list blocking, sudo approval, and timeout branch."""
    from jarvis_core.security.terminal import TerminalSecurityManager
    from jarvis_core.security.terminal_schema import (
        CommandExecutionRequest,
        CommandPattern,
        ExecutionPolicy,
        TerminalSecurityConfig,
    )

    config_path = tmp_path / "terminal.yaml"
    config_path.write_text(
        "\n".join(
            [
                "execution_policy: auto",
                "allow_list:",
                "  - pattern: echo",
                "    is_regex: false",
                "deny_list:",
                "  - pattern: blocked_cmd",
                "    is_regex: false",
                "    reason: denied",
                "max_execution_time_seconds: 1",
                "require_confirmation_for_sudo: true",
            ]
        ),
        encoding="utf-8",
    )

    yaml_manager = TerminalSecurityManager.from_yaml(config_path)
    blocked = yaml_manager.check_command(CommandExecutionRequest(command="unknown command"))
    assert blocked.allowed is False
    denied = yaml_manager.check_command(CommandExecutionRequest(command="blocked_cmd now"))
    assert denied.allowed is False

    sudo_manager = TerminalSecurityManager(
        TerminalSecurityConfig(
            execution_policy=ExecutionPolicy.AUTO,
            allow_list=[CommandPattern(pattern="sudo echo", is_regex=False)],
            deny_list=[],
            require_confirmation_for_sudo=True,
        )
    )
    sudo_result = await sudo_manager.execute_command(
        CommandExecutionRequest(command="sudo echo test"),
        approved=False,
    )
    assert sudo_result.allowed is False
    assert sudo_result.blocked_reason == "Approval required for sudo command"

    class SlowProcess:
        returncode = 0

        async def communicate(self):
            await asyncio.sleep(0.05)
            return b"", b""

        def kill(self) -> None:
            return None

    async def fake_create_subprocess_shell(*_args, **_kwargs):
        return SlowProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_shell", fake_create_subprocess_shell)

    timeout_manager = TerminalSecurityManager(
        TerminalSecurityConfig(
            execution_policy=ExecutionPolicy.AUTO,
            allow_list=[CommandPattern(pattern="pwd", is_regex=False)],
            deny_list=[],
            max_execution_time_seconds=1,
        )
    )
    timed = await timeout_manager.execute_command(
        CommandExecutionRequest(command="pwd", timeout=0.001, environment={"X": "1"}),
        approved=True,
    )
    assert timed.executed is True
    assert timed.blocked_reason == "Command timed out"


def test_advanced_and_lab_feature_paths() -> None:
    """Cover remaining utility classes and factory helpers."""
    from jarvis_core.advanced.features import (
        GDPRDataHandler,
        MLPipelineBuilder,
        ModelComparisonTool,
        RegressionWizard,
        TeamWorkspace,
        VolcanoPlotBuilder,
        get_hipaa_checker,
        get_meta_analysis,
        get_systematic_review,
        get_team_workspace,
    )
    from jarvis_core.lab.automation import (
        CommunitySharing,
        CostTracker,
        CustomToolBuilder,
        DependencyManager,
        DocumentationGenerator,
        EnterpriseToolManager,
        SandboxEnvironment,
        ToolInteroperability,
        ToolMarketplace,
        ToolTestingFramework,
        ToolVersioning,
        UsageAnalytics,
        get_lab_controller,
        get_mcp_manager,
        get_robotic_arm,
        get_sample_tracker,
        get_web_scraper,
    )

    regression = RegressionWizard().linear_regression([1, 2, 3], [2, 4, 6])
    assert regression["slope"] == 2.0
    assert MLPipelineBuilder().create_pipeline(["a", "b"])["status"] == "ready"
    compared = ModelComparisonTool().compare({"a": 0.1, "b": 0.9})
    assert compared["best_model"] == "b"

    volcano = VolcanoPlotBuilder().build([1.2, 0.2], [2.0, 0.5], ["G1", "G2"])
    assert volcano["significant_genes"][0]["gene"] == "G1"

    anonymized = GDPRDataHandler().anonymize({"name": "alice", "age": 30}, ["name"])
    assert anonymized["name"] != "alice"

    workspace_api = TeamWorkspace()
    workspace = workspace_api.create_workspace("Team", ["alice"])
    workspace_api.add_member(workspace.id, "bob", "editor")
    assert len(workspace_api.list_workspaces("bob")) == 1
    workspace_api.remove_member(workspace.id, "bob")
    assert workspace_api.list_workspaces("bob") == []

    assert get_meta_analysis() is not None
    assert get_systematic_review() is not None
    assert get_hipaa_checker() is not None
    assert get_team_workspace() is not None

    cost = CostTracker()
    cost.set_pricing("api", 0.5)
    cost.record_call("api", 2)
    assert cost.get_total_cost()["total"] == 1.0

    usage = UsageAnalytics()
    usage.record("tool_a")
    usage.record("tool_a")
    usage.record("tool_b")
    assert usage.get_analytics()["total_calls"] == 3

    versioning = ToolVersioning()
    versioning.add_version("tool", "1.0")
    assert versioning.versions["tool"] == ["1.0"]

    assert CustomToolBuilder().create_tool("x", "print(1)")["status"] == "created"
    assert ToolMarketplace().search("community")[0]["name"] == "Community Tool"
    assert DependencyManager().resolve("tool") == ["dependency_1", "dependency_2"]
    assert SandboxEnvironment().execute("print(1)")["safe"] is True
    assert ToolTestingFramework().test("tool", [{"case": 1}])["passed"] == 1
    assert "Usage" in DocumentationGenerator().generate({"name": "Demo"})
    assert CommunitySharing().share({"name": "demo"})["status"] == "shared"
    assert EnterpriseToolManager().list_approved_tools()[0]["name"] == "approved_tool"
    assert ToolInteroperability().check_compatibility("a", "b")["compatible"] is True

    assert get_lab_controller() is not None
    assert get_robotic_arm() is not None
    assert get_sample_tracker() is not None
    assert get_web_scraper() is not None
    assert get_mcp_manager() is not None
