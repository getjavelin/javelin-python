import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
import re

SWAGGER_FILE_PATH = Path(".github/scripts/swagger.yaml")

MODELS_FILE_PATH = Path("javelin_sdk/models.py")

FIELDS_TO_EXCLUDE = {
    'Gateway': ['created_at', 'modified_at', 'created_by', 'modified_by'],
    'Provider': ['created_at', 'modified_at', 'created_by', 'modified_by'],
    'Route': ['created_at', 'modified_at', 'created_by', 'modified_by'],
    'Template': ['created_at', 'modified_at', 'created_by', 'modified_by'],
    'APIKey': ['created_at', 'modified_at', 'created_by', 'modified_by', 'organization'],
}

def read_swagger():
    with SWAGGER_FILE_PATH.open() as f:
        return yaml.safe_load(f)

def parse_swagger(swagger_data):
    models = {}
    for model_name, model_spec in swagger_data['definitions'].items():
        properties = model_spec.get('properties', {})
        model_name = model_name.split('.')[-1]
        models[model_name] = {
            prop: details for prop, details in properties.items()
            if prop not in FIELDS_TO_EXCLUDE.get(model_name, [])
        }
    return models

def get_python_type(openapi_type: str, items: Optional[Dict[str, Any]] = None) -> str:
    type_mapping = {
        'string': 'str',
        'integer': 'int',
        'number': 'float',
        'boolean': 'bool',
        'array': 'List',
        'object': 'Dict[str, Any]',
    }
    if openapi_type == 'array' and items:
        item_type = get_python_type(items.get('type', 'Any'))
        return f'List[{item_type}]'
    return type_mapping.get(openapi_type, 'Any')

def generate_model_code(model_name: str, properties: Dict[str, Any]) -> str:
    model_code = f"class {model_name}(BaseModel):\n"
    for prop, details in properties.items():
        field_type = get_python_type(details.get('type'), details.get('items'))
        description = details.get('description', '')
        default = 'None' if details.get('required') != True else '...'
        model_code += f"    {prop}: {field_type} = Field({default}, description=\"{description}\")\n"
    return model_code

def update_models_file(new_models: Dict[str, Dict[str, Any]]):
    current_content = MODELS_FILE_PATH.read_text()
    updated_content = current_content

    for model_name, properties in new_models.items():
        if f"class {model_name}(BaseModel):" in current_content:
            # Update existing model
            start_index = current_content.index(f"class {model_name}(BaseModel):")
            end_index = current_content.find("\n\nclass", start_index)
            if end_index == -1:  # If it's the last model in the file
                end_index = len(current_content)
            existing_model = current_content[start_index:end_index]
            
            # Only add new fields, don't update existing ones
            existing_fields = set(re.findall(r'(\w+):', existing_model))
            new_fields = set(properties.keys()) - existing_fields
            
            if new_fields:
                new_field_code = "\n".join(
                    f"    {prop}: {get_python_type(details.get('type'), details.get('items'))} = "
                    f"Field({'None' if details.get('required') != True else '...'}, description=\"{details.get('description', '')}\")"
                    for prop, details in properties.items() if prop in new_fields
                )
                
                if "pass" in existing_model:
                    updated_model = existing_model.replace("pass", new_field_code.strip())
                else:
                    updated_model = existing_model + "\n" + new_field_code
                
                updated_content = updated_content.replace(existing_model, updated_model)
        else:
            print(f"Skipping new model: {model_name}")

    if updated_content != current_content:
        MODELS_FILE_PATH.write_text(updated_content)
        print("Models file updated")
    else:
        print("No changes needed")

def main():
    swagger_data = read_swagger()
    new_models = parse_swagger(swagger_data)
    update_models_file(new_models)

if __name__ == "__main__":
    main()
