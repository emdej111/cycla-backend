import io

import pytest


@pytest.fixture(autouse=True)
def _isolate_uploads(tmp_path, monkeypatch):
    from src.core.config import get_settings

    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path))
    yield


def test_upload_rejects_unsupported_file_type(client, auth_headers):
    response = client.post(
        "/documents/upload",
        files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_upload_pdf_stores_document_and_runs_analysis(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.documents.analyze_medical_document",
        lambda document_text, user_profile: {
            "summary": "Hormone panel within typical range.",
            "key_values": [{"name": "TSH", "value": "2.1", "reference_range": "0.4-4.0", "flag": "normal"}],
            "flags": [],
        },
    )
    monkeypatch.setattr(
        "src.api.routes.documents._extract_text",
        lambda path, content_type: "TSH: 2.1 mIU/L (ref 0.4-4.0)",
    )

    response = client.post(
        "/documents/upload",
        files={"file": ("labs.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "labs.pdf"
    assert body["affects_personalization"] is False

    listing = client.get("/documents/", headers=auth_headers)
    assert listing.status_code == 200
    assert len(listing.json()["documents"]) == 1

    doc_id = body["id"]
    analysis = client.get(f"/documents/{doc_id}/analysis", headers=auth_headers)
    assert analysis.status_code == 200
    assert analysis.json()["claude_analysis"]["summary"] == "Hormone panel within typical range."


def test_document_upload_survives_analysis_failure(client, auth_headers, monkeypatch):
    def _boom(document_text, user_profile):
        raise RuntimeError("Claude unavailable")

    monkeypatch.setattr("src.api.routes.documents.analyze_medical_document", _boom)
    monkeypatch.setattr("src.api.routes.documents._extract_text", lambda path, content_type: "some text")

    response = client.post(
        "/documents/upload",
        files={"file": ("labs.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["affects_personalization"] is False


def test_analysis_404_for_other_users_document(client, auth_headers):
    response = client.get("/documents/9999/analysis", headers=auth_headers)
    assert response.status_code == 404
