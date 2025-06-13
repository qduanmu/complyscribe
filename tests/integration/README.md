# Integration Testing

The purpose of the integration tests is to validate that complyscribe produces output that downstream utilities, like complytime, can consume.

The `complytime_home` fixture in `tests/integration/conftest.py` will download, cache, and install complytime to a temporary directory per test.

If integration tests fail, your cached complytime download may be stale; delete `/tmp/complyscribe-complytime-cache` and try again.

