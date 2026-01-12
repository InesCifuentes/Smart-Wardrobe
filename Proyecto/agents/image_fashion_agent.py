import os
import requests
import json
import logging
from agents.agent_prompt import IMAGE_FASHION_PROMPT
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

load_dotenv()

class ImageFashionAgent:
    """
    Agent that suggests fashion items based on image metadata and user requests.
    """

    def __init__(self, model_name="meta-llama/Llama-3.1-8B-Instruct"):
        self.api_key = os.getenv("HF_API_KEY")
        if not self.api_key:
            raise ValueError("⚠️ HF_API_KEY not found in .env")
        self.model_name = model_name
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def generate_suggestions(self, metadata, user_request, filters=None):
        """
        Generates suggestions based on image metadata, user request and optional user filters.

        `filters` should be a dict containing keys like `gender`, `styles`, `colors`, `season`, `occasions`.
        These filters will be included in the user message so the model can consider them.
        """

        metadata_json = json.dumps(metadata or {}, separators=(",", ":"))
        filters_json = json.dumps(filters or {}, separators=(",", ":"))

        # Log the filters for debugging
        logging.info(f"Using filters: {filters_json}")

        # Build a single, unambiguous JSON payload in the user message so the model
        # clearly receives `Filters`, `Metadata` and `Request` keys.
        combined = {
            "Filters": filters or {},
            "Metadata": metadata or {},
            "Request": user_request
        }

        combined_json = json.dumps(combined, ensure_ascii=False, separators=(',', ':'))

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": IMAGE_FASHION_PROMPT},
                {"role": "user", "content": combined_json}
            ]
        }

        response = requests.post(
            "https://router.huggingface.co/v1/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            raise RuntimeError(f"Model error {response.status_code}: {response.text}")

        content = response.json()["choices"][0]["message"]["content"]

        # Log the model response for debugging
        logging.info(f"Model response: {content}")

        try:
            suggestions = json.loads(content)
            if not isinstance(suggestions, list):
                raise ValueError("Invalid response format")

            return suggestions
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse model response: {e}")