from app import app


def client():
    return app.test_client()


def test_health():
    r = client().get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_version():
    assert "version" in client().get("/version").get_json()


def test_quote_returns_a_number():
    r = client().get("/api/quote?amount=300000&rate=6.5&years=30")
    assert r.status_code == 200
    assert r.get_json()["monthly_repayment"] > 0


def test_quote_missing_params():
    assert client().get("/api/quote?amount=300000").status_code == 400


def test_promo_quote_returns_a_number():
    r = client().get("/api/quote?amount=500000&rate=6.5&years=30")
    assert r.status_code == 200
    assert r.get_json()["monthly_repayment"] > 0
