import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
TEST_DB = Path(__file__).resolve().parent / "test_farmacerca.db"
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"

from fastapi.testclient import TestClient  # noqa: E402
import app  # noqa: E402


def main():
    app.init_db()
    client = TestClient(app.app)

    for path in ["/", "/inventory", "/inventory?q=Paracetamol", "/branches", "/alerts", "/transfers", "/products/1", "/health"]:
        response = client.get(path)
        assert response.status_code == 200, (path, response.status_code)

    transfer = client.post(
        "/transfers",
        data={"product_id": 1, "source_branch_id": 1, "destination_branch_id": 4, "quantity": 5},
        follow_redirects=False,
    )
    assert transfer.status_code == 303

    print("Smoke test OK: navegación, detalle de producto y transferencia funcionando.")
    TEST_DB.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
