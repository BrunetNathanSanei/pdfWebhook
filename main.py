import pytesseract
import numpy as np
import cv2
import pdfplumber
from flask import Flask, request, jsonify
import logging
from io import BytesIO
import requests

app = Flask(__name__)
img_extension = {}

logging.basicConfig(level=logging.INFO)


@app.route("/webhook", methods=['POST'])
def webhook():
    if "file" not in request.files :
        return "Aucun fichier PDF reçu", 400
    
    file = request.files["file"]
    extension = file.filename.split('.')[-1]
    print('file extension : {extension}')
    if extension == 'pdf' :
        text = ""
        with pdfplumber.open(file.stream) as pdf :
            for page in pdf.pages :
                text += page.extract_text() + "\n"
        print(f'text : {text}')
        return text
    elif extension.lower() in img_extension:
        file_bytes = np.frombuffer(file.read(), np.uint8)

        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        print(img.shape)
        img_gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        #threshold_img = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        text = pytesseract.image_to_string(img_gray)
        return text
    else :
        return "Aucun fichier PDF reçu", 400

@app.route("/test",methods = ['GET','POST'])
def test():
    app.logger.info("Requête reçue sur /test")
    if request.method == 'GET':
        return jsonify({"status" : "get ok"}),200
    elif request.method == 'POST':
        try :
            file_url = request.form["file_url"]
            file = requests.get(file_url)
            text = ""
            with pdfplumber.open(BytesIO(file.content)) as pdf:
                for page in pdf.pages:
                    text += page.extract_text()
            text = clean_text(text)
            app.logger.info(text)
            return text
        except : 
            app.logger.info("No url found")
            return jsonify({'No url found'}),400
    else :
        print("pas de méthode, ok")
        return jsonify({"status" : "no methods ok"}),200


@app.route("/send_pdf",methods = ['POST'])
def send_pdf():
    if "file" not in request.files :
        return "Aucun fichier PDF reçu", 400
    
    
    file = request.files["file"]
    extension = file.filename.split('.')[-1]
    print(f'file extension : {extension}')
    if extension == 'pdf' :
        text = ""
        with pdfplumber.open(file.stream) as pdf :
            for page in pdf.pages :
                text += page.extract_text() + "\n"
        begin_pattern = "DEMANDE DE FINANCEMENT"
        # if begin_pattern in text :
        #     text = text.split(begin_pattern)[1]
        text = clean_text(text)

        return text
        
    else :
        return "Aucun fichier PDF reçu", 400


def clean_text(text)->str:
    remove_pattern = ["GALLEA Quentin","06-80-75-04-20", "quentin@credit-avenue.fr","Pour vous aider à faire valoir vos droits"]
    split_pattern_renseignement = "Renseignements emprunteurs"
    split_pattern_pro = "Situation professionnelle –"
    split_pattern_charge = "Personnes à charge"
    end_patterns = [" Patrimoine"," Crédit à la consommation"," Épargne",]
    for pattern in remove_pattern :
        text = text.replace(pattern,"")
    # Garde tout ce qui est après "Renseignements emprunteurs"
    print(f"split_pattern_renseignement in text : {split_pattern_renseignement in text}")
    if split_pattern_renseignement in text :
        text = text.split(split_pattern_renseignement)[1]
    # Coupe en 2 à "Situation professionnelle"
    if split_pattern_pro in text :
        part0 = text.split(split_pattern_pro)[0]
        part1 = "\n".join(text.split(split_pattern_pro)[1:])
        # Enlève de la partie du haut ce qui concerne "Personnes à charge"
        if split_pattern_charge in part0:
            part0=text.split(split_pattern_charge)[0]
        for end in end_patterns :
            if end in part1:
                part1 =part1.split(end)[0]
                break
        text = part0 + part1
        return text
    else :
        return text

if __name__ == "__main__":
    app.run(host = "0.0.0.0",port = 5000)
