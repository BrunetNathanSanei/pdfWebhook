from io import BytesIO
import requests
import json
import logging
import mimetypes
from os.path import getsize
from zipfile import ZipFile
from .config import ZIP_DIR,WEBHOOK_URL,MISTRAL_LLM_MODEL,MISTRAL_OCR_MODEL,SUPPORTED_EXTENSION,MAX_FILE_SIZE,MAX_CHAR,ABSOLUTE_MAX_CHAR,RESUME_FILE_WITH_MISTRAL
from .utils import create_dir, list_files_walk,clean,extract_pdf,upload_pdf,post_processing_mistral,remove_dir,is_pdf

def process(convId,userId,zip_url,client):
    zip_dir = ZIP_DIR+convId+'/'
    # Create the dir if does not exist
    list_files = list_files_walk(zip_dir)
    text_list = []
    for file in list_files:
            text = get_text(file,client)
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

def extract_zip(convId,userId,zip_url):
    try :
        files = requests.get(zip_url)
        print(BytesIO(files.content))
        zip_dir = ZIP_DIR+convId+'/'
        # Create the dir if does not exist
        create_dir(zip_dir)
        # Get the zip and extract it in the folder
        zip = ZipFile(BytesIO(files.content))
        zip.extractall(zip_dir)
        return {"sucess" : True}
    except Exception as e :
        raise ValueError(e)

def get_text(file_path,client):
    file_name = file_path.split('/')[-1]
    if getsize(file_path) > MAX_FILE_SIZE :
        print(f"{file_name} trop lourd")
        return ""
    elif is_pdf(file_path) and mimetypes.guess_type(file_path)[0] in SUPPORTED_EXTENSION:
        text = extract_pdf(file_path,pdf_dir="",stream=None)
        if text.strip() == "" :
            print(f"{file_name} envoyé à ocr mistral")    
            try :
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
            except :
                text = ""
            return text
        elif len(text) > ABSOLUTE_MAX_CHAR :
            logging.info(f"{file_name} fichier trop long et ignoré - longueur: {len(text)}")
            return ""
        elif len(text) > MAX_CHAR and RESUME_FILE_WITH_MISTRAL :
            logging.info(f"{file_name} fichier trop long et résumé - longueur : {len(text)}")
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
            logging.info(f"{file_name} résumé - longueur : {len(text)}")
            return text
        else :
            logging.info(f"{file_name} Fichier non résumé : {len(text)}")
            return text
    else :
        logging.info(f"{file_name} isn't a pdf")
        return ""