# Tests package

# TestClient(app) does not fire startup events unless used as a context manager, so apply the same
# hardening the server does at startup (retire plaintext passwords, re-hash the documented demo logins).
from app.main import harden_on_startup  # noqa: E402
harden_on_startup()
