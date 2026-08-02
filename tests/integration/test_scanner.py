from datetime import datetime, timezone

import pytest

from modules.username_search.models import PlatformResult
from modules.username_search.platforms import PlatformSpec
import modules.username_search.scanner as scanner


@pytest.mark.asyncio
async def test_scan_summary_counts_each_outcome(monkeypatch):
    specs = [PlatformSpec(name=name, url_template=f"https://{name}.example/{{username}}", check_method="status_code") for name in ("found", "missing", "error")]
    outcomes = {"found": True, "missing": False, "error": None}

    async def fake_check(client, spec, username):
        return PlatformResult(platform=spec.name, url=spec.url_template.format(username=username), exists=outcomes[spec.name], confidence="high" if outcomes[spec.name] is not None else "low", checked_at=datetime.now(timezone.utc))

    monkeypatch.setattr(scanner, "PLATFORMS", specs)
    monkeypatch.setattr(scanner, "check_platform", fake_check)
    summary = await scanner.scan_username("alice")
    assert (summary.found, summary.not_found, summary.errored) == (1, 1, 1)
    assert summary.total_platforms == 3
    assert summary.found + summary.not_found + summary.errored == summary.total_platforms
