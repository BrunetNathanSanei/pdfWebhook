import pytesseract
import numpy as np
import cv2
import pdfplumber
from flask import Flask, request, jsonify

app = Flask(__name__)
img_extension = {}


@app.route("/webhook", methods=['POST'])
def webhook():
    if "file" not in request.files :
        return "Aucun fichier PDF reçu", 400
    
    file = request.files["file"]
    extension = file.filename.split('.')[-1]
    print(extension)
    if extension == 'pdf' :
        text = ""
        with pdfplumber.open(file.stream) as pdf :
            for page in pdf.pages :
                text += page.extract_text() + "\n"
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

if __name__ == "__main__":
    app.run(host = "0.0.0.0",port = 5000)


# img = cv.imread("1444x920_20mn-30763.jpeg")

# img_gray = cv.cvtColor(img,cv.COLOR_BAYER_BG2GRAY)
# threshold_img = cv.threshold(img_gray, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)[1]

# cv.imshow('Image',img)
# cv.waitKey(10000)

# text = pytesseract.image_to_string(img)

# print(text)

