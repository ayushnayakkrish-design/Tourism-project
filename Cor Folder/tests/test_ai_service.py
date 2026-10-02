from app.services.ai_service import AIService


def test_extract_output_text_from_raw_responses_payload():
    payload = {
        "output": [{"type": "message", "content": [{"type": "output_text", "text": '{"bullets":["Route is feasible"]}'}]}]
    }
    assert AIService._extract_output_text(payload) == '{"bullets":["Route is feasible"]}'
