import pytesseract
import numpy as np
import cv2
import pdfplumber
from flask import Flask, request, jsonify
import logging
from io import BytesIO

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
            file = request.get(file_url)
            app.logger.info(file.filename)
            text = ""
            with pdfplumber.open(BytesIO(file.content)) as pdf:
                for page in pdf.pages:
                    text += page.extract_text()
            app.logger.info(text)
            return text
        except : 
            app.logger.info("No url found")
            return jsonify({'No url found'}),400
    else :
        print("pas de méthode, ok")
        return jsonify({"status" : "no methods ok"}),200


if __name__ == "__main__":
    app.run(host = "0.0.0.0",port = 5000)
