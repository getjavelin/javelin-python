import logging
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

import jmespath
from pydantic import BaseModel

from .models import ArrayHandling, ModelSpec, TransformRule, TypeHint

logger = logging.getLogger(__name__)


class UnifiedModelAdapter:
    def __init__(self, model_spec: Optional[ModelSpec] = None):
        self.model_spec = model_spec
        self._register_transform_functions()

    def _register_transform_functions(self):
        self.transform_functions = {
            "format_messages": self._format_messages,
            "format_claude_completion": self._format_claude_completion,
            "format_mistral_completion": self._format_mistral_completion,
        }

    def transform(
        self, data: Dict[str, Any], rules: List[TransformRule]
    ) -> Dict[str, Any]:
        result = {}

        for rule in rules:
            try:
                if rule.conditions and not self._check_conditions(
                    rule.conditions, data
                ):
                    continue

                value = self._get_value(rule.source_path, data)
                if value is None:
                    value = rule.default_value
                    if value is None:
                        continue

                if value is not None and rule.transform_function:
                    transform_func = self.transform_functions.get(
                        rule.transform_function
                    )
                    if transform_func:
                        value = transform_func(value)

                if rule.array_handling and isinstance(value, (list, tuple)):
                    value = self._handle_array(value, rule.array_handling)

                if rule.type_hint and value is not None:
                    value = self._convert_type(value, rule.type_hint)

                if value is not None:
                    self._set_nested_value(result, rule.target_path, value)

            except Exception as e:
                logger.error(
                    f"Error processing rule {rule.source_path} -> {rule.target_path}: {str(e)}"
                )
                continue

        return result

    def prepare_request(
        self, provider: str, model: str, **request_data: Any
    ) -> Dict[str, Any]:
        if not self.model_spec:
            return request_data

        transformed = self.transform(request_data, self.model_spec.input_rules)

        if provider.lower() == "openai":
            transformed["model"] = model

        return transformed

    def parse_response(
        self, provider: str, model: str, response: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not self.model_spec:
            return response

        transformed = self.transform(response, self.model_spec.output_rules)

        result = {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            **transformed,
        }

        if "choices" not in result:
            result["choices"] = []

        for i, choice in enumerate(result.get("choices", [])):
            if isinstance(choice, dict):
                choice.setdefault("index", i)
                choice.setdefault("finish_reason", "stop")
                if "message" not in choice:
                    choice["message"] = {
                        "role": "assistant",
                        "content": choice.get("content", ""),
                    }

        if "usage" not in result:
            result["usage"] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }

        result["usage"]["total_tokens"] = result["usage"].get(
            "prompt_tokens", 0
        ) + result["usage"].get("completion_tokens", 0)

        return result

    def _check_conditions(self, conditions: List[str], data: Dict[str, Any]) -> bool:
        for condition in conditions:
            try:
                if "type ==" in condition:
                    type_value = data.get("type", "")
                    if "completion" in condition and type_value in [
                        "completion",
                        "completions",
                    ]:
                        return True
                    expected_type = (
                        condition.split("type ==")[1].strip().strip("'").strip('"')
                    )
                    if type_value != expected_type:
                        return False
            except Exception as e:
                logger.error(f"Error checking condition {condition}: {str(e)}")
                return False
        return True

    def _get_value(self, path: str, data: Dict[str, Any]) -> Any:
        try:
            if path in ["messages", "prompt"] and path in data:
                return data[path]

            if path in data:
                return data[path]

            return jmespath.search(path, data)
        except Exception as e:
            logger.error(f"Error getting value for path {path}: {str(e)}")
            return None

    def _handle_array(self, value: Any, array_handling: ArrayHandling) -> Any:
        try:
            if array_handling == ArrayHandling.JOIN:
                return " ".join(str(v) for v in value if v is not None)
            elif array_handling == ArrayHandling.FIRST:
                return value[0] if value else None
            elif array_handling == ArrayHandling.LAST:
                return value[-1] if value else None
            elif array_handling == ArrayHandling.FLATTEN:
                return [item for sublist in value for item in sublist]
        except Exception as e:
            logger.error(f"Error handling array operation {array_handling}: {str(e)}")
            return value

    def _convert_type(self, value: Any, type_hint: TypeHint) -> Any:
        try:
            if type_hint == TypeHint.FLOAT:
                return float(value)
            elif type_hint == TypeHint.INTEGER:
                return int(value)
            elif type_hint == TypeHint.BOOLEAN:
                return bool(value)
            elif type_hint == TypeHint.STRING:
                return str(value)
        except (ValueError, TypeError):
            logger.warning(f"Failed to convert {value} to {type_hint}")
            return value

    def _set_nested_value(self, obj: Dict[str, Any], path: str, value: Any) -> None:
        parts = path.split(".")
        current = obj

        for i, part in enumerate(parts[:-1]):
            if "[" in part:
                base_part = part.split("[")[0]
                index = int(part.split("[")[1].split("]")[0])
                if base_part not in current:
                    current[base_part] = []
                while len(current[base_part]) <= index:
                    current[base_part].append({})
                current = current[base_part][index]
            else:
                if part not in current:
                    current[part] = {}
                current = current[part]

        last_part = parts[-1]
        if "[" in last_part:
            base_part = last_part.split("[")[0]
            index = int(last_part.split("[")[1].split("]")[0])
            if base_part not in current:
                current[base_part] = []
            while len(current[base_part]) <= index:
                current[base_part].append(None)
            current[base_part][index] = value
        else:
            current[last_part] = value

    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        if not messages:
            return ""
        formatted_messages = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "system":
                formatted_messages.append(f"System: {content}")
            elif role == "user":
                formatted_messages.append(f"Human: {content}")
            elif role == "assistant":
                formatted_messages.append(f"Assistant: {content}")
        return "\n".join(formatted_messages)

    def _format_claude_completion(self, prompt: str) -> List[Dict[str, str]]:
        return [{"role": "user", "content": prompt}]

    def _format_mistral_completion(self, prompt: str) -> List[Dict[str, str]]:
        return [{"role": "user", "content": prompt}]


class ModelAdapterFactory:
    @classmethod
    def get_adapter(
        cls, provider: str, model: str, model_spec: Optional[ModelSpec] = None
    ) -> UnifiedModelAdapter:
        return UnifiedModelAdapter(model_spec)
