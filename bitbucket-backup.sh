#!/bin/bash
# Bitbucket Repository Backup Script
# Simple & Reliable - No virtual environments needed

set -e

# Colors and formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# Get script directory and backup base directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_BASE_DIR="$(dirname "$SCRIPT_DIR")"

# Load environment variables from config file
load_env_config() {
    local env_file=""
    
    # Try multiple locations for .env file
    if [[ -f "$BACKUP_BASE_DIR/config/.env" ]]; then
        env_file="$BACKUP_BASE_DIR/config/.env"
    elif [[ -f "$SCRIPT_DIR/../config/.env" ]]; then
        env_file="$SCRIPT_DIR/../config/.env"
    elif [[ -f "/opt/bitbucket-backup/config/.env" ]]; then
        env_file="/opt/bitbucket-backup/config/.env"
    fi
    
    if [[ -n "$env_file" && -f "$env_file" ]]; then
        source "$env_file"
        log_info "Loaded environment variables from: $env_file"
    else
        log_warning "No .env file found. Using environment variables or defaults."
    fi
}

# Initialize configuration variables after loading env
init_config() {
    # Load environment first
    load_env_config
    
    # Set configuration with loaded values or defaults
    ATLASSIAN_EMAIL="${ATLASSIAN_EMAIL:-your-atlassian-email@domain.com}"
    BITBUCKET_API_TOKEN="${BITBUCKET_API_TOKEN:-your-api-token}"
    BITBUCKET_USERNAME="${BITBUCKET_USERNAME:-your-bitbucket-username}"
    BITBUCKET_WORKSPACE="${BITBUCKET_WORKSPACE:-your-source-workspace}"
    BACKUP_WORKSPACE="${BACKUP_WORKSPACE:-your-backup-workspace}"
    
    # Other settings
    BACKUP_DIR="${BACKUP_BASE_DIR}/repositories"
    METADATA_DIR="${BACKUP_BASE_DIR}/metadata"
    TEMP_DIR="${BACKUP_BASE_DIR}/temp"
    LOG_DIR="${BACKUP_BASE_DIR}/logs"
    
    # Backup scheduling (every 3 days)
    BACKUP_INTERVAL_HOURS=72
    BACKUP_STATE_FILE="${BACKUP_BASE_DIR}/.last_backup"
    RETENTION_COUNT=5
}

# Logging functions
log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] - $1 - $2" >> "${LOG_DIR}/backup_$(date +%Y%m%d_%H%M%S).log"
}

log_info() {
    log "INFO" "$1"
    echo -e "ℹ️  $1"
}

log_success() {
    log "SUCCESS" "$1"
    echo -e "✅ $1"
}

log_error() {
    log "ERROR" "$1"
    echo -e "❌ $1"
}

log_warning() {
    log "WARNING" "$1"
    echo -e "⚠️  $1"
}

# Check dependencies
check_dependencies() {
    log_info "Checking system dependencies..."
    
    local required_commands=("git" "curl" "jq" "python3")
    local missing_commands=()
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_commands+=("$cmd")
        fi
    done
    
    if [[ ${#missing_commands[@]} -gt 0 ]]; then
        log_error "Missing required commands: ${missing_commands[*]}"
        log_info "Please install missing dependencies"
        exit 1
    fi
    
    log_success "All dependencies are available"
}

# Validate configuration
validate_config() {
    log_info "Validating configuration..."
    
    local config_valid=true
    
    if [[ -z "$ATLASSIAN_EMAIL" || "$ATLASSIAN_EMAIL" == "your-atlassian-email@domain.com" ]]; then
        log_error "ATLASSIAN_EMAIL not set or using default value"
        config_valid=false
    fi
    
    if [[ -z "$BITBUCKET_API_TOKEN" || "$BITBUCKET_API_TOKEN" == "your-api-token" ]]; then
        log_error "BITBUCKET_API_TOKEN not set or using default value"
        config_valid=false
    fi
    
    if [[ -z "$BITBUCKET_WORKSPACE" || "$BITBUCKET_WORKSPACE" == "your-source-workspace" ]]; then
        log_error "BITBUCKET_WORKSPACE not set or using default value"
        config_valid=false
    fi
    
    if [[ -z "$BACKUP_WORKSPACE" || "$BACKUP_WORKSPACE" == "your-backup-workspace" ]]; then
        log_error "BACKUP_WORKSPACE not set or using default value"
        config_valid=false
    fi
    
    if [[ "$config_valid" != true ]]; then
        log_error "Configuration validation failed!"
        log_info "Please edit /opt/bitbucket-backup/config/.env with your credentials"
        exit 1
    fi
    
    log_success "Configuration validation passed"
}

# Test Bitbucket API connection
test_api_connection() {
    log_info "Testing Bitbucket API connection..."
    
    local response=$(curl -s -u "${ATLASSIAN_EMAIL}:${BITBUCKET_API_TOKEN}" \
        -H "Accept: application/json" \
        "https://api.bitbucket.org/2.0/repositories/${BITBUCKET_WORKSPACE}" \
        -w "%{http_code}")
    
    local http_code="${response: -3}"
    
    if [[ "$http_code" == "200" ]]; then
        log_success "Bitbucket API connection successful"
        
        # Count repositories
        local repo_count=$(echo "${response%???}" | jq -r '.size // 0')
        log_info "Found ${repo_count} repositories in workspace"
        
    elif [[ "$http_code" == "401" ]]; then
        log_error "Authentication failed - check Atlassian email and API token"
        exit 1
    elif [[ "$http_code" == "404" ]]; then
        log_error "Workspace not found - check BITBUCKET_WORKSPACE value"
        exit 1
    else
        log_error "API connection failed with HTTP code: $http_code"
        exit 1
    fi
}

# Setup directory structure
setup_directories() {
    log_info "Setting up directory structure..."
    
    local directories=(
        "$BACKUP_DIR"
        "$METADATA_DIR"
        "$TEMP_DIR"
        "$LOG_DIR"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
    done
    
    log_success "Directory structure ready"
}

# Main backup process
run_backup() {
    log_info "🚀 Starting full backup process..."
    
    # Setup directory structure first
    setup_directories
    
    # Export all environment variables so Python can access them
    export ATLASSIAN_EMAIL="$ATLASSIAN_EMAIL"
    export BITBUCKET_API_TOKEN="$BITBUCKET_API_TOKEN"
    export BITBUCKET_USERNAME="$BITBUCKET_USERNAME"
    export BITBUCKET_WORKSPACE="$BITBUCKET_WORKSPACE"
    export BACKUP_WORKSPACE="$BACKUP_WORKSPACE"
    export BACKUP_BASE_DIR="$BACKUP_BASE_DIR"
    
    # Print debug info
    log_info "Environment check:"
    log_info "  ATLASSIAN_EMAIL: ${ATLASSIAN_EMAIL:0:10}..."
    log_info "  BITBUCKET_WORKSPACE: $BITBUCKET_WORKSPACE"
    log_info "  BACKUP_WORKSPACE: $BACKUP_WORKSPACE"
    
    # Run Python backup script with environment variables
    cd "$BACKUP_BASE_DIR"
    
    # Method 1: Direct execution with env vars
    if env ATLASSIAN_EMAIL="$ATLASSIAN_EMAIL" \
           BITBUCKET_API_TOKEN="$BITBUCKET_API_TOKEN" \
           BITBUCKET_USERNAME="$BITBUCKET_USERNAME" \
           BITBUCKET_WORKSPACE="$BITBUCKET_WORKSPACE" \
           BACKUP_WORKSPACE="$BACKUP_WORKSPACE" \
           BACKUP_BASE_DIR="$BACKUP_BASE_DIR" \
           python3 scripts/bitbucket-backup.py; then
        log_success "Backup completed successfully!"
        echo "$(date '+%Y-%m-%d %H:%M:%S')" > "$BACKUP_STATE_FILE"
    else
        log_error "Backup failed!"
        exit 1
    fi
}

# Check if backup is due
is_backup_due() {
    if [[ ! -f "$BACKUP_STATE_FILE" ]]; then
        return 0  # No previous backup, so it's due
    fi
    
    local last_backup=$(cat "$BACKUP_STATE_FILE" 2>/dev/null || echo "1970-01-01 00:00:00")
    local last_backup_epoch=$(date -d "$last_backup" +%s 2>/dev/null || echo 0)
    local current_epoch=$(date +%s)
    local time_diff=$(( (current_epoch - last_backup_epoch) / 3600 ))
    
    if [[ $time_diff -ge $BACKUP_INTERVAL_HOURS ]]; then
        return 0  # Backup is due
    else
        local hours_remaining=$(( BACKUP_INTERVAL_HOURS - time_diff ))
        log_info "Backup not due yet. Next backup in ${hours_remaining} hours."
        return 1  # Backup not due
    fi
}

# Main function
main() {
    # Initialize configuration (loads .env file automatically)
    init_config
    
    # Handle command line arguments
    case "${1:-}" in
        --test-only)
            log_info "🧪 Running connection test only..."
            check_dependencies
            validate_config
            test_api_connection
            log_success "Connection test completed successfully!"
            exit 0
            ;;
        --force)
            log_info "🔄 Forcing backup run (ignoring schedule)..."
            check_dependencies
            validate_config
            test_api_connection
            setup_directories
            run_backup
            exit 0
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --test-only    Test API connection and configuration only"
            echo "  --force        Force backup run (ignore schedule)"
            echo "  --help, -h     Show this help message"
            echo ""
            echo "Configuration file: /opt/bitbucket-backup/config/.env"
            echo "Required variables:"
            echo "  ATLASSIAN_EMAIL      - Your Atlassian account email"
            echo "  BITBUCKET_API_TOKEN  - Your Bitbucket API token"
            echo "  BITBUCKET_WORKSPACE  - Source workspace name"
            echo "  BACKUP_WORKSPACE     - Backup workspace name"
            exit 0
            ;;
        "")
            # Normal scheduled run
            check_dependencies
            validate_config
            
            if is_backup_due; then
                test_api_connection
                setup_directories
                run_backup
            fi
            ;;
        *)
            log_error "Unknown option: $1"
            log_info "Use --help for usage information"
            exit 1
            ;;
    esac
}

main "$@"