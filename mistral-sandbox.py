from mistralai import Mistral
import datauri
import os
import base64
import mimetypes
import re

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
   main()

