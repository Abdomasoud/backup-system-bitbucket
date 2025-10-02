#!/bin/bash
# Bitbucket Backup System Setup - Ubuntu 24 Compatible
# Automated virtual environment setup with root user

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
BACKUP_DIR="/opt/bitbucket-backup"
VENV_DIR="$BACKUP_DIR/venv"

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
║     � Bitbucket Backup Setup - Ubuntu 24 Ready        ║
║                                                          ║
║  • Automated virtual environment creation                ║
║  • Python dependency auto-installation                   ║
║  • Root user execution (no permission issues)           ║
║  • Full backup automation included                       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
EOF
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        log_info "Please run: sudo $0"
        exit 1
    fi
    
    log_success "Running as root user - no permission issues"
}

install_basic_dependencies() {
    log_info "Installing basic system dependencies..."
    
    apt update -qq
    apt install -y \
        git \
        python3 \
        python3-pip \
        python3-venv \
        curl \
        jq \
        tar \
        gzip
    
    log_success "Basic dependencies installed"
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
    
    # Set proper permissions (all as root)
    chmod 755 "$BACKUP_DIR"
    chmod 755 "$BACKUP_DIR"/*
    
    log_success "Backup directory structure created at: $BACKUP_DIR"
}

create_venv() {
    log_info "Creating Python virtual environment for Ubuntu 24 (as root)..."
    
    # Ensure the backup directory exists
    mkdir -p /opt/bitbucket-backup
    cd /opt/bitbucket-backup
    
    # Remove any existing venv to start fresh
    if [[ -d "venv" ]]; then
        log_info "Removing existing virtual environment..."
        rm -rf venv
    fi
    
    # Create a clean virtual environment (Ubuntu 24 compatible)
    log_info "Creating new virtual environment..."
    if python3 -m venv venv; then
        log_success "Virtual environment created successfully"
    else
        log_error "Failed to create virtual environment"
        log_info "Trying alternative approach with --system-site-packages..."
        if python3 -m venv venv --system-site-packages; then
            log_success "Virtual environment created with system packages"
        else
            log_error "All virtual environment creation methods failed"
            log_info "Checking Python installation..."
            python3 --version
            exit 1
        fi
    fi
    
    # Verify venv was created
    if [[ -f "venv/bin/activate" ]]; then
        log_success "Virtual environment structure verified"
    else
        log_error "Virtual environment creation incomplete"
        exit 1
    fi
}

install_dependencies() {
    log_info "Installing Python dependencies in virtual environment..."
    
    # Change to backup directory
    cd /opt/bitbucket-backup
    
    # Activate virtual environment
    log_info "Activating virtual environment..."
    source venv/bin/activate
    
    # Verify we're in the venv
    which python3
    which pip
    
    # Upgrade pip first (suppress warnings)
    log_info "Upgrading pip..."
    pip install --upgrade pip --quiet
    
    # Install required packages
    log_info "Installing requests and python-dotenv..."
    if pip install requests python-dotenv --quiet; then
        log_success "All dependencies installed successfully"
    else
        log_error "Failed to install dependencies"
        log_info "Checking pip version and trying again..."
        pip --version
        
        # Try installing one by one for better error diagnosis
        log_info "Installing requests..."
        pip install requests --quiet || log_error "Failed to install requests"
        
        log_info "Installing python-dotenv..."
        pip install python-dotenv --quiet || log_error "Failed to install python-dotenv"
    fi
    
    # Verify installations
    log_info "Verifying installations..."
    python3 -c "import requests; import dotenv; print('All imports successful')" && log_success "Dependencies verified" || log_error "Import verification failed"
    
    deactivate
}

copy_backup_scripts() {
    log_info "Copying backup scripts..."
    
    # Get the directory where the setup script is located (where the backup files are)
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    log_info "Script directory: $script_dir"
    log_info "Looking for files in: $script_dir"
    
    # Check if files exist before copying
    local files_to_copy=(
        "bitbucket-backup.py"
        "bitbucket-backup.sh"
        ".env.example"
    )
    
    for file in "${files_to_copy[@]}"; do
        if [[ -f "$script_dir/$file" ]]; then
            log_info "Found: $file"
        else
            log_error "Missing: $file in $script_dir"
            ls -la "$script_dir"
            exit 1
        fi
    done
    
    # Copy the backup scripts
    cp "$script_dir/bitbucket-backup.py" "$BACKUP_DIR/scripts/"
    cp "$script_dir/bitbucket-backup.sh" "$BACKUP_DIR/scripts/"
    cp "$script_dir/.env.example" "$BACKUP_DIR/config/"
    
    # Make scripts executable
    chmod +x "$BACKUP_DIR/scripts/"*.sh
    chmod +x "$BACKUP_DIR/scripts/"*.py
    
    log_success "Backup scripts copied successfully"
    log_info "Copied files:"
    ls -la "$BACKUP_DIR/scripts/"
    ls -la "$BACKUP_DIR/config/"
}

create_simple_cron() {
    log_info "Creating simple cron job for backups..."
    
    # Create a wrapper script that sources environment and activates venv
    cat > "$BACKUP_DIR/scripts/cron-wrapper.sh" << EOF
#!/bin/bash
# Cron wrapper for backup script - Ubuntu 24 compatible

# Change to backup directory
cd /opt/bitbucket-backup

# Activate virtual environment
source venv/bin/activate

# Source environment variables
source config/.env

# Run backup script
./scripts/bitbucket-backup.sh

# Deactivate virtual environment
deactivate
EOF

    chmod +x "$BACKUP_DIR/scripts/cron-wrapper.sh"
    
    log_info "To add to cron, run as the user you want:"
    log_info "crontab -e"
    log_info "Add this line for backup every 3 days at 2 AM:"
    log_info "0 2 */3 * * /opt/bitbucket-backup/scripts/cron-wrapper.sh >> /opt/bitbucket-backup/logs/cron.log 2>&1"
    
    log_success "Cron wrapper created"
}

show_manual_steps() {
    cat << EOF

🎉 Basic setup completed!

📋 Manual steps needed:

1. Install Python dependencies (you'll do this manually):
   pip3 install requests python-dotenv

2. Configure your credentials:
   sudo nano $BACKUP_DIR/config/.env
   
   Set these values:
   - ATLASSIAN_EMAIL=your-email@domain.com
   - BITBUCKET_API_TOKEN=your-api-token
   - BITBUCKET_WORKSPACE=your-workspace
   - BACKUP_WORKSPACE=your-backup-workspace

3. Test the backup:
   cd $BACKUP_DIR
   source config/.env
   ./scripts/bitbucket-backup.sh --test-only

4. Test Python environment:
   source venv/bin/activate
   python3 -c "import requests, dotenv; print('Environment ready!')"
   deactivate

5. Run first backup:
   ./scripts/bitbucket-backup.sh --force

6. Add to cron (optional):
   crontab -e
   Add: 0 2 */3 * * /opt/bitbucket-backup/scripts/cron-wrapper.sh >> /opt/bitbucket-backup/logs/cron.log 2>&1

📁 Files created:
$BACKUP_DIR/
├── venv/                        # Python virtual environment
├── scripts/
│   ├── bitbucket-backup.py       # Full backup engine
│   ├── bitbucket-backup.sh       # Main backup script
│   └── cron-wrapper.sh          # Cron helper
├── config/
│   └── .env.example             # Configuration template
├── logs/                        # Log directory
├── repositories/                # Where backups will be stored
└── metadata/                    # Repository metadata

EOF
}

main() {
    show_banner
    check_root
    install_basic_dependencies
    create_backup_directory
    create_venv
    install_dependencies
    copy_backup_scripts
    create_simple_cron
    show_manual_steps
}

main "$@"