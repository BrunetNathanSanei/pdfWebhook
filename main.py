import numpy as np

from flask import Flask, request, jsonify
import logging
from io import BytesIO
import requests
import pandas as pd
import json
from zipfile import ZipFile
from os import listdir, remove,walk,mkdir
from os.path import isfile, join, exists
from mistralai import Mistral
import os
import threading

from pdfWebhook import split_text, clean,preprocessing,create_dir, extract_pdf, process,get_borrowers,create_delimiters_list,text_without_com,get_informations,get_loan,ZIP_DIR

app = Flask(__name__)
img_extension = {}

ZIP_DIR ="zip/extract/"
api_key = os.environ.get("MISTRAL_API_KEY")
client = Mistral(api_key = api_key)

logging.basicConfig(level=logging.INFO)

@app.route("/test",methods = ['GET','POST'])
def test():
    app.logger.info("Requête reçue sur /test")
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
            app.logger.info("No url found")
            return jsonify({'No url found'}),400
    else :
        print("pas de méthode, ok")
        return jsonify({"status" : "no methods ok"}),200


@app.route("/carcasse",methods = ['POST'])
def carcasse():
    app.logger.info("Requête reçu sur /carcasse")
    if len(request.form) > 0:
        file_url = request.form["file_url"]
        file = requests.get(file_url)
        text = extract_pdf(file_name=None, stream=BytesIO(file.content))
    elif "file" in request.files :
        file = request.files["file"]
        text = extract_pdf(file_name=None,stream=file.stream)
    else :
        app.logger.info("Aucun fichier reçu")
        return "Aucun fichier reçu", 400   
    
    text = preprocessing(text)
    borrowers = get_borrowers(text)
    delimiters = create_delimiters_list(borrowers)
    
    text_parts = split_text(text=text,delimiters=delimiters)
    if False : 
        with open("data/text_parts.json",'w',encoding='utf-8') as f:
            json.dump(text_parts,f,indent=4,ensure_ascii=False)
    text = text_without_com(text_parts=text_parts)
    informations = get_informations(borrowers,text_parts)
    total,taux,duree,contexte = get_loan(text_parts)
    data = {"text" : text,"borrowers" : informations , "loan" : {"total" : total,"taux" : taux, "duration" :duree, "contexte" : contexte} }
    # app.logger.info(data)
    return data

@app.route("/pdf2text", methods = ['POST'])
def pdf2text():
    if "file" not in request.files :
        return "Aucun fichier PDF reçu", 400
    file = request.files["file"]
    extension = file.filename.split('.')[-1]
    print(f'file extension : {extension}')
    if extension == 'pdf' :
        text = extract_pdf(file.stream)
        return text
        
    else :
        return "Aucun fichier PDF reçu", 400 

@app.route("/archive", methods = ['POST'])
def archive():
    
    app.logger.info("Requête reçu sur /archive")
    file_url = request.form["file_url"]
    convId = request.form["convId"]
    userId = request.form["userId"]
    thread = threading.Thread(target = process, args=(convId,userId,file_url,app,client),daemon=True)
    thread.start()
    response = jsonify({"status": "accepted"})
    response.status_code = 200
    return response 

@app.route("/send_archive", methods = ["POST"])
def send_archive():
    app.logger.info("Requête reçu sur /send_archive")
    file_url = request.form["file_url"]
    file = requests.get(file_url)
    app.logger.info(BytesIO(file.content))
    zip_dir = ZIP_DIR
    # Create the dir if does not exist
    create_dir(zip_dir)
    # Get the zip and extract it in the folder
    zip = ZipFile(BytesIO(file.content))
    zip.extractall(zip_dir)
    response = jsonify({"status": "accepted"})
    response.status_code = 200
    return response 

@app.route("/analyse",methods = ["POST"])
def analyse():
    app.logger.info("Requête reçu sur /archive")
    convId = request.form["convId"]
    userId = request.form["userId"]
    thread = threading.Thread(target = process, args=(convId,userId),daemon=True)
    thread.start()
    response = jsonify({"status": "accepted"})
    response.status_code = 200
    return response 

@app.route("/remove_file",methods = ['GET'])
def remove_file():
    zip_dir = ZIP_DIR
    clean(zip_dir)
    app.logger.info("Nettoyage terminé")
    return jsonify({"status" : "files removed"}),200

if __name__ == "__main__":
    app.run(host = "0.0.0.0",port = 5000)
