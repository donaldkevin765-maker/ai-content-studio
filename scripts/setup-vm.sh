#!/usr/bin/env bash
# ============================================================================
# Oracle Cloud VM Setup Script — AI Content Studio
# ============================================================================
# Esegui questo script sulla VM Oracle FRESCA per installare tutto.
# Uso: bash setup-vm.sh
# ============================================================================
set -euo pipefail

echo "=========================================="
echo "AI Content Studio — Setup VM Oracle"
echo "=========================================="

# ── 1. System update + Docker ────────────────────────
echo ""
echo "[1/6] Installazione Docker e dipendenze..."

sudo apt-get update -qq
sudo apt-get install -y -qq \
    ca-certificates curl gnupg lsb-release git

# Docker
curl -fsSL https://get.docker.com | sudo bash
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# Docker Compose
sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

echo "✓ Docker installato: $(docker --version)"
echo "✓ Docker Compose: $(docker-compose --version)"

# ── 2. Clona il repository ───────────────────────────
echo ""
echo "[2/6] Clonazione repository..."

REPO_URL="https://github.com/donaldkevin765-maker/ai-content-studio.git"
if [ ! -d /home/ubuntu/ai-content-studio ]; then
    git clone "$REPO_URL" /home/ubuntu/ai-content-studio
fi
cd /home/ubuntu/ai-content-studio

echo "✓ Repository clonato"

# ── 3. Crea file .env ────────────────────────────────
echo ""
echo "[3/6] Configurazione ambiente..."

if [ ! -f .env ]; then
    cat > .env << 'EOF'
# ── Database ──────────────────────────────────────────
DB_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -32)

# ── Supabase (per storage assets) ─────────────────────
SUPABASE_URL=https://endxgujdxrzssccfikql.supabase.co
SUPABASE_SERVICE_KEY=
SUPABASE_ACCESS_TOKEN=
SUPABASE_JWT_SECRET=
SUPABASE_PROJECT_REF=endxgujdxrzssccfikql

# ── HuggingFace (per immagini AI) ─────────────────────
HF_API_TOKEN=

# ── Backend ───────────────────────────────────────────
SECRET_KEY=$(openssl rand -base64 48)
CORS_ORIGINS=https://ai-content-studio-lac.vercel.app,http://localhost:3000

# ── DuckDNS (dominio gratis) ──────────────────────────
DUCK_DNS_TOKEN=
DUCK_DNS_DOMAIN=ai-content-studio
EOF
    echo "✓ File .env creato — MODIFICA I VALORI VUOTI!"
    echo "  nano /home/ubuntu/ai-content-studio/.env"
else
    echo "✓ File .env già esistente"
fi

# ── 4. Configura DuckDNS + SSL ───────────────────────
echo ""
echo "[4/6] Configurazione SSL (Let's Encrypt + DuckDNS)..."

# DuckDNS aggiornamento IP
if [ -n "$(grep DUCK_DNS_TOKEN .env | cut -d= -f2)" ] && [ "$(grep DUCK_DNS_TOKEN .env | cut -d= -f2)" != "YOUR_TOKEN" ]; then
    DUCK_TOKEN=$(grep DUCK_DNS_TOKEN .env | cut -d= -f2)
    DUCK_DOMAIN=$(grep DUCK_DNS_DOMAIN .env | cut -d= -f2)
    
    # Aggiorna IP DuckDNS
    curl -s "https://www.duckdns.org/update?domains=${DUCK_DOMAIN}&token=${DUCK_TOKEN}&ip="
    
    # Certbot per SSL (standalone)
    sudo apt-get install -y -qq certbot
    sudo certbot certonly --standalone \
        -d "${DUCK_DOMAIN}.duckdns.org" \
        --non-interactive \
        --agree-tos \
        -m admin@${DUCK_DOMAIN}.duckdns.org || true
    
    # Copia certificati per Nginx
    sudo mkdir -p /home/ubuntu/ai-content-studio/nginx/ssl
    sudo cp /etc/letsencrypt/live/${DUCK_DOMAIN}.duckdns.org/fullchain.pem \
        /home/ubuntu/ai-content-studio/nginx/ssl/
    sudo cp /etc/letsencrypt/live/${DUCK_DOMAIN}.duckdns.org/privkey.pem \
        /home/ubuntu/ai-content-studio/nginx/ssl/
    sudo chown -R ubuntu:ubuntu /home/ubuntu/ai-content-studio/nginx/ssl
    
    # Rinnovo automatico
    echo "0 3 * * * root certbot renew --quiet && docker-compose -f /home/ubuntu/ai-content-studio/docker-compose.yml restart nginx" | \
        sudo tee /etc/cron.d/certbot-renew
fi

# ── 5. Avvia i container ─────────────────────────────
echo ""
echo "[5/6] Avvio dei container Docker..."

cd /home/ubuntu/ai-content-studio
docker-compose pull
docker-compose up -d --build

echo "✓ Container avviati"
echo "  docker-compose ps — per vedere lo stato"

# ── 6. Mostra riepilogo ─────────────────────────────
echo ""
echo "=========================================="
echo "✅ Setup completato!"
echo "=========================================="
echo ""
echo "Servizi:"
echo "  Backend API:  http://$(curl -s ifconfig.me):8000"
echo "  Postgres:     localhost:5432"
echo "  Redis:        localhost:6379"
echo ""
echo "Comandi utili:"
echo "  docker-compose logs -f backend   # Log backend"
echo "  docker-compose logs -f celery    # Log worker"
echo "  docker-compose ps                # Stato servizi"
echo "  docker-compose restart backend   # Riavvio backend"
echo ""
echo "Prima di usare: MODIFICA .env con i valori reali:"
echo "  nano /home/ubuntu/ai-content-studio/.env"
echo "  docker-compose up -d --build"
echo ""
