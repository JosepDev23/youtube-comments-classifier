#!/bin/bash

PROYECTO="$HOME/youtube-comments-classifier"

VENV="$PROYECTO/venv"

if [ ! -d "$VENV" ]; then
    echo "El entorno virtual no existe. Creándolo..."
    python3 -m venv "$VENV"
fi

source "$VENV/bin/activate"

echo "Entorno virtual activado."
cd "$PROYECTO"
echo "Ubicado en: $(pwd)"

exec bash