import requests
import pdfplumber
from io import BytesIO
from PyPDF2 import PdfReader
# from pypdf import PdfReader
import re
import os
from os import listdir, remove
from os.path import isfile, join
import pandas as pd
import numpy as np
import io
from zipfile import ZipFile


PDF_DIR = "demande_financement/pdf/"
RESULT_DIR = "demande_financement/results/"


text_test = """"
DEMANDE DE FINANCEMENT
Monsieur Mathieu ADLI (Associé / Caution)
Madame Jessica ADLI (Associé / Caution)
Madame Sandrine ADLI (Associé / Caution)
Monsieur Patrick ADLI (Associé / Caution)
Société SARL ADLI (Société liée)
Projet
ACQUISITION DANS L'ANCIEN
USAGE LOCATIF
9 AVENUE DU PASTEUR
CHALLIES 34300 AGDE
Banque / Interlocuteur
Banque CAISSE D'EPARGNE (Code apporteur: -)
Agence bancaire
Interlocuteur
Adresse
Coordonnées
Email
Tél Mobile
Tél Fixe
 Renseignements emprunteurs
Type Individu Individu Individu Individu Société
Rôle Associé / Caution Associé / Caution Associé / Caution Associé / Caution Société liée
Civilité Monsieur Madame Madame Monsieur
Nom ADLI ADLI ADLI ADLI
Prénom Mathieu Jessica Sandrine Patrick
Date de naissance 05/07/1997 (28 ans) 28/06/1993 (32 ans) 08/01/1971 (54 ans) 12/08/1964 (61 ans)
Lieu de naissance BEZIERS BEZIERS MACON BEZIERS
Pays de naissance France France France France
Code postal de naissance 34500 34500 71000 34500
naissance
Nationalité France France France France
Société SARL ADLI
Adresse mail adlimathieu@gmail.com jessica.adli@yahoo.fr sand.adli@yahoo.fr
Téléphone portable 06-27-86-97-73 07-68-70-10-28 06-14-29-44-96 07-88-89-98-34
Adresse postale 1 Impasse Vincent Scotto4 Rue Jean Rostand 3 Rue Des Myosotis 3 Rue Des Myosotis
Complément d'adresse App C13
Code postal 34500 34500 34410 34410
Ville BEZIERS Beziers Sauvian Sauvian
Pays France France France France
Statut d'occupation Propriétaire Propriétaire Propriétaire Propriétaire
Date d'occupation 01/12/2022 01/11/2020 01/01/1994 01/11/1994
Situation familiale Célibataire Célibataire Marié(e) Marié(e)
Date mariage / pacs /
27/06/1992 27/06/1992
divorce
Régime matrimonial Communauté universelleCommunauté universelle
 Société - Interlocuteurs
Société Rôle Nom Téléphone Email
Société SARL ADLI Président / Gérant Mathieu ADLI 06-27-86-97-73 adlimathieu@gmail.com
Président / Gérant Jessica ADLI 07-68-70-10-28 jessica.adli@yahoo.fr
Président / Gérant Sandrine ADLI 06-14-29-44-96 sand.adli@yahoo.fr
Président / Gérant Patrick ADLI 07-88-89-98-34
 Situation professionnelle – Monsieur Mathieu ADLI
Statut
professionnel
Type de Date Date fin Revenu Période
Intitulé Employeur contrat embauche de contrat mensuel d’essai
Salarié(e) Non- Gestionnaire De Paye AUGEFI CDI 01/09/2022 1 990,00 € Non
cadre
Entreprise soumise au contrôle de l’Autorité de Contrôle Prudentiel et de Résolution (ACPR) située 4 Place de Budapest CS 92459 75436 Paris Cedex 09.(www.acpr.banque-france.fr)
Assurance de responsabilité civile professionnelle conforme aux articles L512-6 , L512-7 et R512-14 du Code des Assurances.
En cas de réclamation, envoyez un courrier à l’attention de la Direction.
Nous nous engageons à en accuser réception sous 10 jours et à apporter une réponse dans un délai maximum de 2 mois
 Situation professionnelle – Madame Jessica ADLI
Statut
professionnel
Type de Date Date fin Revenu Période
Intitulé Employeur contrat embauche de contrat mensuel d’essai
Enseignant Professeur Des Ecoles EDUCATION NATIONALE 01/09/2017 3 300,00 € Non
 Situation professionnelle – Madame Sandrine ADLI
Statut
professionnel
Type de Date Date fin Revenu Période
Intitulé Employeur contrat embauche de contrat mensuel d’essai
Salarié(e) Cadre Assistante De Direction MVF COMMUNICATION CDI 01/11/2022 1 495,00 € Non
 Situation professionnelle – Monsieur Patrick ADLI
Statut
professionnel
Type de Date Date fin Revenu Période
Intitulé Employeur contrat embauche de contrat mensuel d’essai
Salarié(e) Cadre Magasinier Vendeur AGROVIN CDI 01/06/2011 1 530,00 € Non
Entreprise soumise au contrôle de l’Autorité de Contrôle Prudentiel et de Résolution (ACPR) située 4 Place de Budapest CS 92459 75436 Paris Cedex 09.(www.acpr.banque-france.fr)
Assurance de responsabilité civile professionnelle conforme aux articles L512-6 , L512-7 et R512-14 du Code des Assurances.
En cas de réclamation, envoyez un courrier à l’attention de la Direction.
Nous nous engageons à en accuser réception sous 10 jours et à apporter une réponse dans un délai maximum de 2 mois
 Crédit à la consommation
Organisme Mensualité
Type prêteur Montant initial Taux ass. comprise Dont ass.
Madame Sandrine
Consommation NaN € 514,09 € NaN €
ADLI, Monsieur
"""


def test_botpress_file():

    url = 'https://files.bpcontent.cloud/2025/09/17/13/20250917132156-XVRVCEDQ.pdf'

    r = requests.get(url)

    with open('pdf-test.pdf','wb') as f:
        f.write(r.content)

    with pdfplumber.open(BytesIO(r.content)) as pdf:
        print(pdf.pages[0].extract_text())
    return None


def test_carcasse(online = False, file_path = None, file_url = None):
    if online :
        url = "http://37.187.39.26:5000/carcasse"
    else : 
        url = "http://127.0.0.1:5000/carcasse"
    if file_path is not None :
        files = {'file' : open(file_path, 'rb')}
        r = requests.post(url=url,files=files)
    elif file_url is not None:
        data = {"file_url" : file_url}
        r = requests.post(url=url,data=data)
    else :
        return None
    return r


def test_send_pdf(file_name,render=False):
    if render :
        url = "https://pdfwebhook.onrender.com/carcasse"
    else :
        url = "http://127.0.0.1:5000/carcasse"
    files = {'file' : open(file_name, 'rb')}

    r = requests.post(url=url,files=files)
    return r

def main2():
    pdf_dir = "demande_financement/pdf/"
    result_dir = "demande_financement/results/"
    files = [f for f in listdir(pdf_dir) if isfile(join(pdf_dir,f))]
    for file in files :
        text = test_send_pdf(file_name=join(pdf_dir,file))
        with open(join(result_dir,file).replace(".pdf",".txt"),"w") as f:
            f.write(text)

def preprocessing(text:str)->str:
    pattern_list = ["Établie le [0-9/]*\n","GALLEA Quentin\n","06-80-75-04-20\n","quentin@credit-avenue.fr\n","[0-9]{1,2}/[0-9]{1,2}\n"]
    for pattern in pattern_list :
        text = re.sub(pattern,"",text)
    return text

def extract_pdf(file_name:str,pdf_dir = PDF_DIR):
    text = ""
    with pdfplumber.open(("").join([pdf_dir,file_name])) as pdf :
        for page in pdf.pages :
            text += page.extract_text() + "\n"
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
                extracted_text = re.search(f"{delimiter}.*{next_delimiter}", text, re.DOTALL).group()
                extracted_text = re.sub(f"{delimiter}|{next_delimiter}","",extracted_text).strip()
                text_parts[delimiter] = extracted_text
            else :
                text_parts[delimiter] = text.split(delimiter)[1]
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
                  "Projet",
                  " Renseignements emprunteurs",
                  " Personnes à charge"
                  " Commentaires – Situation personnelle",
                  " Société - Interlocuteurs",
                  " Situation professionnelle –",
                  "Commentaires – Situation professionnelle",
                  " Patrimoine",
                  " Crédit à la consommation",
                  " Épargne",
                  " Commentaires – Épargne"
                  " Situation bancaire",
                  " Habitudes de vie",
                  " Récapitulatif projet",
                  "Commentaires – Projet",
                  " Données Financières",
                  " Plan de Financement"
                  "Garantie(s) Proposée(s)",
                  "Assurance(s)",
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
    informations = {borrower : {"birth_date": None, "address": None, "salary": None} for borrower in borrowers}
    
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
    result = re.search(f"\n{beginning}.*",text).group()
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
    return total,taux,duree

def workflow(file):
    text = extract_pdf(file)
    text = preprocessing(text)
    borrowers = get_borrowers(text)
    delimiters = create_delimiters_list(borrowers)
    
    text_parts = split_text(text=text,delimiters=delimiters)
    
    informations = get_informations(borrowers,text_parts)
    total,taux,duree = get_loan(text_parts)
    return text,{"borrowers" : informations , "total" : total,"taux" : taux, "duration" :duree}

def workflow2():
    render = False
    files = [f for f in listdir(PDF_DIR) if isfile(join(PDF_DIR,f))]
    r = test_send_pdf(PDF_DIR + files[0],render=render)
    return None

def main3():
    folder = "zip/"
    zip_name = "Partage_MINITAUX_Actelo.zip"
    with ZipFile(folder + zip_name ,'r') as zip_object :
        zip_object.extractall(folder)
    
def main4():
    DIR_PATH = "/home/nathan/workspace/pdfWebhook/zip/Partage_MINITAUX_Actelo/Pièce d'identité (CNI Passeport Titre de séjour...)/"
    file_name = "image (1).pdf"

    reader = PdfReader(DIR_PATH + file_name)
    page = reader.pages[0]
    for i, image_file_object in enumerate(page.images):
        file_name = "out-image-" + str(i) + "-" + image_file_object.name
        image_file_object.image.save(file_name)

def zip():
    file_url = "https://files.bpcontent.cloud/2025/12/03/15/20251203152054-3TAZ1V2N.zip"
    file_path = "/home/nathan/workspace/pdfWebhook/zip/Partage_MINITAUX_Actelo/archive2.zip"
    clean_files = True
    online = False
    zip_dir = "zip/test/"
    image_dir = "image/"
    # Get the zip and extract it in the folder
    if online :
        file = requests.get(file_url)
        zip = ZipFile(io.BytesIO(file.content))
    else : 
        zip = ZipFile(file_path)
    zip.extractall(zip_dir)
    data = {}
    # Check if the files are pdf, extract the image and save it, extract the text from all the pdf
    list_files = list_files_walk(zip_dir)

    list_files = list(filter(lambda x : x is not None,list_files))
    for file_path in list_files:
        file_name = file_path.split('/')[-1]
        # print(file_name)
        # print(os.path.isdir(file_path))
        if file_path[-3:] != 'pdf':
            continue
        text = extract_pdf(file_path,pdf_dir="")
        if text.strip() == "" :
            reader = PdfReader(file_path)
            page = reader.pages[0]
            for i, image_file_object in enumerate(page.images):
                file_name = f"{image_dir}{file_name.split('.')[0]}-{str(i)}-{image_file_object.name}" # image dir, name of the pdf the image is from, number of the image
                image_file_object.image.save(file_name)
                text = ocr(file_name)
                # Store the text retru nby the ocr
                data[file_name] = text
        else :
            # Store the text from pdf
            data[file_name] = text
    # Remove all the files extracted and the images saved
    if clean_files :
        clean(zip_dir)
        clean(image_dir)

def list_files_walk(start_path='.'):
    files_list = []
    for root, dirs, files in os.walk(start_path):
        for file in files:
            files_list.append(os.path.join(root, file))
    return files_list


def ocr(file_name):
    return f"{file_name} -> ocr result"

def clean(dir : str) -> None:
    # Ajouter supprimer dossier.
    for f in list_files_walk(dir):
        if os.path.exists(f) :
            remove(f)
        else :
            print("File does not exist")
    return None

def get_pdf(dir : str):
    for f in listdir(dir):
        file_path = dir + f
        if file_path[-3:] != 'pdf':
            continue
        reader = PdfReader(file_path)

def get_zip(url : str,extract_dir = "zip/") :
    file = requests.get(url)
    zip = ZipFile(io.BytesIO(file.content))
    zip.extractall(extract_dir)
    return None


def test_zip(zip_url : str, render = False):
    if render :
        url = "http://vps-fd7f6448.vps.ovh.net:5000/archive"
    else :
        url = "http://127.0.0.1:5000/archive"
    data = {
        "file_url" : zip_url
    }
    print(data)
    r = requests.post(url=url,data=data)
    print(r.status_code)
    print(r.text)
    return None

def test_get_files_list(online : bool, zip_url : str):
    if online : 
        url = "http://37.187.39.26:5000/get_file_list"
    else : 
        url = "http://127.0.0.1:5000/get_file_list"
    data = {
        "file_url" : zip_url
    }
    r = requests.post(url=url,data=data)
    file_list = r.json()
    return file_list

def test_get_text(file_path,online=False):
    if online : 
        url = "http://37.187.39.26:5000/get_text"
    else : 
        url = "http://127.0.0.1:5000/get_text"
    data = {
        "file_path" : file_path
    }
    r = requests.post(url = url, data = data)
    print(r.status_code)
    print(r.text)
    return None

def test_delete_file(online = False):
    if online : 
        url = "http://37.187.39.26:5000/remove_file"
    else : 
        url = "http://127.0.0.1:5000/remove_file"
    r = requests.get(url = url)
    print(r.status_code)
    return None   

def workflow_zip():   
    zip_url = "https://files.bpcontent.cloud/2025/12/29/14/20251229140021-90TBC5V0.zip"
    online = False
    file_list = test_get_files_list(online = online, zip_url=zip_url)
    text_list = []
    for file in file_list:
        text = test_get_text(file,online=online)
        text_list.append(text)
    test_delete_file(online=online)

def workflow_carcasse():
    file_url = "https://files.bpcontent.cloud/2025/12/31/14/20251231143746-BZLKU8A9.pdf"
    #  file_path = "/home/nathan/workspace/pdfWebhook/demande_financement/pdf/ADLI.pdf"
    result = test_carcasse(online=True,file_url=file_url)
    print(result.text)

def workflow_file_list():
    zip_url = "https://files.bpcontent.cloud/2025/12/29/14/20251229140021-90TBC5V0.zip"
    online = True
    test_get_files_list(online = online, zip_url=zip_url)

def workflow_get_text():
    file_path = "zip/extract/Partage_MINITAUX_Actelo/3 derniers mois de relev\u00e9 de compte bancaire (tous les comptes)/Releve n 010 du 06-10-2025_CCHQ 85108707173 M GIMENO JEROME.pdf"
    test_get_text(file_path)


def workflow_archive():
    zipUrl = "https://files.bpcontent.cloud/2026/01/23/09/20260123093014-YIBY7V9Z.zip"
    convId = "convo-1"
    online = False
    if online : 
        url = "http://37.187.39.26:5000/archive"
    else : 
        url = "http://127.0.0.1:5000/archive"
    data = {
        "file_url" : zipUrl,
        "convId" : convId
    }
    r = requests.post(url=url,data=data)
    print(r.text)

def clean(dir : str) :
    for element in os.listdir(dir):
        if os.path.isdir(dir+element):
            element += '/'
            clean(dir+element)
            os.rmdir(dir+element)
            print(f"Folder '{element}' deleted")
        else :
            if os.path.exists(dir+element):
                os.remove(dir+element)
                print(f"File '{element}' deleted")
            else :
                print(f"File '{element}' does not exist")
    

if __name__ == "__main__":
    # url = "http://127.0.0.1:5000/test"
    # response = requests.get(url)

    # print("Status code :", response.status_code)
    # print("Réponse JSON :", response.json())
    workflow_archive()

