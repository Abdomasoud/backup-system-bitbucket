#!/bin/bash
# Bitbucket Backup System Setup - Ubuntu 22+ Simple & Reliable
# No virtual environments, direct system Python installation

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
BACKUP_DIR="/opt/bitbucket-backup"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $@"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $@"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $@"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $@"
}

show_banner() {
    cat << 'EOF'
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║      🚀 Bitbucket Backup Setup - Ubuntu 22+ Ready      ║
║                                                          ║
║  • Simple system Python installation                    ║
║  • No virtual environment complexity                    ║
║  • Root user execution (bulletproof)                    ║
║  • Full backup automation included                      ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
EOF
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        log_info "Please run: sudo -i first, then run this script"
        exit 1
    fi
    
    log_success "Running as root user - perfect!"
}

install_system_dependencies() {
    log_info "Installing system dependencies..."
    
    # Update package list
    apt update -qq
    
    # Install required packages
    apt install -y \
        git \
        python3 \
        python3-pip \
        curl \
        jq \
        tar \
        gzip \
        python3-requests \
        python3-dotenv
    
    log_success "System dependencies installed"
}

install_python_packages() {
    log_info "Installing Python packages (system-wide)..."
    
    # Install packages system-wide (works perfectly for root)
    pip3 install --break-system-packages requests python-dotenv || \
    pip3 install requests python-dotenv
    
    # Verify installations
    if python3 -c "import requests; import dotenv; print('✅ All imports successful')" 2>/dev/null; then
        log_success "Python packages installed and verified"
    else
        log_warning "Package verification failed, but continuing..."
    fi
}

create_backup_directory() {
    log_info "Creating backup directory structure..."
    
    # Create main backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Create subdirectories
    mkdir -p "$BACKUP_DIR/scripts"
    mkdir -p "$BACKUP_DIR/config" 
    mkdir -p "$BACKUP_DIR/logs"
    mkdir -p "$BACKUP_DIR/repositories"
    mkdir -p "$BACKUP_DIR/metadata"
    mkdir -p "$BACKUP_DIR/temp"
    
    # Set proper permissions
    chmod 755 "$BACKUP_DIR"
    chmod 755 "$BACKUP_DIR"/*
    
    log_success "Backup directory structure created at: $BACKUP_DIR"
}

copy_backup_scripts() {
    log_info "Copying backup scripts..."
    
    # Get current directory (where setup.sh is)
    local script_dir="$PWD"
    
    log_info "Copying files from: $script_dir"
    
    # Check if files exist
    local files_to_copy=(
        "bitbucket-backup.py"
        "bitbucket-backup.sh"
        ".env.example"
    )
    
    for file in "${files_to_copy[@]}"; do
        if [[ -f "$script_dir/$file" ]]; then
            log_info "✓ Found: $file"
        else
            log_error "✗ Missing: $file in $script_dir"
            exit 1
        fi
    done
    
    # Copy files to destination
    cp "$script_dir/bitbucket-backup.py" "$BACKUP_DIR/scripts/"
    cp "$script_dir/bitbucket-backup.sh" "$BACKUP_DIR/scripts/"
    cp "$script_dir/.env.example" "$BACKUP_DIR/config/"
    
    # Make scripts executable
    chmod +x "$BACKUP_DIR/scripts/"*.sh
    chmod +x "$BACKUP_DIR/scripts/"*.py
    
    log_success "All backup scripts copied successfully"
}

create_cron_wrapper() {
    log_info "Creating cron wrapper script..."
    
    # Create simple cron wrapper (no venv activation needed)
    cat > "$BACKUP_DIR/scripts/cron-wrapper.sh" << 'EOF'
#!/bin/bash
# Cron wrapper for backup script - Simple and reliable

# Change to backup directory
cd /opt/bitbucket-backup

# Source environment variables
source config/.env

# Run backup script
./scripts/bitbucket-backup.sh

# Log completion
echo "$(date): Cron backup completed" >> logs/cron.log
EOF

    chmod +x "$BACKUP_DIR/scripts/cron-wrapper.sh"
    
    log_success "Cron wrapper created"
}

show_completion_message() {
    cat << EOF

🎉 Setup completed successfully!

📋 Next steps:

1. Configure your credentials:
   nano $BACKUP_DIR/config/.env
   
   Set these values:
   ATLASSIAN_EMAIL=your-email@domain.com
   BITBUCKET_API_TOKEN=your-api-token
   BITBUCKET_WORKSPACE=your-workspace
   BACKUP_WORKSPACE=your-backup-workspace

2. Test the backup system:
   cd $BACKUP_DIR
   ./scripts/bitbucket-backup.sh --test-only

3. Run your first backup:
   ./scripts/bitbucket-backup.sh --force

4. Add to cron for automation (optional):
   crontab -e
   Add: 0 2 */3 * * /opt/bitbucket-backup/scripts/cron-wrapper.sh >> /opt/bitbucket-backup/logs/cron.log 2>&1

📁 Created structure:
$BACKUP_DIR/
├── scripts/
│   ├── bitbucket-backup.py       # Core backup engine
│   ├── bitbucket-backup.sh       # Main backup script
│   └── cron-wrapper.sh          # Cron automation
├── config/
│   └── .env.example             # Configuration template
├── logs/                        # Backup logs
├── repositories/                # Repository backups (organized by repo)
└── metadata/                    # Backup metadata

🔑 Get your Bitbucket API token:
1. Go to https://bitbucket.org/account/settings/app-passwords/
2. Create app password with Repositories:Read permission
3. Use generated token in .env file

EOF
}

main() {
    show_banner
    check_root
    install_system_dependencies
    install_python_packages
    create_backup_directory
    copy_backup_scripts
    create_cron_wrapper
    show_completion_message
}

main "$@"