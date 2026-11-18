#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y curl git ufw certbot python3-certbot-nginx

if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker "${USER}"
    rm -f get-docker.sh
fi

sudo apt-get install -y docker-compose-plugin

sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

if [ ! -f .env ]; then
    cat <<EOF > .env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$(openssl rand -hex 16)
POSTGRES_DB=faultline
ANTHROPIC_API_KEY=
CLAUDE_MODEL=claude-3-5-sonnet-20241022
EOF
fi

docker compose up -d --build
