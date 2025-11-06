import requests
import pdfplumber
from io import BytesIO
from PyPDF2 import PdfReader
import re
from os import listdir
from os.path import isfile, join

def test_botpress_file():

    url = 'https://files.bpcontent.cloud/2025/09/17/13/20250917132156-XVRVCEDQ.pdf'

    r = requests.get(url)

    with open('pdf-test.pdf','wb') as f:
        f.write(r.content)

    with pdfplumber.open(BytesIO(r.content)) as pdf:
        print(pdf.pages[0].extract_text())
    return None

def extract_pdf_fields(path):
    reader = PdfReader(path)
    print(reader)
    # fields = reader.get_fields()
    # return {k: v.get('/V') for k, v in fields.items()}

def test_pdf():
    with pdfplumber.open("Demande_de_financement - 2025-04-15T113120.447 (1).pdf") as pdf:
        text = pdf.pages[0].extract_text()
        if text:
            print("✅ Le PDF contient du texte visible.")
            print(text)
        else:
            print("⚠️ Aucune donnée texte (probablement un scan ou un PDF image).")
    return None

def test_webhook():
    url = "https://pdfwebhook.onrender.com/test"
    url_local = "http://192.168.1.107:5000/test"
    data = {
        "file_url" : "https://www.yvelines.fr/wp-content/uploads/2009/11/modele-bulletin-de-salaire.pdf"
    }
    r = requests.post(url=url,data=data)
    print(r.status_code)
    print(r.text)
    return None


def test_send_pdf(file_name):
    url = "http://127.0.0.1:5000/send_pdf"
    files = {'file' : open(file_name, 'rb')}

    r = requests.post(url=url,files=files)
    return r.text

if __name__ == "__main__":
    pdf_dir = "demande_financement/pdf/"
    result_dir = "demande_financement/results/"
    files = [f for f in listdir(pdf_dir) if isfile(join(pdf_dir,f))]
    for file in files :
        text = test_send_pdf(file_name=join(pdf_dir,file))
        with open(join(result_dir,file).replace(".pdf",".txt"),"w") as f:
            f.write(text)
    

    #test_webhook()