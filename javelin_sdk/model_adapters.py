from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from pydantic import BaseModel
import jmespath
import logging
import uuid
import time

logger = logging.getLogger(__name__)

class ArrayHandling(str, Enum):
    JOIN = "join"
    FIRST = "first"
    LAST = "last"
    FLATTEN = "flatten"

class TypeHint(str, Enum):
    FLOAT = "float"
    INTEGER = "int"
    BOOLEAN = "bool"
    STRING = "str"

class TransformRule(BaseModel):
    source_path: str
    target_path: str
    default_value: Any = None
    transform_function: Optional[str] = None
    conditions: Optional[List[str]] = None
    array_handling: Optional[ArrayHandling] = None
    type_hint: Optional[TypeHint] = None

class ModelSpec(BaseModel):
    input_rules: List[TransformRule]
    output_rules: List[TransformRule]

class UnifiedModelAdapter:
    """Unified adapter for handling multiple model types and providers"""
    
    def __init__(self, model_spec: Optional[ModelSpec] = None):
        self.model_spec = model_spec
        self._register_transform_functions()

    def _register_transform_functions(self):
        """Register available transformation functions"""
        self.transform_functions = {
            "format_messages": self._format_messages,
            "format_claude_completion": self._format_claude_completion,
            "format_mistral_completion": self._format_mistral_completion
        }

    def transform(self, data: Dict[str, Any], rules: List[TransformRule]) -> Dict[str, Any]:
        """Transform data using provided rules"""
        result = {}
        
        for rule in rules:
            try:
                # Skip if conditions not met
                if rule.conditions and not self._check_conditions(rule.conditions, data):
                    continue

                # Get value using source path
                value = self._get_value(rule.source_path, data)
                if value is None:
                    value = rule.default_value
                    if value is None:
                        continue

                # Apply transformation if specified
                if value is not None and rule.transform_function:
                    transform_func = self.transform_functions.get(rule.transform_function)
                    if transform_func:
                        value = transform_func(value)

                # Handle array operations
                if rule.array_handling and isinstance(value, (list, tuple)):
                    value = self._handle_array(value, rule.array_handling)

                # Apply type conversion
                if rule.type_hint and value is not None:
                    value = self._convert_type(value, rule.type_hint)

                # Set nested value
                if value is not None:
                    self._set_nested_value(result, rule.target_path, value)

            except Exception as e:
                logger.error(f"Error processing rule {rule.source_path} -> {rule.target_path}: {str(e)}")
                continue

        return result

    def prepare_request(self, provider: str, model: str, **request_data: Any) -> Dict[str, Any]:
        """Prepare request data for the specified provider and model"""
        if not self.model_spec:
            return request_data

        # Transform input data
        transformed = self.transform(request_data, self.model_spec.input_rules)
        
        # Add provider-specific metadata
        if provider.lower() == "openai":
            transformed["model"] = model
            
        return transformed

    def parse_response(self, provider: str, model: str, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse response data from the specified provider and model"""
        if not self.model_spec:
            return response

        # Transform output data
        transformed = self.transform(response, self.model_spec.output_rules)
        
        # Add standard response fields
        result = {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            **transformed
        }
        
        # Ensure choices array exists and is properly formatted
        if "choices" not in result:
            result["choices"] = []
            
        for i, choice in enumerate(result.get("choices", [])):
            if isinstance(choice, dict):
                choice.setdefault("index", i)
                choice.setdefault("finish_reason", "stop")
                if "message" not in choice:
                    choice["message"] = {
                        "role": "assistant",
                        "content": choice.get("content", "")
                    }
        
        # Ensure usage exists and calculate total tokens
        if "usage" not in result:
            result["usage"] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        
        result["usage"]["total_tokens"] = (
            result["usage"].get("prompt_tokens", 0) +
            result["usage"].get("completion_tokens", 0)
        )
        
        return result

    def _check_conditions(self, conditions: List[str], data: Dict[str, Any]) -> bool:
        """Check if all conditions are met"""
        for condition in conditions:
            try:
                if "type ==" in condition:
                    type_value = data.get("type", "")
                    if "completion" in condition and type_value in ["completion", "completions"]:
                        return True
                    expected_type = condition.split("type ==")[1].strip().strip("'").strip('"')
                    if type_value != expected_type:
                        return False
            except Exception as e:
                logger.error(f"Error checking condition {condition}: {str(e)}")
                return False
        return True

    def _get_value(self, path: str, data: Dict[str, Any]) -> Any:
        """Get value from data using path"""
        try:
            # Direct access for special paths
            if path in ["messages", "prompt"] and path in data:
                return data[path]
            
            # Handle direct dictionary access
            if path in data:
                return data[path]
            
            # Use jmespath for complex paths
            return jmespath.search(path, data)
        except Exception as e:
            logger.error(f"Error getting value for path {path}: {str(e)}")
            return None

    def _handle_array(self, value: Any, array_handling: ArrayHandling) -> Any:
        """Handle array operations"""
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
        return value

    def _convert_type(self, value: Any, type_hint: TypeHint) -> Any:
        """Convert value to specified type"""
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
        return value

    def _set_nested_value(self, obj: Dict[str, Any], path: str, value: Any) -> None:
        """Set nested value with array support"""
        parts = path.split('.')
        current = obj
        
        for i, part in enumerate(parts[:-1]):
            if '[' in part:
                base_part = part.split('[')[0]
                index = int(part.split('[')[1].split(']')[0])
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
        if '[' in last_part:
            base_part = last_part.split('[')[0]
            index = int(last_part.split('[')[1].split(']')[0])
            if base_part not in current:
                current[base_part] = []
            while len(current[base_part]) <= index:
                current[base_part].append(None)
            current[base_part][index] = value
        else:
            current[last_part] = value

    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format messages into a single string"""
        if not messages:
            return ""
        formatted_messages = []
        for msg in messages:
            role = msg.get('role', '')
            content = msg.get('content', '')
            if role == 'system':
                formatted_messages.append(f"System: {content}")
            elif role == 'user':
                formatted_messages.append(f"Human: {content}")
            elif role == 'assistant':
                formatted_messages.append(f"Assistant: {content}")
        return "\n".join(formatted_messages)

    def _format_claude_completion(self, prompt: str) -> List[Dict[str, str]]:
        """Format completion prompt for Claude"""
        return [{"role": "user", "content": prompt}]

    def _format_mistral_completion(self, prompt: str) -> List[Dict[str, str]]:
        """Format completion prompt for Mistral"""
        return [{"role": "user", "content": prompt}]

class ModelAdapterFactory:
    """Factory for creating model adapters"""
    
    @classmethod
    def get_adapter(cls, provider: str, model: str, model_spec: Optional[ModelSpec] = None) -> UnifiedModelAdapter:
        """Get appropriate adapter instance for the provider and model"""
        return UnifiedModelAdapter(model_spec)