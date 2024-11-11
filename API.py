from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import json
import csv
import xml.etree.ElementTree as ET
import re

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key="AIzaSyDnWQvuxUs24SpQnUND5WkgFQdMBsd_UiE")

def format_schedule_text(text: str) -> str:
    # Formata os dias da semana com negrito
    text = re.sub(r"(\*\*?[A-Za-zÀ-ú]+(?:-\w+)?\**?\s*[\w\s]+:[\n\s]+)", r"<b>\1</b>", text)
    
    # Aplica negrito nas disciplinas e professores
    text = re.sub(r"(\*\*?[A-Za-zÀ-ú\s]+[\w\s]+(\([A-Za-zÀ-ú]+\))?)", r"<b>\1</b>", text)
    
    # Substitui as quebras de linha
    text = text.replace("\n", "<br>")
    
    return text

@app.post("/process-file/")
async def process_file(file: UploadFile = File(...)):
    try:
        # Valida se o arquivo é um dos tipos permitidos
        if file.content_type not in ["text/csv", "text/plain", "application/xml", "application/json"]:
            raise HTTPException(status_code=400, detail="Arquivo não suportado. Envie um arquivo .csv, .txt, .xml ou .json.")
        
        # Lê o conteúdo do arquivo
        content = await file.read()
        try:
            decoded_content = content.decode("utf-8")
        except UnicodeDecodeError:
            decoded_content = content.decode("latin1")  # Tenta com 'latin1' se 'utf-8' falhar

        # Determina o formato do arquivo e estrutura o conteúdo para o Gemini
        if file.content_type == "text/csv":
            # Processa arquivos CSV
            csv_content = decoded_content.splitlines()
            csv_reader = csv.DictReader(csv_content)
            csv_data = [row for row in csv_reader]
            structured_content = json.dumps(csv_data, ensure_ascii=False)

        elif file.content_type == "text/plain":
            # Processa arquivos TXT
            structured_content = decoded_content

        elif file.content_type == "application/xml":
            # Processa arquivos XML
            try:
                root = ET.fromstring(decoded_content)
                xml_data = {child.tag: child.text for child in root}
                structured_content = json.dumps(xml_data, ensure_ascii=False)
            except ET.ParseError as e:
                raise HTTPException(status_code=400, detail=f"Erro ao processar XML: {str(e)}")

        elif file.content_type == "application/json":
            # Processa arquivos JSON
            try:
                json_data = json.loads(decoded_content)
                structured_content = json.dumps(json_data, ensure_ascii=False)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail=f"Erro ao processar JSON: {str(e)}")

        # Configura o prompt para a API Gemini incluindo o conteúdo estruturado
        prompt = f"Analise o conteúdo deste arquivo '{file.filename}'. Aqui está o conteúdo processado:\n\n{structured_content}\n\nResponda em português."

        # Conecta-se à API Gemini para processar o conteúdo
        response = genai.GenerativeModel("gemini-1.5-flash")
        result = response.generate_content([prompt])

        # Formata o texto de resposta com negrito e quebras de linha
        formatted_result = format_schedule_text(result.text)

        return {"analysis": formatted_result}

    except Exception as e:
        print(f"Erro: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar o arquivo com a API Gemini: {str(e)}")
