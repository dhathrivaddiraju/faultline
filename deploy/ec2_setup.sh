#!/usr/bin/env bash
# ==============================================================================
# Faultline Automated AWS EC2 / Ubuntu Provisioning Script
# Installs Docker, Docker Compose, sets up SSL via Certbot, and starts services.
# ==============================================================================

set -e

echo ">>> [1/5] Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y curl git ufw certbot python3-certbot-nginx

echo ">>> [2/5] Installing Docker & Docker Compose..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

sudo apt-get install -y docker-compose-plugin

echo ">>> [3/5] Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

echo ">>> [4/5] Creating environment file..."
if [ ! -f .env ]; then
    cat <<EOF > .env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$(openssl rand -hex 16)
POSTGRES_DB=faultline
ANTHROPIC_API_KEY=
CLAUDE_MODEL=claude-3-5-sonnet-20241022
EOF
    echo "Generated new .env configuration file."
fi

echo ">>> [5/5] Building and launching Faultline stack..."
docker compose up -d --build

echo "=========================================================="
echo " Faultline is now online!"
echo " Frontend: http://$(curl -s http://checkip.amazonaws.com):3000"
echo " API Docs: http://$(curl -s http://checkip.amazonaws.com):8000/docs"
echo " Ingestion: http://$(curl -s http://checkip.amazonaws.com):8000/api/v1/capture"
echo "=========================================================="
