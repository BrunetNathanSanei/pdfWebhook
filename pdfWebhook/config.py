import os

PDF_DIR="zip/"
ZIP_DIR ="zip/extract/"
SUPPORTED_EXTENSION = ('application/pdf')
MAX_FILE_SIZE = 5000000 # octets
MAX_CHAR = 7500 # Resumer le pdf au délà de cette taille
ABSOLUTE_MAX_CHAR = 40000 # Ne pas prendre en compte le pdf au délà de cette taille

# BOTPRESS

WEBHOOK_URL = 'https://webhook.botpress.cloud/71137732-2ecf-48c1-b7e6-4484236e0433'

# MISTRAL

API_KEY = os.environ.get("MISTRAL_API_KEY")
MISTRAL_LLM_MODEL = "mistral-large-latest"
MISTRAL_OCR_MODEL = "mistral-ocr-latest"
RESUME_FILE_WITH_MISTRAL = True