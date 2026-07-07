#!/bin/bash
# Avvia il backend AI Content Studio in locale
# I progetti restano salvati in data/video_ai.db
# I video generati vanno in output/videos/

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Attiva l'ambiente virtuale
source .venv/bin/activate 2>/dev/null || {
    echo "Creazione ambiente virtuale..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]" 
}

echo "=== Avvio backend su http://localhost:8000 ==="
echo "Documentazione API: http://localhost:8000/docs"
echo "Premi Ctrl+C per fermarlo"
echo ""

python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
