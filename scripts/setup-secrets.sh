#!/usr/bin/env bash
# ============================================================================
# Setup script: configura le variabili d'ambiente rimanenti
# ============================================================================
# Questo script configura:
#   1. HF_API_TOKEN (richiede azione manuale: generare un token su huggingface.co)
#   2. GitHub Secrets (per il workflow di compilazione video in CI)
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"

echo "=== Setup Secrets per AI Content Studio ==="
echo ""

# ────────────────────────────────────────
# 1. HF_API_TOKEN
# ────────────────────────────────────────
echo "─── 1. HuggingFace API Token ───"
echo ""
echo "Per generare immagini AI reali (SDXL / SD3.5) serve un token gratuito."
echo ""
echo "Passaggi:"
echo "  1. Vai su https://huggingface.co/settings/tokens"
echo "  2. Clicca 'Create new token' → seleziona 'Read'"
echo "  3. Imposta nome es: 'ai-content-studio'"
echo "  4. Copia il token (inizia con hf_)"
echo ""
echo "Poi esegui:"
echo "  npx vercel env add HF_API_TOKEN production \\"
echo "    --value \"hf_IL_TUO_TOKEN_QUI\" \\"
echo "    --cwd \"$BACKEND_DIR\" \\"
echo "    --yes"
echo ""
echo "  npx vercel --prod --cwd \"$BACKEND_DIR\" --yes"
echo ""

# Prompt per configurare ora
read -rp "Hai già un token HF? Inseriscilo qui (o lascia vuoto per dopo): " HF_TOKEN
if [ -n "$HF_TOKEN" ]; then
    echo ""
    echo "Configurazione HF_API_TOKEN su Vercel..."
    npx vercel env add HF_API_TOKEN production --value "$HF_TOKEN" --cwd "$BACKEND_DIR" --yes
    echo "✓ HF_API_TOKEN configurato!"
    echo "Ridistribuzione del backend..."
    npx vercel --prod --cwd "$BACKEND_DIR" --yes
    echo "✓ Backend ridistribuito con HF_API_TOKEN"
else
    echo "Saltato. Puoi configurarlo manualmente in seguito."
fi
echo ""

# ────────────────────────────────────────
# 2. GitHub Secrets
# ────────────────────────────────────────
echo "─── 2. GitHub Secrets per workflow compile-video ───"
echo ""
echo "Il workflow .github/workflows/compile-video.yml usa ffmpeg in GitHub Actions"
echo "per compilare video quando Vercel non può (es. formati 4K pesanti)."
echo ""
echo "Serve configurare i seguenti GitHub Secrets nel repository:"
echo "  - SUPABASE_URL"
echo "  - SUPABASE_SERVICE_KEY"
echo "  - DATABASE_URL"
echo ""

# Leggi valori dal .env del backend
ENV_FILE="$BACKEND_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    echo "Valori trovati in $ENV_FILE:"
    grep -E "^(SUPABASE_URL=|SUPABASE_SERVICE_KEY=|DATABASE_URL=)" "$ENV_FILE" || echo "(nessun valore trovato)"
else
    echo "(file $ENV_FILE non trovato, usa i valori dal tuo .env)"
fi
echo ""

if command -v gh &>/dev/null; then
    echo "Rilevato gh CLI."

    # Controlla autenticazione
    if gh auth status &>/dev/null; then
        echo "Autenticazione gh valida. Configurazione secrets..."
        echo ""

        for key in SUPABASE_URL SUPABASE_SERVICE_KEY DATABASE_URL; do
            value=$(grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d'=' -f2-)
            if [ -n "$value" ]; then
                echo "Imposto $key..."
                echo "$value" | gh secret set "$key" --repo "$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo ".")" 2>/dev/null || \
                echo "  ✗ Impossibile impostare $key. Imposta manualmente."
            else
                echo "  Saltato $key (valore non trovato)"
            fi
        done
        echo "✓ Secrets configurati!"
    else
        echo "gh non autenticato. Esegui: gh auth login"
        echo "Oppure configura i secrets manualmente su:"
        echo "  https://github.com/$(git -C "$PROJECT_DIR" config --get remote.origin.url 2>/dev/null | sed 's/.*://;s/\.git$//' || echo '<your-repo>')/settings/secrets/actions"
    fi
else
    echo "gh CLI non installato."
    echo ""
    echo "Per configurare manualmente i secrets:"
    echo "  1. Vai su GitHub → repository → Settings → Secrets and variables → Actions"
    echo "  2. Clicca 'New repository secret' per ognuno:"
    echo "     - Name: SUPABASE_URL"
    echo "       Value: $(grep -E "^SUPABASE_URL=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d'=' -f2- || echo "<dal tuo .env>")"
    echo "     - Name: SUPABASE_SERVICE_KEY"
    echo "       Value: $(grep -E "^SUPABASE_SERVICE_KEY=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d'=' -f2- || echo "<dal tuo .env>")"
    echo "     - Name: DATABASE_URL"
    echo "       Value: $(grep -E "^DATABASE_URL=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d'=' -f2- || echo "<dal tuo .env>")"
    echo ""
    echo "Oppure installa gh CLI:"
    echo "  brew install gh"
    echo "  gh auth login"
    echo "  bash scripts/setup-secrets.sh"
fi

echo ""
echo "=== Setup completato ==="
echo "Riepilogo:"
echo "  ✓ Backend: https://backend-azure-kappa-69.vercel.app"
echo "  ✓ Frontend: https://ai-content-studio-lac.vercel.app"
echo "  ⬜ HF_API_TOKEN: $( [ -n "$HF_TOKEN" ] && echo 'configurato' || echo 'da configurare' )"
echo "  ⬜ GitHub Secrets: da verificare"
echo ""
echo "Per testare la pipeline completa:"
echo "  1. Crea un progetto dalla UI: https://ai-content-studio-lac.vercel.app"
echo "  2. Aggiungi un video e genera script"
echo "  3. Clicca 'Render' per generare audio/immagini"
echo "  4. Clicca 'Compile' per compilare il video finale"
echo ""
