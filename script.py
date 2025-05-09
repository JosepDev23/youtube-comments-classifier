# =======================
# Extracción de comentarios de YouTube
# =======================

from googleapiclient.discovery import build # type: ignore
import pandas as pd # type: ignore
import argparse
import os

parser = argparse.ArgumentParser(
    description="Extrae y clasifica los comentarios de un video de YouTube."
)
parser.add_argument(
    "video_id",
    help="ID del video de YouTube a procesar (p. ej. KGhCveH03Mo)",
)
args = parser.parse_args()
VIDEO_ID = args.video_id

YT_API_KEY: str | None = os.getenv("YT_API_KEY")
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY: str | None = os.getenv("DEEPSEEK_API_KEY")

youtube = build("youtube", "v3", developerKey=YT_API_KEY)

def obtener_comentarios(video_id):
    comments = []
    request = youtube.commentThreads().list(
        part="snippet,replies",
        videoId=video_id,
        maxResults=100
    )
    response = request.execute()

    while response:
        for item in response["items"]:
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            author = snippet["authorDisplayName"]
            text = snippet["textDisplay"]
            likes = snippet["likeCount"]
            replies = item["snippet"]["totalReplyCount"]
            published_at = snippet["publishedAt"]

            comments.append([author, text, likes, replies, published_at])

        if "nextPageToken" in response:
            response = youtube.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=100,
                pageToken=response["nextPageToken"]
            ).execute()
        else:
            break

    return comments

comentarios = obtener_comentarios(VIDEO_ID)
df = pd.DataFrame(comentarios, columns=["Autor", "Comentario", "Likes", "Respuestas", "Fecha"])
df.to_csv("comentarios_youtube.csv", index=False, encoding="utf-8")

# =======================
# Preprocesamiento de texto
# =======================

import re
import nltk
import html
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt_tab')

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    text = text.lower()
    text = html.unescape(text)  # Decodifica entidades HTML (&amp; -> &, etc.)
    text = re.sub(r'https?://\S+|www\.\S+', '', text)  # Elimina URLs
    text = re.sub(r'\n', ' ', text)  # Elimina saltos de línea
    text = re.sub(r'[^\w\s\?\!\.\,]', '', text)  # Conserva ?, !, ., ,
    text = re.sub(r'\s+[a-z]\s+', ' ', text)  # Elimina palabras de un carácter
    text = re.sub(r'^b\s+', '', text)
    text = re.sub(r'\s+', ' ', text)  # Elimina espacios extra
    tokens = word_tokenize(text)
    tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]
    return ' '.join(tokens)

df["Comentario_Preprocesado"] = df["Comentario"].apply(preprocess_text)

df.to_csv("comentarios_youtube_preprocesado.csv", index=False, encoding="utf-8")


import openai # type: ignore
import google.generativeai as genai # type: ignore
import requests

# =======================
# Configuración de APIs
# =======================

# ChatGPT
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Gemini
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("models/gemini-2.0-flash")

# DeepSeek
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# =======================
# Funciones de consulta
# =======================

def get_chatgpt_response(text):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Clasifica el siguiente comentario de YouTube en una sola palabra: Positivo, Negativo, Sugerencia o Pregunta. No des ninguna explicación, solo responde con una de esas tres palabras exactas."},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content.strip().capitalize()
    except Exception as e:
        print(f"[ChatGPT] Error: {e}")
        return "Error"


def get_gemini_response(text):
    try:
        prompt = f"""
            Clasifica el siguiente comentario de YouTube en una sola palabra: Positivo, Negativo, Sugerencia o Pregunta.
            No des ninguna explicación, solo responde con una de esas tres palabras exactas.

            Comentario:
            {text}
            """

        response = gemini_model.generate_content(prompt)
        return response.text.strip().capitalize()
    except Exception as e:
        print(f"[Gemini] Error: {e}")
        return "Error"

def get_deepseek_response(text):
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Clasifica el siguiente comentario de YouTube en una sola palabra: Positivo, Negativo, Sugerencia o Pregunta. No des ninguna explicación, solo responde con una de esas tres palabras exactas."},
                {"role": "user", "content": text}
            ]
        }

        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
        result = response.json()

        if "choices" not in result:
            print("[DeepSeek] Respuesta inesperada:")
            print(result)
            return "Error"

        return result["choices"][0]["message"]["content"].strip().capitalize()

    except Exception as e:
        print(f"[DeepSeek] Error: {e}")
        return "Error"

# =======================
# Clasificación de comentarios
# =======================

def clasificacion_consenso(texto):
    votos = {"Positivo": 0, "Negativo": 0, "Pregunta": 0, "Sugerencia": 0}

    r1 = get_chatgpt_response(texto)
    r2 = get_gemini_response(texto)
    r3 = get_deepseek_response(texto)

    if r1 in votos: votos[r1] += 5
    if r2 in votos: votos[r2] += 3
    if r3 in votos: votos[r3] += 3

    consenso = max(votos, key=votos.get)

    return consenso


df = pd.read_csv("comentarios_youtube_preprocesado.csv")

df["Clasificación"] = df["Comentario_Preprocesado"].apply(clasificacion_consenso)

df.to_csv("comentarios_clasificados_consenso.csv", index=False, encoding="utf-8")
print("\n✔ Clasificación completada y guardada en comentarios_clasificados_consenso.csv\n")
print("📊 Resumen de clasificaciones:")
print(df["Clasificación"].value_counts())
print(f"\n🧮 Total de comentarios clasificados: {len(df)}")
