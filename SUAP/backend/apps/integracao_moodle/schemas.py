from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MoodleApiSettings:
    base_url: str
    token: str
    rest_format: str = "json"
    timeout: int = 30
    rest_path: str = "webservice/rest/server.php"
    verify_ssl: bool = True

    def __post_init__(self):
        object.__setattr__(self, "base_url", (self.base_url or "").strip())
        object.__setattr__(self, "token", (self.token or "").strip())
        object.__setattr__(self, "rest_path", (self.rest_path or "webservice/rest/server.php").strip())
        object.__setattr__(self, "rest_format", (self.rest_format or "json").strip().lower())

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.token)