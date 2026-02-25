from flask import Blueprint,request,jsonify,current_app
import requests
from io import BytesIO
import json
import threading
from mistralai import Mistral
from zipfile import ZipFile
from .utils import split_text, clean,preprocessing,create_dir, extract_pdf,get_borrowers,create_delimiters_list,text_without_com,get_informations,get_loan, is_pdf
from .core import process,get_text
from .config import ZIP_DIR,API_KEY

courtia = Blueprint('courtia',__name__)
client = Mistral(api_key = API_KEY)


@courtia.route("/test",methods = ['GET','POST'])
def test():
    current_app.logger.info("Requête reçue sur /test")
    if request.method == 'GET':
        return jsonify({"status" : "get ok"}),200
    elif request.method == 'POST':
        try :
            convId = request.form["convId"]
            userId = request.form["userId"]
            webhook_url = 'https://webhook.botpress.cloud/62f1753b-b8cd-4403-a3b9-908fd6915d8f'
            data = {
                "example": "example",
                "convId" : convId,
                "userId" : userId
            }
            headers = {
                'Content-Type': 'application/json',
            }
            response = requests.post(webhook_url, data=json.dumps(data), headers=headers)
            return jsonify({"status" : "response send on webhook"}),200
        except : 
            current_app.logger.info("No url found")
            return jsonify({'No url found'}),400
    else :
        print("pas de méthode, ok")
        return jsonify({"status" : "no methods ok"}),200

@courtia.route("/carcasse",methods = ['POST'])
def carcasse():
    current_app.logger.info("Requête reçu sur /carcasse")
    if len(request.form) > 0:
        file_url = request.form["file_url"]
        file = requests.get(file_url)
        try :
            text,first_page = extract_pdf(file_name=None, stream=BytesIO(file.content),first_page=True)
        except :
            return {"error": "invalid_pdf"}, 400
    elif "file" in request.files :
        file = request.files["file"]
        text,first_page = extract_pdf(file_name=None,stream=file.stream,first_page=True)
        
    else :
        current_app.logger.info("Aucun fichier reçu")
        return "Aucun fichier reçu", 400
    
    try :
        text = preprocessing(text)
        borrowers = get_borrowers(first_page)
        delimiters = create_delimiters_list(borrowers)
        
        text_parts = split_text(text=text,delimiters=delimiters)
        text = text_without_com(text_parts=text_parts)
        informations = get_informations(borrowers,text_parts)
        total,taux,duree,contexte = get_loan(text_parts)
        data = {"text" : text,"borrowers" : informations , "loan" : {"total" : total,"taux" : taux, "duration" :duree, "contexte" : contexte} }
        # app.logger.info(data)
    except :
        current_app.logger.info(text)
        data = {"text" : text }
    return data



@courtia.route("/archive", methods = ['POST'])
def archive():
    
    current_app.logger.info("Requête reçu sur /archive")
    file_url = request.form["file_url"]
    convId = request.form["convId"]
    userId = request.form["userId"]
    thread = threading.Thread(target = process, args=(convId,userId,file_url,client),daemon=True)
    thread.start()
    response = jsonify({"status": "accepted"})
    response.status_code = 200
    return response 

@courtia.route("/send_archive", methods = ["POST"])
def send_archive():
    current_app.logger.info("Requête reçu sur /send_archive")
    file_url = request.form["file_url"]
    file = requests.get(file_url)
    current_app.logger.info(BytesIO(file.content))
    zip_dir = ZIP_DIR
    # Create the dir if does not exist
    create_dir(zip_dir)
    # Get the zip and extract it in the folder
    zip = ZipFile(BytesIO(file.content))
    zip.extractall(zip_dir)
    response = jsonify({"status": "accepted"})
    response.status_code = 200
    return response 

@courtia.route("/analyse",methods = ["POST"])
def analyse():
    current_app.logger.info("Requête reçu sur /archive")
    convId = request.form["convId"]
    userId = request.form["userId"]
    thread = threading.Thread(target = process, args=(convId,userId),daemon=True)
    thread.start()
    response = jsonify({"status": "accepted"})
    response.status_code = 200
    return response 

@courtia.route("/remove_file",methods = ['GET'])
def remove_file():
    zip_dir = ZIP_DIR
    clean(zip_dir)
    current_app.logger.info("Nettoyage terminé")
    return jsonify({"status" : "files removed"}),200