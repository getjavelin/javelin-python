import time
import uuid
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
import jmespath
import logging

from .models import ModelSpec, TransformRule, TypeHint, ArrayHandling

logger = logging.getLogger(__name__)

class ModelAdapter(ABC):
    def __init__(self, model_spec: Optional[ModelSpec] = None):
        self.model_spec = model_spec
        logger.debug(f"Initializing ModelAdapter with spec: {model_spec}")

    @abstractmethod
    def prepare_request(self, provider: str, model: str, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    def parse_response(self, provider: str, model: str, response: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def transform(self, data: Dict[str, Any], rules: List[TransformRule]) -> Dict[str, Any]:
        logger.debug(f"Transform called with data: {data}")
        logger.debug(f"Transform rules: {rules}")
        
        # Don't copy original data to avoid duplicates
        result = {}
        
        for rule in rules:
            logger.debug(f"\nProcessing rule: {rule}")
            try:
                # Check conditions first
                if rule.conditions:
                    condition_met = all(
                        self._evaluate_condition(cond, data)
                        for cond in rule.conditions
                    )
                    if not condition_met:
                        logger.debug(f"Conditions not met for rule: {rule.conditions}")
                        continue

                # Get source value
                value = self._get_value(rule.source_path, data)
                
                # Use default if value is None
                if value is None:
                    value = rule.default_value
                    
                # Apply transform function if specified
                if rule.transform_function and hasattr(self, rule.transform_function):
                    transform_method = getattr(self, rule.transform_function)
                    value = transform_method(value)

                # Handle array operations
                if rule.array_handling and isinstance(value, (list, tuple)):
                    if rule.array_handling == ArrayHandling.JOIN:
                        value = " ".join(str(v) for v in value if v is not None)
                    elif rule.array_handling == ArrayHandling.FIRST:
                        value = value[0] if value else None
                    elif rule.array_handling == ArrayHandling.LAST:
                        value = value[-1] if value else None

                # Apply type coercion
                if rule.type_hint and value is not None:
                    value = self._coerce_type(value, rule.type_hint)

                # Set value if not None
                if value is not None:
                    self._set_nested_value(result, rule.target_path, value)

            except Exception as e:
                logger.error(f"Rule processing error: {e}")
                continue

        # Remove None values
        result = {k: v for k, v in result.items() if v is not None}
        logger.debug(f"Final transform result: {result}")
        return result

    def _evaluate_condition(self, condition: str, data: Dict[str, Any]) -> bool:
        """Evaluate a condition string against data"""
        try:
            type_value = data.get("type", "")
            # Handle both completion/completions
            if "completion" in condition and type_value in ["completion", "completions"]:
                return True
            return eval(f"'{type_value}' {condition.split('type ==')[1]}")
        except Exception as e:
            logger.error(f"Condition evaluation error: {e}")
            return False

    def _get_value(self, source_path: str, data: Dict[str, Any]) -> Any:
        """Get value using source path"""
        if source_path == "messages" and "messages" in data:
            return data["messages"]
        elif source_path == "prompt" and "prompt" in data:
            return data["prompt"]
        else:
            try:
                return jmespath.search(source_path, data)
            except Exception as e:
                logger.error(f"Error searching for {source_path}: {e}")
                return None

    def _handle_array(self, value: Any, array_handling: ArrayHandling) -> Any:
        """Handle array operations"""
        if array_handling == ArrayHandling.JOIN:
            return " ".join(str(v) for v in value)
        elif array_handling == ArrayHandling.FIRST:
            return value[0] if value else None
        elif array_handling == ArrayHandling.LAST:
            return value[-1] if value else None

    def _coerce_type(self, value: Any, type_hint: TypeHint) -> Any:
        """Coerce type"""
        if type_hint == TypeHint.FLOAT:
            return float(value)
        elif type_hint == TypeHint.INTEGER:
            return int(value)
        elif type_hint == TypeHint.BOOLEAN:
            return bool(value)
        elif type_hint == TypeHint.STRING:
            return str(value)

    def _set_nested_value(self, result: Dict[str, Any], target_path: str, value: Any) -> None:
        """Set nested value"""
        current = result
        parts = target_path.split('.')
        
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value

class BaseAdapter(ModelAdapter):
    def prepare_request(self, provider: str, model: str, **kwargs) -> Dict[str, Any]:
        """Prepare request based on provider and model"""
        print(f"Preparing request for {provider}/{model}")
        print(f"Input kwargs: {kwargs}")
        
        if not self.model_spec:
            print("No model spec found, returning kwargs as-is")
            return kwargs

        result = self.transform(kwargs, self.model_spec.input_rules)
        
        # Remove None values
        if "inputText" in result and result["inputText"] is None:
            del result["inputText"]
        if "prompt" in result and result["prompt"] is None:
            del result["prompt"]
            
        print(f"Transformed request: {result}")
        return result

    def parse_response(self, provider: str, model: str, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse response based on provider and model"""
        print(f"Parsing response for {provider}/{model}")
        
        if not self.model_spec:
            return response
            
        # Transform output using rules from model spec
        transformed = self.transform(response, self.model_spec.output_rules)
        
        result = {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": transformed.get("choices", []),
            "usage": transformed.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        }

        # Ensure proper message structure
        if "choices" in result and result["choices"]:
            choice = result["choices"][0]
            if "message" not in choice:
                choice["message"] = {
                    "role": "assistant",
                    "content": choice.get("content", "")
                }
            if "finish_reason" not in choice:
                choice["finish_reason"] = "stop"
            if "index" not in choice:
                choice["index"] = 0

        # Calculate total tokens
        if "usage" in result:
            result["usage"]["total_tokens"] = (
                result["usage"].get("prompt_tokens", 0) +
                result["usage"].get("completion_tokens", 0)
            )

        return result

    def format_messages(self, messages: List[Dict[str, str]]) -> str:
        print(f"\nFormatting messages: {messages}")
        if not messages:
            print("No messages to format")
            return ""
        result = " ".join(msg.get('content', '') for msg in messages)
        print(f"Formatted result: {result}")
        return result

class ModelAdapterFactory:
    @classmethod
    def get_adapter(cls, provider: str, model: str, model_spec: Optional[ModelSpec] = None) -> ModelAdapter:
        return BaseAdapter(model_spec)
