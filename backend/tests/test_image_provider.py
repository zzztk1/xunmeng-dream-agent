import base64
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai import image_provider, stepfun, volcano
from app.core.config import settings
from app.services.orchestrator import _normalize


class ImageProviderTests(unittest.TestCase):
    def test_stepfun_json_mode_payload(self):
        response = MagicMock()
        response.json.return_value = {"choices": [{"message": {"content": '{"ok":true}'}}]}
        client = MagicMock()
        client.__enter__.return_value = client
        client.post.return_value = response
        with patch.object(settings, "STEPFUN_API_KEY", "test-only-key"), \
             patch("app.ai.stepfun.httpx.Client", return_value=client):
            content = stepfun.chat([{"role": "user", "content": "json"}], json_mode=True)
        self.assertEqual(content, '{"ok":true}')
        _, kwargs = client.post.call_args
        self.assertEqual(kwargs["json"]["response_format"], {"type": "json_object"})
        self.assertEqual(kwargs["json"]["max_tokens"], 4096)

    def test_narrative_model_marker_is_auditable(self):
        self.assertEqual(_normalize({"scenes": [{"text": "x"}]})["_model"], "fallback")
        self.assertEqual(_normalize({"scenes": [{"text": "x"}], "_model": "step-3.5-flash"})["_model"], "step-3.5-flash")

    def test_dispatches_to_stepfun_by_default(self):
        with patch.object(settings, "IMAGE_PROVIDER", "stepfun"), \
             patch("app.ai.image_provider.stepfun.generate_image", return_value=(b"step", None)) as call:
            result = image_provider.generate_image("dream", seed=7)
        self.assertEqual(result, (b"step", None))
        call.assert_called_once_with("dream", ref_url=None, seed=7, timeout=150.0)

    def test_dispatches_to_volcano_when_selected(self):
        with patch.object(settings, "IMAGE_PROVIDER", "volcano"), \
             patch("app.ai.image_provider.volcano.generate_image", return_value=(b"volcano", "https://tmp")) as call:
            result = image_provider.generate_image("dream", ref_url="https://ref", seed=9)
        self.assertEqual(result, (b"volcano", "https://tmp"))
        call.assert_called_once_with("dream", ref_url="https://ref", seed=9, timeout=150.0)

    def test_volcano_payload_and_download(self):
        response = MagicMock()
        response.json.return_value = {"data": [{"url": "https://temporary.example/image.jpeg"}]}
        image_response = MagicMock(content=b"jpeg-bytes")
        client = MagicMock()
        client.__enter__.return_value = client
        client.post.return_value = response
        client.get.return_value = image_response
        with patch.object(settings, "IMAGE_PROVIDER", "volcano"), \
             patch.object(settings, "VOLCANO_API_KEY", "test-only-key"), \
             patch.object(settings, "VOLCANO_IMAGE_MODEL", "seedream-test"), \
             patch("app.ai.volcano.httpx.Client", return_value=client):
            data, url = volcano.generate_image("moonlit station", ref_url="https://ref", seed=42)
        self.assertEqual(data, b"jpeg-bytes")
        self.assertEqual(url, "https://temporary.example/image.jpeg")
        _, kwargs = client.post.call_args
        self.assertTrue(kwargs["headers"]["Authorization"].startswith("Bearer "))
        self.assertEqual(kwargs["json"]["model"], "seedream-test")
        self.assertEqual(kwargs["json"]["image"], "https://ref")
        self.assertEqual(kwargs["json"]["seed"], 42)
        client.get.assert_called_once_with("https://temporary.example/image.jpeg")

    def test_volcano_accepts_base64_response(self):
        response = MagicMock()
        response.json.return_value = {"data": [{"b64_json": base64.b64encode(b"png-bytes").decode()}]}
        client = MagicMock()
        client.__enter__.return_value = client
        client.post.return_value = response
        with patch.object(settings, "VOLCANO_API_KEY", "test-only-key"), \
             patch("app.ai.volcano.httpx.Client", return_value=client):
            data, url = volcano.generate_image("quiet sea")
        self.assertEqual(data, b"png-bytes")
        self.assertIsNone(url)


if __name__ == "__main__":
    unittest.main()
