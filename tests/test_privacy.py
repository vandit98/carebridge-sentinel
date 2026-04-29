from carebridge_sentinel.privacy import REDACTED, redact


def test_redact_masks_common_phi_and_tokens():
    text = (
        "MRN: ABC-123, DOB 1957-09-12, phone 555-123-4567, "
        "email elena@example.com, SSN 123-45-6789, Bearer abc.def.ghi"
    )

    output = redact(text)

    assert "ABC-123" not in output
    assert "1957-09-12" not in output
    assert "555-123-4567" not in output
    assert "elena@example.com" not in output
    assert "123-45-6789" not in output
    assert "abc.def.ghi" not in output
    assert output.count(REDACTED) >= 6
