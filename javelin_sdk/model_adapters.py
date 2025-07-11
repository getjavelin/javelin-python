import logging
from typing import Any, Dict, List, Optional

import jmespath

from .models import ArrayHandling, ModelSpec, TransformRule, TypeHint

logger = logging.getLogger(__name__)


class TransformationRuleManager:
    def __init__(self, client):
        """Initialize the transformation rule manager with both
        local and remote capabilities"""
        self.client = client
        self.cache = {}
        self.cache_ttl = 3600
        self.last_fetch = {}

    def get_rules(self, provider_url: str, model_name: str) -> ModelSpec:
        """Get transformation rules for a provider/model combination"""
        model_name = model_name.lower()

        try:
            rules = self._fetch_remote_rules(provider_url, model_name)
            if rules:
                return rules
        except Exception as e:
            logger.error(
                f"Error fetching remote rules for {provider_url}/{model_name}: {str(e)}"
            )

        raise ValueError(
            f"No transformation rules found for {provider_url} and {model_name}"
        )

    def _fetch_remote_rules(
        self, provider_url: str, model_name: str
    ) -> Optional[ModelSpec]:
        """Fetch transformation rules from remote service"""
        try:
            response = self.client.get_model_specs(provider_url, model_name)
            if response:
                input_rules = response["model_spec"].get(
                    "openai_request_transform_rules", []
                )
                output_rules = response["model_spec"].get(
                    "openai_response_transform_rules", []
                )
                stream_response_path = response["model_spec"].get(
                    "stream_response_path", None
                )

                processed_stream_path = (
                    stream_response_path[0] if len(stream_response_path) > 0 else None
                )

                return ModelSpec(
                    input_rules=[TransformRule(**rule) for rule in (input_rules or [])],
                    output_rules=[
                        TransformRule(**rule) for rule in (output_rules or [])
                    ],
                    stream_response_path=processed_stream_path,
                )

            print(f"No remote rules found for {provider_url}/{model_name}")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch remote rules: {str(e)}")
            return None


class ModelTransformer:
    def __init__(self):
        """Initialize the model transformer"""
        pass  # No need to store rules anymore

    def transform(
        self, data: Dict[str, Any], rules: List[TransformRule]
    ) -> Dict[str, Any]:
        """Transform data using provided rules"""
        result = {}

        for rule in rules:
            try:
                processed_value = self._process_rule(rule, data)
                if processed_value is not None:
                    if isinstance(processed_value, dict):
                        result.update(processed_value)
                    else:
                        self._set_nested_value(
                            result, rule.target_path, processed_value
                        )
            except Exception as e:
                logger.error(
                    f"Error processing rule {rule.source_path} -> "
                    f"{rule.target_path}: {str(e)}"
                )
                continue

        return result

    def _process_rule(self, rule: TransformRule, data: Dict[str, Any]) -> Any:
        """Process a single transformation rule"""
        # Handle additional data
        if rule.additional_data:
            return rule.additional_data

        # Skip passthrough rules
        if rule.type_hint == TypeHint.PASSTHROUGH:
            return None

        # Check conditions
        if rule.conditions and not self._check_conditions(rule.conditions, data):
            return None

        # Get value using source path
        value = self._get_value(rule.source_path, data)
        if value is None:
            value = rule.default_value
            if value is None:
                return None

        # Apply transformations
        value = self._apply_transformations(value, rule)

        return value

    def _apply_transformations(self, value: Any, rule: TransformRule) -> Any:
        """Apply all transformations to a value"""
        if value is None:
            return value

        # Apply transformation function
        if rule.transform_function:
            transform_method = getattr(self, rule.transform_function, None)
            if transform_method:
                value = transform_method(value)

        # Handle array operations
        if rule.array_handling and isinstance(value, (list, tuple)):
            if isinstance(value, list):
                value = self._handle_array(value, rule.array_handling)
            else:
                # Convert tuple to list for processing
                value = self._handle_array(list(value), rule.array_handling)

        # Apply type conversion
        if rule.type_hint and value is not None:
            value = self._convert_type(value, rule.type_hint)

        return value

    def _check_conditions(self, conditions: List[str], data: Dict[str, Any]) -> bool:
        """Check if all conditions are met"""
        for condition in conditions:
            try:
                if "type ==" in condition:
                    type_value = data.get("type", "")
                    expected_type = (
                        condition.split("type ==")[1].strip().strip("'").strip('"')
                    )
                    # Handle both completion/completions
                    if "completion" in expected_type and type_value in [
                        "completion",
                        "completions",
                    ]:
                        continue
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

    def _handle_array(self, value: List[Any], handling: ArrayHandling) -> Any:
        """Handle array operations"""
        try:
            if handling == ArrayHandling.JOIN:
                return " ".join(str(v) for v in value if v is not None)
            elif handling == ArrayHandling.FIRST:
                return value[0] if value else None
            elif handling == ArrayHandling.LAST:
                return value[-1] if value else None
        except Exception as e:
            logger.error(f"Error handling array: {str(e)}")
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
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to convert {value} to {type_hint}: {str(e)}")
            return value
        return value

    def _set_nested_value(self, obj: Dict[str, Any], path: str, value: Any) -> None:
        """Set nested value in dictionary"""
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

    def format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format messages into a single string"""
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

    def format_claude_completion(self, prompt: str) -> List[Dict[str, str]]:
        """Format completion prompt for Claude"""
        return [{"role": "user", "content": prompt}]

    def format_mistral_completion(self, prompt: str) -> List[Dict[str, str]]:
        """Format completion prompt for Mistral"""
        return [{"role": "user", "content": prompt}]

    def format_claude_messages(
        self, messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Format messages for Claude by combining system and user messages"""
        formatted_messages = []
        system_messages = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "system":
                system_messages.append(content)
            else:
                if system_messages and role == "user":
                    # Prepend system messages to first user message
                    combined_content = "\n".join(system_messages) + "\n\n" + content
                    formatted_messages.append(
                        {"role": "user", "content": combined_content}
                    )
                    system_messages = []  # Clear after using
                else:
                    formatted_messages.append({"role": role, "content": content})

        # Handle any remaining system messages
        if system_messages and not formatted_messages:
            formatted_messages.append(
                {"role": "user", "content": "\n".join(system_messages)}
            )

        return formatted_messages

    def format_vertex_messages(
        self, messages: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """Format messages for Vertex AI"""
        if not messages:
            return []

        formatted_messages = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "system":
                # Convert system to USER for Vertex AI
                formatted_messages.append({"author": "USER", "content": content})
            elif role == "user":
                formatted_messages.append({"author": "USER", "content": content})
            elif role == "assistant":
                formatted_messages.append({"author": "MODEL", "content": content})

        return formatted_messages
