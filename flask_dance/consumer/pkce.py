import hashlib
from base64 import urlsafe_b64encode

from oauthlib.common import generate_token


def create_code_verifier(length=48):
    """
    Creates a random code verifier using :generate_token: method from :oauthlib.common:
    :param length: Code verifier length. Default: 48
    :return: Code verifier as an urlsafe string.
    """
    return generate_token(length=length)


def _create_s256_code_challenge(code_verifier):
    """
    Calculates SHA 256 code challenge based on provided code_verifier.
    :param code_verifier: Code verifier used to calculate code challenge value. Should be a random urlsafe string.
    :return: Code challenge string.
    """
    _encoding = "utf-8"

    _code_hash = hashlib.sha256(code_verifier.encode(encoding=_encoding)).digest()
    code_challenge = urlsafe_b64encode(_code_hash).decode(encoding=_encoding).replace("=", "")
    return code_challenge


CODE_CHALLENGES_METHODS = {
    "S256": _create_s256_code_challenge,
}


def is_valid_code_challenge_method(method):
    return method in CODE_CHALLENGES_METHODS.keys()


def create_code_challenge(code_verifier, method):
    if is_valid_code_challenge_method(method):
        code_challenge = CODE_CHALLENGES_METHODS[method](code_verifier)
        return code_challenge
    return None
