import base64
import os
import unittest

from app.authentication.invalid_token_exception import InvalidTokenException
from app.authentication.jwt_decoder import JWTDecryptor
from tests.app.authentication import TEST_DO_NOT_USE_SR_PRIVATE_PEM, TEST_DO_NOT_USE_SR_PRIVATE_PEM_PASSWORD

# public key from jwt.io

TEST_DO_NOT_USE_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDdlatRjRjogo3Wojg
GHFHYLugdUWAY9iR3fy4arWNA1KoS8kVw33cJibXr8bvwUAUparCwlv
dbH6dvEOfou0/gCFQsHUfQrSDv+MuSUMAe8jzKE4qW+jK+xQU9a03GU
nKHkkle+Q0pX/g6jXZ7r1/xAK5Do2kQ+X5xK9cipRgEKwIDAQAB
-----END PUBLIC KEY-----"""

# jwt.io public key signed

jwtio_header = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkVEQ1JSTSJ9"
jwtio_payload = "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6IjE0NTQ5MzU3NjciLCJleHAi" \
                "OiIyMDc1Mjk3MTQ4In0"
jwtio_signature = "1PVw5ku4uzif8iaXpbEhsSkbnug5mXMYMvBUUpGQyJ73mqtl7oApntEyC-z9jSunqAA0JytOVnV1s39PbCE1tfFtZIcyEddC4d" \
                  "M7oCHAXEjZukUnhX5XQDC323zGQbbOOgoaldHYJU8I_pdbILEtK7QFPKB4mkvEH2YhAIQya3s"

jwtio_signed = jwtio_header + "." + jwtio_payload + "." + jwtio_signature


class JWTTest(unittest.TestCase):  # pylint: disable=too-many-public-methods
    def setUp(self):
        self.decryptor_args = (
            TEST_DO_NOT_USE_SR_PRIVATE_PEM,
            TEST_DO_NOT_USE_SR_PRIVATE_PEM_PASSWORD,
            TEST_DO_NOT_USE_PUBLIC_KEY
        )

        self.leeway = 120

    def test_jwt_io(self):
        decoder = JWTDecryptor(*self.decryptor_args)
        token = decoder.decode_signed_jwt_token(jwtio_signed, self.leeway)
        self.assertEqual("John Doe", token.get("name"))

    def test_does_not_contain_two_instances_of_full_stop(self):
        jwe = jwtio_signed.replace('.', '', 1)
        self.assertInDecodeSignedJWTException(jwe, "Invalid Token")

    def test_jwt_contains_empty_header(self):
        token_without_header = "e30." + jwtio_payload + "." + jwtio_signature

        self.assertInDecodeSignedJWTException(token_without_header, "Missing Headers")

    def test_jwt_does_not_contain_header_at_all(self):
        token_without_header = "." + jwtio_payload + "." + jwtio_signature

        self.assertInDecodeSignedJWTException(token_without_header, "Missing Headers")

    def test_jwt_contains_empty_payload(self):
        token_without_payload = jwtio_header + ".e30." + jwtio_signature

        self.assertInDecodeSignedJWTException(token_without_payload, "Missing Payload")

    def test_jwt_does_not_contain_payload(self):
        token_without_payload = jwtio_header + ".." + jwtio_signature

        self.assertInDecodeSignedJWTException(token_without_payload, "Missing Payload")

    def test_jwt_does_not_contain_signature(self):
        jwt = jwtio_header + "." + jwtio_payload + ".e30"

        self.assertInDecodeSignedJWTException(jwt, "Signature verification failed")

    def test_jose_header_missing_type(self):
        header = base64.urlsafe_b64encode(b'{"alg":"RS256", "kid":"EDCRRM"}')
        jwt = header.decode() + "." + jwtio_payload + "." + jwtio_signature

        self.assertInDecodeSignedJWTException(jwt, "Missing Type")

    def test_jose_header_invalid_type(self):
        header = base64.urlsafe_b64encode(b'{"alg":"RS256", "kid":"EDCRRM", "typ":"TEST"}')
        jwt = header.decode() + "." + jwtio_payload + "." + jwtio_signature

        self.assertInDecodeSignedJWTException(jwt, "Invalid Type")

    def test_jose_header_contains_multiple_type(self):
        header = base64.urlsafe_b64encode(b'{"alg":"RS256", "kid":"EDCRRM","typ":"JWT","typ":"TEST"}')
        jwt = header.decode() + "." + jwtio_payload + "." + jwtio_signature

        self.assertInDecodeSignedJWTException(jwt, "Multiple 'typ' Headers")

    def test_jose_header_missing_alg(self):
        header = base64.urlsafe_b64encode(b'{"kid":"EDCRRM","typ":"JWT"}')
        jwt = header.decode() + "." + jwtio_payload + "." + jwtio_signature

        self.assertInDecodeSignedJWTException(jwt, "Missing Algorithm")

    def test_jose_header_invalid_alg(self):
        header = base64.urlsafe_b64encode(b'{"alg":"invalid","kid":"EDCRRM","typ":"JWT"}')
        jwt = header.decode() + "." + jwtio_payload + "." + jwtio_signature

        self.assertInDecodeSignedJWTException(jwt, "Invalid Algorithm")

    def test_jose_header_none_alg(self):
        header = base64.urlsafe_b64encode(b'{"alg":"None","kid":"EDCRRM","typ":"JWT"}')
        jwt = header.decode() + "." + jwtio_payload + "." + jwtio_signature

        self.assertInDecodeSignedJWTException(jwt, "Invalid Algorithm")

    def test_jose_header_contains_multiple_alg(self):
        header = base64.urlsafe_b64encode(b'{"alg":"RS256", "alg":"HS256","kid":"EDCRRM", "typ":"JWT"}')
        jwt = header.decode() + "." + jwtio_payload + "." + jwtio_signature

        self.assertInDecodeSignedJWTException(jwt, "Multiple 'alg' Headers")

    def test_jose_header_missing_kid(self):
        header = base64.urlsafe_b64encode(b'{"alg":"RS256", "typ":"JWT"}')
        jwt = header.decode() + "." + jwtio_payload + "." + jwtio_signature

        self.assertInDecodeSignedJWTException(jwt, "Missing kid")

    def test_jose_header_contains_multiple_kid(self):
        header = base64.urlsafe_b64encode(b'{"alg":"RS256", "kid":"EDCRRM", "kid":"test", "typ":"JWT"}')
        jwt = header.decode() + "." + jwtio_payload + "." + jwtio_signature

        self.assertInDecodeSignedJWTException(jwt, "Multiple 'kid' Headers")

    def test_jose_header_contains_invalid_kid(self):
        header = base64.urlsafe_b64encode(b'{"alg":"RS256", "kid":"UNKNOWN", "typ":"JWT"}')
        jwt = header.decode() + "." + jwtio_payload + "." + jwtio_signature

        self.assertInDecodeSignedJWTException(jwt, "Invalid Key Identifier")

    def test_signature_not_2048_bits(self):
        jwt = jwtio_header + "." + jwtio_payload + "." + base64.urlsafe_b64encode(os.urandom(255)).decode()

        self.assertInDecodeSignedJWTException(jwt, "Signature verification")

    def test_payload_corrupt(self):
        jwt = jwtio_header + ".asdasd." + jwtio_signature

        self.assertInDecodeSignedJWTException(jwt, "Corrupted Payload")

    def test_header_corrupt(self):
        jwt = "asdsadsa" + "." + jwtio_payload + "." + jwtio_signature

        self.assertInDecodeSignedJWTException(jwt, "Corrupted Header")

    def test_signature_corrupt(self):
        jwt = jwtio_header + "." + jwtio_payload + ".asdasddas"

        self.assertInDecodeSignedJWTException(jwt, "DecodeError")

    def test_payload_contains_malformed_json(self):
        payload = base64.urlsafe_b64encode(b'{"user":"jimmy,"iat": "1454935765","exp": "2075297148"')
        jwt = jwtio_header + "." + payload.decode() + "." + jwtio_signature

        self.assertInDecodeSignedJWTException(jwt, "DecodeError")

    def test_payload_contains_corrupted_json(self):
        payload = base64.urlsafe_b64encode(b'{"user":"jimmy","iat": "1454935765","exp": "2075297148"}ABDCE')
        jwt = jwtio_header + "." + payload.decode() + "." + jwtio_signature

        self.assertInDecodeSignedJWTException(jwt, "DecodeError")

    def test_payload_does_not_contain_exp(self):
        valid_token_no_exp = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkVEQ1JSTSJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibm" \
                             "FtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6IjE0NTQ5MzU3NjcifQ.VupTBEOEzeDjxd37PQ34xv" \
                             "BlLzeGTA0xFdGnLZDcnxAS1AjNcJ66edRmr4tmPIXnD6Mgen3HSB36xuXSnfzPld2msFHUXmB18CoaJQK19BXEY" \
                             "vosrBPzc1ohSvam_DgXCzdSMAcWSE63e6LTWNCT93-npD3p9tjdY_TWpEOOg14"

        self.assertInDecodeSignedJWTException(valid_token_no_exp, "Missing exp claim")

    def test_payload_does_not_contain_iat(self):
        valid_token_no_iat = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkVEQ1JSTSJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibm" \
                             "FtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImV4cCI6IjIwNzUyOTcxNDgifQ.SXWoPBkiXBW9KYaSvjISwQ" \
                             "gdKQuNJ6o5oXA8rwEFiIE9UYo0yALhsQf5BbYs7RmVq760jde2FqwbwHze_XHFlOcg9nODfevEbRAUxjt_jpDaI" \
                             "LWmzreVw8jYTie9qn-F-7Tb6R1fgvvi5Fd7h0Py_LTLTZ72H1NOXCMtL_bbv6Y"

        self.assertInDecodeSignedJWTException(valid_token_no_iat, "Missing iat claim")

    def test_payload_invalid_exp(self):
        valid_token_with_invalid_exp = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkVEQ1JSTSJ9.eyJzdWIiOiIxMjM0NTY3" \
                                       "ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6IjE0NTQ5MzU3NjUiLCJle" \
                                       "HAiOiI_In0.0ApxEXw1rzo21XQo8WgcPvnz0e8QnT0GaoXVbCj-OdJtB7GArPzaiQ1cU53WaJsvGE" \
                                       "zHTczc6Y0xN7WzcTdcXN8Yjenf4VqoiYc6_FXGJ1s9Brd0JOFPyVipTFxPoWvYTWLXE-CAEpXrEb3" \
                                       "0kB3nRjHFV_yVhLiiZUU-gpUHqNQ"

        self.assertInDecodeSignedJWTException(valid_token_with_invalid_exp, "Expiration Time claim (exp) must be an integer")

    def test_payload_invalid_iat(self):
        valid_token_with_invalid_iat = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkVEQ1JSTSJ9.eyJzdWIiOiIxMjM0NTY3" \
                                       "ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6ImEiLCJleHAiOiIyMDc1M" \
                                       "jk3MTQ4In0.1NIuxcD1FsZlU17NxK4UHdCfzl7qTV03qEaTRcqTC6A1Fs2Alc7mSQgkF_SpUw4Ylt" \
                                       "n-7DhO2InfcwDA0VhxBOHDL6ZzcEvzw-49iD-AaSd4aINIkDK-Iim5uzbKzgQCuZqSXFqxsZlezA4" \
                                       "BtwV7Lv2puqdPrXT8k3SvM2rOwRw"

        self.assertInDecodeSignedJWTException(valid_token_with_invalid_iat, "Issued At claim (iat) must be an integer")

    def test_payload_expired_exp(self):
        valid_token_with_exp_in_the_past = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkVEQ1JSTSJ9.eyJzdWIiOiIxMjM" \
                                           "0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6IjE0NTQ5MzU" \
                                           "3NjUiLCJleHAiOiIxNDU0OTM1NzY2In0.PLIaSBh3jiPCsYgx7l1m8enorE7FzYUxVHgarlm" \
                                           "ZiMzpNjNmEzBYBq0yCk7wzkbrJhe5slliaMDY6C4hrAGo8oIUwYp_bQxxDCzyfeXiqdewdPe" \
                                           "L2X8D47Yw-KRt2XF03LXnMEyAaHD9CPhtnSWYUijka5h5yJIG62JTOGWvKGU"

        self.assertInDecodeSignedJWTException(valid_token_with_exp_in_the_past, "Signature has expired")

    def test_payload_exp_less_than_iat(self):
        valid_token_with_exp_less_than_iat = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkVEQ1JSTSJ9.eyJzdWIiOiIxM" \
                                             "jM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6IjE0NTQ" \
                                             "5MzU3NjUiLCJleHAiOiIxNDU0OTM1NzY0In0.p2T1go1DblkgYiYHj_cLV1Jd169sG4bqv" \
                                             "qncTSpYPYawMIkjeb7s0IWFaswi348YLvcaAuQxaq3H5sw6RG3338TmFWYMJhvJTOYCZBC" \
                                             "pvkuu2PTKBAxYlQt9dHuWnFODYtjFgdsJigMrePdY9FIqyifyUAJsUHhA7WagOxUwW_I"

        self.assertInDecodeSignedJWTException(valid_token_with_exp_less_than_iat, "Signature has expired")

    def test_payload_iat_in_future(self):
        # set iat to Oct 2035
        valid_token_with_iat_in_future = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkVEQ1JSTSJ9.eyJzdWIiOiIxMjM0N" \
                                         "TY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6IjIwNzUyOTcxNDc" \
                                         "iLCJleHAiOiIyMDc1Mjk3MTQ4In0.2MQNPXUAiT3AFhbQWoNZ3bs14WeQDloiJfP-3s9ddprzY" \
                                         "tj4omGaym32WvD-f4kBjuEwe479QzpJQoV_oTYCwB8VmFnKd4lKWKMUnNHQYcG0GWVB1Y9qWuW" \
                                         "nPG32kfS2Z7YuMkCgar8qttajB_YRcwhes4rIVaObFFXywnSinCQ"

        self.assertInDecodeSignedJWTException(valid_token_with_iat_in_future, "Issued At claim (iat) cannot be in the future")

    def test_payload_contains_more_than_one_iat(self):
        payload = base64.urlsafe_b64encode(b'{"user":"jimmy",'
                                           b'"iat": "1454935765",'
                                           b'"iat": "1454935765",'
                                           b'"exp": "2075297148"}')
        jwt = jwtio_header + "." + payload.decode() + "." + jwtio_signature

        self.assertInDecodeSignedJWTException(jwt, "Multiple iat claims")

    def test_payload_contains_more_than_one_exp(self):
        payload = base64.urlsafe_b64encode(b'{"user":"jimmy",'
                                           b'"iat": "1454935765",'
                                           b'"exp": "1454935765",'
                                           b'"exp": "2075297148"}')
        jwt = jwtio_header + "." + payload.decode() + "." + jwtio_signature

        self.assertInDecodeSignedJWTException(jwt, "Multiple exp claims")

    def assertInDecodeSignedJWTException(self, jwe, error):
        decoder = JWTDecryptor(*self.decryptor_args)
        with self.assertRaises(InvalidTokenException) as ite:
            decoder.decode_signed_jwt_token(jwe, self.leeway)

        if error not in ite.exception.value:
            raise AssertionError('"{}" not found in decode exception'.format(error))

if __name__ == '__main__':
    unittest.main()
