import base64
import io
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from imagegen_mastery.inspection import inspect_image
from imagegen_mastery.profiles import get_profile
from imagegen_mastery.providers import ProviderError
from imagegen_mastery.workflow import run_loop


class ProfileTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source.png"
        Image.new("RGB", (12, 8), "blue").save(self.source)
        self.review = {"defects": [], "uncertainties": [], "locks": []}

    def run_case(self, **options):
        return run_loop({"intent": "Blue rectangle"}, self.root / "run", authorized=True,
                        **{"budget": "2", "max_revisions": 0, **options})

    def test_profiles_round_up_and_fail_closed(self):
        self.assertEqual(get_profile("image", "google", None).reserve, Decimal("2.04"))
        self.assertEqual(get_profile("vision", "openai", None).reserve, Decimal("0.22"))
        self.assertEqual(get_profile("vision", "openai", "gpt-5.4-nano-2026-03-17").reserve, Decimal("0.09"))
        with patch("urllib.request.OpenerDirector.open") as transport:
            with self.assertRaisesRegex(ValueError, "maximum cost.*OpenAI"):
                self.run_case(image_provider="openai", image_model="gpt-image-2.5-flare")
            with self.assertRaisesRegex(ValueError, "No verified vision"):
                self.run_case(vision_provider="google", vision_model="unreviewed")
            transport.assert_not_called()
            self.assertFalse((self.root / "run").exists())

    def test_lite_preflights_revision_input_slots_before_generation(self):
        with patch("urllib.request.OpenerDirector.open") as transport, self.assertRaisesRegex(ValueError, "input images"):
            self.run_case(image_model="gemini-3.1-flash-lite-image", max_revisions=1, references=[self.source])
        transport.assert_not_called()

    def test_all_google_loop_reserves_the_selected_pair_and_sends_pixels(self):
        image_part = {"inlineData": {"mimeType": "image/png", "data": base64.b64encode(self.source.read_bytes()).decode()}}
        image_response = {"candidates": [{"content": {"parts": [image_part]}}]}
        parts = [{"text": "ignored internal part", "thought": True}, {"text": json.dumps(self.review)}]
        vision_response = {"candidates": [{"finishReason": "STOP", "content": {"parts": parts}}],
                           "usageMetadata": {"promptTokenCount": 901, "totalTokenCount": 983}}
        with patch.dict("os.environ", {"GEMINI_API_KEY": "example"}, clear=True), patch(
            "urllib.request.OpenerDirector.open", side_effect=[
                io.BytesIO(json.dumps(body).encode()) for body in (image_response, vision_response)
            ]) as transport:
            result = self.run_case(image_model="gemini-3.1-flash-lite-image", vision_provider="google", budget="0.51")
        self.assertEqual(result["status"], "no_observed_defects")
        self.assertEqual((result["cost_basis"], result["reserved_usd"]), ("reservations_only", "0.51"))
        self.assertEqual([(r["model"], r["reserve_usd"]) for r in result["requests"]],
                         [("gemini-3.1-flash-lite-image", "0.14"), ("gemini-3.1-flash-lite", "0.37")])
        image_request, vision_request = [call.args[0] for call in transport.call_args_list]
        self.assertTrue(image_request.full_url.endswith("/gemini-3.1-flash-lite-image:generateContent"))
        self.assertTrue(vision_request.full_url.endswith("/gemini-3.1-flash-lite:generateContent"))
        payload = json.loads(vision_request.data)
        self.assertEqual(payload["generationConfig"]["responseMimeType"], "application/json")
        self.assertEqual(payload["generationConfig"]["maxOutputTokens"], 2048)
        parts = payload["contents"][0]["parts"]
        self.assertEqual(parts[1]["text"], "candidate")
        with Image.open(io.BytesIO(base64.b64decode(parts[2]["inlineData"]["data"]))) as image:
            self.assertEqual(image.getpixel((0, 0)), (0, 0, 255))
        evidence = json.loads((self.root / "run" / "v000.json").read_text())
        self.assertEqual(evidence["provider_usage"]["promptTokenCount"], 901)

    def test_selected_pair_requires_full_reservation_before_render(self):
        with patch("urllib.request.OpenerDirector.open") as transport:
            result = self.run_case(image_model="gemini-3.1-flash-lite-image", vision_provider="google", budget="0.50")
        self.assertEqual((result["status"], result["requests"]), ("budget_limit", []))
        transport.assert_not_called()

    def test_google_inspector_rejects_blocked_partial_and_invalid_evidence(self):
        content = {"parts": [{"text": json.dumps(self.review)}]}
        responses = [{"candidates": [{"content": content, "finishReason": "MAX_TOKENS"}]},
                     {"promptFeedback": {"blockReason": "SAFETY"}},
                     {"candidates": [{"content": {"parts": [{"text": "{}"}]}, "finishReason": "STOP"}]}]
        for response in responses:
            with self.subTest(response=response), patch.dict("os.environ", {"GEMINI_API_KEY": "example"}), patch(
                "imagegen_mastery.inspection._post", return_value=response
            ), self.assertRaisesRegex(ProviderError, "invalid evidence"):
                inspect_image(self.source, ["blue"], provider="google", authorized=True)

    def test_selected_openai_snapshot_and_service_tier(self):
        response = {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(self.review)}}],
                    "usage": {"completion_tokens": 51, "prompt_tokens": 99}}
        with patch.dict("os.environ", {"OPENAI_API_KEY": "example"}, clear=True), patch(
            "imagegen_mastery.inspection._post", return_value=response
        ) as post:
            result = inspect_image(self.source, ["blue"], model="gpt-5.4-nano-2026-03-17", authorized=True)
        payload = post.call_args.args[2]
        self.assertEqual((payload["model"], payload["service_tier"]), ("gpt-5.4-nano-2026-03-17", "default"))
        self.assertEqual(result["provider_usage"]["completion_tokens"], 51)
