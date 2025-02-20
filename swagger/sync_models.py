import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import re
import os
import requests

SWAGGER_FILE_PATH = Path(os.path.join(os.path.dirname(__file__), "swagger.yaml"))
MODELS_FILE_PATH = Path(
    os.path.join(os.path.dirname(__file__), "..", "javelin_sdk", "models.py")
)

FIELDS_TO_EXCLUDE = {
    "Gateway": [
        "created_at",
        "modified_at",
        "created_by",
        "modified_by",
        "response_chain",
        "request_chain",
    ],
    "Provider": ["created_at", "modified_at", "created_by", "modified_by"],
    "Route": ["created_at", "modified_at", "created_by", "modified_by"],
    "Template": ["created_at", "modified_at", "created_by", "modified_by"],
}

MODELS_TO_EXCLUDE = [
    "Gateways",
    "Budget",
    "ContentTypes",
    "Dlp",
    "PromptSafety",
    "ContentFilter",
    "Model",
    "Routes",
    "Secrets",
    "Message",
    "Usage",
    "Choice",
    "QueryResponse",
    "JavelinConfig",
    "HttpMethod",
    "Request",
    "ChatCompletion",
    "ResponseMessage",
    "APIKey",
]

MODEL_CLASS_MAPPING = {}


def read_swagger():
    with SWAGGER_FILE_PATH.open() as f:
        return yaml.safe_load(f)


def parse_swagger(swagger_data):
    models = {}
    for full_model_name, model_spec in swagger_data["components"]["schemas"].items():
        model_name = full_model_name.split(".")[-1]
        properties = model_spec.get("properties", {})
        models[model_name] = {
            prop: details
            for prop, details in properties.items()
            if prop not in FIELDS_TO_EXCLUDE.get(model_name, [])
        }
    return models


def get_python_type(openapi_type: str, items: Optional[Dict[str, Any]] = None) -> str:
    type_mapping = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "array": "List",
        "object": "Dict[str, Any]",
    }
    if openapi_type == "array" and items:
        item_type = get_python_type(items.get("type", "Any"))
        return f"List[{item_type}]"
    return type_mapping.get(openapi_type, "Any")


def generate_model_code(model_name: str, properties: Dict[str, Any]) -> str:
    model_code = f"class {model_name}(BaseModel):\n"
    for prop, details in properties.items():
        field_type = get_python_type(details.get("type"), details.get("items"))
        description = details.get("description", "").replace('"', '\\"')
        default = "None" if details.get("required") != True else "..."
        if default == "None":
            field_type = f"Optional[{field_type}]"
        model_code += f'    {prop}: {field_type} = Field(default={default}, description="{description}")\n'
    return model_code


def update_models_file(new_models: Dict[str, Dict[str, Any]]):
    current_content = MODELS_FILE_PATH.read_text()
    updated_content = current_content

    for model_name, properties in new_models.items():
        if model_name in MODELS_TO_EXCLUDE:
            print(f"Skipping excluded model: {model_name}")
            continue

        class_name = MODEL_CLASS_MAPPING.get(model_name, model_name)
        if f"class {class_name}(BaseModel):" in current_content:
            # Update existing model
            start_index = current_content.index(f"class {class_name}(BaseModel):")
            end_index = current_content.find("\n\nclass", start_index)
            if end_index == -1:  # If it's the last model in the file
                end_index = len(current_content)
            existing_model = current_content[start_index:end_index]

            # Only add new fields, don't update existing ones
            existing_fields = set(re.findall(r"(\w+):", existing_model))
            new_fields = set(properties.keys()) - existing_fields

            if new_fields:
                new_field_code = "\n".join(
                    f"    {prop}: {'Optional[' if properties[prop].get('required') != True else ''}"
                    f"{get_python_type(properties[prop].get('type'), properties[prop].get('items'))}"
                    f"{']' if properties[prop].get('required') != True else ''} = "
                    f"Field(default={'None' if properties[prop].get('required') != True else '...'}, "
                    f"description={repr(properties[prop].get('description', ''))})"
                    for prop in new_fields
                )

                updated_model = existing_model + "\n" + new_field_code
                updated_content = updated_content.replace(existing_model, updated_model)
                print(f"Updated existing model: {class_name}")
        else:
            # This is a new model, add it
            new_model_code = generate_model_code(class_name, properties)
            updated_content += f"\n\n{new_model_code}"
            print(f"Added new model: {class_name}")

    if updated_content != current_content:
        MODELS_FILE_PATH.write_text(updated_content)
        print("Models file updated")
    else:
        print("No changes needed")


def modify_and_convert_swagger(input_file, output_file):
    with open(input_file, "r") as file:
        swagger_data = yaml.safe_load(file)

    # Add info section with title and version
    swagger_data["info"] = {
        "title": "Javelin Admin API",
        "version": "1.0",
        "contact": {},
        "description": "This is the Javelin Admin API",
    }

    # Remove 'providername' from '/v1/admin/providers/secrets/keys' path
    if "/v1/admin/providers/secrets/keys" in swagger_data["paths"]:
        path = swagger_data["paths"]["/v1/admin/providers/secrets/keys"]
        for method in path.values():
            if "parameters" in method:
                method["parameters"] = [
                    param
                    for param in method["parameters"]
                    if param.get("name") != "providername"
                ]

    # Remove 'templatename' from '/v1/admin/dataprotection/templates' path
    if "/v1/admin/dataprotection/templates" in swagger_data["paths"]:
        path = swagger_data["paths"]["/v1/admin/dataprotection/templates"]
        for method in path.values():
            if "parameters" in method:
                method["parameters"] = [
                    param
                    for param in method["parameters"]
                    if param.get("name") != "templatename"
                ]

    # Add host and basePath
    swagger_data["host"] = "api-dev.javelin.live"
    swagger_data["basePath"] = "/v1/admin"

    url = "https://converter.swagger.io/api/convert"
    headers = {"Accept": "application/yaml"}
    response = requests.post(url, json=swagger_data, headers=headers)

    if response.status_code == 200:
        openapi3_data = yaml.safe_load(response.text)

        with open(output_file, "w") as file:
            yaml.dump(openapi3_data, file, default_flow_style=False)
        print(f"OpenAPI 3.0 specification has been created and saved to {output_file}")
    else:
        print(
            f"Error converting to OpenAPI 3.0: {response.status_code} - {response.text}"
        )


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(current_dir, "swagger.yaml")
    output_file = os.path.join(current_dir, "swagger.yaml")
    modify_and_convert_swagger(input_file, output_file)
    swagger_data = read_swagger()
    new_models = parse_swagger(swagger_data)
    update_models_file(new_models)


if __name__ == "__main__":
    main()
