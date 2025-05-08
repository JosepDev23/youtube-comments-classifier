
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