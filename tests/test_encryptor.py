"""Tests for envoy_cfg.encryptor."""

import pytest

try:
    from cryptography.fernet import Fernet  # noqa: F401
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not CRYPTO_AVAILABLE, reason="cryptography package not installed"
)

from envoy_cfg.encryptor import ConfigEncryptor, EncryptionError, ENCRYPTED_PREFIX


@pytest.fixture
def encryptor():
    return ConfigEncryptor(key="test-secret-passphrase")


def test_encrypt_value_has_prefix(encryptor):
    result = encryptor.encrypt_value("mysecret")
    assert result.startswith(ENCRYPTED_PREFIX)


def test_decrypt_value_roundtrip(encryptor):
    plaintext = "super-secret-value"
    encrypted = encryptor.encrypt_value(plaintext)
    assert encryptor.decrypt_value(encrypted) == plaintext


def test_decrypt_without_prefix_raises(encryptor):
    with pytest.raises(EncryptionError, match="prefix"):
        encryptor.decrypt_value("no-prefix-here")


def test_decrypt_with_wrong_key_raises():
    enc1 = ConfigEncryptor(key="key-one")
    enc2 = ConfigEncryptor(key="key-two")
    encrypted = enc1.encrypt_value("data")
    with pytest.raises(EncryptionError, match="Decryption failed"):
        enc2.decrypt_value(encrypted)


def test_encrypt_config_encrypts_specified_keys(encryptor):
    config = {"host": "localhost", "password": "s3cr3t", "port": 5432}
    result = encryptor.encrypt_config(config, keys=["password"])
    assert result["host"] == "localhost"
    assert result["port"] == 5432
    assert result["password"].startswith(ENCRYPTED_PREFIX)


def test_encrypt_config_ignores_missing_keys(encryptor):
    config = {"host": "localhost"}
    result = encryptor.encrypt_config(config, keys=["password"])
    assert "password" not in result


def test_encrypt_config_does_not_mutate_original(encryptor):
    config = {"password": "plain"}
    encryptor.encrypt_config(config, keys=["password"])
    assert config["password"] == "plain"


def test_decrypt_config_decrypts_prefixed_values(encryptor):
    encrypted_pw = encryptor.encrypt_value("topsecret")
    config = {"host": "db.example.com", "password": encrypted_pw}
    result = encryptor.decrypt_config(config)
    assert result["password"] == "topsecret"
    assert result["host"] == "db.example.com"


def test_decrypt_config_nested(encryptor):
    encrypted_token = encryptor.encrypt_value("tok123")
    config = {"database": {"token": encrypted_token, "name": "mydb"}}
    result = encryptor.decrypt_config(config)
    assert result["database"]["token"] == "tok123"
    assert result["database"]["name"] == "mydb"


def test_no_key_raises_encryption_error(monkeypatch):
    monkeypatch.delenv("ENVOY_CFG_SECRET_KEY", raising=False)
    with pytest.raises(EncryptionError, match="encryption key"):
        ConfigEncryptor()


def test_key_from_env_var(monkeypatch):
    monkeypatch.setenv("ENVOY_CFG_SECRET_KEY", "env-based-key")
    enc = ConfigEncryptor()
    assert enc.decrypt_value(enc.encrypt_value("hello")) == "hello"
