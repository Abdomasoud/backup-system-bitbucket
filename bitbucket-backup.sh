#!/bin/bash
# Simple Bitbucket Backup Script
# No systemd, no venv - just pure backup automation

set -e

# Load environment variables from config file if it exists
if [[ -f "${BACKUP_BASE_DIR}/config/.env" ]]; then
    source "${BACKUP_BASE_DIR}/config/.env"
    log_info "Loaded environment variables from config/.env"
elif [[ -f "$(dirname "$0")/../config/.env" ]]; then
    source "$(dirname "$0")/../config/.env"
    log_info "Loaded environment variables from ../config/.env"
fi

# Configuration - Edit these values or set as environment variables
ATLASSIAN_EMAIL="${ATLASSIAN_EMAIL:-your-atlassian-email@domain.com}"
BITBUCKET_API_TOKEN="${BITBUCKET_API_TOKEN:-your-api-token}"
BITBUCKET_WORKSPACE="${BITBUCKET_WORKSPACE:-your-source-workspace}"
BACKUP_WORKSPACE="${BACKUP_WORKSPACE:-your-backup-workspace}"

# Backup configuration
BACKUP_BASE_DIR="${BACKUP_BASE_DIR:-/opt/bitbucket-backup}"
MAX_BACKUPS="${MAX_BACKUPS:-5}"
BACKUP_INTERVAL_DAYS="${BACKUP_INTERVAL_DAYS:-3}"

# Logging configuration
LOGS_DIR="${BACKUP_BASE_DIR}/logs"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="${LOGS_DIR}/backup_${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Ensure we have required directories
mkdir -p "${BACKUP_BASE_DIR}" "${LOGS_DIR}"

# Logging function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} - ${level} - ${message}" | tee -a "${LOG_FILE}"
}

log_info() {
    log "INFO" "$@"
    echo -e "${BLUE}ℹ️  $@${NC}"
}

log_success() {
    log "SUCCESS" "$@"
    echo -e "${GREEN}✅ $@${NC}"
}

log_error() {
    log "ERROR" "$@"
    echo -e "${RED}❌ $@${NC}"
}

log_warning() {
    log "WARNING" "$@"
    echo -e "${YELLOW}⚠️  $@${NC}"
}

log_process() {
    log "PROCESS" "$@"
    echo -e "${PURPLE}🔄 $@${NC}"
}

# Check if we're running on the right schedule (every 3 days)
check_schedule() {
    local last_run_file="${BACKUP_BASE_DIR}/.last_backup_run"
    local current_date=$(date +%s)
    local interval_seconds=$((BACKUP_INTERVAL_DAYS * 24 * 60 * 60))
    
    if [[ -f "$last_run_file" ]]; then
        local last_run=$(cat "$last_run_file")
        local time_diff=$((current_date - last_run))
        
        if [[ $time_diff -lt $interval_seconds ]]; then
            local hours_remaining=$(( (interval_seconds - time_diff) / 3600 ))
            log_info "Backup not due yet. Next backup in ${hours_remaining} hours."
            
            # Unless forced
            if [[ "$1" != "--force" ]]; then
                exit 0
            else
                log_warning "Forcing backup despite schedule..."
            fi
        fi
    fi
    
    # Update last run timestamp
    echo "$current_date" > "$last_run_file"
}

# Check dependencies
check_dependencies() {
    log_info "Checking system dependencies..."
    
    local missing_deps=()
    
    # Check required tools
    for tool in git python3 curl jq; do
        if ! command -v "$tool" &> /dev/null; then
            missing_deps+=("$tool")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_info "Please install missing dependencies"
        exit 1
    fi
    
    # Check Python modules
    if ! python3 -c "import requests, json, os" 2>/dev/null; then
        log_error "Missing Python modules. Please install:"
        log_error "pip3 install requests python-dotenv"
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
        log_info "Please set the required environment variables or edit this script"
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
        "${BACKUP_BASE_DIR}/repositories"
        "${BACKUP_BASE_DIR}/metadata"
        "${BACKUP_BASE_DIR}/logs"
        "${BACKUP_BASE_DIR}/temp"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        log_info "Created directory: $dir"
    done
    
    log_success "Directory structure ready"
}

# Main backup process
run_backup() {
    log_info "🚀 Starting Bitbucket backup process..."
    log_info "Timestamp: $TIMESTAMP"
    log_info "Workspace: $BITBUCKET_WORKSPACE → $BACKUP_WORKSPACE"
    
    # Set environment variables for Python script
    export ATLASSIAN_EMAIL
    export BITBUCKET_API_TOKEN
    export BITBUCKET_WORKSPACE
    export BACKUP_WORKSPACE
    export BACKUP_BASE_DIR
    export MAX_BACKUPS
    
    # Run the Python backup script
    local python_script="$(dirname "$0")/bitbucket-backup.py"
    
    if [[ -f "$python_script" ]]; then
        log_process "Executing Python backup script..."
        
        if python3 "$python_script"; then
            log_success "Python backup script completed successfully"
        else
            log_error "Python backup script failed"
            return 1
        fi
    else
        log_error "Python backup script not found: $python_script"
        return 1
    fi
    
    return 0
}

# Generate backup report
generate_report() {
    log_info "Generating backup report..."
    
    local report_file="${LOGS_DIR}/backup_report_${TIMESTAMP}.txt"
    local repos_dir="${BACKUP_BASE_DIR}/repositories"
    
    cat > "$report_file" << EOF
===================================
Bitbucket Backup Report
===================================
Backup Date: $(date)
Workspace: ${BITBUCKET_WORKSPACE}
Backup Location: ${BACKUP_BASE_DIR}
Max Backups per Repo: ${MAX_BACKUPS}

Repository Summary:
EOF
    
    if [[ -d "$repos_dir" ]]; then
        for repo_dir in "$repos_dir"/*; do
            if [[ -d "$repo_dir" ]]; then
                local repo_name=$(basename "$repo_dir")
                local backup_count=$(find "$repo_dir" -name "*.tar.gz" 2>/dev/null | wc -l)
                local latest_backup=$(find "$repo_dir" -name "*.tar.gz" -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
                
                echo "  📁 $repo_name:" >> "$report_file"
                echo "     - Backups: $backup_count" >> "$report_file"
                
                if [[ -n "$latest_backup" ]]; then
                    local backup_size=$(du -h "$latest_backup" 2>/dev/null | cut -f1)
                    echo "     - Latest: $(basename "$latest_backup") (${backup_size})" >> "$report_file"
                fi
                
                echo "" >> "$report_file"
            fi
        done
    fi
    
    echo "" >> "$report_file"
    echo "Disk Usage:" >> "$report_file"
    echo "$(du -sh "$BACKUP_BASE_DIR" 2>/dev/null || echo 'Unable to calculate')" >> "$report_file"
    
    log_success "Backup report generated: $report_file"
    
    # Display summary
    log_info "📊 Backup Summary:"
    cat "$report_file" | grep -E "(Repository Summary:|📁|Disk Usage:)" | while read -r line; do
        log_info "$line"
    done
}

# Show help
show_help() {
    cat << EOF
🔄 Simple Bitbucket Backup System

A straightforward backup solution for all Bitbucket repositories with:
- Automatic repository discovery and cloning
- Mirror repository creation
- Compressed tar.gz backups with rotation
- Metadata backup (PRs, issues, branches, tags)
- Retention management (keeps 5 backups per repo)
- Scheduled execution every 3 days

Usage:
  $0 [OPTIONS]

Options:
  --help          Show this help message
  --force         Force backup even if not scheduled
  --test-only     Only test API connection, don't backup

Environment Variables:
  ATLASSIAN_EMAIL        Your Atlassian account email
  BITBUCKET_API_TOKEN    Your Bitbucket API token
  BITBUCKET_WORKSPACE    Source workspace to backup
  BACKUP_WORKSPACE       Target workspace for mirrors
  BACKUP_BASE_DIR        Local backup directory (default: /opt/bitbucket-backup)
  MAX_BACKUPS           Number of backups to retain (default: 5)

Setup:
1. Create a Bitbucket API token with repository permissions
2. Set environment variables or edit this script  
3. Run with --test-only first to verify configuration
4. Add to cron for automatic execution:
   0 2 */3 * * /path/to/bitbucket-backup.sh

EOF
}

# Main function
main() {
    # Parse command line arguments
    case "${1:-}" in
        --help|-h)
            show_help
            exit 0
            ;;
        --test-only)
            log_info "🧪 Running connection test only..."
            check_dependencies
            validate_config
            test_api_connection
            log_success "Connection test completed successfully!"
            exit 0
            ;;
        --force)
            log_warning "🔧 Forcing backup execution..."
            ;;
        *)
            # Check if backup is due (unless forced)
            check_schedule "$1"
            ;;
    esac
    
    # Pre-flight checks
    check_dependencies
    validate_config
    test_api_connection
    setup_directories
    
    # Run backup
    if run_backup; then
        log_success "🎉 Backup process completed successfully!"
        generate_report
        
        log_info "💾 Backup Location: ${BACKUP_BASE_DIR}"
        log_info "📊 Check logs: ${LOG_FILE}"
        
    else
        log_error "💥 Backup process failed!"
        exit 1
    fi
}

# Trap errors and cleanup
trap 'log_error "Script interrupted or failed at line $LINENO"' ERR

# Run main function with all arguments
main "$@"