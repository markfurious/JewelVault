"""
Claude API Service Wrapper.
Provides LLM capabilities for agent decision-making and natural language understanding.
"""
import os
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ClaudeMessage:
    """Message structure for Claude API."""
    role: str  # "user" or "assistant"
    content: str


class ClaudeService:
    """
    Wrapper for Claude API calls.

    Supports:
    - Natural language parsing
    - Decision generation
    - Structured output extraction
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.default_model = "claude-sonnet-4-5-20250929"
        self.max_tokens = 4096

        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. "
                "Please set it in your environment or .env file."
            )

    def _make_request(self, messages: List[ClaudeMessage], system_prompt: str = "", **kwargs) -> Dict[str, Any]:
        """
        Make request to Claude API.

        Args:
            messages: List of conversation messages
            system_prompt: System instruction
            **kwargs: Additional parameters (model, temperature, etc.)

        Returns:
            API response dict
        """
        import requests

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": kwargs.get("model", self.default_model),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }

        if system_prompt:
            payload["system"] = system_prompt

        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]

        response = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        return response.json()

    def parse_natural_language(
        self,
        query: str,
        context: Optional[str] = None,
        expected_entities: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Parse natural language query into structured intent.

        Args:
            query: User's natural language query
            context: Optional context about the domain
            expected_entities: List of entities to extract

        Returns:
            Structured dict with intent, entities, and parameters
        """
        system_prompt = """You are an AI agent that parses natural language queries for a jewelry inventory management system.

Extract the following from user queries:
- intent: What action the user wants to perform
- entities: Specific products, categories, or values mentioned
- parameters: Numeric values, dates, or other modifiers
- confidence: How confident you are in the parsing (0.0-1.0)

Available intents:
- update_inventory: Change stock levels or status
- create_product: Add new product to catalog
- process_sale: Record a sale transaction
- update_prices: Modify product prices
- generate_recommendations: Get product recommendations
- analyze_anomalies: Detect unusual patterns
- log_ar_session: Record AR try-on session
- create_reorder: Generate reorder request

Respond ONLY with valid JSON in this format:
{
    "intent": "intent_name",
    "entities": {...},
    "parameters": {...},
    "confidence": 0.95,
    "reasoning": "brief explanation"
}"""

        user_message = f"Query: {query}"
        if context:
            user_message += f"\nContext: {context}"
        if expected_entities:
            user_message += f"\nExtract these entities: {', '.join(expected_entities)}"

        messages = [ClaudeMessage(role="user", content=user_message)]

        try:
            response = self._make_request(messages, system_prompt, temperature=0.1)
            content = response["content"][0]["text"]

            # Extract JSON from response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(content[json_start:json_end])
            else:
                return {"error": "Failed to parse response", "raw": content}

        except Exception as e:
            return {"error": str(e), "query": query}

    def generate_decision(
        self,
        situation: str,
        options: List[str],
        criteria: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a decision based on situation and options.

        Args:
            situation: Description of the current situation
            options: List of possible actions
            criteria: Decision criteria

        Returns:
            Decision with selected option and reasoning
        """
        system_prompt = """You are a decision-making AI for a jewelry inventory system.

Analyze the situation and select the best action from the options.
Consider business impact, risk, and operational efficiency.

Respond ONLY with valid JSON:
{
    "selected_option": "option_name",
    "confidence": 0.95,
    "reasoning": "why this option was selected",
    "risks": ["potential risks to consider"],
    "alternative": "backup option if needed"
}"""

        user_message = f"Situation: {situation}\n"
        user_message += f"Options: {', '.join(options)}\n"
        if criteria:
            user_message += f"Criteria: {criteria}"

        messages = [ClaudeMessage(role="user", content=user_message)]

        try:
            response = self._make_request(messages, system_prompt, temperature=0.2)
            content = response["content"][0]["text"]

            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(content[json_start:json_end])
            else:
                return {"error": "Failed to parse response", "raw": content}

        except Exception as e:
            return {"error": str(e), "selected_option": None}

    def extract_structured_data(
        self,
        text: str,
        schema: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Extract structured data from text according to schema.

        Args:
            text: Input text to parse
            schema: Field definitions (field_name: description)

        Returns:
            Extracted data dict
        """
        system_prompt = """Extract structured data from text according to the schema.
Respond ONLY with valid JSON matching the schema fields."""

        schema_desc = "\n".join(f"- {k}: {v}" for k, v in schema.items())
        user_message = f"Schema:\n{schema_desc}\n\nText to parse:\n{text}"

        messages = [ClaudeMessage(role="user", content=user_message)]

        try:
            response = self._make_request(messages, system_prompt, temperature=0.1)
            content = response["content"][0]["text"]

            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(content[json_start:json_end])
            else:
                return {"error": "Failed to parse response", "raw": content}

        except Exception as e:
            return {"error": str(e)}

    def summarize(self, data: Any, max_length: int = 200) -> str:
        """
        Generate a human-readable summary of data.

        Args:
            data: Data to summarize
            max_length: Maximum summary length

        Returns:
            Summary string
        """
        system_prompt = f"""Summarize the following data concisely in max {max_length} characters.
Focus on key actions taken and outcomes."""

        if isinstance(data, dict):
            data_str = json.dumps(data, indent=2, default=str)
        else:
            data_str = str(data)

        messages = [ClaudeMessage(role="user", content=data_str)]

        try:
            response = self._make_request(messages, system_prompt, temperature=0.3, max_tokens=100)
            return response["content"][0]["text"].strip()
        except Exception as e:
            return f"Summary unavailable: {str(e)}"
