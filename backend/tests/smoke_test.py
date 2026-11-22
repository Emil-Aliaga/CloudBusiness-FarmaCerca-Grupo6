import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TEST_DB = Path(__file__).resolve().parent / "test_farmacerca.db"
TEST_DB.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["ENVIRONMENT"] = "test"
os.environ["SEED_DEMO_DATA"] = "true"

from fastapi.testclient import TestClient  # noqa: E402
import app  # noqa: E402


def main():
    app.init_db()
    client = TestClient(app.app)

    for path in [
        "/health",
        "/api/dashboard",
        "/api/inventory",
        "/api/inventory?q=Paracetamol",
        "/api/branches",
        "/api/alerts",
        "/api/transfers",
        "/api/products/1",
    ]:
        response = client.get(path)
        assert response.status_code == 200, (path, response.status_code, response.text)

    update = client.patch("/api/inventory/1", json={"stock": 40})
    assert update.status_code == 200, update.text

    transfer = client.post("/api/transfers", json={
        "product_id": 1,
        "source_branch_id": 1,
        "destination_branch_id": 4,
        "quantity": 5,
    })
    assert transfer.status_code == 201, transfer.text

    print("Backend smoke test OK")
    TEST_DB.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
