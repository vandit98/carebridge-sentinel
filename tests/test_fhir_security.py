import os

import pytest

from carebridge_sentinel.fhir import validate_fhir_base_url


def test_fhir_url_requires_https_by_default(monkeypatch):
    monkeypatch.delenv("CAREBRIDGE_ALLOW_INSECURE_FHIR", raising=False)

    with pytest.raises(ValueError, match="HTTPS"):
        validate_fhir_base_url("http://example.com/fhir")


def test_fhir_url_blocks_private_ip_without_allowlist(monkeypatch):
    monkeypatch.delenv("CAREBRIDGE_ALLOWED_FHIR_HOSTS", raising=False)

    with pytest.raises(ValueError, match="local/private"):
        validate_fhir_base_url("https://127.0.0.1/fhir")


def test_fhir_url_allows_explicit_host_allowlist(monkeypatch):
    monkeypatch.setenv("CAREBRIDGE_ALLOWED_FHIR_HOSTS", "127.0.0.1")

    validate_fhir_base_url("https://127.0.0.1/fhir")
