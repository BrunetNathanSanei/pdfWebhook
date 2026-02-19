from io import BytesIO
import requests
import json
import logging
from zipfile import ZipFile
from .config import ZIP_DIR,WEBHOOK_URL,MISTRAL_LLM_MODEL,MISTRAL_OCR_MODEL
from .utils import create_dir, list_files_walk,clean,extract_pdf,upload_pdf,post_processing_mistral,remove_dir

def process(convId,userId,file_url,app,client):
    file = requests.get(file_url)
    app.logger.info(BytesIO(file.content))
    zip_dir = ZIP_DIR+convId+'/'
    # Create the dir if does not exist
    create_dir(zip_dir)
    # Get the zip and extract it in the folder
    zip = ZipFile(BytesIO(file.content))
    zip.extractall(zip_dir)
    # Check if the files are pdf, extract the image and save it, extract the text from all the pdf
    list_files = list_files_walk(zip_dir)
    text_list = []
    for file in list_files:

        text = get_text(file,app,client)
        text_list.append(text)
    clean(zip_dir)
    remove_dir(zip_dir)
    logging.info("Nettoyage terminé")
    data = {
        "convId" : convId,
        "userId" : userId,
        "text_list" : text_list
    }
    headers = {
        'Content-Type': 'application/json',
    }
    requests.post(WEBHOOK_URL, data=json.dumps(data), headers=headers)
    logging.info("Webhook contacté")

def get_text(file_path,app,client):
    text = extract_pdf(file_path,pdf_dir="",stream=None)
    file_name = file_path.split('/')[-1]
    if text.strip() == "" :
            app.logger.info(f"{file_name} envoyé à mistral : {text.strip() == ""}")    
            ocr_response = client.ocr.process(
            model = MISTRAL_OCR_MODEL,
            document = {
                "type" : "document_url",
                "document_url" : upload_pdf(filename=file_path,client=client)
            },
            include_image_base64=False
            )
            full_text = ""
            pages  = [page.markdown for page in ocr_response.pages]
            full_text = "\n".join(pages)
            text = post_processing_mistral(full_text)         
    else :
        logging.info(f"{file_name} non envoyé : {text.strip() == ""}")
    logging.info(f"{file_name} : {len(text)}")
    if len(text) > 3500 :
        requete = client.chat.stream(
            model=MISTRAL_LLM_MODEL,
            messages=[
                {
                    "role" : "user",
                    "content" : f"Résumé ce texte : {text}",
                },
            ]
        )
        chunk_list = [chunk.data.choices[0].delta.content for chunk in requete]
        text = "".join(chunk_list)
    return text