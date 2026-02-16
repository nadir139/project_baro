#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# SpeedLead AI - Client Provisioning Script
# Creates a new OpenClaw instance for a client
#
# Usage: ./scripts/provision-client.sh <client-id> <company-name> <sector>
# Example: ./scripts/provision-client.sh acme-srl "Acme S.r.l." manifattura
# ═══════════════════════════════════════════════════════════

set -euo pipefail

CLIENT_ID="${1:?Usage: $0 <client-id> <company-name> <sector>}"
COMPANY_NAME="${2:?Usage: $0 <client-id> <company-name> <sector>}"
SECTOR="${3:-generico}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CLIENT_DIR="$PROJECT_DIR/clients/$CLIENT_ID"

echo "═══════════════════════════════════════════"
echo "  SpeedLead AI - Provisioning Client"
echo "═══════════════════════════════════════════"
echo "  Client ID:    $CLIENT_ID"
echo "  Company:      $COMPANY_NAME"
echo "  Sector:       $SECTOR"
echo "  Directory:    $CLIENT_DIR"
echo "═══════════════════════════════════════════"
echo ""

# Check if client already exists
if [ -d "$CLIENT_DIR" ]; then
    echo "ERROR: Client directory already exists: $CLIENT_DIR"
    exit 1
fi

# Create client directory
echo "[1/5] Creating client directory..."
mkdir -p "$CLIENT_DIR"

# Copy .env template
echo "[2/5] Creating .env from template..."
cp "$PROJECT_DIR/.env.example" "$CLIENT_DIR/.env"

# Update .env with client info
sed -i "s/CLIENT_ID=.*/CLIENT_ID=$CLIENT_ID/" "$CLIENT_DIR/.env"
sed -i "s/CLIENT_NAME=.*/CLIENT_NAME=\"$COMPANY_NAME\"/" "$CLIENT_DIR/.env"
sed -i "s/CLIENT_SECTOR=.*/CLIENT_SECTOR=$SECTOR/" "$CLIENT_DIR/.env"

# Find next available ports
LAST_OPENCLAW_PORT=$(find "$PROJECT_DIR/clients" -name ".env" -exec grep OPENCLAW_PORT {} \; 2>/dev/null | sort -t= -k2 -n | tail -1 | cut -d= -f2)
LAST_VOICE_PORT=$(find "$PROJECT_DIR/clients" -name ".env" -exec grep VOICE_PORT {} \; 2>/dev/null | sort -t= -k2 -n | tail -1 | cut -d= -f2)

OPENCLAW_PORT=${LAST_OPENCLAW_PORT:-18789}
VOICE_PORT=${LAST_VOICE_PORT:-8765}
OPENCLAW_PORT=$((OPENCLAW_PORT + 1))
VOICE_PORT=$((VOICE_PORT + 1))

sed -i "s/OPENCLAW_PORT=.*/OPENCLAW_PORT=$OPENCLAW_PORT/" "$CLIENT_DIR/.env"
sed -i "s/VOICE_PORT=.*/VOICE_PORT=$VOICE_PORT/" "$CLIENT_DIR/.env"

echo "  OpenClaw port: $OPENCLAW_PORT"
echo "  Voice port: $VOICE_PORT"

# Create docker-compose override for this client
echo "[3/5] Creating Docker Compose override..."
cat > "$CLIENT_DIR/docker-compose.yml" << EOF
# SpeedLead AI - Client: $CLIENT_ID ($COMPANY_NAME)
# Generated on $(date -u +"%Y-%m-%dT%H:%M:%SZ")

version: "3.9"

services:
  openclaw:
    extends:
      file: ../../docker-compose.yml
      service: openclaw
    container_name: speedlead-openclaw-$CLIENT_ID
    env_file: .env
    ports:
      - "$OPENCLAW_PORT:18789"
    volumes:
      - openclaw-data-$CLIENT_ID:/home/node/.openclaw
      - ../../skills:/home/node/.openclaw/workspace/skills
      - ../../config:/home/node/.openclaw/config

  voice-bridge:
    extends:
      file: ../../docker-compose.yml
      service: voice-bridge
    container_name: speedlead-voice-$CLIENT_ID
    env_file: .env
    ports:
      - "$VOICE_PORT:8765"

volumes:
  openclaw-data-$CLIENT_ID:
EOF

# Create client-specific config
echo "[4/5] Creating client config..."
cat > "$CLIENT_DIR/config.json" << EOF
{
  "client_id": "$CLIENT_ID",
  "company_name": "$COMPANY_NAME",
  "sector": "$SECTOR",
  "agent_name": "Marco",
  "company_description": "",
  "products_services": "",
  "unique_selling_points": "",
  "target_customers": "",
  "price_range": "",
  "owner_phone": "",
  "owner_email": ""
}
EOF

echo "[5/5] Done!"
echo ""
echo "═══════════════════════════════════════════"
echo "  Client $CLIENT_ID provisioned!"
echo "═══════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Edit $CLIENT_DIR/.env with API keys"
echo "  2. Edit $CLIENT_DIR/config.json with company details"
echo "  3. Start: cd $CLIENT_DIR && docker compose up -d"
echo "  4. Pair WhatsApp: docker compose exec openclaw openclaw channels login"
echo ""
