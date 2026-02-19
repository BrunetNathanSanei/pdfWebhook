import os

PDF_DIR="zip/"
ZIP_DIR ="zip/extract/"

# BOTPRESS

WEBHOOK_URL = 'https://webhook.botpress.cloud/71137732-2ecf-48c1-b7e6-4484236e0433'

# MISTRAL

API_KEY = os.environ.get("MISTRAL_API_KEY")
MISTRAL_LLM_MODEL = "mistral-large-latest"
MISTRAL_OCR_MODEL = "mistral-ocr-latest"