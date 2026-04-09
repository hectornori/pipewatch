"""Entry-point CLI for pipewatch."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

from pipewatch.config import from_file
from pipewatch.monitor import PipelineMonitor

logger = logging.getLogger(__name__)


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        level=level,
    )


@click.group()
@click.option(
    "--config",
    "-c",
    default="config.yaml",
    show_default=True,
    help="Path to pipewatch config file.",
)
@click.option("--verbose", "-v", is_flag=True, default=False, help="Enable debug output.")
@click.pass_context
def cli(ctx: click.Context, config: str, verbose: bool) -> None:
    """pipewatch — monitor ETL pipelines and alert on failure."""
    _configure_logging(verbose)
    ctx.ensure_object(dict)
    config_path = Path(config)
    if not config_path.exists():
        click.echo(f"Config file not found: {config_path}", err=True)
        sys.exit(1)
    ctx.obj["config"] = from_file(config_path)


@cli.command("run")
@click.pass_context
def run_checks(ctx: click.Context) -> None:
    """Run all enabled pipeline checks once."""
    config = ctx.obj["config"]
    monitor = PipelineMonitor(config)
    results = monitor.run_all()

    failures = [r for r in results if not r.success]
    for result in results:
        status = click.style("OK", fg="green") if result.success else click.style("FAIL", fg="red")
        click.echo(f"  [{status}] {result.pipeline_name} ({result.duration_seconds:.2f}s)")

    if failures:
        click.echo(f"\n{len(failures)} pipeline(s) failed.", err=True)
        sys.exit(1)
    else:
        click.echo("\nAll pipelines healthy.")


@cli.command("list")
@click.pass_context
def list_pipelines(ctx: click.Context) -> None:
    """List all configured pipelines."""
    config = ctx.obj["config"]
    for p in config.pipelines:
        enabled_label = click.style("enabled", fg="green") if p.enabled else click.style("disabled", fg="yellow")
        click.echo(f"  {p.name:30s} [{enabled_label}]  cmd: {p.check_command}")


def main() -> None:  # pragma: no cover
    cli()


if __name__ == "__main__":  # pragma: no cover
    main()
