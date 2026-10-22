"""Structured form coverage and the server-only reporting-service boundary."""
import copy
import json
from pathlib import Path
import sys

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from primer import reporting_bridge


@pytest.fixture
def bridge_client(monkeypatch):
    # Do not consult the developer's local credential file during tests.
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("REPORTING_SERVICE_URL", "https://reporting.example")
    monkeypatch.setenv("REPORTING_API_KEY", "test-key-only")
    app = FastAPI()
    app.include_router(reporting_bridge.router)
    with TestClient(app) as client:
        yield client


def fake_upstream(monkeypatch, response=None, error=None):
    calls = []

    class Client:
        def __init__(self, **kwargs):
            assert kwargs == {"timeout": 15, "follow_redirects": False}

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def request(self, method, url, **kwargs):
            calls.append((method, url, kwargs))
            if error:
                raise error
            return response

    monkeypatch.setattr(reporting_bridge.httpx, "AsyncClient", Client)
    return calls


def test_calculation_proxy_keeps_credentials_server_side(bridge_client, monkeypatch):
    result = {"calculator_id": "pirads_v2_1", "status": "incomplete", "missing_inputs": ["zone"]}
    calls = fake_upstream(monkeypatch, httpx.Response(200, json=result))
    response = bridge_client.post("/api/radiology/reporting/calculators/pirads_v2_1/calculate",
                                  json={"inputs": {"zone": None}})
    assert response.status_code == 200
    assert response.json() == result
    assert response.headers["cache-control"] == "no-store"
    assert "test-key-only" not in response.text
    method, url, request = calls[0]
    assert method == "POST"
    assert url == "https://reporting.example/v1/calculators/pirads_v2_1/calculate"
    assert request["headers"] == {"Authorization": "Bearer test-key-only"}
    assert request["json"] == {"inputs": {"zone": None}}


def test_unknown_calculators_never_reach_upstream(bridge_client, monkeypatch):
    calls = fake_upstream(monkeypatch)
    assert bridge_client.get("/api/radiology/reporting/calculators/unknown").status_code == 404
    assert bridge_client.post("/api/radiology/reporting/calculators/unknown/calculate", json={}).status_code == 404
    assert calls == []


@pytest.mark.parametrize("code", [400, 404, 409, 422])
def test_reviewable_upstream_errors_are_preserved(bridge_client, monkeypatch, code):
    error = {"error": {"code": "invalid_calculation", "message": "Review inputs."}}
    fake_upstream(monkeypatch, httpx.Response(code, json=error))
    response = bridge_client.get("/api/radiology/reporting/calculators/acr_tirads_2017")
    assert response.status_code == code
    assert response.json() == error
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("code", [401, 403, 500])
def test_upstream_auth_and_server_errors_are_redacted(bridge_client, monkeypatch, code):
    fake_upstream(monkeypatch, httpx.Response(code, json={"private_detail": "do not relay"}))
    response = bridge_client.get("/api/radiology/reporting/calculators/acr_tirads_2017")
    assert response.status_code == 503
    assert "private_detail" not in response.text


def test_unavailable_or_unconfigured_upstream_does_not_leak_details(bridge_client, monkeypatch):
    calls = fake_upstream(monkeypatch, error=RuntimeError("private upstream information"))
    response = bridge_client.get("/api/radiology/reporting/calculators/cadrads_2_0")
    assert response.status_code == 503
    assert "private upstream information" not in response.text
    monkeypatch.delenv("REPORTING_API_KEY")
    response = bridge_client.get("/api/radiology/reporting/calculators/cadrads_2_0")
    assert response.status_code == 503
    assert len(calls) == 1


def test_oversized_calculation_payload_never_reaches_upstream(bridge_client, monkeypatch):
    calls = fake_upstream(monkeypatch)
    response = bridge_client.post("/api/radiology/reporting/calculators/cadrads_2_0/calculate",
                                  json={"inputs": {"extra": "x" * 100_001}})
    assert response.status_code == 413
    assert calls == []


def test_every_clinical_guide_has_an_unanswered_structured_form():
    source = json.loads((ROOT / "data/curriculum/11-radiology.json").read_text())
    nodes = source["nodes"]
    guide_ids = {node["id"] for node in nodes if node["id"].startswith("rad.")}
    catalogue = json.loads((ROOT / "data/radiology/structured-reporting.json").read_text())
    assert len(guide_ids) == 96
    assert set(catalogue["forms"]) == guide_ids
    for guide_id, form in catalogue["forms"].items():
        assert form["guide_id"] == guide_id
        fields = [field for section in form["sections"] for field in section["fields"]]
        assert fields and any(field["type"] == "select" for field in fields)
        assert all(field["default"] is None for field in fields)
        assert form["checklist"] and all(item["default"] is None for item in form["checklist"])
        by_id = {field["id"]: field for field in fields}
        assert len(by_id) == len(fields)
        for field in fields:
            condition = field.get("visible_when")
            if condition:
                assert condition["field_id"] in by_id
                assert ("equals" in condition) != ("in" in condition)


def test_structured_forms_attach_to_guide_without_mutating_catalogue(monkeypatch):
    from primer import radiology
    nodes = json.loads((ROOT / "data/curriculum/11-radiology.json").read_text())["nodes"]
    nodes = [node for node in nodes if node["id"].startswith("rad.")]
    # Media integrity has its own contracts; this test targets form attachment.
    monkeypatch.setattr(radiology, "validate_image_source", lambda value: None)
    from primer import source_native_inspectors
    monkeypatch.setattr(source_native_inspectors, "references",
                        lambda: {"ra.ct-pulmonary-nodules": [{"id": "test-native-inspector"}]})
    radiology.attach_references(nodes)
    catalogue = json.loads((ROOT / "data/radiology/structured-reporting.json").read_text())
    for node in nodes:
        form = node["radiology_reference"]["structured_form"]
        assert form["guide_id"] == node["id"]
        assert form["form_version"] == catalogue["schema_hash"]
        original = copy.deepcopy(catalogue["forms"][node["id"]])
        assert {key: value for key, value in form.items() if key != "form_version"} == original
    nodes[0]["radiology_reference"]["structured_form"]["sections"].clear()
    radiology.attach_references(nodes)
    assert nodes[0]["radiology_reference"]["structured_form"]["sections"]
