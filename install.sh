#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THIRD_PARTY="$SCRIPT_DIR/third_party"
WHISPER_DIR="$THIRD_PARTY/whisper.cpp"

echo "[1/6] Dépendances système..."
sudo apt-get update -qq
sudo apt-get install -y python3-tk python3-venv cmake build-essential libportaudio2 git

echo "[2/6] Clonage de whisper.cpp..."
mkdir -p "$THIRD_PARTY"
if [ ! -d "$WHISPER_DIR" ]; then
    git clone https://github.com/ggml-org/whisper.cpp.git "$WHISPER_DIR"
else
    echo "  whisper.cpp déjà présent, skip."
fi

echo "[3/6] Téléchargement du modèle ggml-tiny..."
cd "$WHISPER_DIR"
if [ ! -f "models/ggml-tiny.bin" ]; then
    sh ./models/download-ggml-model.sh tiny
else
    echo "  ggml-tiny.bin déjà présent, skip."
fi

echo "[4/6] Compilation de whisper.cpp..."
cmake -B build -DCMAKE_BUILD_TYPE=Release > /dev/null
cmake --build build -j"$(nproc)" > /dev/null
echo "  Binaire : $WHISPER_DIR/build/bin/whisper-cli"
cd "$SCRIPT_DIR"

echo "[5/6] Dépendances Python..."
python3 -m venv "$SCRIPT_DIR/.venv"
"$SCRIPT_DIR/.venv/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"
echo "  faster-whisper téléchargera ses modèles au premier lancement."

echo "[6/6] Commande record..."
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
