#!/usr/bin/env bash
set -e

# Répertoire d'installation standard XDG
INSTALL_DIR="$HOME/.local/share/allo"
BIN_DIR="$HOME/.local/bin"
WRAPPER="$BIN_DIR/record"

# Vérifie les dépendances système requises.
# Si des paquets sont manquants, affiche la commande d'installation et quitte.
check_system_deps() {
    local missing=()

    if ! command -v python3 >/dev/null 2>&1; then
        missing+=("python3")
    fi

    if ! python3 -m venv --help >/dev/null 2>&1; then
        missing+=("python3-venv")
    fi

    if ! python3 -c "import tkinter" >/dev/null 2>&1; then
        missing+=("python3-tk")
    fi

    if ! dpkg-query -W -f='${Status}' libportaudio2 2>/dev/null | grep -q "install ok installed"; then
        missing+=("libportaudio2")
    fi

    if [ ${#missing[@]} -ne 0 ]; then
        local deps_str
        deps_str=$(printf ", %s" "${missing[@]}")
        deps_str="${deps_str:2}"  # supprime le préfixe ", "
        echo "Dépendances système manquantes : $deps_str"
        echo "Installez-les avec :"
        echo "  sudo apt-get install ${missing[*]}"
        exit 1
    fi
}

# Vérifie que ~/.local/bin est présent dans le PATH.
# Sinon, affiche un message d'avertissement avec la commande à ajouter.
check_path() {
    case ":$PATH:" in
        *":$HOME/.local/bin:"*) ;;
        *":$BIN_DIR:"*) ;;
        *)
            echo ""
            echo "Attention : ~/.local/bin n'est pas dans votre PATH."
            echo 'Ajoutez cette ligne à ~/.bashrc ou ~/.zshrc :'
            echo '  export PATH="$HOME/.local/bin:$PATH"'
            ;;
    esac
}

# Crée (ou recrée) le wrapper dans ~/.local/bin/record.
create_wrapper() {
    mkdir -p "$BIN_DIR"
    cat > "$WRAPPER" <<EOF
#!/usr/bin/env bash
exec $INSTALL_DIR/.venv/bin/python3 $INSTALL_DIR/record.py "\$@"
EOF
    chmod +x "$WRAPPER"
}

# Détection du mode : install, update, ou déjà installé.
if [ -d "$INSTALL_DIR" ]; then
    if [ "${1:-}" = "--update" ]; then
        MODE="update"
    else
        echo "Déjà installé. Utilisez --update pour mettre à jour."
        exit 0
    fi
else
    MODE="install"
fi

# Étape 1 : vérification des dépendances système (toujours).
echo "[1/4] Vérification des dépendances système..."
check_system_deps

if [ "$MODE" = "install" ]; then
    # Étape 2 : clonage du dépôt.
    echo "[2/4] Clonage du dépôt..."
    git clone https://github.com/rr-djk/allo.git "$INSTALL_DIR"

    # Étape 3 : création de l'environnement virtuel.
    echo "[3/4] Création de l'environnement virtuel Python..."
    python3 -m venv "$INSTALL_DIR/.venv"

    # Étape 4 : installation des dépendances Python.
    echo "[4/4] Installation des dépendances Python..."
    "$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
    echo "  faster-whisper téléchargera ses modèles au premier lancement."

    create_wrapper
    check_path

elif [ "$MODE" = "update" ]; then
    # Étape 2 : mise à jour du dépôt.
    echo "[2/3] Mise à jour du dépôt..."
    cd "$INSTALL_DIR"
    git pull

    # Étape 3 : mise à jour des dépendances Python.
    echo "[3/3] Mise à jour des dépendances Python..."
    "$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

    # Réécriture du wrapper pour garantir la cohérence.
    create_wrapper
fi

echo ""
echo "Installation terminée. Lancez : record &"
