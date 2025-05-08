
# FIRST STEP: Get data from YouTube comments (csv)

from googleapiclient.discovery import build # type: ignore
import pandas as pd # type: ignore

API_KEY = "AIzaSyDNiIKo2W_bvImZ2khuwEmMRt_hgXKYez0"
VIDEO_ID = "KGhCveH03Mo"

youtube = build("youtube", "v3", developerKey=API_KEY)

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

#SECOND STEP: Preproceso de los datos

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
    text = html.unescape(text)  # ✅ Decodifica entidades HTML (&amp; -> &, etc.)
    text = re.sub(r'https?://\S+|www\.\S+', '', text)  # ✅ Elimina URLs
    text = re.sub(r'\n', ' ', text)  # Elimina saltos de línea
    text = re.sub(r'[^\w\s\?\!\.\,]', '', text)  # Conserva ?, !, ., ,
    text = re.sub(r'\s+[a-z]\s+', ' ', text)  # Elimina palabras de un carácter
    text = re.sub(r'^b\s+', '', text)
    text = re.sub(r'\s+', ' ', text)  # Elimina espacios extra
    tokens = word_tokenize(text)
    tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]
    return ' '.join(tokens)

corpus = [preprocess_text(text) for text in df["Comentario"]]
df["Comentario"] = corpus
df.to_csv("comentarios_youtube_preprocesado.csv", index=False, encoding="utf-8")



#THIRD STEP: Obtener clasificación de los comentarios

import openai # type: ignore
import google.generativeai as genai # type: ignore
import requests

# =======================
# Configuración de APIs
# =======================
# OpenAI (ChatGPT)
openai_client = openai.OpenAI(api_key="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")

# Gemini (Google)
genai.configure(api_key="AIzaSyCBpbI1JHrgVe1ii5d_i2Jzde2fL7MqquM")
gemini_model = genai.GenerativeModel("models/gemini-2.0-flash")

# DeepSeek (simulada como ejemplo)
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = "sk-97c2b9a9aeb446ffba33d91b9359cc8e"

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

        # Diagnóstico: mostrar respuesta si no contiene 'choices'
        if "choices" not in result:
            print("[DeepSeek] Respuesta inesperada:")
            print(result)
            return "Error"

        return result["choices"][0]["message"]["content"].strip().capitalize()

    except Exception as e:
        print(f"[DeepSeek] Error: {e}")
        return "Error"


# =======================
# Consenso ponderado
# =======================

import time

def clasificacion_consenso(texto):
    votos = {"Positivo": 0, "Negativo": 0, "Neutral": 0}

    r1 = get_chatgpt_response(texto)
    r2 = get_gemini_response(texto)
    r3 = get_deepseek_response(texto)

    print(f"\nComentario: {texto}")
    print(f"ChatGPT: {r1}, Gemini: {r2}, DeepSeek: {r3}")

    if r1 in votos: votos[r1] += 5
    if r2 in votos: votos[r2] += 3
    if r3 in votos: votos[r3] += 3

    return max(votos, key=votos.get)

# =======================
# Ejemplo de uso con CSV
# =======================


df = pd.read_csv("comentarios_youtube_preprocesado.csv")

df["Clasificación"] = df["Comentario"].apply(clasificacion_consenso)

df.to_csv("comentarios_clasificados_consenso.csv", index=False, encoding="utf-8")
print("✔ Clasificación completada y guardada en comentarios_clasificados_consenso.csv")