"""Single Entry CLI.

Per V4-P01, this provides a unified CLI entry point.
`jarvis run <workflow>` is the single recommended entry.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from ..config import load_config, Config
from ..errors import JarvisError, ValidationError
from ..workflows import (
    run_literature_to_plan,
    run_plan_to_grant,
    run_plan_to_paper,
    run_plan_to_talk,
)
from ..bundle_v2 import create_bundle_v2


WORKFLOWS = {
    "literature_to_plan": "PDF/URL → Research Plan",
    "plan_to_grant": "Research Plan → Grant Proposal",
    "plan_to_paper": "Research Plan → Paper Structure",
    "plan_to_talk": "Research Plan → Presentation",
}


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="jarvis",
        description="JARVIS Research OS - Unified CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # run command
    run_parser = subparsers.add_parser("run", help="Run a workflow")
    run_parser.add_argument(
        "workflow",
        choices=list(WORKFLOWS.keys()),
        help="Workflow to run",
    )
    run_parser.add_argument(
        "--inputs", "-i",
        nargs="+",
        help="Input files (PDF/URL)",
    )
    run_parser.add_argument(
        "--query", "-q",
        help="Research query/focus",
    )
    run_parser.add_argument(
        "--concepts", "-c",
        nargs="+",
        default=[],
        help="Focus concepts",
    )
    run_parser.add_argument(
        "--out", "-o",
        default="output",
        help="Output directory (Bundle v2)",
    )
    run_parser.add_argument(
        "--config",
        help="Config YAML file",
    )
    run_parser.add_argument(
        "--preset",
        choices=["quick", "deep"],
        help="Use a preset configuration",
    )

    # list command
    list_parser = subparsers.add_parser("list", help="List available resources")
    list_parser.add_argument(
        "resource",
        choices=["workflows", "modules", "presets"],
        help="Resource type to list",
    )

    # version command
    subparsers.add_parser("version", help="Show version")

    return parser


def run_workflow(
    workflow: str,
    inputs: List[str] = None,
    query: str = "",
    concepts: List[str] = None,
    output_dir: str = "output",
    config: Optional[Config] = None,
) -> dict:
    """Execute a workflow.

    Args:
        workflow: Workflow name.
        inputs: Input files/URLs.
        query: Research query.
        concepts: Focus concepts.
        output_dir: Output directory.
        config: Optional configuration.

    Returns:
        Execution result dict.
    """
    from ..paper_vector import (
        PaperVector, MetadataVector, ConceptVector, MethodVector,
        TemporalVector, ImpactVector,
    )

    inputs = inputs or []
    concepts = concepts or []

    # Create vectors from inputs (simplified for demo)
    vectors = []
    for i, inp in enumerate(inputs):
        # Extract concepts from filename/path
        inp_concepts = {c: 0.5 for c in concepts[:3]} if concepts else {"research": 0.5}
        vectors.append(PaperVector(
            paper_id=f"paper_{i}",
            source_locator=inp,
            metadata=MetadataVector(year=2024),
            concept=ConceptVector(concepts=inp_concepts),
            method=MethodVector(methods={"analysis": 0.5}),
            temporal=TemporalVector(novelty=0.5),
            impact=ImpactVector(future_potential=0.5),
        ))

    # If no inputs but query provided, create from query
    if not vectors and query:
        concepts = concepts or query.split()[:3]

    # Execute workflow
    if workflow == "literature_to_plan":
        artifact = run_literature_to_plan(vectors, concepts or ["research"])
    elif workflow == "plan_to_grant":
        plan = run_literature_to_plan(vectors, concepts or ["research"])
        artifact = run_plan_to_grant(plan, vectors, concepts)
    elif workflow == "plan_to_paper":
        plan = run_literature_to_plan(vectors, concepts or ["research"])
        artifact = run_plan_to_paper(plan, vectors)
    elif workflow == "plan_to_talk":
        plan = run_literature_to_plan(vectors, concepts or ["research"])
        artifact = run_plan_to_talk(plan, vectors)
    else:
        raise ValidationError(f"Unknown workflow: {workflow}")

    # Create and export bundle
    bundle = create_bundle_v2([artifact], vectors, {"query": query, "workflow": workflow})
    bundle.export(output_dir)

    return {
        "status": "success",
        "workflow": workflow,
        "output_dir": output_dir,
        "artifact_kind": artifact.kind,
    }


def list_resources(resource: str) -> None:
    """List available resources."""
    if resource == "workflows":
        print("Available workflows:")
        for name, desc in WORKFLOWS.items():
            print(f"  {name}: {desc}")
    elif resource == "modules":
        from ..module_registry import list_modules
        modules = list_modules()
        print(f"Available modules ({len(modules)}):")
        for mod in modules[:20]:
            print(f"  {mod}")
        if len(modules) > 20:
            print(f"  ... and {len(modules) - 20} more")
    elif resource == "presets":
        print("Available presets:")
        print("  quick: Fast analysis with single input")
        print("  deep: Comprehensive analysis with multiple inputs")


def cli_main(args: List[str] = None) -> int:
    """Main CLI entry point.

    Args:
        args: Command line arguments (defaults to sys.argv).

    Returns:
        Exit code.
    """
    parser = create_parser()
    parsed = parser.parse_args(args)

    if not parsed.command:
        parser.print_help()
        return 0

    try:
        if parsed.command == "version":
            print("JARVIS Research OS v4.0")
            return 0

        if parsed.command == "list":
            list_resources(parsed.resource)
            return 0

        if parsed.command == "run":
            config = None
            if parsed.config:
                config = load_config(parsed.config)

            result = run_workflow(
                workflow=parsed.workflow,
                inputs=parsed.inputs or [],
                query=parsed.query or "",
                concepts=parsed.concepts,
                output_dir=parsed.out,
                config=config,
            )
            print(f"✓ Workflow '{result['workflow']}' completed")
            print(f"  Output: {result['output_dir']}/")
            return 0

    except JarvisError as e:
        print(f"Error: {e}", file=sys.stderr)
        return e.exit_code
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(cli_main())
