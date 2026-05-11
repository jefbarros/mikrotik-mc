import pytest

from src.sanitizer import sanitize_text


@pytest.mark.parametrize(
    "sample,expected",
    [
        ("password=abc", "password=********"),
        ("passwd=abc", "passwd=********"),
        ("pwd=abc", "pwd=********"),
        ("secret=MinhaSenha123", "secret=********"),
        ("shared-secret=minha-chave", "shared-secret=********"),
        ("pre-shared-key=abc", "pre-shared-key=********"),
        ("token=abc", "token=********"),
        ("api-key=abc", "api-key=********"),
        ("apikey=abc", "apikey=********"),
        ("access-token=abc", "access-token=********"),
        ("refresh-token=abc", "refresh-token=********"),
        ("certificate=abc", "certificate=********"),
        ("identity=abc", "identity=********"),
        ("auth-key=abc", "auth-key=********"),
        ("passphrase=abc", "passphrase=********"),
        ("smtp-password=abc", "smtp-password=********"),
        ("wireguard-private-key=abc", "wireguard-private-key=********"),
        ("wpa-pre-shared-key=abc", "wpa-pre-shared-key=********"),
        ('password="abc 123"', "password=********"),
        ("password=abc 123 next=value", "password=******** next=value"),
        ("email=usuario@dominio.com.br", "email=***@***.***"),
    ],
)
def test_sensitive_patterns_are_masked(sample, expected):
    assert sanitize_text(sample) == expected


def test_does_not_remove_entire_line():
    text = "name=vpn secret=abc profile=default"
    assert sanitize_text(text) == "name=vpn secret=******** profile=default"


def test_common_text_is_unchanged():
    text = "interface ether1 running yes"
    assert sanitize_text(text) == text

