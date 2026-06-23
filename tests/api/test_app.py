from app.main import app


def test_app_can_be_imported():
    assert app is not None


def test_app_metadata():
    assert app.title == 'Audio Transcription API'
    assert app.version == '0.1.0'
    assert 'Faster Whisper' in app.description
