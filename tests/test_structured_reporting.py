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
    monkeypatch.setenv("REPORTING_SERVICE_URL", "https://radiology-reporting-api.vercel.app")
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
    assert url == "https://radiology-reporting-api.vercel.app/v1/calculators/pirads_v2_1/calculate"
    assert request["headers"] == {"Authorization": "Bearer test-key-only"}
    assert request["json"] == {"inputs": {"zone": None}}


@pytest.mark.parametrize("identifier", ["acr_tirads_2017", "pirads_v2_1", "cadrads_2_0", "prostate_volume_psad"])
def test_upstream_paths_come_only_from_literal_route_map(bridge_client, monkeypatch, identifier):
    calls = fake_upstream(monkeypatch, httpx.Response(200, json={"calculator_id": identifier}))
    response = bridge_client.get("/api/radiology/reporting/calculators/" + identifier)
    assert response.status_code == 200
    assert calls[0][0:2] == ("GET", "https://radiology-reporting-api.vercel.app/v1/" + reporting_bridge.CALCULATOR_PATHS[identifier])


@pytest.mark.parametrize("origin", ["https://untrusted.example", "http://169.254.169.254", "http://127.0.0.1:22",
                                   "https://radiology-reporting-api.vercel.app.evil.example",
                                   "https://radiology-reporting-api.vercel.app/private",
                                   "https://user:password@radiology-reporting-api.vercel.app"])
def test_unapproved_origin_cannot_receive_reporting_key(bridge_client, monkeypatch, origin):
    calls = fake_upstream(monkeypatch)
    monkeypatch.setenv("REPORTING_SERVICE_URL", origin)
    response = bridge_client.get("/api/radiology/reporting/calculators/pirads_v2_1")
    assert response.status_code == 503
    assert "test-key-only" not in response.text
    assert calls == []


@pytest.mark.parametrize("origin", ["http://localhost:8770", "http://127.0.0.1:8770"])
def test_explicit_local_reporting_origins_remain_available(bridge_client, monkeypatch, origin):
    calls = fake_upstream(monkeypatch, httpx.Response(200, json={"status": "incomplete"}))
    monkeypatch.setenv("REPORTING_SERVICE_URL", origin)
    assert bridge_client.get("/api/radiology/reporting/calculators/pirads_v2_1").status_code == 200
    assert calls[0][1] == origin + "/v1/calculators/pirads_v2_1"


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
    assert len(guide_ids) == 96
    cardiology = json.loads((ROOT / "data/radiology/cardiology-investigations.json").read_text())
    cardiology_ids = {item["id"] for item in cardiology["investigations"]}
    assert cardiology_ids == {"cardiology.echocardiography", "cardiology.percutaneous-angiography"}
    guide_ids.update(cardiology_ids)
    catalogue = json.loads((ROOT / "data/radiology/structured-reporting.json").read_text())
    assert len(catalogue["forms"]) == 98
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


def test_reporting_response_adds_form_without_mutating_canonical_lesson_data():
    catalogue = json.loads((ROOT / "data/radiology/structured-reporting.json").read_text())
    for guide_id, form in catalogue["forms"].items():
        canonical = {"id": "an-investigation", "module_id": guide_id,
                     "radiology_reference": {"overview": "Existing authored reference."}}
        before = copy.deepcopy(canonical)
        response = reporting_bridge.with_structured_form(canonical)
        assert canonical == before
        attached = response["radiology_reference"]["structured_form"]
        assert attached["guide_id"] == guide_id
        assert attached["form_version"] == catalogue["schema_hash"]
        additions = {"form_version", "descriptor_form", "descriptor_version", "snapshot_id"}
        assert {key: value for key, value in attached.items() if key not in additions} == form
        assert attached["descriptor_form"]["guide_id"] == guide_id
        assert attached["descriptor_form"]["selected_investigation_id"] == canonical["id"]
        assert attached["descriptor_version"] == reporting_bridge.descriptor_forms()["forms"][guide_id]["schema_hash"]
        attached["sections"].clear()
        assert reporting_bridge.with_structured_form(canonical)["radiology_reference"]["structured_form"]["sections"]
    unknown = {"module_id": "cardiology.echo", "radiology_reference": {"overview": "Separate source."}}
    assert reporting_bridge.with_structured_form(unknown) == unknown
