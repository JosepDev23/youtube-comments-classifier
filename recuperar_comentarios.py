import pandas as pd
import argparse

# Configurar argumentos de línea de comandos
parser = argparse.ArgumentParser(description="Filtra comentarios por tipo y los ordena por relevancia.")
parser.add_argument("tipo", help="Tipo de comentario a filtrar (por ejemplo: Pregunta, Opinión, Crítica)")
parser.add_argument("cantidad", type=int, help="Número de comentarios relevantes a mostrar")
args = parser.parse_args()

# Cargar el archivo CSV
archivo = "comentarios_clasificados_consenso.csv"
df = pd.read_csv(archivo)

# Filtrar los comentarios del tipo indicado
filtro_tipo = args.tipo
comentarios_filtrados = df[df['Clasificación'] == filtro_tipo].copy()

if comentarios_filtrados.empty:
    print(f"No se encontraron comentarios del tipo: {filtro_tipo}")
else:
    # Asegurar que los campos numéricos estén en formato correcto
    comentarios_filtrados['Likes'] = pd.to_numeric(comentarios_filtrados['Likes'], errors='coerce').fillna(0).astype(int)
    comentarios_filtrados['Respuestas'] = pd.to_numeric(comentarios_filtrados['Respuestas'], errors='coerce').fillna(0).astype(int)

    # Calcular la relevancia
    comentarios_filtrados['Relevancia'] = comentarios_filtrados['Likes'] + 5 * comentarios_filtrados['Respuestas']

    # Ordenar por relevancia
    comentarios_ordenados = comentarios_filtrados.sort_values(by='Relevancia', ascending=False)

    # Mostrar solo la cantidad de comentarios especificada
    top_n = args.cantidad
    print(f"\nTop {top_n} comentarios tipo '{filtro_tipo}' más relevantes:\n")
    for index, row in comentarios_ordenados.head(top_n).iterrows():
        print(f"- Relevancia: {row['Relevancia']}\n  Comentario: {row['Comentario']}\n")
