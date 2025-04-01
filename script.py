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
            likes = snippet["likeCount"]  # Número de likes
            replies = item["snippet"]["totalReplyCount"]  # Número de respuestas
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

print("Comentarios guardados en 'comentarios_youtube.csv'.")