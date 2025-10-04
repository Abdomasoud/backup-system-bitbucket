#!/bin/bash
# Bitbucket Repository Backup Script
# Simple & Reliable - No virtual environments needed
#
# 🚀 RECOMMENDED: Use the Python version for enhanced features:
#    python3 bitbucket-backup.py
#
# Features available in Python version:
# ✅ Auto-discovery of ALL workspaces & repositories
# ✅ Dual-account migration support
# ✅ Enhanced error reporting & troubleshooting
# ✅ Collaboration data restoration (issues, PRs, wikis)
# ✅ Advanced filtering and workspace mapping
#
# This shell script provides basic single-workspace backup functionality

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
        # Use set -a to automatically export all variables
        set -a
        source "$env_file"
        set +a
        log_info "Loaded environment variables from: $env_file"
    else
        log_warning "No .env file found. Using environment variables or defaults."
    fi
}

# Check if enhanced features are configured that require Python version
check_enhanced_features() {
    local enhanced_features=()
    
    if [[ "$AUTO_DISCOVER_ALL" == "true" ]]; then
        enhanced_features+=("Auto-discovery of ALL workspaces")
    fi
    
    if [[ "$MIGRATION_MODE" == "true" ]]; then
        enhanced_features+=("Cross-account migration")
    fi
    
    if [[ "$RESTORE_ISSUES" == "true" || "$RESTORE_WIKI" == "true" || "$RESTORE_PRS" == "true" ]]; then
        enhanced_features+=("Collaboration data restoration")
    fi
    
    if [[ -n "$SOURCE_BITBUCKET_WORKSPACES" && "$SOURCE_BITBUCKET_WORKSPACES" == *","* ]]; then
        enhanced_features+=("Multi-workspace processing")
    fi
    
    if [[ ${#enhanced_features[@]} -gt 0 ]]; then
        log_warning "Enhanced features detected in configuration:"
        for feature in "${enhanced_features[@]}"; do
            echo -e "   🔥 $feature"
        done
        echo ""
        log_info "🚀 For full feature support, use the Python version:"
        echo -e "   ${BOLD}python3 bitbucket-backup.py${NC}"
        echo ""
        log_info "Shell script will attempt basic single-workspace backup only..."
        echo ""
        sleep 3
    fi
}

# Initialize configuration variables after loading env
init_config() {
    # Load environment first
    load_env_config
    
    # Detect configuration format and set compatibility variables
    if [[ -n "$SOURCE_ATLASSIAN_EMAIL" && -n "$DEST_ATLASSIAN_EMAIL" ]]; then
        # DUAL-ACCOUNT FORMAT DETECTED
        log_info "Using dual-account configuration format"
        
        # Check for enhanced features that require Python version
        check_enhanced_features
    else
        log_error "Missing dual-account configuration!"
        log_error "Required variables: SOURCE_ATLASSIAN_EMAIL, SOURCE_BITBUCKET_API_TOKEN, DEST_ATLASSIAN_EMAIL, DEST_BITBUCKET_API_TOKEN"
        log_info "Please configure your .env file with dual-account format"
        exit 1
    fi
    
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
    log_info "Validating dual-account configuration..."
    
    local config_valid=true
    
    # Check required dual-account variables
    if [[ -z "$SOURCE_ATLASSIAN_EMAIL" ]]; then
        log_error "SOURCE_ATLASSIAN_EMAIL not set"
        config_valid=false
    fi
    
    if [[ -z "$SOURCE_BITBUCKET_API_TOKEN" ]]; then
        log_error "SOURCE_BITBUCKET_API_TOKEN not set"
        config_valid=false
    fi
    
    if [[ -z "$DEST_ATLASSIAN_EMAIL" ]]; then
        log_error "DEST_ATLASSIAN_EMAIL not set"
        config_valid=false
    fi
    
    if [[ -z "$DEST_BITBUCKET_API_TOKEN" ]]; then
        log_error "DEST_BITBUCKET_API_TOKEN not set"
        config_valid=false
    fi
    
    if [[ "$config_valid" != true ]]; then
        log_error "Configuration validation failed!"
        log_info "Please configure your .env file with dual-account format:"
        log_info "  SOURCE_ATLASSIAN_EMAIL=your-source@email.com"
        log_info "  SOURCE_BITBUCKET_API_TOKEN=source-token"
        log_info "  DEST_ATLASSIAN_EMAIL=your-dest@email.com"
        log_info "  DEST_BITBUCKET_API_TOKEN=dest-token"
        log_info "For enhanced features, use: python3 bitbucket-backup.py"
        exit 1
    fi
    
    log_success "Dual-account configuration validation passed"
}

# Test Bitbucket API connection
test_api_connection() {
    log_info "Testing source account API connection..."
    
    # Test source account connection
    local source_response=$(curl -s -u "${SOURCE_ATLASSIAN_EMAIL}:${SOURCE_BITBUCKET_API_TOKEN}" \
        -H "Accept: application/json" \
        "https://api.bitbucket.org/2.0/user" \
        -w "%{http_code}")
    
    local source_http_code="${source_response: -3}"
    
    if [[ "$source_http_code" == "200" ]]; then
        log_success "Source account API connection successful"
    elif [[ "$source_http_code" == "401" ]]; then
        log_error "Source account authentication failed - check SOURCE_ATLASSIAN_EMAIL and SOURCE_BITBUCKET_API_TOKEN"
        exit 1
    else
        log_error "Source account API connection failed with HTTP code: $source_http_code"
        exit 1
    fi
    
    # Test destination account connection
    log_info "Testing destination account API connection..."
    local dest_response=$(curl -s -u "${DEST_ATLASSIAN_EMAIL}:${DEST_BITBUCKET_API_TOKEN}" \
        -H "Accept: application/json" \
        "https://api.bitbucket.org/2.0/user" \
        -w "%{http_code}")
    
    local dest_http_code="${dest_response: -3}"
    
    if [[ "$dest_http_code" == "200" ]]; then
        log_success "Destination account API connection successful"
    elif [[ "$dest_http_code" == "401" ]]; then
        log_error "Destination account authentication failed - check DEST_ATLASSIAN_EMAIL and DEST_BITBUCKET_API_TOKEN"
        exit 1
    else
        log_error "Destination account API connection failed with HTTP code: $dest_http_code"
        exit 1
    fi
    
    log_success "Both accounts validated successfully"
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

# Check if Python script should be used instead of shell script
should_use_python() {
    # Check for enhanced features that require Python
    if [[ "$AUTO_DISCOVER_ALL" == "true" ]] || \
       [[ "$MIGRATION_MODE" == "true" ]] || \
       [[ "$RESTORE_ISSUES" == "true" ]] || \
       [[ "$RESTORE_WIKI" == "true" ]] || \
       [[ "$RESTORE_PRS" == "true" ]] || \
       [[ -n "$SOURCE_ATLASSIAN_EMAIL" && -n "$DEST_ATLASSIAN_EMAIL" ]]; then
        return 0  # True - use Python
    else
        return 1  # False - use shell script
    fi
}

# Export all environment variables from .env file
export_all_env_vars() {
    local env_file=""
    
    # Find the .env file
    if [[ -f "$BACKUP_BASE_DIR/config/.env" ]]; then
        env_file="$BACKUP_BASE_DIR/config/.env"
    elif [[ -f "$SCRIPT_DIR/../config/.env" ]]; then
        env_file="$SCRIPT_DIR/../config/.env"
    elif [[ -f "/opt/bitbucket-backup/config/.env" ]]; then
        env_file="/opt/bitbucket-backup/config/.env"
    fi
    
    if [[ -n "$env_file" && -f "$env_file" ]]; then
        log_info "📋 Exporting all variables from: $env_file"
        
        # Export all non-comment, non-empty lines as environment variables
        while IFS= read -r line || [[ -n "$line" ]]; do
            # Skip comments and empty lines
            if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "${line// }" ]]; then
                continue
            fi
            
            # Remove inline comments and whitespace
            line=$(echo "$line" | sed 's/#.*//' | sed 's/[[:space:]]*$//')
            
            # Skip if line is empty after cleaning
            if [[ -z "$line" ]]; then
                continue
            fi
            
            # Export the variable if it contains =
            if [[ "$line" == *"="* ]]; then
                export "$line"
                # Debug: show what we're exporting (without token values)
                var_name=$(echo "$line" | cut -d'=' -f1)
                if [[ "$var_name" == *"TOKEN"* ]]; then
                    log_info "   Exported: $var_name=***HIDDEN***"
                else
                    log_info "   Exported: $line"
                fi
            fi
        done < "$env_file"
    else
        log_error "Could not find .env file to export variables"
        exit 1
    fi
}

# Run Python script with proper environment
run_python_script() {
    local python_script=""
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Look for Python script in multiple locations
    if [[ -f "$script_dir/bitbucket-backup.py" ]]; then
        python_script="$script_dir/bitbucket-backup.py"
    elif [[ -f "$BACKUP_BASE_DIR/bitbucket-backup.py" ]]; then
        python_script="$BACKUP_BASE_DIR/bitbucket-backup.py"
    elif [[ -f "/opt/bitbucket-backup/bitbucket-backup.py" ]]; then
        python_script="/opt/bitbucket-backup/bitbucket-backup.py"
    else
        log_error "Python script not found! Please ensure bitbucket-backup.py is available."
        exit 1
    fi
    
    log_info "🐍 Using Python script for enhanced features: $python_script"
    
    # Export ALL environment variables from .env file
    export_all_env_vars
    
    # Verify critical variables are set
    log_info "🔍 Verifying critical environment variables..."
    if [[ -n "$SOURCE_ATLASSIAN_EMAIL" ]]; then
        log_info "   ✅ SOURCE_ATLASSIAN_EMAIL: ${SOURCE_ATLASSIAN_EMAIL}"
    fi
    if [[ -n "$DEST_ATLASSIAN_EMAIL" ]]; then
        log_info "   ✅ DEST_ATLASSIAN_EMAIL: ${DEST_ATLASSIAN_EMAIL}"
    fi
    if [[ -n "$SOURCE_BITBUCKET_API_TOKEN" ]]; then
        log_info "   ✅ SOURCE_BITBUCKET_API_TOKEN: ***SET***"
    fi
    if [[ -n "$DEST_BITBUCKET_API_TOKEN" ]]; then
        log_info "   ✅ DEST_BITBUCKET_API_TOKEN: ***SET***"
    fi
    
    # Change to the directory containing the Python script
    cd "$(dirname "$python_script")"
    
    # Run Python script with the passed arguments
    case "${1:-}" in
        --test-only|--test)
            log_info "🧪 Running Python configuration test..."
            python3 "$(basename "$python_script")" test
            ;;
        *)
            log_info "🚀 Running Python backup/migration..."
            python3 "$(basename "$python_script")"
            ;;
    esac
}

# Main function
main() {
    # Initialize configuration (loads .env file automatically)
    init_config
    
    # Check if we should use Python script for enhanced features
    if should_use_python; then
        log_info "🔥 Enhanced features detected - delegating to Python script"
        run_python_script "$@"
        exit $?
    fi
    
    # Continue with shell script for basic functionality
    log_info "📜 Using shell script for basic backup functionality"
    
    # Handle command line arguments
    case "${1:-}" in
        --test-only|--test)
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
            echo ""
            echo "Required dual-account configuration:"
            echo "  SOURCE_ATLASSIAN_EMAIL      - Source account email"
            echo "  SOURCE_BITBUCKET_API_TOKEN  - Source account API token"
            echo "  DEST_ATLASSIAN_EMAIL        - Destination account email"  
            echo "  DEST_BITBUCKET_API_TOKEN    - Destination account API token"
            echo ""
            echo "🐍 Enhanced features (auto-delegated to Python script):"
            echo "  • Auto-discovery of ALL workspaces"
            echo "  • Cross-account migration with collaboration data"
            echo "  • Issues, PRs, and wiki restoration"
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