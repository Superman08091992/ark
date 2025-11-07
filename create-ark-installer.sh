#!/bin/bash
##############################################################################
# ARK Self-Extracting Installer Builder
# Creates a single executable file that contains everything
##############################################################################

set -e

VERSION="1.0.0"
OUTPUT_FILE="ark-installer"

echo "🔨 Building ARK Self-Extracting Installer..."
echo ""

# Create temporary directory for bundling
TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

echo "1️⃣  Bundling files..."

# Copy scripts
cp create-usb-host-system.sh "$TMP_DIR/"
cp install-ark-host.sh "$TMP_DIR/"

# Copy core files if they exist
[ -f intelligent-backend.cjs ] && cp intelligent-backend.cjs "$TMP_DIR/"
[ -f agent_tools.cjs ] && cp agent_tools.cjs "$TMP_DIR/"

# Copy documentation
for doc in ARK_OS_ARCHITECTURE.md PORTABLE_USB_EXTERNAL_HOST_ARCHITECTURE.md \
           PORTABLE_ARK_GUIDE.md IMPLEMENTATION_STATUS.md; do
    [ -f "$doc" ] && cp "$doc" "$TMP_DIR/"
done

echo "2️⃣  Creating tarball..."
tar -czf "$TMP_DIR/payload.tar.gz" -C "$TMP_DIR" \
    create-usb-host-system.sh install-ark-host.sh \
    $([ -f intelligent-backend.cjs ] && echo "intelligent-backend.cjs" || true) \
    $([ -f agent_tools.cjs ] && echo "agent_tools.cjs" || true) \
    *.md 2>/dev/null || true

echo "3️⃣  Creating self-extracting script..."

cat > "$OUTPUT_FILE" << 'INSTALLER_EOF'
#!/bin/bash
##############################################################################
# ARK OS Installer - Self-Extracting Archive
# 
# This single file contains everything needed to:
# - Create ARK USB identity nodes
# - Install ARK host services
# - Access complete documentation
#
# Usage:
#   ./ark-installer --help
#   ./ark-installer usb /media/myusb
#   ./ark-installer host
#   ./ark-installer both /media/myusb
#   ./ark-installer extract [directory]
##############################################################################

VERSION="1.0.0"

show_help() {
    cat << 'HELP_EOF'
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║              ARK OS INSTALLER v1.0.0                                  ║
║              Single-File Self-Extracting Installer                    ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝

USAGE:
  ./ark-installer COMMAND [OPTIONS]

COMMANDS:
  usb <path>          Create USB identity node at specified path
  host                Install ARK host service on this machine
  both <path>         Create USB node + generate host installer
  extract [dir]       Extract all files to directory (default: ./ark-extracted)
  docs                Extract documentation only
  --help, -h          Show this help message
  --version, -v       Show version information

EXAMPLES:
  # Create USB node
  ./ark-installer usb /media/myusb

  # Install host service (requires sudo)
  sudo ./ark-installer host

  # Create USB + host installer
  ./ark-installer both /media/myusb

  # Extract all files for inspection
  ./ark-installer extract ./my-ark-files

  # Just view documentation
  ./ark-installer docs

WHAT'S INSIDE:
  ✓ create-usb-host-system.sh (USB node creator)
  ✓ install-ark-host.sh (Host service installer)
  ✓ intelligent-backend.cjs (Kyle's brain)
  ✓ agent_tools.cjs (Tool registry)
  ✓ Complete architecture documentation
  ✓ Setup guides and examples

SIZE: ~30KB compressed

MORE INFO:
  GitHub: https://github.com/Superman08091992/ark
  PR: https://github.com/Superman08091992/ark/pull/1

HELP_EOF
}

show_version() {
    echo "ARK OS Installer v$VERSION"
    echo "Self-extracting archive"
    echo ""
    echo "Included components:"
    echo "  - USB identity node creator"
    echo "  - Host service installer"
    echo "  - Core backend files"
    echo "  - Complete documentation"
}

extract_payload() {
    local extract_dir="${1:-.}"
    
    echo "📦 Extracting ARK files to: $extract_dir"
    mkdir -p "$extract_dir"
    
    # Find the start of the tarball (after __PAYLOAD__ marker)
    local payload_start=$(awk '/^__PAYLOAD__/ {print NR + 1; exit 0; }' "$0")
    
    # Extract the tarball
    tail -n +$payload_start "$0" | tar -xzf - -C "$extract_dir"
    
    echo "✅ Extracted to: $extract_dir"
    echo ""
    echo "📂 Contents:"
    ls -lh "$extract_dir"
}

extract_docs() {
    local doc_dir="${1:-./ark-docs}"
    
    echo "📚 Extracting documentation to: $doc_dir"
    mkdir -p "$doc_dir"
    
    local payload_start=$(awk '/^__PAYLOAD__/ {print NR + 1; exit 0; }' "$0")
    tail -n +$payload_start "$0" | tar -xzf - -C "$doc_dir" '*.md' 2>/dev/null || true
    
    echo "✅ Documentation extracted to: $doc_dir"
    echo ""
    ls -1 "$doc_dir"/*.md 2>/dev/null || echo "No documentation files found"
}

run_usb_creator() {
    local usb_path="$1"
    
    if [ -z "$usb_path" ]; then
        echo "❌ Error: USB path required"
        echo "Usage: $0 usb <path>"
        exit 1
    fi
    
    # Extract to temp directory
    local tmp_dir=$(mktemp -d)
    trap "rm -rf $tmp_dir" EXIT
    
    extract_payload "$tmp_dir" >/dev/null
    
    # Run USB creator
    bash "$tmp_dir/create-usb-host-system.sh" usb "$usb_path"
}

run_host_installer() {
    # Extract to temp directory
    local tmp_dir=$(mktemp -d)
    trap "rm -rf $tmp_dir" EXIT
    
    extract_payload "$tmp_dir" >/dev/null
    
    # Run host installer
    bash "$tmp_dir/install-ark-host.sh"
}

run_both() {
    local usb_path="$1"
    
    if [ -z "$usb_path" ]; then
        echo "❌ Error: USB path required"
        echo "Usage: $0 both <path>"
        exit 1
    fi
    
    # Extract to temp directory
    local tmp_dir=$(mktemp -d)
    trap "rm -rf $tmp_dir" EXIT
    
    extract_payload "$tmp_dir" >/dev/null
    
    # Run both
    bash "$tmp_dir/create-usb-host-system.sh" both "$usb_path"
}

# Main execution
case "${1:-}" in
    --help|-h|help)
        show_help
        exit 0
        ;;
    --version|-v|version)
        show_version
        exit 0
        ;;
    extract)
        extract_payload "${2:-.}"
        exit 0
        ;;
    docs)
        extract_docs "${2:-./ark-docs}"
        exit 0
        ;;
    usb)
        run_usb_creator "$2"
        exit 0
        ;;
    host)
        run_host_installer
        exit 0
        ;;
    both)
        run_both "$2"
        exit 0
        ;;
    *)
        echo "❌ Unknown command: ${1:-<none>}"
        echo ""
        echo "Run: $0 --help"
        exit 1
        ;;
esac

exit 0

__PAYLOAD__
INSTALLER_EOF

echo "4️⃣  Appending payload..."
cat "$TMP_DIR/payload.tar.gz" >> "$OUTPUT_FILE"

echo "5️⃣  Setting permissions..."
chmod +x "$OUTPUT_FILE"

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║              ✅ ARK INSTALLER CREATED! ✅                            ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📦 Output file: $(pwd)/$OUTPUT_FILE"
echo "📊 Size: $(du -h "$OUTPUT_FILE" | cut -f1)"
echo ""
echo "🚀 Usage:"
echo "   ./$OUTPUT_FILE --help"
echo "   ./$OUTPUT_FILE usb /media/myusb"
echo "   ./$OUTPUT_FILE host"
echo "   ./$OUTPUT_FILE both /media/myusb"
echo ""
echo "📤 Distribution:"
echo "   1. Upload to GitHub Releases"
echo "   2. Host at https://ark.1true.org/$OUTPUT_FILE"
echo "   3. Users download once, run anywhere"
echo ""
echo "🎉 Single-command download + install:"
echo "   curl -sSL https://ark.1true.org/install | bash"
echo ""

