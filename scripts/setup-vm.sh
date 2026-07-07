#!/usr/bin/env bash
# ============================================================================
# AI Content Studio — Setup completo per Oracle Cloud VM
# ============================================================================
# Esegui come ubuntu sulla VM FRESCA.
#   curl -fsSL https://raw.githubusercontent.com/donaldkevin765-maker/ai-content-studio/main/scripts/setup-vm.sh | bash
# Oppure (dopo aver clonato):
#   bash setup-vm.sh
# ============================================================================
set -euo pipefail

# ── Colori ─────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()   { echo -e "${RED}[ERR]${NC} $1"; }

cd /home/ubuntu

info "=========================================="
info "AI Content Studio — Setup VM Oracle"
info "=========================================="

# ── 1. System update + Docker ────────────────────────
info "[1/7] Installazione Docker e dipendenze..."

sudo apt-get update -qq
sudo apt-get install -y -qq \
    ca-certificates curl gnupg lsb-release git jq

if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sudo bash
fi
sudo systemctl enable docker
sudo usermod -aG docker ubuntu || true

if ! command -v docker-compose &>/dev/null; then
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | jq -r .tag_name)
    sudo curl -SL "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

ok "Docker: $(docker --version 2>/dev/null || echo 'OK')"
ok "Docker Compose: $(docker-compose --version 2>/dev/null || echo 'OK')"

# ── 2. Clona repo ────────────────────────────────────
info "[2/7] Clonazione repository..."

REPO_URL="https://github.com/donaldkevin765-maker/ai-content-studio.git"
TARGET="/home/ubuntu/ai-content-studio"

if [ ! -d "$TARGET" ]; then
    git clone "$REPO_URL" "$TARGET"
    ok "Repository clonato"
else
    cd "$TARGET" && git pull
    ok "Repository già presente, aggiornato"
fi
cd "$TARGET"

# ── 3. File .env interattivo ─────────────────────────
info "[3/7] Configurazione ambiente..."

ENV_FILE="$TARGET/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo ""
    info "Inserisci le credenziali (Invio = salta, verrà chiesto dopo)"
    echo ""

    read -p "  SUPABASE_SERVICE_KEY [richiesto]: " SUPABASE_SERVICE_KEY
    read -p "  SUPABASE_ACCESS_TOKEN [opzionale]: " SUPABASE_ACCESS_TOKEN
    read -p "  SUPABASE_JWT_SECRET [opzionale]: " SUPABASE_JWT_SECRET
    read -p "  HF_API_TOKEN [richiesto per immagini AI]: " HF_API_TOKEN
    read -p "  DuckDNS domain [default: ai-content-studio]: " DUCK_DOMAIN
    DUCK_DOMAIN=${DUCK_DOMAIN:-ai-content-studio}
    read -p "  DuckDNS token [opzionale senza SSL]: " DUCK_TOKEN

    DB_PASS=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -32)
    SECRET=$(openssl rand -base64 48)

    cat > "$ENV_FILE" << EOF
# ── Database locale ──────────────────────────────────────
DB_PASSWORD=$DB_PASS

# ── Supabase (solo per Storage — assets) ─────────────────
SUPABASE_URL=https://endxgujdxrzssccfikql.supabase.co
SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY:-}
SUPABASE_ACCESS_TOKEN=${SUPABASE_ACCESS_TOKEN:-}
SUPABASE_JWT_SECRET=${SUPABASE_JWT_SECRET:-}
SUPABASE_PROJECT_REF=endxgujdxrzssccfikql

# ── HuggingFace (obbligatorio per immagini AI) ───────────
HF_API_TOKEN=${HF_API_TOKEN:-}

# ── Backend ──────────────────────────────────────────────
SECRET_KEY=$SECRET
CORS_ORIGINS=https://ai-content-studio-lac.vercel.app,http://localhost:3000,https://${DUCK_DOMAIN}.duckdns.org

# ── DuckDNS ──────────────────────────────────────────────
DUCK_DNS_TOKEN=${DUCK_TOKEN:-}
DUCK_DNS_DOMAIN=${DUCK_DOMAIN}
EOF

    ok ".env creato: $ENV_FILE"
    if [ -z "$SUPABASE_SERVICE_KEY" ]; then
        warn "  SUPABASE_SERVICE_KEY vuoto — modificalo: nano $ENV_FILE"
    fi
    if [ -z "$HF_API_TOKEN" ]; then
        warn "  HF_API_TOKEN vuoto — le immagini AI useranno placeholder"
    fi
else
    ok ".env già esistente"
    # Carica le variabili per dopo
    source <(grep -E '^[^#]' "$ENV_FILE" | sed 's/ *= */=/g')
fi

# ── 4. DuckDNS auto-update service ────────────────────
info "[4/7] Configurazione DuckDNS..."

DUCK_TOKEN=${DUCK_DNS_TOKEN:-$(grep DUCK_DNS_TOKEN "$ENV_FILE" | cut -d= -f2)}
DUCK_DOMAIN=${DUCK_DNS_DOMAIN:-$(grep DUCK_DNS_DOMAIN "$ENV_FILE" | cut -d= -f2)}
DUCK_DOMAIN=${DUCK_DOMAIN:-ai-content-studio}

if [ -n "$DUCK_TOKEN" ] && [ "$DUCK_TOKEN" != "YOUR_TOKEN" ] && [ "$DUCK_TOKEN" != "your-duckdns-token" ]; then
    # Aggiornamento immediato
    PUBLIC_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip)
    curl -s "https://www.duckdns.org/update?domains=${DUCK_DOMAIN}&token=${DUCK_TOKEN}&ip=${PUBLIC_IP}"
    ok "DuckDNS aggiornato: ${DUCK_DOMAIN}.duckdns.org → ${PUBLIC_IP}"

    # Systemd service per aggiornamento automatico ogni 5 min
    sudo tee /etc/systemd/system/duckdns.service > /dev/null << SERVICEEOF
[Unit]
Description=DuckDNS Auto-Update
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/curl -s "https://www.duckdns.org/update?domains=${DUCK_DOMAIN}&token=${DUCK_TOKEN}&ip="
User=ubuntu
SERVICEEOF

    sudo tee /etc/systemd/system/duckdns.timer > /dev/null << TIMEREOF
[Unit]
Description=DuckDNS Update Timer

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
TIMEREOF

    sudo systemctl daemon-reload
    sudo systemctl enable duckdns.timer
    sudo systemctl start duckdns.timer
    ok "DuckDNS auto-update attivo (ogni 5 min)"
else
    warn "DUCK_DNS_TOKEN non configurato — salta DuckDNS. Lo farò dopo con:"
    warn "  nano $ENV_FILE"
    warn "  bash $0  # (riesegui lo script)"
fi

# ── 5. SSL Let's Encrypt ──────────────────────────────
info "[5/7] Certificato SSL (Let's Encrypt)..."

if [ -n "$DUCK_TOKEN" ] && [ "$DUCK_TOKEN" != "YOUR_TOKEN" ]; then
    sudo apt-get install -y -qq certbot

    # Nginx potrebbe già usare la porta 80 — fermiamo temporaneamente
    sudo systemctl stop nginx 2>/dev/null || true
    docker-compose stop nginx 2>/dev/null || true

    FQDN="${DUCK_DOMAIN}.duckdns.org"
    sudo certbot certonly --standalone \
        -d "$FQDN" \
        --non-interactive \
        --agree-tos \
        -m "admin@${FQDN}" \
        --http-01-port 8888 2>/dev/null || {
        # Se standalone:8888 fallisce, prova con webroot
        warn "Standalone fallito, tentativo con webroot..."
        sudo mkdir -p /var/www/certbot
        # Avvia un nginx minimo per la challenge
        docker run --rm -d --name temp-nginx \
            -v /var/www/certbot:/usr/share/nginx/html:ro \
            -p 80:80 nginx:alpine 2>/dev/null || true
        sleep 2
        sudo certbot certonly --webroot \
            -d "$FQDN" \
            -w /var/www/certbot \
            --non-interactive \
            --agree-tos \
            -m "admin@${FQDN}" || true
        docker stop temp-nginx 2>/dev/null || true
    }

    # Copia certificati nel volume Nginx
    sudo mkdir -p "$TARGET/nginx/ssl"
    if [ -f "/etc/letsencrypt/live/${FQDN}/fullchain.pem" ]; then
        sudo cp "/etc/letsencrypt/live/${FQDN}/fullchain.pem" "$TARGET/nginx/ssl/"
        sudo cp "/etc/letsencrypt/live/${FQDN}/privkey.pem" "$TARGET/nginx/ssl/"
        sudo chown -R ubuntu:ubuntu "$TARGET/nginx/ssl"
        chmod 644 "$TARGET/nginx/ssl/fullchain.pem"
        chmod 600 "$TARGET/nginx/ssl/privkey.pem"
        ok "SSL configurato per ${FQDN}"

        # Cron rinnovo automatico
        sudo tee /etc/cron.d/certbot-renew > /dev/null << CRONEOF
0 3 * * * root certbot renew --quiet --deploy-hook "cp /etc/letsencrypt/live/${FQDN}/fullchain.pem $TARGET/nginx/ssl/ && cp /etc/letsencrypt/live/${FQDN}/privkey.pem $TARGET/nginx/ssl/ && docker-compose -f $TARGET/docker-compose.yml restart nginx"
CRONEOF
        ok "Rinnovo SSL automatico configurato (ogni notte alle 3:00)"
    else
        warn "Certificato SSL non ottenuto — si procede senza HTTPS"
        warn "  Poi esegui manualmente: sudo certbot certonly --standalone -d ${FQDN}"
    fi
else
    warn "DuckDNS non configurato — salto SSL"
fi

# ── 6. Avvia container ───────────────────────────────
info "[6/7] Avvio dei container Docker..."

cd "$TARGET"
docker-compose pull
docker-compose up -d --build
docker image prune -f

ok "Container avviati."
ok "  docker-compose ps  — per vedere lo stato"
ok "  docker-compose logs -f backend  — log del backend"
ok "  docker-compose logs -f celery   — log dei worker"

# ── 7. Test sanitario ────────────────────────────────
info "[7/7] Test di verifica..."

sleep 5  # dai tempo ai container di partire

# Health check
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "??")

if curl -sf "http://localhost:8000/health" > /dev/null 2>&1; then
    ok "Backend: http://localhost:8000/health → OK"
    ok "Locale:  http://${PUBLIC_IP}:8000/health"
    if [ -n "${DUCK_TOKEN:-}" ] && [ "$DUCK_TOKEN" != "YOUR_TOKEN" ]; then
        ok "Pubblico: https://${DUCK_DOMAIN}.duckdns.org/health"
    fi
    ok "Documentazione: http://${PUBLIC_IP}:8000/docs"
else
    warn "Health check fallito. Controlla i log: docker-compose logs backend"
fi

echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}✅ Setup completato!${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo "Comandi utili:"
echo "  docker-compose logs -f backend    # Log backend"
echo "  docker-compose logs -f celery     # Log worker Celery"
echo "  docker-compose ps                 # Stato servizi"
echo "  docker-compose restart backend    # Riavvio rapido"
echo ""
echo "Se non hai inserito tutte le credenziali:"
echo "  nano /home/ubuntu/ai-content-studio/.env"
echo "  docker-compose up -d --build"
echo ""
