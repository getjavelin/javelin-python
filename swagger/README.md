# Swagger Model Sync

This directory contains a script (`sync_models.py`) for synchronizing Python models with a Swagger/OpenAPI specification from javelin admin repo.

## Purpose

The `sync_models.py` script updates existing models in the Python SDK with missing attributes from the `swagger.yaml` file. This ensures that the SDK models stay up-to-date with the API specification.

## Key Features

- Updates existing models with missing attributes
- Preserves manually added models and attributes
- Does not automatically add new models from swagger.yaml

## Usage

1. Ensure you have the latest `swagger.yaml` file in the appropriate directory.
2. Run the script:

   ```
   python sync_models.py
   ```

3. Review the changes made to the `models.py` file.
