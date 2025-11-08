#!/bin/bash
##############################################################################
# ARK Installer with Bundled Model
# Creates installer that includes a pre-downloaded AI model
##############################################################################

set -e

VERSION="1.0.0"
OUTPUT_FILE="ark-installer-with-model"

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║       ARK Installer Builder (with embedded model)                    ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed!"
    echo ""
    echo "Install ollama first:"
    echo "  curl -fsSL https://ollama.ai/install.sh | sh"
    echo ""
    exit 1
fi

# Ask which model to bundle
echo "📦 Which model do you want to bundle in the installer?"
echo ""
echo "  1) llama3.2:1b     - Smallest (1.3GB) [RECOMMENDED]"
echo "  2) llama3.2:3b     - Medium (2GB)"
echo "  3) qwen2.5:3b      - Reasoning (2.5GB)"
echo "  4) phi3:mini       - Fast (2.4GB)"
echo "  5) Custom model name"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1) MODEL="llama3.2:1b" ;;
    2) MODEL="llama3.2:3b" ;;
    3) MODEL="qwen2.5:3b" ;;
    4) MODEL="phi3:mini" ;;
    5)
        read -p "Enter model name (e.g., mistral:7b): " MODEL
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "📥 Selected model: $MODEL"
echo ""

# Check if model is already downloaded
if ! ollama list | grep -q "^$MODEL"; then
    echo "⬇️  Model not found locally. Downloading..."
    ollama pull "$MODEL"
fi

echo ""
echo "📂 Exporting model from Ollama..."

# Create temp directory
TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

# Export model to GGUF format
MODEL_FILE="$TMP_DIR/model.gguf"

# Ollama stores models in ~/.ollama/models/
OLLAMA_DIR="$HOME/.ollama/models"

# Find the model blob
echo "🔍 Locating model files..."

# Get model manifest
MODEL_NAME=$(echo "$MODEL" | cut -d: -f1)
MODEL_TAG=$(echo "$MODEL" | cut -d: -f2)
MODEL_TAG=${MODEL_TAG:-latest}

# Find model path
MODEL_PATH="$OLLAMA_DIR/manifests/registry.ollama.ai/library/$MODEL_NAME/$MODEL_TAG"

if [ ! -f "$MODEL_PATH" ]; then
    echo "❌ Model manifest not found at: $MODEL_PATH"
    echo "Available models:"
    ollama list
    exit 1
fi

echo "✅ Found model manifest"

# Read manifest to find blob
MODEL_BLOB=$(jq -r '.layers[] | select(.mediaType == "application/vnd.ollama.image.model") | .digest' "$MODEL_PATH" 2>/dev/null | head -1)

if [ -z "$MODEL_BLOB" ]; then
    echo "❌ Could not extract model blob from manifest"
    exit 1
fi

# Copy model blob
BLOB_PATH="$OLLAMA_DIR/blobs/$MODEL_BLOB"
if [ ! -f "$BLOB_PATH" ]; then
    echo "❌ Model blob not found at: $BLOB_PATH"
    exit 1
fi

echo "📦 Copying model blob ($MODEL_BLOB)..."
cp "$BLOB_PATH" "$MODEL_FILE"

MODEL_SIZE=$(du -h "$MODEL_FILE" | cut -f1)
echo "✅ Model extracted: $MODEL_SIZE"

echo ""
echo "🔨 Building installer with embedded model..."

# Create bundle directory
BUNDLE_DIR="$TMP_DIR/bundle"
mkdir -p "$BUNDLE_DIR"

# Copy scripts
cp create-usb-host-system.sh "$BUNDLE_DIR/"
cp install-ark-host.sh "$BUNDLE_DIR/"

# Copy core files if they exist
[ -f intelligent-backend.cjs ] && cp intelligent-backend.cjs "$BUNDLE_DIR/"
[ -f agent_tools.cjs ] && cp agent_tools.cjs "$BUNDLE_DIR/"

# Copy model
cp "$MODEL_FILE" "$BUNDLE_DIR/bundled-model.gguf"

# Create model metadata
cat > "$BUNDLE_DIR/model-info.txt" << EOF
MODEL_NAME=$MODEL
MODEL_SIZE=$MODEL_SIZE
BUNDLE_DATE=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
EOF

# Create tarball
echo "📦 Creating archive..."
tar -czf "$TMP_DIR/payload.tar.gz" -C "$BUNDLE_DIR" .

PAYLOAD_SIZE=$(du -h "$TMP_DIR/payload.tar.gz" | cut -f1)
echo "✅ Payload size: $PAYLOAD_SIZE"

# Create self-extracting installer
echo "🔧 Creating self-extracting installer..."

cat > "$OUTPUT_FILE" << 'INSTALLER_HEADER'
#!/bin/bash
##############################################################################
# ARK OS Installer - With Embedded AI Model
# 
# This installer includes a pre-downloaded AI model for offline installation
##############################################################################

VERSION="1.0.0"

show_help() {
    cat << 'HELP_EOF'
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║       ARK OS INSTALLER v1.0.0 (with embedded model)                  ║
║       Single-File Self-Extracting Installer                          ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝

This installer includes a pre-downloaded AI model for offline setup.

USAGE:
  ./ark-installer-with-model COMMAND [OPTIONS]

COMMANDS:
  usb <path>          Create USB identity node at specified path
  host                Install ARK host service (includes bundled model)
  both <path>         Create USB node + install host with bundled model
  extract [dir]       Extract all files including model
  model-info          Show information about the bundled model
  --help, -h          Show this help message
  --version, -v       Show version information

EXAMPLES:
  # Show bundled model info
  ./ark-installer-with-model model-info

  # Install host with bundled model (no download needed)
  sudo ./ark-installer-with-model host

  # Create USB and install host
  ./ark-installer-with-model both /media/myusb

BUNDLED MODEL:
  This installer includes a pre-downloaded AI model.
  No internet connection needed during installation!
  The model will be imported into Ollama automatically.

MORE INFO:
  GitHub: https://github.com/Superman08091992/ark

HELP_EOF
}

# Extract payload
extract_payload() {
    local extract_dir="$1"
    mkdir -p "$extract_dir"
    
    echo "📦 Extracting files..."
    payload_start=$(awk '/^__PAYLOAD__/ {print NR + 1; exit 0; }' "$0")
    tail -n +$payload_start "$0" | tar -xzf - -C "$extract_dir"
    echo "✅ Files extracted to: $extract_dir"
}

# Install bundled model
install_bundled_model() {
    echo ""
    echo "📥 Installing bundled AI model..."
    
    # Read model info
    if [ -f model-info.txt ]; then
        source model-info.txt
        echo "   Model: $MODEL_NAME"
        echo "   Size: $MODEL_SIZE"
        echo "   Bundled: $BUNDLE_DATE"
    fi
    
    if [ -f bundled-model.gguf ]; then
        echo ""
        echo "🔧 Importing model into Ollama..."
        
        # Create Modelfile for import
        cat > Modelfile << MODELFILE_EOF
FROM ./bundled-model.gguf
MODELFILE_EOF
        
        # Import model
        if ollama create "${MODEL_NAME:-embedded-model}" -f Modelfile; then
            echo "✅ Model imported successfully!"
            
            # Test the model
            echo ""
            echo "🧪 Testing model..."
            echo "Hello, this is a test." | ollama run "${MODEL_NAME:-embedded-model}" 2>/dev/null | head -3
            echo "✅ Model is working!"
        else
            echo "⚠️  Model import failed. Model file is available at: $(pwd)/bundled-model.gguf"
            echo "   You can import it manually later with:"
            echo "   ollama create <model-name> -f Modelfile"
        fi
        
        rm -f Modelfile
    else
        echo "⚠️  Bundled model file not found"
    fi
}

# Handle commands
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -v|--version)
        echo "ARK Installer (with model) v$VERSION"
        exit 0
        ;;
    model-info)
        extract_dir=$(mktemp -d)
        trap "rm -rf $extract_dir" EXIT
        extract_payload "$extract_dir"
        cd "$extract_dir"
        
        if [ -f model-info.txt ]; then
            echo "╔═══════════════════════════════════════════════════════════════════════╗"
            echo "║                     BUNDLED MODEL INFORMATION                         ║"
            echo "╚═══════════════════════════════════════════════════════════════════════╝"
            echo ""
            cat model-info.txt
            echo ""
            echo "Model file: bundled-model.gguf"
            echo "File size: $(du -h bundled-model.gguf | cut -f1)"
        else
            echo "❌ Model information not found"
        fi
        exit 0
        ;;
    host)
        extract_dir=$(mktemp -d)
        trap "rm -rf $extract_dir" EXIT
        extract_payload "$extract_dir"
        cd "$extract_dir"
        
        # Run host installer
        bash install-ark-host.sh
        
        # Install bundled model after host setup
        install_bundled_model
        
        exit 0
        ;;
    usb)
        if [ -z "$2" ]; then
            echo "❌ Error: USB path required"
            echo "Usage: $0 usb <path>"
            exit 1
        fi
        
        extract_dir=$(mktemp -d)
        trap "rm -rf $extract_dir" EXIT
        extract_payload "$extract_dir"
        cd "$extract_dir"
        
        bash create-usb-host-system.sh "$2"
        exit 0
        ;;
    both)
        if [ -z "$2" ]; then
            echo "❌ Error: USB path required"
            echo "Usage: $0 both <path>"
            exit 1
        fi
        
        extract_dir=$(mktemp -d)
        trap "rm -rf $extract_dir" EXIT
        extract_payload "$extract_dir"
        cd "$extract_dir"
        
        bash create-usb-host-system.sh "$2"
        bash install-ark-host.sh
        install_bundled_model
        
        exit 0
        ;;
    extract)
        extract_dir="${2:-./ark-extracted}"
        extract_payload "$extract_dir"
        echo ""
        echo "📂 All files extracted, including bundled AI model!"
        exit 0
        ;;
    *)
        show_help
        exit 1
        ;;
esac

# Payload marker
__PAYLOAD__
INSTALLER_HEADER

# Append payload
cat "$TMP_DIR/payload.tar.gz" >> "$OUTPUT_FILE"
chmod +x "$OUTPUT_FILE"

FINAL_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║            ✅ INSTALLER WITH MODEL CREATED! ✅                       ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📦 Output file: $OUTPUT_FILE"
echo "📊 Total size: $FINAL_SIZE"
echo "🤖 Bundled model: $MODEL ($MODEL_SIZE)"
echo ""
echo "🚀 Usage:"
echo "   ./$OUTPUT_FILE model-info    # Show model info"
echo "   ./$OUTPUT_FILE host          # Install with bundled model"
echo ""
echo "✅ No internet connection needed for AI model during installation!"
