"""
Integration tests for the Stock Portfolio REST API.
Requires the Spring Boot app to be running at BASE_URL.
"""

import os
import pytest
import requests

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080/api/stocks")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_stock(symbol="AAPL", quantity=10, buy_price=175.50):
    """POST a stock and return the parsed response body."""
    payload = {"symbol": symbol, "quantity": quantity, "buyPrice": buy_price}
    response = requests.post(BASE_URL, json=payload)
    assert response.status_code == 201, (
        f"Expected 201 Created, got {response.status_code}: {response.text}"
    )
    return response.json()


def delete_stock(stock_id):
    """DELETE a stock and assert 204 No Content."""
    response = requests.delete(f"{BASE_URL}/{stock_id}")
    assert response.status_code == 204, (
        f"Expected 204 No Content, got {response.status_code}: {response.text}"
    )


# ---------------------------------------------------------------------------
# Test: GET /api/stocks  —  list all stocks
# ---------------------------------------------------------------------------

class TestListStocks:
    def test_list_stocks_returns_200(self):
        response = requests.get(BASE_URL)
        assert response.status_code == 200

    def test_list_stocks_returns_json_array(self):
        response = requests.get(BASE_URL)
        assert response.headers["Content-Type"].startswith("application/json")
        assert isinstance(response.json(), list)

    def test_list_stocks_includes_created_stock(self):
        stock = create_stock("MSFT", 5, 420.00)
        stock_id = stock["id"]

        try:
            ids = [s["id"] for s in requests.get(BASE_URL).json()]
            assert stock_id in ids, f"Stock id {stock_id} not found in list"
        finally:
            delete_stock(stock_id)


# ---------------------------------------------------------------------------
# Test: POST /api/stocks  —  add a stock
# ---------------------------------------------------------------------------

class TestAddStock:
    def test_add_stock_returns_201(self):
        payload = {"symbol": "GOOGL", "quantity": 3, "buyPrice": 170.25}
        response = requests.post(BASE_URL, json=payload)
        assert response.status_code == 201
        delete_stock(response.json()["id"])

    def test_add_stock_response_contains_id(self):
        stock = create_stock("TSLA", 2, 250.00)
        assert "id" in stock and stock["id"] is not None
        delete_stock(stock["id"])

    def test_add_stock_fields_are_persisted(self):
        stock = create_stock("AMZN", 7, 185.99)
        try:
            assert stock["symbol"]   == "AMZN"
            assert stock["quantity"] == 7
            assert float(stock["buyPrice"]) == pytest.approx(185.99, rel=1e-4)
        finally:
            delete_stock(stock["id"])

    def test_add_multiple_stocks_get_unique_ids(self):
        s1 = create_stock("NFLX", 4, 630.00)
        s2 = create_stock("NVDA", 6, 880.00)
        try:
            assert s1["id"] != s2["id"]
        finally:
            delete_stock(s1["id"])
            delete_stock(s2["id"])


# ---------------------------------------------------------------------------
# Test: GET /api/stocks/{id}  —  get by id
# ---------------------------------------------------------------------------

class TestGetStockById:
    def test_get_existing_stock_returns_200(self):
        stock = create_stock("META", 1, 510.00)
        try:
            response = requests.get(f"{BASE_URL}/{stock['id']}")
            assert response.status_code == 200
        finally:
            delete_stock(stock["id"])

    def test_get_stock_returns_correct_data(self):
        stock = create_stock("AMD", 12, 175.00)
        try:
            fetched = requests.get(f"{BASE_URL}/{stock['id']}").json()
            assert fetched["id"]       == stock["id"]
            assert fetched["symbol"]   == "AMD"
            assert fetched["quantity"] == 12
            assert float(fetched["buyPrice"]) == pytest.approx(175.00, rel=1e-4)
        finally:
            delete_stock(stock["id"])

    def test_get_nonexistent_stock_returns_404(self):
        response = requests.get(f"{BASE_URL}/999999")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Test: PUT /api/stocks/{id}  —  update a stock
# ---------------------------------------------------------------------------

class TestUpdateStock:
    def test_update_stock_returns_200(self):
        stock = create_stock("ORCL", 5, 130.00)
        try:
            updated_payload = {"symbol": "ORCL", "quantity": 10, "buyPrice": 135.00}
            response = requests.put(f"{BASE_URL}/{stock['id']}", json=updated_payload)
            assert response.status_code == 200
        finally:
            delete_stock(stock["id"])

    def test_update_stock_persists_changes(self):
        stock = create_stock("IBM", 3, 195.00)
        try:
            updated_payload = {"symbol": "IBM", "quantity": 9, "buyPrice": 200.00}
            requests.put(f"{BASE_URL}/{stock['id']}", json=updated_payload)
            fetched = requests.get(f"{BASE_URL}/{stock['id']}").json()
            assert fetched["quantity"] == 9
            assert float(fetched["buyPrice"]) == pytest.approx(200.00, rel=1e-4)
        finally:
            delete_stock(stock["id"])

    def test_update_nonexistent_stock_returns_404(self):
        payload = {"symbol": "XYZ", "quantity": 1, "buyPrice": 1.00}
        response = requests.put(f"{BASE_URL}/999999", json=payload)
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Test: DELETE /api/stocks/{id}  —  delete a stock
# ---------------------------------------------------------------------------

class TestDeleteStock:
    def test_delete_stock_returns_204(self):
        stock = create_stock("PYPL", 2, 65.00)
        response = requests.delete(f"{BASE_URL}/{stock['id']}")
        assert response.status_code == 204

    def test_deleted_stock_is_no_longer_retrievable(self):
        stock = create_stock("SNAP", 8, 12.00)
        delete_stock(stock["id"])
        response = requests.get(f"{BASE_URL}/{stock['id']}")
        assert response.status_code == 404

    def test_deleted_stock_absent_from_list(self):
        stock = create_stock("UBER", 3, 75.00)
        delete_stock(stock["id"])
        ids = [s["id"] for s in requests.get(BASE_URL).json()]
        assert stock["id"] not in ids

    def test_delete_nonexistent_stock_returns_404(self):
        response = requests.delete(f"{BASE_URL}/999999")
        assert response.status_code == 404
