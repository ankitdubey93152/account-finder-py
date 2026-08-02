from typing import Literal

from pydantic import BaseModel, Field


class PlatformSpec(BaseModel):
    name: str
    url_template: str
    check_method: Literal["status_code", "text_match", "text_absence", "json_field"]
    existence_indicator: str | None = None
    absence_indicator: str | None = None
    expected_status: int = 200
    json_exists_path: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    min_delay_seconds: float = 0.5
    enabled: bool = True


# Only endpoints with an explicitly documented/public response contract are enabled.
PLATFORMS: list[PlatformSpec] = [
    PlatformSpec(name="GitHub", url_template="https://api.github.com/users/{username}", check_method="json_field", json_exists_path="login"),
    PlatformSpec(name="Reddit", url_template="https://www.reddit.com/user/{username}/about.json", check_method="json_field", json_exists_path="data.name", headers={"Accept": "application/json"}),
    PlatformSpec(name="GitLab", url_template="https://gitlab.com/{username}", check_method="text_absence", absence_indicator="Page Not Found"),
    PlatformSpec(name="Docker Hub", url_template="https://hub.docker.com/v2/users/{username}/", check_method="status_code"),
    PlatformSpec(name="Keybase", url_template="https://keybase.io/{username}", check_method="status_code"),
]
