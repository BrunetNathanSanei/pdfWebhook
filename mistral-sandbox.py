from mistralai import Mistral
import datauri
import os
import base64
import mimetypes
import re
import requests
from os import listdir, remove,walk,mkdir
from os.path import isfile, join, exists, getsize
from zipfile import ZipFile
from io import BytesIO

MISTRAL_API_KEY = "kDmMno9Tv66m5rxeZnEVYBLPjoZ5ys9F"
client = Mistral(api_key = MISTRAL_API_KEY)

def main():
   filename = "CT 2022 2.pdf"
   ocr_response = client.ocr.process(
      model = "mistral-ocr-latest",
      document = {
         "type" : "document_url",
         "document_url" : upload_pdf(filename=filename)
      },
      include_image_base64=True
   )
   full_text = ""
   pages  = [page.markdown for page in ocr_response.pages]
   full_text = "\n".join(pages)
   text = post_processing_mistral(full_text)
   request = client.chat.stream(
      model="mistral-large-latest",
      messages=[
         {
            "role" : "user",
            "content" : f"Résumé ce texte : {text}",
         },
      ]
   )
   chunk_list = [chunk.data.choices[0].delta.content for chunk in request]
   text = "".join(chunk_list)
   print(text)

def post_processing_mistral(text:str):
    pattern_list = pattern_list = [
    r"!\[img-\d+\.(?:jpg|jpeg|png|gif)\]\(img-\d+\.(?:jpg|jpeg|png|gif)\)"
    ]
    for pattern in pattern_list:
       text = re.sub(pattern,"",text)
       text = text.strip()
    return text


def get_file_list(file_url :str):
   print("Requête reçu sur /get_file_list")
   file = requests.get(file_url)
   zip_dir = "zip/tests/"
   # Create the dir if does not exist
   create_dir(zip_dir)
   # Get the zip and extract it in the folder
   zip = ZipFile(BytesIO(file.content))
   zip.extractall(zip_dir)
   # Check if the files are pdf, extract the image and save it, extract the text from all the pdf
   list_files = list_files_walk(zip_dir)
   nb_files = len(list_files)
   print(nb_files)

   print(get_files_size(file_list=list_files)/1000,"Kb")
   return list_files

def get_files_size(file_list):
   total = 0
   for file in file_list:
      total += getsize(file)
   return total


def list_files_walk(start_path='.'):
    files_list = []
    for root, dirs, files in walk(start_path):
        for file in files:
            files_list.append(join(root, file))
    return files_list


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

def load_image(image_path):
  mime_type, _ = mimetypes.guess_type(image_path)
  with open(image_path, "rb") as image_file:
    image_data = image_file.read()
  base64_encoded = base64.b64encode(image_data).decode('utf-8')
  base64_url = f"data:{mime_type};base64,{base64_encoded}"
  return base64_url

if __name__ == "__main__":
   url = "https://files.bpcontent.cloud/2026/01/08/13/20260108132351-CXKMMS91.zip"
   get_file_list(url)

