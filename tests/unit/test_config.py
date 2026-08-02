from core.config import settings

def test_default_settings():
    assert settings.APP_NAME == "OSINT Digital Footprint Analyzer"
    assert settings.DEFAULT_TIMEOUT_SECONDS == 8.0
    assert settings.MAX_CONCURRENT_REQUESTS == 10
    assert "sqlite" in settings.DATABASE_URL
