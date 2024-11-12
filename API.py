from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import json
import csv
import xmltodict
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
    text = re.sub(r"(\*\*?[A-Za-zÀ-ú]+(?:-\w+)?\**?\s*[\w\s]+:[\n\s]+)", r"<b>\1</b>", text)
    text = re.sub(r"(\*\*?[A-Za-zÀ-ú\s]+[\w\s]+(\([A-Za-zÀ-ú]+\))?)", r"<b>\1</b>", text)
    text = text.replace("\n", "<br>")
    
    return text

@app.post("/process-file/")
async def process_file(file: UploadFile = File(...)):
    try:
        if not (file.filename.endswith(".csv") or file.filename.endswith(".txt") or file.filename.endswith(".xml") or file.filename.endswith(".json")):
            raise HTTPException(status_code=400, detail="Arquivo não suportado. Envie um arquivo .csv, .txt, .xml ou .json.")
        
        content = await file.read()
        
        try:
            decoded_content = content.decode("utf-8")
        except UnicodeDecodeError:
            decoded_content = content.decode("latin1")

        if file.filename.endswith(".csv"):
            csv_content = decoded_content.splitlines()
            csv_reader = csv.DictReader(csv_content)
            csv_data = [row for row in csv_reader]
            structured_content = json.dumps(csv_data, ensure_ascii=False)

        elif file.filename.endswith(".txt"):
            structured_content = decoded_content

        elif file.filename.endswith(".xml"):
            try:
                xml_dict = xmltodict.parse(decoded_content)
                structured_content = json.dumps(xml_dict, ensure_ascii=False)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Erro ao processar XML: {str(e)}")

        elif file.filename.endswith(".json"):
            try:
                json_data = json.loads(decoded_content)
                structured_content = json.dumps(json_data, ensure_ascii=False)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail=f"Erro ao processar JSON: {str(e)}")

        prompt = f"Analise o conteúdo deste arquivo '{file.filename}'. Aqui está o conteúdo processado:\n\n{structured_content}\n\nResponda em português."

        response = genai.GenerativeModel("gemini-1.5-flash")
        result = response.generate_content([prompt])

        formatted_result = format_schedule_text(result.text)

        return {"analysis": formatted_result}

    except Exception as e:
        print(f"Erro: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar o arquivo com a API Gemini: {str(e)}")
