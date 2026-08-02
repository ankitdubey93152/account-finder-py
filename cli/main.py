import asyncio
from pathlib import Path
from typing import Literal

from rich.console import Console
from rich.table import Table
from sqlalchemy import text
import typer

from core.config import settings
from core.exceptions import OSINTError
from database.session import AsyncSessionLocal
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
    """Check core configuration and database health."""

    async def _check_db() -> str:
        try:
            async with AsyncSessionLocal() as db:
                await db.execute(text("SELECT 1"))
            return "ok"
        except Exception as exc:
            return f"unreachable ({exc})"

    db_status = asyncio.run(_check_db())
    if db_status == "ok":
        console.print(f"[bold green]System Health Status: OK[/bold green] (Database: {db_status}, Environment: {settings.ENV})")
    else:
        console.print(f"[bold red]System Health Status: DEGRADED[/bold red] (Database: {db_status})")


@app.command()
def username(
    name: str,
    concurrency: int = typer.Option(15, min=1, max=20),
    format: Literal["table", "json", "csv"] = typer.Option("table"),
    output: Path | None = typer.Option(None),
) -> None:
    """Check public profile endpoints for a username."""
    if output and format == "table":
        raise typer.BadParameter("--output requires --format json or csv")

    try:
        summary = asyncio.run(scan_username(name, concurrency))
    except OSINTError as exc:
        console.print(f"[bold red]OSINT Error:[/bold red] {exc.message}")
        if exc.detail:
            console.print(f"[dim]Detail: {exc.detail}[/dim]")
        raise typer.Exit(code=1)
    except Exception as exc:
        console.print(f"[bold red]Unexpected Error:[/bold red] {exc}")
        raise typer.Exit(code=1)

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
            status = (
                "[green]yes[/green]"
                if result.exists is True
                else "[red]no[/red]"
                if result.exists is False
                else "[yellow]inconclusive[/yellow]"
            )
            table.add_row(result.platform, status, result.confidence, f"{result.response_time_ms or '-'} ms")
        console.print(table)
        return

    if output:
        output.write_text(content, encoding="utf-8")
        console.print(f"[bold green]Successfully wrote {format} results to {output}[/bold green]")
    else:
        console.print(content)


if __name__ == "__main__":
    app()
