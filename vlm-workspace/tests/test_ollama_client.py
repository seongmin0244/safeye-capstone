import unittest

from app.local.ollama_client import OllamaClient


class FakeOllamaClient(OllamaClient):
    def __init__(self):
        super().__init__(base_url='http://example.test', model='qwen3-vl:8b')
        self.calls = []

    async def _post(self, path, payload, timeout=None):
        self.calls.append(payload.copy())
        if len(self.calls) == 1:
            return {
                'message': {'content': ''},
                'total_duration': 1_000_000,
                'load_duration': 0,
                'prompt_eval_duration': 0,
                'eval_duration': 0,
                'prompt_eval_count': 0,
                'eval_count': 0,
            }
        return {
            'message': {'content': '{"observed_objects": [{"name": "worker", "attributes": ["helmet"], "location": "center"}], "spatial_relations": [], "uncertain": [], "hazard_detected": false, "hazard_type": "없음", "severity": "INFO", "reasoning": "visible worker", "recommended_actions": [], "references": [], "confidence": 0.8}'},
            'total_duration': 2_000_000,
            'load_duration': 0,
            'prompt_eval_duration': 0,
            'eval_duration': 0,
            'prompt_eval_count': 0,
            'eval_count': 0,
        }


class OllamaClientCompatibilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_chat_json_retries_without_structured_format_when_model_returns_empty_text(self):
        client = FakeOllamaClient()
        obj, timing = await client.chat_json(b'img', 'Describe the image', {'type': 'object'})
        self.assertEqual(obj['hazard_detected'], False)
        self.assertEqual(client.calls[0]['format'], {'type': 'object'})
        self.assertEqual(client.calls[1]['format'], 'json')
        self.assertFalse(client.calls[0]['think'])
        self.assertFalse(client.calls[1]['think'])
        self.assertGreater(timing.total_ms, 0)

    async def test_chat_json_rejects_partial_json_after_fallback(self):
        class PartialOllamaClient(OllamaClient):
            def __init__(self):
                super().__init__(base_url='http://example.test', model='qwen3-vl:8b')

            async def _post(self, path, payload, timeout=None):
                return {
                    'message': {
                        'content': '{"hazard_type":"PPE","confidence":0.9}'
                    },
                    'total_duration': 1_000_000,
                }

        with self.assertRaisesRegex(Exception, 'incomplete JSON'):
            await PartialOllamaClient().chat_json(
                b'img', 'Describe the image', {'type': 'object'}
            )


if __name__ == '__main__':
    unittest.main()
