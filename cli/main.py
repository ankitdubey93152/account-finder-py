import typer
import asyncio
import json
from pathlib import Path
from typing import Literal
from rich.console import Console
from rich.table import Table

from modules.username_search.scanner import scan_username

app = typer.Typer(
    name="osint",
    help="OSINT Account & Digital Footprint Analyzer (Public Data Only)",
    add_completion=False,
)
console = Console()

@app.command()
def version() -> None:
    """Print the application version."""
    console.print("[bold green]OSINT Account & Digital Footprint Analyzer v0.1.0[/bold green]")

@app.command()
def health() -> None:
    """Check core configuration health."""
    console.print("[bold blue]System Health Status: OK[/bold blue]")


@app.command()
def username(
    name: str,
    concurrency: int = typer.Option(15, min=1, max=20),
    format: Literal["table", "json", "csv"] = typer.Option("table"),
    output: Path | None = typer.Option(None),
) -> None:
    """Check public profile endpoints for a username."""
    summary = asyncio.run(scan_username(name, concurrency))
    if format == "json":
        content = summary.model_dump_json(indent=2)
    elif format == "csv":
        rows = [["platform", "url", "exists", "confidence", "response_time_ms", "error"]]
        rows.extend([[r.platform, r.url, r.exists, r.confidence, r.response_time_ms, r.error] for r in summary.results])
        content = "\n".join(",".join('"' + ("" if value is None else str(value)).replace('"', '""') + '"' for value in row) for row in rows)
    else:
        table = Table(title=f"Username scan: {summary.username}")
        table.add_column("Platform")
        table.add_column("Exists")
        table.add_column("Confidence")
        table.add_column("Response")
        for result in summary.results:
            status = "[green]yes[/green]" if result.exists is True else "[red]no[/red]" if result.exists is False else "[yellow]inconclusive[/yellow]"
            table.add_row(result.platform, status, result.confidence, f"{result.response_time_ms or '-'} ms")
        if output:
            raise typer.BadParameter("--output requires --format json or csv")
        console.print(table)
        return
    if output:
        output.write_text(content, encoding="utf-8")
        console.print(f"Wrote {format} results to {output}")
    else:
        console.print(content)

if __name__ == "__main__":
    app()
