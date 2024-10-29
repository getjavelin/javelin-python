import re
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
        """Transform data using provided rules. Handles nested structures and arrays."""
        result = {}
        
        for rule in rules:
            try:
                # Skip if conditions not met
                if rule.conditions and not all(
                    self._evaluate_condition(cond, data) 
                    for cond in rule.conditions
                ):
                    continue

                # Extract value using jmespath
                value = self._extract_value(rule.source_path, data)
                
                # Use default if no value found
                if value is None:
                    value = rule.default_value
                    if value is None:
                        continue

                # Apply any transform function
                if value is not None and rule.transform_function:
                    value = self._apply_transform(value, rule.transform_function)

                # Handle arrays
                if value is not None and rule.array_handling:
                    value = self._handle_array_value(value, rule.array_handling)

                # Apply type conversion
                if value is not None and rule.type_hint:
                    value = self._convert_type(value, rule.type_hint)

                # Set the transformed value
                if value is not None:
                    self._set_nested_value(result, rule.target_path, value)

            except Exception as e:
                logger.error(f"Error processing rule {rule}: {str(e)}")
                continue

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

class BaseAdapter:
    def __init__(self, model_spec: Optional[ModelSpec] = None):
        self.model_spec = model_spec
        logger.debug(f"Initializing ModelAdapter with spec: {model_spec}")

    def prepare_request(self, provider: str, model: str, **kwargs) -> Dict[str, Any]:
        """Prepare request based on provider and model"""
        print(f"Preparing request for {provider}/{model}")
        print(f"Input kwargs: {kwargs}")
        
        if not self.model_spec:
            return kwargs

        result = self.transform(kwargs, self.model_spec.input_rules)
        print(f"Transformed request: {result}")
        return result

    def parse_response(self, provider: str, model: str, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse response based on provider and model"""
        print(f"Parsing response for {provider}/{model}")
        
        if not self.model_spec:
            return response

        transformed = self.transform(response, self.model_spec.output_rules)
        
        result = {
            "id": f"chatcmpl-{str(uuid.uuid4())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [],
            "usage": transformed.get("usage", {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            })
        }

        # Handle choices from transformed data
        if "choices" in transformed:
            result["choices"] = transformed["choices"]
            
        # Calculate total tokens
        if "usage" in result:
            result["usage"]["total_tokens"] = (
                result["usage"].get("prompt_tokens", 0) +
                result["usage"].get("completion_tokens", 0)
            )

        return result

    def transform(self, data: Dict[str, Any], rules: List[TransformRule]) -> Dict[str, Any]:
        """Transform data using provided rules"""
        result = {}
        
        for rule in rules:
            try:
                # Check conditions
                if rule.conditions and not self._check_conditions(rule.conditions, data):
                    continue

                # Get value using source path
                value = self._get_value(rule.source_path, data)
                if value is None:
                    value = rule.default_value
                    if value is None:
                        continue

                # Handle array operations if specified
                if rule.array_handling and isinstance(value, (list, tuple)):
                    if rule.array_handling == ArrayHandling.JOIN:
                        value = " ".join(str(v) for v in value if v is not None)
                    elif rule.array_handling == ArrayHandling.FIRST:
                        value = value[0] if value else None
                    elif rule.array_handling == ArrayHandling.LAST:
                        value = value[-1] if value else None

                # Apply type conversion
                if rule.type_hint and value is not None:
                    value = self._convert_type(value, rule.type_hint)

                # Set the value in result
                if value is not None:
                    self._set_value(result, rule.target_path, value)

            except Exception as e:
                logger.error(f"Error processing rule {rule}: {str(e)}")
                continue

        return result

    def _check_conditions(self, conditions: List[str], data: Dict[str, Any]) -> bool:
        """Check if all conditions are met"""
        for condition in conditions:
            try:
                if "type ==" in condition:
                    type_value = data.get("type", "")
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
            # Direct access for simple paths
            if path in data:
                return data[path]
            
            # Use jmespath for complex paths
            return jmespath.search(path, data)
        except Exception as e:
            logger.error(f"Error getting value for path {path}: {str(e)}")
            return None

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

    def _set_value(self, obj: Dict[str, Any], path: str, value: Any) -> None:
        """Set value in object using dot notation path"""
        parts = path.split('.')
        current = obj
        
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
            
        current[parts[-1]] = value
class ModelAdapterFactory:
    @classmethod
    def get_adapter(cls, provider: str, model: str, model_spec: Optional[ModelSpec] = None) -> ModelAdapter:
        return BaseAdapter(model_spec)
