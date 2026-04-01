#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[1/3] Dépendances système..."
sudo apt-get update -qq
sudo apt-get install -y python3-tk python3-venv libportaudio2

echo "[2/3] Dépendances Python..."
python3 -m venv "$SCRIPT_DIR/.venv"
"$SCRIPT_DIR/.venv/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"
echo "  faster-whisper téléchargera ses modèles au premier lancement."

echo "[3/3] Commande record..."
RECORD_SH="$SCRIPT_DIR/record.sh"
RECORD_BIN="/usr/local/bin/record"

# Réécrire record.sh avec le bon interpréteur Python
cat > "$RECORD_SH" <<EOF
#!/usr/bin/env bash
exec "$SCRIPT_DIR/.venv/bin/python3" "$SCRIPT_DIR/record.py" "\$@"
EOF
chmod +x "$RECORD_SH"
sudo cp "$RECORD_SH" "$RECORD_BIN"
echo "  Commande installée : $RECORD_BIN"

echo ""
echo "Installation terminée."
echo "Lance l'app avec : record &"
