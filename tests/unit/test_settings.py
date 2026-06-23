from app.settings import Settings, get_settings


def test_default_database_url() -> None:
    settings = Settings()
    assert settings.database_url == 'sqlite:///./data/app.db'


def test_default_upload_dir() -> None:
    settings = Settings()
    assert settings.upload_dir == './data/uploads'


def test_environment_variables_override_defaults(monkeypatch) -> None:
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///test.db')
    monkeypatch.setenv('UPLOAD_DIR', '/tmp/uploads')
    settings = Settings()
    assert settings.database_url == 'sqlite:///test.db'
    assert settings.upload_dir == '/tmp/uploads'


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()
