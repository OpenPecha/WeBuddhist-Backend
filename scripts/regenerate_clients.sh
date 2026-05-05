#!/bin/bash

# Regenerate OpenAPI Python clients from spec files
# Run this script when external API specs change

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Regenerating OpenPecha API client..."

# Remove existing generated client
rm -rf pecha_api/external_clients/open_pecha_client

# Regenerate from spec
poetry run openapi-python-client generate \
  --path pecha_api/assets/api/open_pech_api.yaml \
  --output-path pecha_api/external_clients/open_pecha_client \
  --config openapi-client-config.yaml

echo "Client regeneration complete!"
echo ""
echo "Generated client location: pecha_api/external_clients/open_pecha_client/"
