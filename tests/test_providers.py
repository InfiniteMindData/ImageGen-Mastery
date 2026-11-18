import base64
import io
import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from PIL import Image

from imagegen_mastery import providers


def image_bytes(fmt):
    with io.BytesIO() as buffer:
        Image.new("RGB", (8, 8), "red").save(buffer, format=fmt)
        return buffer.getvalue()


class ProviderTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {
            "OPENAI_API_KEY": "openai-test-credential",
            "GEMINI_API_KEY": "google-test-credential",
        }, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        transport = patch("urllib.request.OpenerDirector.open")
        self.http = transport.start()
        self.addCleanup(transport.stop)
        self.png = image_bytes("PNG")
        self.encoded_png = base64.b64encode(self.png).decode("ascii")

    def respond(self, body):
        self.http.return_value = io.BytesIO(json.dumps(body).encode())

    def test_openai_sends_images_request_and_decodes_generated_png(self):
        self.respond({"created": 1710000000, "data": [{"b64_json": self.encoded_png}]})
        result = providers.generate("openai", "gpt-image-1", "A café in ink", authorized=True)
        self.assertEqual(result, self.png)
        request = self.http.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.openai.com/v1/images/generations")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Authorization"), "Bearer openai-test-credential")
        payload = json.loads(request.data)
        self.assertEqual(payload["model"], "gpt-image-1")
        self.assertEqual(payload["prompt"], "A café in ink")
        self.assertEqual(payload["n"], 1)

    def test_gemini_requests_image_and_selects_final_output(self):
        self.respond({"candidates": [{"content": {"parts": [
            {"thought": True, "inlineData": {"mimeType": "image/png", "data": "ignored"}},
            {"text": "Here is the image"},
            {"inlineData": {"mimeType": "image/png", "data": self.encoded_png}},
        ]}, "finishReason": "STOP"}]})
        result = providers.generate("google", "gemini-3.1-flash-lite-image", "A café in ink", authorized=True)
        self.assertEqual(result, self.png)
        request = self.http.call_args.args[0]
        self.assertEqual(request.full_url, "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite-image:generateContent")
        self.assertEqual(request.get_header("X-goog-api-key"), "google-test-credential")
        self.assertEqual(json.loads(request.data)["contents"], [{"parts": [{"text": "A café in ink"}]}])
        self.assertEqual(json.loads(request.data)["generationConfig"]["responseModalities"], ["IMAGE"])

    def test_gemini_can_return_jpeg_which_is_saved_as_png(self):
        jpeg = base64.b64encode(image_bytes("JPEG")).decode()
        self.respond({"candidates": [{"content": {"parts": [
            {"inlineData": {"mimeType": "image/jpeg", "data": jpeg}},
        ]}}]})
        with Image.open(io.BytesIO(providers.generate("google", "model", "test", authorized=True))) as result:
            self.assertEqual(result.format, "PNG")
            self.assertEqual(result.size, (8, 8))
            self.assertGreater(result.getpixel((0, 0))[0], 250)

    def test_animated_and_oversized_images_cannot_be_saved_as_candidates(self):
        with io.BytesIO() as animated:
            Image.new("RGB", (8, 8), "red").save(animated, format="PNG", save_all=True,
                                                append_images=[Image.new("RGB", (8, 8), "blue")])
            images = [animated.getvalue()]
        for size in ((16385, 1), (4097, 4096)):
            with io.BytesIO() as buffer:
                Image.new("1", size).save(buffer, format="PNG")
                images.append(buffer.getvalue())
        for data in images:
            self.respond({"data": [{"b64_json": base64.b64encode(data).decode()}]})
            with self.subTest(size=len(data)), self.assertRaises(providers.ProviderError):
                providers.generate("openai", "model", "test", authorized=True)

    def test_missing_credentials_fail_before_network_access(self):
        for provider, variable in (("openai", "OPENAI_API_KEY"), ("google", "GEMINI_API_KEY")):
            with self.subTest(provider=provider), patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(providers.ProviderError, variable):
                    providers.generate(provider, "example", "A still life", authorized=True)
                self.http.assert_not_called()

    def test_invalid_model_prompt_or_provider_fails_before_network_access(self):
        for args in [
            ("google", "../other:predict?key=fake", "test"),
            ("openai", "gpt-image-1", "  "),
            ("unknown", "model", "test"),
        ]:
            with self.subTest(args=args), self.assertRaises(providers.ProviderError):
                providers.generate(*args, authorized=True)
        self.http.assert_not_called()

    def test_http_and_network_failures_hide_sensitive_error_text(self):
        secret = "openai-test-credential"
        failures = [
            HTTPError("https://api.openai.com", 401, secret, {}, io.BytesIO(secret.encode())),
            URLError(secret),
        ]
        for failure in failures:
            self.http.side_effect = failure
            with self.subTest(failure=type(failure)), self.assertRaises(providers.ProviderError) as caught:
                providers.generate("openai", "gpt-image-1", "test", authorized=True)
            self.assertNotIn(secret, str(caught.exception))

    def test_malformed_missing_filtered_or_invalid_images_raise_provider_errors(self):
        for provider, body in [
            ("openai", b"invalid json"),
            ("openai", b'{"data":[]}'),
            ("google", b'{"promptFeedback":{"blockReason":"SAFETY"}}'),
            ("google", b'{"candidates":[{"content":{"parts":[{"text":"Text only"}]}}]}'),
            ("openai", b'{"data":[{"b64_json":"???"}]}'),
            ("openai", json.dumps({"data": [{"b64_json": base64.b64encode(image_bytes("JPEG")).decode()}]}).encode()),
            ("openai", json.dumps({"data": [{"b64_json": base64.b64encode(self.png[:32]).decode()}]}).encode()),
        ]:
            self.http.return_value = io.BytesIO(body)
            with self.subTest(provider=provider, body=body[:32]), self.assertRaises(providers.ProviderError):
                providers.generate(provider, "example", "test", authorized=True)

    def test_plain_generation_requires_explicit_authorization(self):
        with self.assertRaisesRegex(ValueError, "authorize-paid"):
            providers.generate("openai", "model", "test")
        self.http.assert_not_called()
