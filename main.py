import numpy as np
import pdfplumber
from flask import Flask, request, jsonify
import logging
from io import BytesIO
import requests
import re
import pandas as pd
import json
from zipfile import ZipFile
from PyPDF2 import PdfReader
from os import listdir, remove,walk,mkdir
from os.path import isfile, join, exists
from mistralai import Mistral
import datauri
import os
import base64
import mimetypes
import threading

app = Flask(__name__)
img_extension = {}

PDF_DIR="zip/"
ZIP_DIR ="zip/extract/"
api_key = os.environ.get("MISTRAL_API_KEY")
# print(api_key)
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
        return text
        
    else :
        return "Aucun fichier PDF reçu", 400

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
    thread = threading.Thread(target = process, args=(convId,userId,file_url),daemon=True)
    thread.start()
    response = jsonify({"status": "accepted"})
    response.status_code = 200
    return response 

def process(convId,userId,file_url):
    file = requests.get(file_url)
    app.logger.info(BytesIO(file.content))
    zip_dir = ZIP_DIR
    # Create the dir if does not exist
    create_dir(zip_dir)
    # Get the zip and extract it in the folder
    zip = ZipFile(BytesIO(file.content))
    zip.extractall(zip_dir)
    # Check if the files are pdf, extract the image and save it, extract the text from all the pdf
    list_files = list_files_walk(zip_dir)
    text_list = []
    for file in list_files:

        text = get_text(file)
        text_list.append(text)
    clean(zip_dir)
    logging.info("Nettoyage terminé")
    webhook_url = 'https://webhook.botpress.cloud/71137732-2ecf-48c1-b7e6-4484236e0433'
    data = {
        "convId" : convId,
        "userId" : userId,
        "text_list" : text_list
    }
    headers = {
        'Content-Type': 'application/json',
    }
    requests.post(webhook_url, data=json.dumps(data), headers=headers)
    logging.info("Webhook contacté")

def get_text(file_path):
    text = extract_pdf(file_path,pdf_dir="",stream=None)
    file_name = file_path.split('/')[-1]
    if text.strip() == "" :
            app.logger.info(f"{file_name} envoyé à mistral : {text.strip() == ""}")    
            ocr_response = client.ocr.process(
            model = "mistral-ocr-latest",
            document = {
                "type" : "document_url",
                "document_url" : upload_pdf(filename=file_path)
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
    if len(text) > 10000 :
        requete = client.chat.stream(
            model="mistral-large-latest",
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


@app.route("/get_file_list",methods = ['POST'])
def get_file_list():
    app.logger.info("Requête reçu sur /get_file_list")
    file_url = request.form["file_url"]
    file = requests.get(file_url)
    app.logger.info(BytesIO(file.content))
    zip_dir = ZIP_DIR
    # Create the dir if does not exist
    create_dir(zip_dir)
    # Get the zip and extract it in the folder
    zip = ZipFile(BytesIO(file.content))
    zip.extractall(zip_dir)
    # Check if the files are pdf, extract the image and save it, extract the text from all the pdf
    list_files = list_files_walk(zip_dir)
    nb_files = len(list_files)

    return jsonify(list_files)


@app.route("/remove_file",methods = ['GET'])
def remove_file():
    zip_dir = ZIP_DIR
    clean(zip_dir)
    app.logger.info("Nettoyage terminé")
    return jsonify({"status" : "files removed"}),200

# @app.route("/get_text", methods = ["POST"])
# def get_text():
#     app.logger.info("Requête reçu sur /get_text")
#     file_path = request.form["file_path"]
#     text = extract_pdf(file_path,pdf_dir="",stream=None)
#     file_name = file_path.split('/')[-1]
#     if text.strip() == "" :
#             app.logger.info(f"{file_name} envoyé à mistral : {text.strip() == ""}")    
#             ocr_response = client.ocr.process(
#             model = "mistral-ocr-latest",
#             document = {
#                 "type" : "document_url",
#                 "document_url" : upload_pdf(filename=file_path)
#             },
#             include_image_base64=False
#             )
#             full_text = ""
#             pages  = [page.markdown for page in ocr_response.pages]
#             full_text = "\n".join(pages)
#             text = post_processing_mistral(full_text)         
#     else :
#         app.logger.info(f"{file_name} non envoyé : {text.strip() == ""}")
#     app.logger.info(f"{file_name} : {len(text)}")
#     if len(text) > 3000 :
#         requete = client.chat.stream(
#             model="mistral-large-latest",
#             messages=[
#                 {
#                     "role" : "user",
#                     "content" : f"Résumé ce texte : {text}",
#                 },
#             ]
#         )
#         chunk_list = [chunk.data.choices[0].delta.content for chunk in requete]
#         text = "".join(chunk_list)
#     return text,200


def create_dir(dir):
    try:
        mkdir(dir)
        print(f"Directory '{dir}' created successfully.")
    except FileExistsError:
        print(f"Directory '{dir}' already exists.")
    except PermissionError:
        print(f"Permission denied: Unable to create '{dir}'.")
    except Exception as e:
        print(f"An error occurred: {e}")

def extract_pdf(file_name : str,stream = None,pdf_dir = PDF_DIR):
    text = ""
    if stream is not None :
        with pdfplumber.open(stream) as pdf :
            pages = [page.extract_text() for page in pdf.pages]
            text = "\n".join(pages)
    else :
        with pdfplumber.open(("").join([pdf_dir,file_name])) as pdf :
            pages = [page.extract_text() for page in pdf.pages]
            text = "\n".join(pages)
    return text


def text_without_com(text_parts:dict)->str:
    text = ""
    for title in text_parts:
        text += title+ '\n'
        text+=text_parts[title]
    return text


def clean_text(text)->str:
    remove_pattern = ["GALLEA Quentin","06-80-75-04-20", "quentin@credit-avenue.fr","Pour vous aider à faire valoir vos droits"]
    split_pattern_renseignement = "Renseignements emprunteurs"
    split_pattern_pro = "Situation professionnelle –"
    split_pattern_charge = "Personnes à charge"
    end_patterns = [" Patrimoine"," Crédit à la consommation"," Épargne",]
    for pattern in remove_pattern :
        text = text.replace(pattern,"")
    # Garde tout ce qui est après "Renseignements emprunteurs"
    # print(f"split_pattern_renseignement in text : {split_pattern_renseignement in text}")
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

def preprocessing(text:str)->str:
    pattern_list = ["Établie le [0-9/]*\n",
                    "GALLEA Quentin\n","06-80-75-04-20\n",
                    "quentin@credit-avenue.fr\n",
                    "[0-9]{1,2}/[0-9]{1,2}\n",
                    ]
    for pattern in pattern_list :
        text = re.sub(pattern,"",text)
    str_list = ["www.acpr.banque-france.fr)","En cas de réclamation, envoyez un courrier à l’attention de la Direction","Nous nous engageons \u00e0 en accuser r\u00e9ception sous 10 jours et \u00e0 apporter une r\u00e9ponse dans un d\u00e9lai maximum de 2 mois\n","Entreprise soumise au contr\u00f4le de l\u2019Autorit\u00e9 de Contr\u00f4le Prudentiel et de R\u00e9solution (ACPR) situ\u00e9e 4 Place de Budapest CS 92459 75436 Paris Cedex 09","Assurance de responsabilit\u00e9 civile professionnelle conforme aux articles L512-6 , L512-7 et R512-14 du Code des Assurances"]
    for string in str_list :
        text = text.replace(string,"")
    return text

def split_text(text:str,delimiters:list,verbose=False):
    text_parts = {}
    for i,delimiter in enumerate(delimiters):
        if delimiter in text :
            # Cherche le delimiter suivant afin d'isoler les texte qui correspond au paragraphe du delimiter en cours
            next_delimiter = find_next_delimiter(remainning_text=text.split(delimiter)[1], remaining_delimiters=delimiters[min(i,len(delimiters)):])
            if verbose :
                print(f"delimiter : {delimiter} | next_delimiter : {next_delimiter}")
            if next_delimiter is not None :
                m  = re.search(f"{delimiter}.*{next_delimiter}", text, re.DOTALL)
                if not m :
                    extracted_text = ""
                else :
                    extracted_text = m.group()
                    extracted_text = re.sub(f"{delimiter}|{next_delimiter}","",extracted_text).strip()
                text_parts[delimiter] = extracted_text
            else :
                text_parts[delimiter] = text.split(delimiter)[1]
    str_list = ["Commentaires – Situation professionnelle"," Commentaires – Situation personnelle"," Commentaires – Épargne","Commentaires – Projet"]
    for key in str_list:
        text_parts.pop(key,None)
    return text_parts

def find_next_delimiter(remainning_text,remaining_delimiters):
    # Cherche le prochain delimiter dans le texte parmis les delimiter de la liste, s'il n'y en a aucun revoie None
    for delimiter in remaining_delimiters:
        if delimiter in remainning_text :
            return delimiter
    return None

def create_delimiters_list(borrowers:list)->list[str]:
    # En fonction du nombre d'emprunteurs, ajoute les section Situation Professionnelle correspondantes 
    delimiters = ["DEMANDE DE FINANCEMENT",
                  " Renseignements emprunteurs",
                  " Personnes à charge",
                  " Commentaires – Situation personnelle",
                  " Commentaires – Situation familiale",
                  " Société - Interlocuteurs",
                  " Situation professionnelle –",
                  " Commentaires – Situation professionnelle",
                  " Patrimoine – Bien immobilier / Détail des prêts",
                  " Patrimoine – Part de société / Détail des prêts",
                  " Crédit à la consommation",
                  " Autres revenus et charges",
                  " Commentaires – Revenus, Charges et Patrimoine",
                  " Épargne",
                  " Commentaires – Épargne",
                  " Commentaires – Situation bancaire",
                  " Situation bancaire",
                  " Habitudes de vie",
                  " Récapitulatif projet",
                  " Commentaires – Projet",
                  " Données Financières",
                  " Plan de Financement",
                  " Garantie(s) Proposée(s)",
                  " Assurance(s)",
                  " Détails des prêts",
                  " Tableau des mensualités avec assurances",
                  " Paliers par prêt",
                  " Détail des échéances",
                  " Récapitulatif",
                  " Graphique",
                  ]
    pro_index = delimiters.index(" Situation professionnelle –")
    delimiters = delimiters[:pro_index]+[f" Situation professionnelle – {borrower}" for borrower in borrowers]+delimiters[pro_index:]
    delimiters.remove(" Situation professionnelle –")
    return delimiters

def get_informations(borrowers:list,text_parts:dict):
    
    # Remove Monsieur or Madame from the borrowers names.
    borrowers = [re.sub("Monsieur |Madame ","",borrower) for borrower in borrowers]
    # informations = dict(zip(borrowers,[{"name" : None ,"birth_date" : None, "address" : None, "salary" : None}]*len(borrowers)))
    informations = {borrower : {"name" : borrower,"birth_date": None, "address": None, "salary": None} for borrower in borrowers}
    
    infos = text_parts[" Renseignements emprunteurs"]
    
    # Birth Date 
    birth_dates = get_row(infos,"Date de naissance")
    birth_dates = re.findall("[0-9]*/[0-9]*/[0-9]*",birth_dates)
    for borrower,birth_date in zip(borrowers,birth_dates):
        informations[borrower]["birth_date"] = birth_date
    
    # Address TODO ajouter adresse pas française
    address = get_row(infos,"Adresse postale")
    address = re.findall("[0-9]+ [^0-9]*",address) #Commence par une suite de nombre puis du texte, s'arrête au porchain nombre

    
    cities = get_row(infos,"Ville")
    cities = re.findall("[a-zA-ZÀ-ÿ-]+",cities)
    
    zip_codes = get_row(infos,"Code postal [0-9]",remove_beginning=False)
    zip_codes = re.sub("Code postal","",zip_codes).strip()
    zip_codes = re.findall("[0-9]{5}",zip_codes)

    cities_from_zip_code = [get_commune_by_cp(zip_code) for zip_code in zip_codes]
    if len(cities) > len(borrowers):
        # TODO ajouter correction erreurs avec la base de données des villes
        # cities = cities[:len(borrowers)]
        cities = cities_from_zip_code
    for borrower,addres,zip_code,city in zip(borrowers,address,zip_codes,cities):
        informations[borrower]["address"] = f"{addres.strip()} {zip_code} {city}"
    # Salary #TODO ajouter plusieurs salaires
    for borrower in borrowers :
        if f" Situation professionnelle – Monsieur {borrower}" in text_parts :
            situation_pro = text_parts[f" Situation professionnelle – Monsieur {borrower}"]
        elif f" Situation professionnelle – Madame {borrower}" in text_parts :
            situation_pro = text_parts[f" Situation professionnelle – Madame {borrower}"]
        else :
            situation_pro = "0,00 €" # Si la personne n'a pas de situation professionnelle déclarée
        situation_pro = re.sub("[0-9]*/[0-9]*/[0-9]*","",situation_pro) # Enlève la date pour ne pas gêner le salaire
        salary = re.search("[0-9]{1,3} [0-9 ]{1,3},[0-9]{2} €|[0-9 ]{1,3},[0-9]{2} €",situation_pro).group() # Chercher un salaire de la forme 111 000,00 € ou 100,00 €.
        salary = re.sub(" |€","",salary)
        salary = float(re.sub(",",".",salary)) # Converti la virgule en point puis le str en float
        informations[borrower]["salary"] = salary

    return informations

def get_commune_by_cp(zip_code:str):
    # TODO Mettre un cas ou le code postal ne trouve pas
    df = pd.read_csv("019HexaSmal.csv", sep=";", encoding="ISO-8859-1",dtype={"Code_postal": str})
    row = df[df["Code_postal"] == zip_code].iloc[0]
    if isinstance(row["Ligne_5"], str):
        return row["Ligne_5"]
    else :
        return row["Nom_de_la_commune"]


def get_row(text:str,beginning:str,remove_beginning = True)->str:
    m = re.search(f"\n{beginning}.*",text)
    if not m :
        return ""
    result = m.group()
    if remove_beginning:
        result = re.sub(beginning,"",result).strip()
    return result

def get_borrowers(text:str)->list[str]:
    # Garde la partie entre DEMANDE DE FINANCEMENT et Projet afin de savoir le nom et le nombre d'emprunteurs
    borrowers = re.search(r"DEMANDE DE FINANCEMENT(.*?)Projet",text,re.DOTALL).group(1)
    # Enlève tout ce qui n'est pas un nom d'emprunteurs
    borrowers = re.sub("DEMANDE DE FINANCEMENT|Projet|Associé|Caution|[()/]|Société .*\n","",borrowers).strip()
    # Split en fonction du saut de ligne pour spérarer les emprunteurs
    borrowers = [x.strip() for x in  borrowers.split('\n')]
    return borrowers   

def get_loan(text_parts:dict)->tuple:
    loan = text_parts[" Détails des prêts"].lower() # Garde que ce qui est après Prêt principal amortissable de la section Détails des prêts
    loan = loan.split("prêt principal amortissable")[1]
    loan = loan.split("%")[0]+'%' # Enlève les données qui sont après le premier % (le taux)
    total = loan.split("€")[0].replace("prêt principal amortissable","").strip() # Recupère le total du prêt (ce qui est avant le €)
    taux = re.search("[0-9,]+ %",loan)[0] # Recupère le taux (juste avant le % )
    duree = loan.split("€")[1].split(taux)[0].strip() # Recupère la durée qui se trouve entre le total et le taux
    contexte = f"Prêt de {total}€ sur {duree} mois avec un taux de {taux}"
    duree = int(duree)
    taux = float(taux[:-2].replace(",","."))
    total = float(total.replace(",",".").replace(" ",""))
    return total,taux,duree,contexte

def list_files_walk(start_path='.'):
    files_list = []
    for root, dirs, files in walk(start_path):
        for file in files:
            files_list.append(join(root, file))
    return files_list

def clean(path : str) :
    for element in os.listdir(path):
        full_path = os.path.join(path,element)
        if os.path.isdir(full_path):
            clean(full_path)
            os.rmdir(full_path)
            print(f"Folder '{element}' deleted")
        else :
            os.remove(full_path)
            print(f"File '{element}' deleted")


def upload_pdf(filename : str):
    uploaded_pdf = client.files.upload(
       file = {
          "file_name" : filename,
          "content" : open(filename,"rb")
       },
       purpose = "ocr"
    )
    signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)
    return signed_url.url


def post_processing_mistral(text:str):
    pattern_list = pattern_list = [
    r"!\[img-\d+\.(?:jpg|jpeg|png|gif)\]\(img-\d+\.(?:jpg|jpeg|png|gif)\)"
    ]
    for pattern in pattern_list:
       text = re.sub(pattern,"",text)
       text = text.strip()
    return text

if __name__ == "__main__":
    app.run(host = "0.0.0.0",port = 5000)
