import requests
import pdfplumber
from io import BytesIO

url = 'https://files.bpcontent.cloud/2025/09/17/13/20250917132156-XVRVCEDQ.pdf'

r = requests.get(url)

with open('pdf-test.pdf','wb') as f:
    f.write(r.content)

with pdfplumber.open(BytesIO(r.content)) as pdf:
    print(pdf.pages[0].extract_text())