#!/usr/bin/env python3
"""
Bitbucket Backup Script - Full Featured
Fetches all repositories, PRs, issues, settings via Bitbucket API and creates backups
Simplified version without boto3 dependency
"""

import os
import json
import requests
import sys
from datetime import datetime
from pathlib import Path
import time
import tarfile
import shutil
import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

class BitbucketMigrationSystem:
    def __init__(self):
        # Migration mode configuration
        self.migration_mode = os.environ.get('MIGRATION_MODE', 'true').lower() == 'true'
        
        # SOURCE ACCOUNT Configuration (account to migrate FROM)
        self.source_email = os.environ.get('SOURCE_ATLASSIAN_EMAIL', '')
        self.source_api_token = os.environ.get('SOURCE_BITBUCKET_API_TOKEN', '')
        self.source_username = os.environ.get('SOURCE_BITBUCKET_USERNAME', '')
        
        # Multi-workspace support
        self.multi_workspace_mode = os.environ.get('MULTI_WORKSPACE_MODE', 'false').lower() == 'true'
        self.source_workspaces = self._parse_workspaces(os.environ.get('SOURCE_BITBUCKET_WORKSPACES', ''))
        self.dest_workspaces = self._parse_workspaces(os.environ.get('DEST_BITBUCKET_WORKSPACES', ''))
        self.workspace_mapping = self._parse_workspace_mapping(os.environ.get('WORKSPACE_MAPPING', ''))
        
        # Single workspace support
        self.source_workspace = os.environ.get('SOURCE_BITBUCKET_WORKSPACE', '')
        self.dest_workspace = os.environ.get('DEST_BITBUCKET_WORKSPACE', '')
        
        # DESTINATION ACCOUNT Configuration (account to migrate TO) 
        self.dest_email = os.environ.get('DEST_ATLASSIAN_EMAIL', '')
        self.dest_api_token = os.environ.get('DEST_BITBUCKET_API_TOKEN', '')
        self.dest_username = os.environ.get('DEST_BITBUCKET_USERNAME', '')
        
        # Migration settings
        self.preserve_repo_names = os.environ.get('PRESERVE_REPO_NAMES', 'true').lower() == 'true'
        self.repo_name_prefix = os.environ.get('REPO_NAME_PREFIX', '')
        self.workspace_name_prefix = os.environ.get('WORKSPACE_NAME_PREFIX', '')
        self.skip_existing_repos = os.environ.get('SKIP_EXISTING_REPOS', 'true').lower() == 'true'
        self.skip_existing_workspaces = os.environ.get('SKIP_EXISTING_WORKSPACES', 'true').lower() == 'true'
        self.create_missing_workspaces = os.environ.get('CREATE_MISSING_WORKSPACES', 'true').lower() == 'true'
        self.migration_batch_size = int(os.environ.get('MIGRATION_BATCH_SIZE', '5'))
        
        # Set up authentication objects
        self.source_auth = (self.source_email, self.source_api_token)
        self.dest_auth = (self.dest_email, self.dest_api_token)
        
        # Local backup configuration
        self.backup_base_dir = os.environ.get('BACKUP_BASE_DIR', '/opt/bitbucket-backup')
        self.max_backups = int(os.environ.get('MAX_BACKUPS', '5'))
        
        # Email notification configuration
        self.email_enabled = os.environ.get('EMAIL_NOTIFICATIONS', 'false').lower() == 'true'
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.email_username = os.environ.get('EMAIL_USERNAME', '')
        self.email_password = os.environ.get('EMAIL_PASSWORD', '')
        self.notification_email = os.environ.get('NOTIFICATION_EMAIL', '')
        self.email_from = os.environ.get('EMAIL_FROM', self.email_username)
        
        # Bitbucket API setup - SOURCE account for reading
        self.base_url = 'https://api.bitbucket.org/2.0'
        self.source_auth = (self.source_email, self.source_api_token)
        self.dest_auth = (self.dest_email, self.dest_api_token)
        self.auth = self.source_auth  # Default to source for backward compatibility
        
        # Performance settings
        self.clone_timeout = int(os.environ.get('CLONE_TIMEOUT', '1800'))  # 30 min
        self.push_timeout = int(os.environ.get('PUSH_TIMEOUT', '3600'))   # 60 min
        
        # Metadata restoration settings
        self.restore_metadata_issues = os.environ.get('RESTORE_ISSUES', 'true').lower() == 'true'
        self.restore_metadata_prs = os.environ.get('RESTORE_PRS', 'false').lower() == 'true'  # PRs as documentation only
        self.restore_metadata_wiki = os.environ.get('RESTORE_WIKI', 'true').lower() == 'true'
        self.restore_metadata_permissions = os.environ.get('RESTORE_PERMISSIONS', 'false').lower() == 'true'
        self.restore_metadata_restrictions = os.environ.get('RESTORE_BRANCH_RESTRICTIONS', 'false').lower() == 'true'
        self.restore_metadata_webhooks = os.environ.get('RESTORE_WEBHOOKS', 'false').lower() == 'true'
        self.restore_metadata_deploy_keys = os.environ.get('RESTORE_DEPLOY_KEYS', 'false').lower() == 'true'
        
        # Auto-discovery settings
        self.auto_discover_all = os.environ.get('AUTO_DISCOVER_ALL', 'false').lower() == 'true'
        self.workspace_include_patterns = self.parse_filter_patterns(os.environ.get('WORKSPACE_INCLUDE_PATTERNS', ''))
        self.workspace_exclude_patterns = self.parse_filter_patterns(os.environ.get('WORKSPACE_EXCLUDE_PATTERNS', ''))
        self.repo_include_patterns = self.parse_filter_patterns(os.environ.get('REPO_INCLUDE_PATTERNS', ''))
        self.repo_exclude_patterns = self.parse_filter_patterns(os.environ.get('REPO_EXCLUDE_PATTERNS', ''))
        self.auto_discovery_max_repos = int(os.environ.get('AUTO_DISCOVERY_MAX_REPOS', '1000'))
        
        # User mapping for cross-account migration
        self.user_mapping = self.load_user_mapping()
        
        # Headers for API requests
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Setup directories
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.setup_directories()
        
        # Initialize backup statistics
        self.backup_stats = {
            'start_time': datetime.now(),
            'end_time': None,
            'total_repos': 0,
            'successful_repos': 0,
            'failed_repos': 0,
            'total_size': 0,
            'repo_details': [],
            'errors': []
        }
        
    def setup_directories(self):
        """Create necessary backup directories"""
        self.repos_dir = os.path.join(self.backup_base_dir, 'repositories')
        self.metadata_dir = os.path.join(self.backup_base_dir, 'metadata')
        self.logs_dir = os.path.join(self.backup_base_dir, 'logs')
        
        os.makedirs(self.repos_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        
    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"{timestamp} - {message}"
        print(log_message)
        
        # Also write to log file
        log_file = os.path.join(self.logs_dir, f'backup_{self.timestamp}.log')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def make_api_request(self, endpoint, params=None, method='GET', data=None):
        """Make authenticated request to Bitbucket API"""
        url = f"{self.base_url}/{endpoint}"
        try:
            if method.upper() == 'POST':
                response = requests.post(url, auth=self.auth, headers=self.headers, params=params, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, auth=self.auth, headers=self.headers, params=params, json=data)
            else:
                response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.log(f"API error for {endpoint}: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                self.log(f"Response: {e.response.text}")
            return None
    
    def load_user_mapping(self):
        """Load user mapping configuration for cross-account migration"""
        try:
            user_mapping_str = os.environ.get('USER_MAPPING', '{}')
            # Format: {"source_username1": "dest_username1", "source_username2": "dest_username2"}
            return json.loads(user_mapping_str) if user_mapping_str else {}
        except Exception as e:
            self.log(f"⚠️ Error loading user mapping: {e}")
            return {}
    
    def parse_filter_patterns(self, patterns_str):
        """Parse comma-separated filter patterns"""
        if not patterns_str or patterns_str.strip() == '':
            return []
        return [pattern.strip() for pattern in patterns_str.split(',') if pattern.strip()]
    
    def fetch_paginated_data(self, endpoint, params=None):
        """Fetch all pages of data from Bitbucket API"""
        all_data = []
        next_url = f"{self.base_url}/{endpoint}"
        
        while next_url:
            try:
                response = requests.get(
                    next_url, 
                    auth=self.auth, 
                    headers=self.headers,
                    params=params if next_url == f"{self.base_url}/{endpoint}" else None
                )
                response.raise_for_status()
                
                data = response.json()
                if 'values' in data:
                    all_data.extend(data['values'])
                
                next_url = data.get('next')
                params = None  # Clear params for subsequent requests
                
            except requests.exceptions.RequestException as e:
                self.log(f"API error for {endpoint}: {e}")
                if hasattr(e, 'response') and hasattr(e.response, 'text'):
                    self.log(f"Response: {e.response.text}")
                break
        
        return all_data
    
    def get_all_repositories(self):
        """Fetch all repositories from the SOURCE workspace"""
        self.log(f"🔍 Fetching all repositories from SOURCE workspace: {self.source_workspace}")
        
        repos = self.fetch_paginated_data_with_auth(f'repositories/{self.source_workspace}', auth=self.source_auth)
        self.log(f"Found {len(repos)} repositories in source workspace")
        
        return repos
    
    def get_destination_repositories(self):
        """Fetch all repositories from the DESTINATION workspace"""
        self.log(f"🔍 Checking existing repositories in DESTINATION workspace: {self.dest_workspace}")
        
        try:
            repos = self.fetch_paginated_data_with_auth(f'repositories/{self.dest_workspace}', auth=self.dest_auth)
            self.log(f"Found {len(repos)} existing repositories in destination workspace")
            return {repo['name']: repo for repo in repos}
        except Exception as e:
            self.log(f"⚠️  Could not fetch destination repositories: {e}")
            return {}
    
    def fetch_paginated_data_with_auth(self, endpoint, params=None, auth=None):
        """Fetch paginated data with specific authentication"""
        if auth is None:
            auth = self.source_auth
            
        all_data = []
        next_url = f"{self.base_url}/{endpoint}"
        
        while next_url:
            try:
                response = requests.get(
                    next_url, 
                    auth=auth, 
                    headers=self.headers,
                    params=params if next_url == f"{self.base_url}/{endpoint}" else None
                )
                response.raise_for_status()
                
                data = response.json()
                if 'values' in data:
                    all_data.extend(data['values'])
                
                next_url = data.get('next')
                params = None
                
            except requests.exceptions.RequestException as e:
                self.log(f"API error for {endpoint}: {e}")
                break
        
        return all_data
    
    def validate_migration_config(self):
        """Validate migration configuration and test API connections"""
        if not self.migration_mode:
            # Standard backup mode - only need source credentials
            missing = []
            if not self.source_email:
                missing.append('SOURCE_ATLASSIAN_EMAIL')
            if not self.source_api_token:
                missing.append('SOURCE_BITBUCKET_API_TOKEN') 
            if not self.source_workspace:
                missing.append('SOURCE_BITBUCKET_WORKSPACE')
                
            if missing:
                self.log(f"❌ Missing source configuration: {', '.join(missing)}")
                return False
            
            # Test source API connection for backup mode
            self.log("🔍 Testing source API connection...")
            return self._test_api_connection(
                email=self.source_email,
                api_token=self.source_api_token,
                workspace=self.source_workspace,
                account_type="SOURCE"
            )
        
        # Migration mode - need both source and destination credentials
        missing = []
        
        # Check source credentials
        if not self.source_email:
            missing.append('SOURCE_ATLASSIAN_EMAIL')
        if not self.source_api_token:
            missing.append('SOURCE_BITBUCKET_API_TOKEN')
        if not self.source_workspace:
            missing.append('SOURCE_BITBUCKET_WORKSPACE')
            
        # Check destination credentials  
        if not self.dest_email:
            missing.append('DEST_ATLASSIAN_EMAIL')
        if not self.dest_api_token:
            missing.append('DEST_BITBUCKET_API_TOKEN')
        if not self.dest_workspace:
            missing.append('DEST_BITBUCKET_WORKSPACE')
            
        if missing:
            self.log(f"❌ Missing migration configuration: {', '.join(missing)}")
            self.log("💡 For migration mode, you need both SOURCE_ and DEST_ credentials")
            return False

        # Test API connections with detailed error reporting
        self.log("🔍 Testing API connections...")
        
        # Test source API connection
        source_valid = self._test_api_connection(
            email=self.source_email,
            api_token=self.source_api_token,
            workspace=self.source_workspace,
            account_type="SOURCE"
        )
        
        # Test destination API connection
        dest_valid = self._test_api_connection(
            email=self.dest_email,
            api_token=self.dest_api_token,
            workspace=self.dest_workspace,
            account_type="DESTINATION"
        )
        
        if not source_valid or not dest_valid:
            return False
            
        self.log("✅ Migration configuration and API connections validated")
        return True
    
    def _test_api_connection(self, email, api_token, workspace, account_type):
        """Test API connection with detailed error reporting"""
        self.log(f"   Testing {account_type} account connection...")
        
        try:
            # Test basic authentication
            response = requests.get(
                'https://api.bitbucket.org/2.0/user',
                auth=(email, api_token),
                timeout=30
            )
            
            if response.status_code == 401:
                self.log(f"❌ {account_type} Authentication Failed:")
                self.log(f"   • Email: {email}")
                self.log(f"   • API Token: {'*' * 8}...{api_token[-4:] if len(api_token) > 4 else '****'}")
                self.log(f"   • Error: Invalid credentials or API token")
                self.log(f"   • Fix: Check your Atlassian email and API token")
                self.log(f"   • Generate new token at: https://bitbucket.org/account/settings/app-passwords/")
                return False
                
            elif response.status_code == 403:
                self.log(f"❌ {account_type} Permission Denied:")
                self.log(f"   • Account: {email}")
                self.log(f"   • Error: API token lacks required permissions")
                self.log(f"   • Required permissions: Account: Read, Repositories: Read/Write")
                self.log(f"   • Fix: Create new API token with proper permissions")
                return False
                
            elif response.status_code != 200:
                self.log(f"❌ {account_type} API Error:")
                self.log(f"   • Status: {response.status_code}")
                self.log(f"   • Response: {response.text[:200]}...")
                return False
            
            # Test workspace access
            workspace_response = requests.get(
                f'https://api.bitbucket.org/2.0/workspaces/{workspace}',
                auth=(email, api_token),
                timeout=30
            )
            
            if workspace_response.status_code == 404:
                self.log(f"❌ {account_type} Workspace Access Error:")
                self.log(f"   • Workspace: {workspace}")
                self.log(f"   • Error: Workspace not found or no access")
                self.log(f"   • Fix: Check workspace name and verify account has access")
                return False
                
            elif workspace_response.status_code != 200:
                self.log(f"❌ {account_type} Workspace Error:")
                self.log(f"   • Workspace: {workspace}")
                self.log(f"   • Status: {workspace_response.status_code}")
                self.log(f"   • Response: {workspace_response.text[:200]}...")
                return False
            
            # Test repository listing permissions
            repos_response = requests.get(
                f'https://api.bitbucket.org/2.0/repositories/{workspace}',
                auth=(email, api_token),
                timeout=30
            )
            
            if repos_response.status_code == 403:
                self.log(f"❌ {account_type} Repository Access Error:")
                self.log(f"   • Workspace: {workspace}")
                self.log(f"   • Error: No permission to list repositories")
                self.log(f"   • Fix: API token needs 'Repositories: Read' permission")
                return False
                
            elif repos_response.status_code != 200:
                self.log(f"⚠️  {account_type} Repository Listing Warning:")
                self.log(f"   • Status: {repos_response.status_code}")
                self.log(f"   • Note: May affect repository discovery")
            
            self.log(f"   ✅ {account_type} account connection successful")
            return True
            
        except requests.exceptions.Timeout:
            self.log(f"❌ {account_type} Connection Timeout:")
            self.log(f"   • Error: Request timed out after 30 seconds")
            self.log(f"   • Fix: Check internet connection and try again")
            return False
            
        except requests.exceptions.ConnectionError:
            self.log(f"❌ {account_type} Connection Error:")
            self.log(f"   • Error: Cannot connect to Bitbucket API")
            self.log(f"   • Fix: Check internet connection and firewall settings")
            return False
            
        except Exception as e:
            self.log(f"❌ {account_type} Unexpected Error:")
            self.log(f"   • Error: {str(e)}")
            self.log(f"   • Fix: Check configuration and try again")
            return False
    
    def _parse_workspaces(self, workspaces_str):
        """Parse comma-separated workspace list"""
        if not workspaces_str:
            return []
        return [ws.strip() for ws in workspaces_str.split(',') if ws.strip()]
    
    def _parse_workspace_mapping(self, mapping_str):
        """Parse workspace mapping string (source:dest,source2:dest2)"""
        if not mapping_str:
            return {}
        
        mapping = {}
        pairs = mapping_str.split(',')
        for pair in pairs:
            if ':' in pair:
                source, dest = pair.split(':', 1)
                mapping[source.strip()] = dest.strip()
        return mapping
    
    def get_workspace_pairs(self):
        """Get source:destination workspace pairs for migration"""
        pairs = []
        
        if not self.multi_workspace_mode:
            # Single workspace mode
            if self.source_workspace and self.dest_workspace:
                pairs.append((self.source_workspace, self.dest_workspace))
            return pairs
        
        # Multi-workspace mode
        if self.workspace_mapping:
            # Use explicit mapping
            for source_ws, dest_ws in self.workspace_mapping.items():
                pairs.append((source_ws, dest_ws))
        elif self.source_workspaces and self.dest_workspaces:
            # Map by position (1:1 mapping)
            for i, source_ws in enumerate(self.source_workspaces):
                if i < len(self.dest_workspaces):
                    dest_ws = self.dest_workspaces[i]
                else:
                    # Auto-generate destination workspace name
                    dest_ws = f"{self.workspace_name_prefix}{source_ws}"
                pairs.append((source_ws, dest_ws))
        elif self.source_workspaces:
            # Auto-generate destination names
            for source_ws in self.source_workspaces:
                dest_ws = f"{self.workspace_name_prefix}{source_ws}"
                pairs.append((source_ws, dest_ws))
        
        return pairs
    
    def get_all_workspaces_repositories(self):
        """Fetch repositories from all source workspaces"""
        all_repositories = {}
        workspace_pairs = self.get_workspace_pairs()
        
        self.log(f"🔍 Scanning {len(workspace_pairs)} workspace pairs for repositories...")
        
        for source_ws, dest_ws in workspace_pairs:
            self.log(f"📂 Scanning workspace: {source_ws}")
            try:
                repos = self.fetch_paginated_data_with_auth(f'repositories/{source_ws}', auth=self.source_auth)
                all_repositories[source_ws] = {
                    'repos': repos,
                    'dest_workspace': dest_ws,
                    'repo_count': len(repos)
                }
                self.log(f"   Found {len(repos)} repositories in {source_ws}")
            except Exception as e:
                self.log(f"❌ Error scanning workspace {source_ws}: {e}")
                all_repositories[source_ws] = {
                    'repos': [],
                    'dest_workspace': dest_ws, 
                    'repo_count': 0,
                    'error': str(e)
                }
        
        total_repos = sum(ws_data['repo_count'] for ws_data in all_repositories.values())
        self.log(f"📊 Total repositories found: {total_repos} across {len(workspace_pairs)} workspaces")
        
        return all_repositories
    
    def create_workspace_if_needed(self, workspace_name):
        """Create workspace in destination account if it doesn't exist"""
        if not self.create_missing_workspaces:
            return True
            
        self.log(f"🏗️  Checking if workspace '{workspace_name}' exists in destination...")
        
        try:
            # Check if workspace exists by trying to access it
            response = requests.get(
                f"{self.base_url}/workspaces/{workspace_name}",
                auth=self.dest_auth,
                headers=self.headers
            )
            
            if response.status_code == 200:
                self.log(f"✅ Workspace '{workspace_name}' already exists")
                return True
            elif response.status_code == 404:
                if self.skip_existing_workspaces:
                    self.log(f"⏭️  Workspace '{workspace_name}' doesn't exist but auto-creation disabled")
                    return False
                
                # Create new workspace
                self.log(f"🏗️  Creating workspace '{workspace_name}'...")
                workspace_data = {
                    "name": workspace_name,
                    "slug": workspace_name,
                    "is_private": True
                }
                
                create_response = requests.post(
                    f"{self.base_url}/workspaces",
                    auth=self.dest_auth,
                    headers=self.headers,
                    json=workspace_data
                )
                
                if create_response.status_code in [200, 201]:
                    self.log(f"✅ Successfully created workspace: {workspace_name}")
                    return True
                else:
                    self.log(f"❌ Failed to create workspace: {create_response.status_code}")
                    return False
            else:
                self.log(f"❌ Error checking workspace: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error with workspace operations: {e}")
            return False
    
    # ========== AUTO-DISCOVERY METHODS ==========
    
    def discover_all_workspaces(self):
        """Automatically discover all workspaces accessible to the source account"""
        self.log("🔍 Auto-discovering all accessible workspaces...")
        
        try:
            # Get all workspaces the authenticated user has access to
            workspaces_data = self.fetch_paginated_data('workspaces', {'role': 'member'})
            
            if not workspaces_data:
                self.log("❌ No workspaces found or API error")
                return []
            
            discovered_workspaces = []
            workspace_details = {}
            
            for workspace in workspaces_data:
                ws_slug = workspace.get('slug', '')
                ws_name = workspace.get('name', ws_slug)
                ws_uuid = workspace.get('uuid', '')
                
                # Get detailed workspace information
                workspace_info = {
                    'slug': ws_slug,
                    'name': ws_name,
                    'uuid': ws_uuid,
                    'is_private': workspace.get('is_private', True),
                    'type': workspace.get('type', 'workspace'),
                    'links': workspace.get('links', {}),
                    'permission': workspace.get('permission', 'unknown'),
                    'created_on': workspace.get('created_on', ''),
                }
                
                discovered_workspaces.append(ws_slug)
                workspace_details[ws_slug] = workspace_info
                
                self.log(f"   🏢 Found workspace: {ws_name} ({ws_slug}) - Permission: {workspace_info['permission']}")
            
            self.log(f"✅ Discovered {len(discovered_workspaces)} workspaces")
            
            # Store workspace details for later use
            self.discovered_workspace_details = workspace_details
            
            return discovered_workspaces
            
        except Exception as e:
            self.log(f"❌ Error discovering workspaces: {e}")
            return []
    
    def discover_all_repositories_in_workspaces(self, workspaces_list):
        """Discover all repositories across multiple workspaces"""
        self.log(f"🔍 Auto-discovering repositories in {len(workspaces_list)} workspaces...")
        
        all_repositories = {}
        total_repo_count = 0
        
        for workspace_slug in workspaces_list:
            try:
                self.log(f"   📂 Scanning workspace: {workspace_slug}")
                
                # Get all repositories in this workspace
                repos_data = self.fetch_paginated_data(f'repositories/{workspace_slug}')
                
                if repos_data:
                    workspace_repos = []
                    for repo in repos_data:
                        repo_info = {
                            'name': repo.get('name', ''),
                            'full_name': repo.get('full_name', ''),
                            'uuid': repo.get('uuid', ''),
                            'description': repo.get('description', ''),
                            'is_private': repo.get('is_private', True),
                            'scm': repo.get('scm', 'git'),
                            'language': repo.get('language', ''),
                            'size': repo.get('size', 0),
                            'has_issues': repo.get('has_issues', False),
                            'has_wiki': repo.get('has_wiki', False),
                            'created_on': repo.get('created_on', ''),
                            'updated_on': repo.get('updated_on', ''),
                            'links': repo.get('links', {}),
                            'workspace': workspace_slug,
                            'auto_discovered': True
                        }
                        workspace_repos.append(repo_info)
                    
                    all_repositories[workspace_slug] = {
                        'workspace_info': self.discovered_workspace_details.get(workspace_slug, {}),
                        'repositories': workspace_repos,
                        'repo_count': len(workspace_repos)
                    }
                    
                    total_repo_count += len(workspace_repos)
                    self.log(f"      📦 Found {len(workspace_repos)} repositories in {workspace_slug}")
                    
                    # Log a few example repos
                    for i, repo in enumerate(workspace_repos[:3]):
                        self.log(f"         - {repo['name']} ({repo['language']}) - {repo['scm']}")
                    if len(workspace_repos) > 3:
                        self.log(f"         ... and {len(workspace_repos) - 3} more repositories")
                else:
                    self.log(f"      📦 No repositories found in {workspace_slug}")
                    all_repositories[workspace_slug] = {
                        'workspace_info': self.discovered_workspace_details.get(workspace_slug, {}),
                        'repositories': [],
                        'repo_count': 0
                    }
                    
            except Exception as e:
                self.log(f"      ❌ Error scanning workspace {workspace_slug}: {e}")
                all_repositories[workspace_slug] = {
                    'workspace_info': self.discovered_workspace_details.get(workspace_slug, {}),
                    'repositories': [],
                    'repo_count': 0,
                    'error': str(e)
                }
        
        self.log(f"✅ Total discovery complete: {total_repo_count} repositories across {len(workspaces_list)} workspaces")
        return all_repositories
    
    def auto_discover_complete_structure(self):
        """Complete auto-discovery: find all workspaces and repositories"""
        self.log("🚀 Starting COMPLETE AUTO-DISCOVERY of Bitbucket structure...")
        
        # Step 1: Discover all workspaces
        discovered_workspaces = self.discover_all_workspaces()
        
        if not discovered_workspaces:
            self.log("❌ No workspaces discovered - cannot proceed with auto-discovery")
            return None
        
        # Step 2: Apply workspace filters if configured
        filtered_workspaces = self.apply_workspace_filters(discovered_workspaces)
        
        # Step 3: Discover all repositories in filtered workspaces
        complete_structure = self.discover_all_repositories_in_workspaces(filtered_workspaces)
        
        # Step 4: Generate discovery summary
        self.log_discovery_summary(complete_structure)
        
        return complete_structure
    
    def apply_workspace_filters(self, discovered_workspaces):
        """Apply filtering rules to discovered workspaces"""
        if not hasattr(self, 'workspace_filters') or not self.workspace_filters:
            self.log("   ℹ️  No workspace filters configured - using all discovered workspaces")
            return discovered_workspaces
        
        filtered = []
        for workspace in discovered_workspaces:
            # Check inclusion filters
            if self.workspace_include_patterns:
                include_match = any(pattern in workspace for pattern in self.workspace_include_patterns)
                if not include_match:
                    self.log(f"   ⏭️  Skipping {workspace} - doesn't match include patterns")
                    continue
            
            # Check exclusion filters
            if self.workspace_exclude_patterns:
                exclude_match = any(pattern in workspace for pattern in self.workspace_exclude_patterns)
                if exclude_match:
                    self.log(f"   ⏭️  Skipping {workspace} - matches exclude patterns")
                    continue
            
            filtered.append(workspace)
            self.log(f"   ✅ Including workspace: {workspace}")
        
        self.log(f"📋 Workspace filtering: {len(discovered_workspaces)} discovered → {len(filtered)} selected")
        return filtered
    
    def log_discovery_summary(self, complete_structure):
        """Log a comprehensive summary of what was discovered"""
        self.log("\n" + "="*60)
        self.log("📊 AUTO-DISCOVERY SUMMARY")
        self.log("="*60)
        
        total_workspaces = len(complete_structure)
        total_repos = sum(ws_data['repo_count'] for ws_data in complete_structure.values())
        
        self.log(f"🏢 Total Workspaces: {total_workspaces}")
        self.log(f"📦 Total Repositories: {total_repos}")
        
        for workspace, data in complete_structure.items():
            repo_count = data['repo_count']
            workspace_info = data.get('workspace_info', {})
            permission = workspace_info.get('permission', 'unknown')
            
            self.log(f"\n📂 {workspace} ({permission} access)")
            self.log(f"   📦 Repositories: {repo_count}")
            
            if repo_count > 0:
                # Show language breakdown
                languages = {}
                private_count = 0
                has_issues_count = 0
                has_wiki_count = 0
                
                for repo in data['repositories']:
                    lang = repo.get('language') or 'Unknown'
                    languages[lang] = languages.get(lang, 0) + 1
                    if repo.get('is_private'):
                        private_count += 1
                    if repo.get('has_issues'):
                        has_issues_count += 1
                    if repo.get('has_wiki'):
                        has_wiki_count += 1
                
                self.log(f"   🔒 Private repos: {private_count}/{repo_count}")
                self.log(f"   🎫 With issues: {has_issues_count}/{repo_count}")
                self.log(f"   📖 With wiki: {has_wiki_count}/{repo_count}")
                
                # Show top languages
                if languages:
                    sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:3]
                    lang_summary = ", ".join([f"{lang}: {count}" for lang, count in sorted_langs])
                    self.log(f"   💻 Languages: {lang_summary}")
        
        self.log("="*60)
        self.log(f"🎯 Ready to migrate {total_repos} repositories from {total_workspaces} workspaces")
        self.log("="*60 + "\n")
    
    def create_destination_workspace_structure(self, complete_structure):
        """Create the complete workspace structure in destination account"""
        self.log("🏗️  Creating destination workspace structure...")
        
        created_workspaces = []
        workspace_mapping = {}
        
        for source_workspace, data in complete_structure.items():
            # Determine destination workspace name
            dest_workspace = self.determine_destination_workspace_name(source_workspace)
            
            # Create workspace if needed
            if self.create_workspace_if_needed(dest_workspace):
                created_workspaces.append(dest_workspace)
                workspace_mapping[source_workspace] = dest_workspace
                self.log(f"   ✅ {source_workspace} → {dest_workspace}")
            else:
                self.log(f"   ❌ Failed to create workspace for: {source_workspace}")
        
        self.log(f"🏗️  Workspace creation complete: {len(created_workspaces)}/{len(complete_structure)} successful")
        return workspace_mapping
    
    def determine_destination_workspace_name(self, source_workspace):
        """Determine the destination workspace name with intelligent naming"""
        # Check explicit workspace mapping first
        if hasattr(self, 'workspace_mapping') and source_workspace in self.workspace_mapping:
            return self.workspace_mapping[source_workspace]
        
        # Apply workspace name prefix if configured
        if hasattr(self, 'workspace_name_prefix') and self.workspace_name_prefix:
            return f"{self.workspace_name_prefix}{source_workspace}"
        
        # Default: use same name (for same-account scenarios or when no prefix configured)
        return source_workspace
    
    def flatten_discovered_structure_to_repositories(self, complete_structure):
        """Flatten auto-discovered structure into a list of repositories for processing"""
        repositories = []
        
        for workspace_slug, workspace_data in complete_structure.items():
            workspace_repos = workspace_data.get('repositories', [])
            
            # Apply repository filters if configured
            filtered_repos = self.apply_repository_filters(workspace_repos, workspace_slug)
            
            for repo in filtered_repos:
                # Ensure repository has workspace information for migration
                repo['workspace'] = workspace_slug
                repo['auto_discovered'] = True
                
                # Set destination workspace if in migration mode
                if self.migration_mode and hasattr(self, 'discovered_workspace_mapping'):
                    repo['dest_workspace'] = self.discovered_workspace_mapping.get(workspace_slug, workspace_slug)
                
                repositories.append(repo)
        
        self.log(f"📋 Flattened structure: {len(repositories)} repositories selected for processing")
        return repositories
    
    def flatten_workspace_repositories(self, workspace_repositories):
        """Flatten multi-workspace repository structure for processing"""
        repositories = []
        for workspace, data in workspace_repositories.items():
            for repo in data.get('repositories', []):
                repo['workspace'] = workspace
                repositories.append(repo)
        return repositories
    
    def apply_repository_filters(self, repositories, workspace_slug):
        """Apply filtering rules to repositories within a workspace"""
        if not self.repo_include_patterns and not self.repo_exclude_patterns:
            return repositories
        
        filtered = []
        for repo in repositories:
            repo_name = repo.get('name', '')
            
            # Check inclusion filters
            if self.repo_include_patterns:
                include_match = any(pattern in repo_name for pattern in self.repo_include_patterns)
                if not include_match:
                    continue
            
            # Check exclusion filters  
            if self.repo_exclude_patterns:
                exclude_match = any(pattern in repo_name for pattern in self.repo_exclude_patterns)
                if exclude_match:
                    continue
            
            # Check max repos limit
            if len(filtered) >= self.auto_discovery_max_repos:
                self.log(f"⚠️ Reached max repository limit ({self.auto_discovery_max_repos}) in {workspace_slug}")
                break
                
            filtered.append(repo)
        
        if len(filtered) != len(repositories):
            self.log(f"   🔍 Repository filtering in {workspace_slug}: {len(repositories)} found → {len(filtered)} selected")
        
        return filtered

    def backup_repository_metadata(self, repo):
        """Backup comprehensive metadata for a single repository"""
        repo_name = repo['name']
        self.log(f"📝 Backing up comprehensive metadata for {repo_name}...")
        
        # Create repo-specific metadata directory
        repo_metadata_dir = os.path.join(self.metadata_dir, repo_name, self.timestamp)
        os.makedirs(repo_metadata_dir, exist_ok=True)
        
        metadata = {
            'repository_info': repo,
            'backup_timestamp': self.timestamp,
            'backup_type': 'comprehensive'
        }
        
        # Fetch pull requests
        try:
            prs = self.fetch_paginated_data(f'repositories/{self.bitbucket_workspace}/{repo_name}/pullrequests', 
                                          {'state': 'MERGED,OPEN,DECLINED,SUPERSEDED'})
            metadata['pull_requests'] = prs
            metadata['total_prs'] = len(prs)
            self.log(f"  - Fetched {len(prs)} pull requests")
        except Exception as e:
            self.log(f"Error fetching PRs for {repo_name}: {e}")
            metadata['pull_requests'] = []
        
        # Fetch issues
        try:
            issues = self.fetch_paginated_data(f'repositories/{self.bitbucket_workspace}/{repo_name}/issues')
            metadata['issues'] = issues
            metadata['total_issues'] = len(issues)
            self.log(f"  - Fetched {len(issues)} issues")
        except Exception as e:
            self.log(f"Error fetching issues for {repo_name}: {e}")
            metadata['issues'] = []
        
        # Fetch branches
        try:
            branches = self.fetch_paginated_data(f'repositories/{self.bitbucket_workspace}/{repo_name}/refs/branches')
            metadata['branches'] = branches
            metadata['total_branches'] = len(branches)
            self.log(f"  - Fetched {len(branches)} branches")
        except Exception as e:
            self.log(f"Error fetching branches for {repo_name}: {e}")
            metadata['branches'] = []
        
        # Fetch tags
        try:
            tags = self.fetch_paginated_data(f'repositories/{self.bitbucket_workspace}/{repo_name}/refs/tags')
            metadata['tags'] = tags
            metadata['total_tags'] = len(tags)
            self.log(f"  - Fetched {len(tags)} tags")
        except Exception as e:
            self.log(f"Error fetching tags for {repo_name}: {e}")
            metadata['tags'] = []
        
        # Fetch repository permissions
        try:
            permissions = self.fetch_repository_permissions(repo_name)
            metadata['permissions'] = permissions
            metadata['total_permissions'] = len(permissions)
            self.log(f"  - Fetched {len(permissions)} permission entries")
        except Exception as e:
            self.log(f"Error fetching permissions for {repo_name}: {e}")
            metadata['permissions'] = []
        
        # Fetch repository wiki (if exists)
        try:
            wiki_data = self.fetch_repository_wiki(repo_name)
            metadata['wiki'] = wiki_data
            metadata['wiki_pages_count'] = len(wiki_data.get('pages', [])) if wiki_data else 0
            self.log(f"  - Fetched wiki with {metadata['wiki_pages_count']} pages")
        except Exception as e:
            self.log(f"Error fetching wiki for {repo_name}: {e}")
            metadata['wiki'] = None
        
        # Fetch repository settings and configuration
        try:
            repo_settings = self.fetch_repository_settings(repo_name)
            metadata['repository_settings'] = repo_settings
            self.log(f"  - Fetched repository settings and configuration")
        except Exception as e:
            self.log(f"Error fetching settings for {repo_name}: {e}")
            metadata['repository_settings'] = {}
        
        # Fetch branch permissions/restrictions
        try:
            branch_restrictions = self.fetch_branch_restrictions(repo_name)
            metadata['branch_restrictions'] = branch_restrictions
            metadata['total_branch_restrictions'] = len(branch_restrictions)
            self.log(f"  - Fetched {len(branch_restrictions)} branch restrictions")
        except Exception as e:
            self.log(f"Error fetching branch restrictions for {repo_name}: {e}")
            metadata['branch_restrictions'] = []
        
        # Fetch webhooks
        try:
            webhooks = self.fetch_repository_webhooks(repo_name)
            metadata['webhooks'] = webhooks
            metadata['total_webhooks'] = len(webhooks)
            self.log(f"  - Fetched {len(webhooks)} webhooks")
        except Exception as e:
            self.log(f"Error fetching webhooks for {repo_name}: {e}")
            metadata['webhooks'] = []
        
        # Fetch deploy keys
        try:
            deploy_keys = self.fetch_deploy_keys(repo_name)
            metadata['deploy_keys'] = deploy_keys
            metadata['total_deploy_keys'] = len(deploy_keys)
            self.log(f"  - Fetched {len(deploy_keys)} deploy keys")
        except Exception as e:
            self.log(f"Error fetching deploy keys for {repo_name}: {e}")
            metadata['deploy_keys'] = []
        
        # Save metadata to JSON file
        metadata_file = os.path.join(repo_metadata_dir, 'metadata.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        return metadata_file
    
    def fetch_repository_permissions(self, repo_name):
        """Fetch repository access permissions"""
        permissions_data = []
        
        # Fetch repository privileges (user/team permissions)
        try:
            # Get repository privileges
            privileges = self.fetch_paginated_data(f'repositories/{self.bitbucket_workspace}/{repo_name}/permissions-config/users')
            for privilege in privileges:
                permissions_data.append({
                    'type': 'user_permission',
                    'user': privilege.get('user', {}),
                    'permission': privilege.get('permission', ''),
                    'type_detail': 'repository_access'
                })
            
            # Get team permissions
            team_privileges = self.fetch_paginated_data(f'repositories/{self.bitbucket_workspace}/{repo_name}/permissions-config/teams')
            for privilege in team_privileges:
                permissions_data.append({
                    'type': 'team_permission',
                    'team': privilege.get('team', {}),
                    'permission': privilege.get('permission', ''),
                    'type_detail': 'repository_access'
                })
                
        except Exception as e:
            self.log(f"Warning: Could not fetch detailed permissions: {e}")
            
        return permissions_data
    
    def fetch_repository_wiki(self, repo_name):
        """Fetch repository wiki content"""
        try:
            # Check if wiki exists and is enabled
            wiki_info = self.make_api_request(f'repositories/{self.bitbucket_workspace}/{repo_name}')
            
            if not wiki_info or not wiki_info.get('has_wiki', False):
                return None
            
            wiki_data = {
                'enabled': True,
                'pages': [],
                'wiki_info': {}
            }
            
            # Try to get wiki pages (this endpoint might not be available for all repos)
            try:
                wiki_pages = self.fetch_paginated_data(f'repositories/{self.bitbucket_workspace}/{repo_name}/wiki')
                
                for page in wiki_pages:
                    page_data = {
                        'title': page.get('title', ''),
                        'slug': page.get('slug', ''),
                        'content': page.get('content', ''),
                        'created_on': page.get('created_on', ''),
                        'updated_on': page.get('updated_on', ''),
                        'author': page.get('author', {})
                    }
                    wiki_data['pages'].append(page_data)
                    
            except Exception as e:
                # Wiki API might not be accessible or wiki might be empty
                self.log(f"Wiki exists but content not accessible via API: {e}")
                wiki_data['pages'] = []
                wiki_data['note'] = 'Wiki exists but content not accessible via API'
            
            return wiki_data
            
        except Exception as e:
            self.log(f"Error checking wiki status: {e}")
            return None
    
    def fetch_repository_settings(self, repo_name):
        """Fetch comprehensive repository settings"""
        settings = {}
        
        try:
            # Get main repository info (includes many settings)
            repo_info = self.make_api_request(f'repositories/{self.bitbucket_workspace}/{repo_name}')
            if repo_info:
                settings.update({
                    'is_private': repo_info.get('is_private', False),
                    'has_issues': repo_info.get('has_issues', False),
                    'has_wiki': repo_info.get('has_wiki', False),
                    'fork_policy': repo_info.get('fork_policy', ''),
                    'language': repo_info.get('language', ''),
                    'description': repo_info.get('description', ''),
                    'website': repo_info.get('website', ''),
                    'mainbranch': repo_info.get('mainbranch', {}),
                    'size': repo_info.get('size', 0),
                    'project': repo_info.get('project', {}),
                    'clone_links': repo_info.get('links', {}).get('clone', [])
                })
            
            # Get repository configuration
            try:
                repo_config = self.make_api_request(f'repositories/{self.bitbucket_workspace}/{repo_name}/src/HEAD/.gitignore')
                if repo_config:
                    settings['gitignore_exists'] = True
                else:
                    settings['gitignore_exists'] = False
            except:
                settings['gitignore_exists'] = False
            
            # Try to get branch model (Git Flow settings)
            try:
                branch_model = self.make_api_request(f'repositories/{self.bitbucket_workspace}/{repo_name}/branching-model')
                settings['branch_model'] = branch_model
            except:
                settings['branch_model'] = None
                
        except Exception as e:
            self.log(f"Error fetching repository settings: {e}")
        
        return settings
    
    def fetch_branch_restrictions(self, repo_name):
        """Fetch branch permissions and restrictions"""
        try:
            restrictions = self.fetch_paginated_data(f'repositories/{self.bitbucket_workspace}/{repo_name}/branch-restrictions')
            
            # Process and clean up restrictions data
            processed_restrictions = []
            for restriction in restrictions:
                processed_restriction = {
                    'id': restriction.get('id'),
                    'kind': restriction.get('kind', ''),
                    'pattern': restriction.get('pattern', ''),
                    'users': restriction.get('users', []),
                    'groups': restriction.get('groups', []),
                    'type': restriction.get('type', ''),
                    'value': restriction.get('value'),
                    'branch_match_kind': restriction.get('branch_match_kind', ''),
                    'branch_type': restriction.get('branch_type', '')
                }
                processed_restrictions.append(processed_restriction)
            
            return processed_restrictions
            
        except Exception as e:
            self.log(f"Error fetching branch restrictions: {e}")
            return []
    
    def fetch_repository_webhooks(self, repo_name):
        """Fetch repository webhooks"""
        try:
            webhooks = self.fetch_paginated_data(f'repositories/{self.bitbucket_workspace}/{repo_name}/hooks')
            
            # Process webhook data (remove sensitive info like secrets)
            processed_webhooks = []
            for webhook in webhooks:
                processed_webhook = {
                    'uuid': webhook.get('uuid', ''),
                    'url': webhook.get('url', ''),
                    'description': webhook.get('description', ''),
                    'subject_type': webhook.get('subject_type', ''),
                    'events': webhook.get('events', []),
                    'active': webhook.get('active', False),
                    'created_at': webhook.get('created_at', ''),
                    'updated_at': webhook.get('updated_at', '')
                    # Note: We intentionally omit webhook secrets for security
                }
                processed_webhooks.append(processed_webhook)
            
            return processed_webhooks
            
        except Exception as e:
            self.log(f"Error fetching webhooks: {e}")
            return []
    
    def fetch_deploy_keys(self, repo_name):
        """Fetch repository deploy keys"""
        try:
            deploy_keys = self.fetch_paginated_data(f'repositories/{self.bitbucket_workspace}/{repo_name}/deploy-keys')
            
            # Process deploy keys (remove private key data for security)
            processed_keys = []
            for key in deploy_keys:
                processed_key = {
                    'id': key.get('id'),
                    'key': key.get('key', '')[:50] + '...' if key.get('key') else '',  # Truncate for security
                    'label': key.get('label', ''),
                    'type': key.get('type', ''),
                    'created_on': key.get('created_on', ''),
                    'repository': key.get('repository', {}),
                    'owner': key.get('owner', {}),
                    'comment': key.get('comment', ''),
                    'last_used': key.get('last_used', '')
                }
                processed_keys.append(processed_key)
            
            return processed_keys
            
        except Exception as e:
            self.log(f"Error fetching deploy keys: {e}")
            return []
    
    def clone_repository(self, repo):
        """Clone repository to local storage"""
        repo_name = repo['name']
        clone_url = None
        
        # Find HTTPS clone URL
        for link in repo['links']['clone']:
            if link['name'] == 'https':
                clone_url = link['href']
                break
        
        if not clone_url:
            self.log(f"❌ No HTTPS clone URL found for {repo_name}")
            return None
        
        # Create repo directory with timestamp
        repo_dir = os.path.join(self.repos_dir, repo_name)
        timestamped_dir = os.path.join(repo_dir, self.timestamp)
        
        os.makedirs(timestamped_dir, exist_ok=True)
        
        self.log(f"📥 Cloning {repo_name}...")
        
        # Fix: Properly construct authenticated URL handling existing credentials
        # Remove any existing credentials and protocol, then add our credentials
        if '@' in clone_url:
            # URL already has credentials, extract just the domain part after @
            base_url = clone_url.split('@', 1)[1]  # Get everything after first @
        else:
            # URL has no credentials, just remove https://
            base_url = clone_url.replace('https://', '')
        
        # Use username instead of email for git authentication (emails have @ symbols)
        username = self.bitbucket_username if self.bitbucket_username else self.bitbucket_workspace
        auth_url = f'https://{username}:{self.bitbucket_api_token}@{base_url}'
        
        # Debug logging
        self.log(f"Debug - Original URL: {clone_url}")
        self.log(f"Debug - Base URL extracted: {base_url}")
        self.log(f"Debug - Using username: {username}")
        self.log(f"Debug - Final auth URL (masked): https://{username}:***@{base_url}")
        
        try:
            # Clone bare repository (more efficient for backups)
            mirror_result = subprocess.run([
                'git', 'clone', '--mirror', auth_url, f'{timestamped_dir}/repo.git'
            ], capture_output=True, text=True, timeout=1800)  # 30 min timeout
            
            if mirror_result.returncode != 0:
                self.log(f"❌ Mirror clone failed: {mirror_result.stderr}")
                return None
            
            # Create working copy (exclude large files for efficiency)
            work_result = subprocess.run([
                'git', 'clone', '--depth=1', auth_url, f'{timestamped_dir}/working'
            ], capture_output=True, text=True, timeout=600)  # 10 min timeout
            
            if work_result.returncode == 0:
                self.log(f"✅ Successfully cloned {repo_name}")
                return timestamped_dir
            else:
                self.log(f"⚠️  Mirror successful but working copy failed: {work_result.stderr}")
                return timestamped_dir  # Still return success for mirror
            
        except subprocess.TimeoutExpired:
            self.log(f"❌ Clone timeout for {repo_name}")
            return None
        except Exception as e:
            self.log(f"❌ Error cloning {repo_name}: {e}")
            return None
    
    def create_migrated_repository(self, repo, existing_dest_repos=None):
        """Create repository in DESTINATION workspace for migration"""
        repo_name = repo['name']
        
        # Determine target repository name
        if self.preserve_repo_names:
            target_name = repo_name
        else:
            target_name = f"{self.repo_name_prefix}{repo_name}"
        
        self.log(f"🔄 Creating repository in destination: {target_name}")
        
        # Check if repository already exists in destination
        if existing_dest_repos and target_name in existing_dest_repos:
            if self.skip_existing_repos:
                self.log(f"⏭️  Skipping {target_name} - already exists in destination")
                return existing_dest_repos[target_name]
            else:
                self.log(f"⚠️  Repository {target_name} already exists but SKIP_EXISTING_REPOS=false")
        
        # Copy repository settings from source
        repo_data = {
            "name": target_name,
            "description": repo.get('description', f"Migrated from {self.source_workspace}/{repo_name}"),
            "is_private": repo.get('is_private', True),
            "fork_policy": repo.get('fork_policy', 'no_public_forks'),
            "has_issues": repo.get('has_issues', True),
            "has_wiki": repo.get('has_wiki', True),
            "language": repo.get('language', ''),
            "website": repo.get('website', '')
        }
        
        try:
            # Create repository in destination workspace using destination auth
            response = requests.post(
                f"{self.base_url}/repositories/{self.dest_workspace}/{target_name}",
                auth=self.dest_auth,
                headers=self.headers,
                json=repo_data
            )
            response.raise_for_status()
            
            migrated_repo = response.json()
            self.log(f"✅ Created repository in destination: {target_name}")
            return migrated_repo
            
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Error creating repository {target_name} in destination: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                self.log(f"Response: {e.response.text}")
            return None
    
    def create_mirror_repository(self, repo):
        """Legacy method - now calls create_migrated_repository for compatibility"""
        return self.create_migrated_repository(repo)
    
    def push_to_destination(self, local_repo_path, dest_repo):
        """Push local repository to destination workspace"""
        if not local_repo_path or not dest_repo:
            return False
        
        dest_name = dest_repo['name']
        
        # Find HTTPS clone URL for destination
        clone_url = None
        for link in dest_repo['links']['clone']:
            if link['name'] == 'https':
                clone_url = link['href']
                break
        
        if not clone_url:
            self.log(f"❌ No HTTPS clone URL found for destination {dest_name}")
            return False
        
        # Extract base URL and use DESTINATION credentials
        if '@' in clone_url:
            base_url = clone_url.split('@', 1)[1]
        else:
            base_url = clone_url.replace('https://', '')
        
        # Use DESTINATION account credentials for push
        dest_username = self.dest_username if self.dest_username else self.dest_workspace
        auth_url = f'https://{dest_username}:{self.dest_api_token}@{base_url}'
        
        try:
            mirror_git_dir = os.path.join(local_repo_path, 'repo.git')
            
            if os.path.exists(mirror_git_dir):
                self.log(f"� Migrating to destination: {dest_name}")
                
                # Add destination remote
                subprocess.run([
                    'git', '-C', mirror_git_dir, 'remote', 'add', 'destination', auth_url
                ], capture_output=True)
                
                # Push with extended timeout for large repositories
                push_result = subprocess.run([
                    'git', '-C', mirror_git_dir, 'push', '--mirror', 'destination'
                ], capture_output=True, text=True, timeout=self.push_timeout)
                
                if push_result.returncode == 0:
                    self.log(f"✅ Successfully migrated to destination: {dest_name}")
                    return True
                else:
                    self.log(f"❌ Migration failed: {push_result.stderr}")
                    # Try regular push if mirror push fails
                    self.log(f"🔄 Trying regular push...")
                    push_result = subprocess.run([
                        'git', '-C', mirror_git_dir, 'push', 'destination', '--all'
                    ], capture_output=True, text=True, timeout=self.push_timeout)
                    
                    if push_result.returncode == 0:
                        # Also push tags
                        subprocess.run([
                            'git', '-C', mirror_git_dir, 'push', 'destination', '--tags'
                        ], capture_output=True, text=True, timeout=600)
                        self.log(f"✅ Successfully migrated (regular push): {dest_name}")
                        return True
                    return False
            else:
                self.log(f"❌ Repository directory not found: {mirror_git_dir}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log(f"❌ Push timeout for {dest_name} (timeout: {self.push_timeout}s)")
            return False
        except Exception as e:
            self.log(f"❌ Error migrating to {dest_name}: {e}")
            return False
    
    def push_to_mirror(self, local_repo_path, mirror_repo):
        """Legacy method - now calls push_to_destination for compatibility"""
        return self.push_to_destination(local_repo_path, mirror_repo)
    
    # ========== METADATA RESTORATION METHODS ==========
    
    def restore_repository_metadata(self, repo_name, metadata_path, dest_repo_name=None):
        """Restore all collaboration data (issues, PRs, wikis, etc.) to destination repository"""
        if not dest_repo_name:
            dest_repo_name = repo_name
            
        self.log(f"🔄 Restoring collaboration data for {dest_repo_name}...")
        
        # Load backed up metadata
        if not os.path.exists(metadata_path):
            self.log(f"❌ Metadata file not found: {metadata_path}")
            return False
            
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception as e:
            self.log(f"❌ Error loading metadata: {e}")
            return False
        
        restoration_results = {
            'issues': 0,
            'pull_requests': 0, 
            'wiki_pages': 0,
            'permissions': 0,
            'branch_restrictions': 0,
            'webhooks': 0,
            'deploy_keys': 0,
            'errors': []
        }
        
        # Restore issues
        if self.restore_metadata_issues and metadata.get('issues'):
            restoration_results['issues'] = self.restore_issues(dest_repo_name, metadata['issues'])
        
        # Restore pull requests
        if self.restore_metadata_prs and metadata.get('pull_requests'):
            restoration_results['pull_requests'] = self.restore_pull_requests(dest_repo_name, metadata['pull_requests'])
        
        # Restore wiki
        if self.restore_metadata_wiki and metadata.get('wiki'):
            restoration_results['wiki_pages'] = self.restore_wiki(dest_repo_name, metadata['wiki'])
        
        # Restore repository permissions
        if self.restore_metadata_permissions and metadata.get('permissions'):
            restoration_results['permissions'] = self.restore_permissions(dest_repo_name, metadata['permissions'])
        
        # Restore branch restrictions
        if self.restore_metadata_restrictions and metadata.get('branch_restrictions'):
            restoration_results['branch_restrictions'] = self.restore_branch_restrictions(dest_repo_name, metadata['branch_restrictions'])
        
        # Restore webhooks
        if self.restore_metadata_webhooks and metadata.get('webhooks'):
            restoration_results['webhooks'] = self.restore_webhooks(dest_repo_name, metadata['webhooks'])
        
        # Restore deploy keys  
        if self.restore_metadata_deploy_keys and metadata.get('deploy_keys'):
            restoration_results['deploy_keys'] = self.restore_deploy_keys(dest_repo_name, metadata['deploy_keys'])
        
        # Log results
        total_restored = sum([restoration_results[key] for key in restoration_results if key != 'errors'])
        self.log(f"✅ Restored {total_restored} collaboration items for {dest_repo_name}")
        for key, count in restoration_results.items():
            if key != 'errors' and count > 0:
                self.log(f"   - {key.replace('_', ' ').title()}: {count}")
        
        if restoration_results['errors']:
            self.log(f"⚠️ {len(restoration_results['errors'])} restoration errors occurred")
            
        return restoration_results
    
    def restore_issues(self, repo_name, issues_data):
        """Restore issues to destination repository"""
        self.log(f"🎫 Restoring {len(issues_data)} issues to {repo_name}...")
        restored_count = 0
        
        for issue in issues_data:
            try:
                # Map users if needed (source account users might not exist in destination)
                mapped_assignee = self.map_user_account(issue.get('assignee'))
                mapped_reporter = self.map_user_account(issue.get('reporter'))
                
                issue_data = {
                    'title': issue.get('title', 'Migrated Issue'),
                    'content': {
                        'raw': self.format_migrated_content(
                            issue.get('content', {}).get('raw', ''),
                            'issue',
                            issue.get('reporter', {}),
                            issue.get('created_on')
                        )
                    },
                    'kind': issue.get('kind', 'bug'),
                    'priority': issue.get('priority', 'minor'),
                    'state': 'new' if issue.get('state') in ['new', 'open'] else 'resolved',
                    'assignee': mapped_assignee
                }
                
                # Create issue via API
                response = self.make_api_request(
                    f'repositories/{self.dest_workspace}/{repo_name}/issues',
                    method='POST',
                    data=issue_data
                )
                
                if response:
                    new_issue_id = response.get('id')
                    self.log(f"   ✅ Created issue: {issue.get('title', 'Untitled')} (ID: {new_issue_id})")
                    
                    # Restore comments
                    if issue.get('comments'):
                        self.restore_issue_comments(repo_name, new_issue_id, issue['comments'])
                    
                    restored_count += 1
                else:
                    self.log(f"   ❌ Failed to create issue: {issue.get('title', 'Untitled')}")
                    
            except Exception as e:
                self.log(f"   ❌ Error restoring issue '{issue.get('title', 'Unknown')}': {e}")
        
        return restored_count
    
    def restore_issue_comments(self, repo_name, issue_id, comments_data):
        """Restore comments for an issue"""
        if not comments_data:
            return
            
        for comment in comments_data:
            try:
                mapped_author = self.map_user_account(comment.get('user'))
                
                comment_data = {
                    'content': {
                        'raw': self.format_migrated_content(
                            comment.get('content', {}).get('raw', ''),
                            'comment',
                            comment.get('user', {}),
                            comment.get('created_on')
                        )
                    }
                }
                
                response = self.make_api_request(
                    f'repositories/{self.dest_workspace}/{repo_name}/issues/{issue_id}/comments',
                    method='POST',
                    data=comment_data
                )
                
                if response:
                    self.log(f"     💬 Restored comment from {comment.get('user', {}).get('display_name', 'Unknown')}")
                    
            except Exception as e:
                self.log(f"     ❌ Error restoring comment: {e}")
    
    def restore_pull_requests(self, repo_name, prs_data):
        """Restore pull requests to destination repository (as documentation)"""
        self.log(f"🔀 Documenting {len(prs_data)} pull requests for {repo_name}...")
        
        # Note: We can't actually recreate PRs with the same branch structure,
        # but we can create comprehensive documentation
        
        try:
            # Create a PR documentation wiki page or issue
            pr_documentation = self.generate_pr_documentation(prs_data)
            
            # Create as wiki page if possible, otherwise as an issue
            wiki_created = self.create_pr_documentation_wiki(repo_name, pr_documentation)
            
            if not wiki_created:
                # Create as an issue for documentation
                self.create_pr_documentation_issue(repo_name, pr_documentation)
            
            return len(prs_data)
            
        except Exception as e:
            self.log(f"❌ Error creating PR documentation: {e}")
            return 0
    
    def restore_wiki(self, repo_name, wiki_data):
        """Restore wiki pages to destination repository"""
        if not wiki_data or not wiki_data.get('pages'):
            return 0
            
        self.log(f"📖 Restoring {len(wiki_data['pages'])} wiki pages to {repo_name}...")
        restored_count = 0
        
        # First, enable wiki if not enabled
        try:
            self.enable_repository_wiki(repo_name)
        except Exception as e:
            self.log(f"⚠️ Could not enable wiki: {e}")
        
        for page in wiki_data['pages']:
            try:
                page_data = {
                    'title': page.get('title', 'Migrated Page'),
                    'content': {
                        'raw': self.format_migrated_content(
                            page.get('content', ''),
                            'wiki',
                            page.get('author', {}),
                            page.get('updated_on')
                        )
                    }
                }
                
                # Create wiki page
                response = self.make_api_request(
                    f'repositories/{self.dest_workspace}/{repo_name}/wiki/{page.get("slug", page.get("title", "migrated-page"))}',
                    method='PUT',
                    data=page_data
                )
                
                if response:
                    self.log(f"   📄 Restored wiki page: {page.get('title', 'Untitled')}")
                    restored_count += 1
                else:
                    self.log(f"   ❌ Failed to restore wiki page: {page.get('title', 'Untitled')}")
                    
            except Exception as e:
                self.log(f"   ❌ Error restoring wiki page '{page.get('title', 'Unknown')}': {e}")
        
        return restored_count
    
    def restore_permissions(self, repo_name, permissions_data):
        """Restore repository permissions (with user mapping)"""
        self.log(f"🔐 Restoring permissions for {repo_name}...")
        restored_count = 0
        
        for permission in permissions_data:
            try:
                if permission.get('type') == 'user_permission':
                    user = permission.get('user', {})
                    mapped_user = self.map_user_account(user)
                    
                    if mapped_user:
                        permission_data = {
                            'permission': permission.get('permission', 'read')
                        }
                        
                        response = self.make_api_request(
                            f'repositories/{self.dest_workspace}/{repo_name}/permissions/{mapped_user["username"]}',
                            method='PUT',
                            data=permission_data
                        )
                        
                        if response:
                            self.log(f"   👤 Restored permission for {mapped_user['username']}: {permission.get('permission')}")
                            restored_count += 1
                            
            except Exception as e:
                self.log(f"   ❌ Error restoring permission: {e}")
        
        return restored_count
    
    def restore_branch_restrictions(self, repo_name, restrictions_data):
        """Restore branch protection rules"""
        self.log(f"🛡️ Restoring branch restrictions for {repo_name}...")
        restored_count = 0
        
        for restriction in restrictions_data:
            try:
                restriction_data = {
                    'kind': restriction.get('kind', 'push'),
                    'pattern': restriction.get('pattern', 'master'),
                    'users': [],  # Will need to map users
                    'groups': []  # Will need to map groups
                }
                
                response = self.make_api_request(
                    f'repositories/{self.dest_workspace}/{repo_name}/branch-restrictions',
                    method='POST',
                    data=restriction_data
                )
                
                if response:
                    self.log(f"   🛡️ Restored branch restriction: {restriction.get('pattern', 'Unknown')}")
                    restored_count += 1
                    
            except Exception as e:
                self.log(f"   ❌ Error restoring branch restriction: {e}")
        
        return restored_count
    
    def restore_webhooks(self, repo_name, webhooks_data):
        """Restore repository webhooks"""
        self.log(f"🪝 Restoring webhooks for {repo_name}...")
        restored_count = 0
        
        for webhook in webhooks_data:
            try:
                webhook_data = {
                    'description': f"Migrated: {webhook.get('description', 'Webhook')}",
                    'url': webhook.get('url', ''),
                    'active': webhook.get('active', True),
                    'events': webhook.get('events', ['repo:push'])
                }
                
                # Only create if URL is provided and valid
                if webhook_data['url']:
                    response = self.make_api_request(
                        f'repositories/{self.dest_workspace}/{repo_name}/hooks',
                        method='POST',
                        data=webhook_data
                    )
                    
                    if response:
                        self.log(f"   🪝 Restored webhook: {webhook.get('description', 'Unknown')}")
                        restored_count += 1
                        
            except Exception as e:
                self.log(f"   ❌ Error restoring webhook: {e}")
        
        return restored_count
    
    def restore_deploy_keys(self, repo_name, deploy_keys_data):
        """Restore deploy keys (public keys only for security)"""
        self.log(f"🔑 Documenting deploy keys for {repo_name} (keys must be manually added)...")
        
        try:
            # Create documentation issue for deploy keys since we can't restore private keys
            deploy_key_doc = self.generate_deploy_key_documentation(deploy_keys_data)
            
            issue_data = {
                'title': '[MIGRATION] Deploy Keys Documentation',
                'content': {'raw': deploy_key_doc},
                'kind': 'task',
                'priority': 'major'
            }
            
            response = self.make_api_request(
                f'repositories/{self.dest_workspace}/{repo_name}/issues',
                method='POST', 
                data=issue_data
            )
            
            if response:
                self.log(f"   📝 Created deploy keys documentation issue")
                return 1
                
        except Exception as e:
            self.log(f"   ❌ Error creating deploy keys documentation: {e}")
        
        return 0
    
    # ========== HELPER METHODS FOR RESTORATION ==========
    
    def format_migrated_content(self, original_content, content_type, original_author, created_date):
        """Format content with migration information"""
        migration_header = f"""
---
**🔄 MIGRATED CONTENT**
- **Original Author:** {original_author.get('display_name', 'Unknown')} (@{original_author.get('username', 'unknown')})
- **Original Date:** {created_date}
- **Migration Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Type:** {content_type.title()}
---

"""
        return migration_header + (original_content or '')
    
    def map_user_account(self, user_info):
        """Map source account users to destination account users"""
        if not user_info:
            return None
            
        # Try to find user mapping in configuration
        username = user_info.get('username', '')
        
        # Check if we have a user mapping configuration
        user_mapping = getattr(self, 'user_mapping', {})
        if username in user_mapping:
            return {'username': user_mapping[username]}
            
        # For now, return None if no mapping found
        # Users will need to be manually assigned after migration
        return None
    
    def generate_pr_documentation(self, prs_data):
        """Generate comprehensive PR documentation"""
        doc_content = f"""# Pull Requests Documentation

**Repository migrated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total PRs:** {len(prs_data)}

---

"""
        
        for pr in prs_data:
            doc_content += f"""
## PR #{pr.get('id', 'Unknown')} - {pr.get('title', 'Untitled')}

- **Author:** {pr.get('author', {}).get('display_name', 'Unknown')}
- **State:** {pr.get('state', 'Unknown')}
- **Created:** {pr.get('created_on', 'Unknown')}
- **Updated:** {pr.get('updated_on', 'Unknown')}
- **Source Branch:** {pr.get('source', {}).get('branch', {}).get('name', 'Unknown')}
- **Destination Branch:** {pr.get('destination', {}).get('branch', {}).get('name', 'Unknown')}

### Description
{pr.get('description', 'No description provided')}

### Comments
"""
            
            if pr.get('comments'):
                for comment in pr['comments']:
                    doc_content += f"""
**{comment.get('user', {}).get('display_name', 'Unknown')}** - {comment.get('created_on', '')}
{comment.get('content', {}).get('raw', '')}

"""
            else:
                doc_content += "No comments\n"
                
            doc_content += "\n---\n"
        
        return doc_content
    
    def generate_deploy_key_documentation(self, deploy_keys_data):
        """Generate deploy key documentation"""
        doc_content = f"""# Deploy Keys Documentation

**Repository migrated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Deploy Keys:** {len(deploy_keys_data)}

⚠️ **IMPORTANT:** Deploy keys contain private information and must be manually recreated.

---

"""
        
        for key in deploy_keys_data:
            doc_content += f"""
## Deploy Key: {key.get('label', 'Unlabeled')}

- **Label:** {key.get('label', 'N/A')}
- **Read Only:** {key.get('read_only', True)}
- **Created:** {key.get('created_on', 'Unknown')}
- **Last Used:** {key.get('last_used', 'Never')}

**Public Key Fingerprint:** {key.get('public_key_fingerprint', 'Not available')}

**Action Required:** Manually add the corresponding private key to this repository's deploy keys section.

---

"""
        
        return doc_content
    
    def enable_repository_wiki(self, repo_name):
        """Enable wiki for repository"""
        try:
            repo_data = {'has_wiki': True}
            response = self.make_api_request(
                f'repositories/{self.dest_workspace}/{repo_name}',
                method='PUT',
                data=repo_data
            )
            return response is not None
        except Exception:
            return False
    
    def create_pr_documentation_wiki(self, repo_name, content):
        """Create PR documentation as wiki page"""
        try:
            page_data = {
                'title': 'Pull Requests Migration Documentation',
                'content': {'raw': content}
            }
            
            response = self.make_api_request(
                f'repositories/{self.dest_workspace}/{repo_name}/wiki/pull-requests-migration',
                method='PUT',
                data=page_data
            )
            
            return response is not None
        except Exception:
            return False
    
    def create_pr_documentation_issue(self, repo_name, content):
        """Create PR documentation as issue"""
        try:
            issue_data = {
                'title': '[MIGRATION] Pull Requests Documentation',
                'content': {'raw': content},
                'kind': 'task',
                'priority': 'major'
            }
            
            response = self.make_api_request(
                f'repositories/{self.dest_workspace}/{repo_name}/issues',
                method='POST',
                data=issue_data
            )
            
            return response is not None
        except Exception:
            return False

    def create_compressed_backup(self, repo_name, repo_path, metadata_path, repo=None):
        """Create tar.gz backup for repository with comprehensive naming"""
        repo_backup_dir = os.path.join(self.repos_dir, repo_name)
        
        # Get current timestamp with more precision
        current_time = datetime.now()
        detailed_timestamp = current_time.strftime('%Y-%m-%d_%H-%M-%S')
        
        # Extract metadata information for filename
        metadata_count = 0
        repo_size_mb = 0
        
        if metadata_path and os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    metadata_count = (
                        metadata.get('total_prs', 0) +
                        metadata.get('total_issues', 0) +
                        metadata.get('total_branches', 0) +
                        metadata.get('total_tags', 0) +
                        metadata.get('total_permissions', 0) +
                        metadata.get('total_webhooks', 0) +
                        metadata.get('total_deploy_keys', 0) +
                        metadata.get('total_branch_restrictions', 0)
                    )
            except Exception as e:
                self.log(f"⚠️ Could not read metadata for filename: {e}")
        
        # Get repository size if available
        if repo_path and os.path.exists(repo_path):
            try:
                # Calculate directory size
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(repo_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        if os.path.exists(filepath):
                            total_size += os.path.getsize(filepath)
                repo_size_mb = round(total_size / (1024 * 1024), 1)
            except Exception:
                pass
        
        # Get workspace info - try to use current workspace or derive from repo
        workspace_name = "unknown"
        if hasattr(self, 'source_workspace') and self.source_workspace:
            workspace_name = self.source_workspace
        elif hasattr(self, 'workspace') and self.workspace:
            workspace_name = self.workspace
        elif repo and isinstance(repo, dict) and 'full_name' in repo:
            # Extract workspace from full_name (workspace/repo-name)
            workspace_name = repo['full_name'].split('/')[0]
        
        # Create comprehensive filename
        # Format: WORKSPACE_REPO-NAME_YYYY-MM-DD_HH-MM-SS_METADATA-COUNT_SIZE-MB.tar.gz
        size_str = f"{repo_size_mb}MB" if repo_size_mb > 0 else "unknown"
        backup_filename = f"{workspace_name}_{repo_name}_{detailed_timestamp}_meta{metadata_count}_{size_str}.tar.gz"
        backup_filepath = os.path.join(repo_backup_dir, backup_filename)
        
        self.log(f"📦 Creating comprehensive backup: {backup_filename}")
        self.log(f"   📊 Metadata items: {metadata_count}")
        self.log(f"   💾 Repository size: {size_str}")
        
        try:
            with tarfile.open(backup_filepath, 'w:gz') as tar:
                # Add repository files with clear naming
                if os.path.exists(repo_path):
                    tar.add(repo_path, arcname=f"repository-{repo_name}")
                
                # Add metadata file with clear naming
                if os.path.exists(metadata_path):
                    tar.add(metadata_path, arcname=f"metadata-{repo_name}.json")
                
                # Create a backup info file for easy identification
                backup_info = {
                    "backup_created": current_time.isoformat(),
                    "repository_name": repo_name,
                    "workspace": workspace_name,
                    "metadata_items": metadata_count,
                    "repository_size_mb": repo_size_mb,
                    "backup_filename": backup_filename,
                    "backup_system_version": "BitbucketMigrationSystem v1.0",
                    "migration_mode": getattr(self, 'migration_mode', False),
                    "multi_workspace_mode": getattr(self, 'multi_workspace_mode', False)
                }
                
                # Write backup info to temp file and add to archive
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_info:
                    json.dump(backup_info, temp_info, indent=2)
                    temp_info_path = temp_info.name
                
                tar.add(temp_info_path, arcname="backup-info.json")
                os.unlink(temp_info_path)  # Clean up temp file
            
            self.log(f"✅ Created comprehensive backup: {backup_filepath}")
            return backup_filepath
            
        except Exception as e:
            self.log(f"❌ Error creating compressed backup: {e}")
            return None
    
    def cleanup_old_backups(self, repo_name):
        """Remove old backups keeping only the specified number"""
        repo_backup_dir = os.path.join(self.repos_dir, repo_name)
        
        if not os.path.exists(repo_backup_dir):
            return
        
        # Get all backup files (both old and new format)
        backup_files = []
        for f in os.listdir(repo_backup_dir):
            if f.endswith('.tar.gz'):
                file_path = os.path.join(repo_backup_dir, f)
                # Get file modification time for better sorting
                mod_time = os.path.getmtime(file_path)
                backup_files.append((f, mod_time))
        
        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x[1], reverse=True)
        
        self.log(f"🧹 Found {len(backup_files)} backup files for {repo_name}")
        if len(backup_files) <= self.max_backups:
            self.log(f"   ✅ All {len(backup_files)} backups will be retained (max: {self.max_backups})")
            return
        
        # Remove old backups
        files_to_remove = backup_files[self.max_backups:]
        self.log(f"   🗑️  Will remove {len(files_to_remove)} old backups (keeping newest {self.max_backups})")
        
        for file_to_remove, _ in files_to_remove:
            file_path = os.path.join(repo_backup_dir, file_to_remove)
            try:
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                size_mb = round(file_size / (1024 * 1024), 1)
                self.log(f"      🗑️  Removed: {file_to_remove} ({size_mb} MB)")
            except Exception as e:
                self.log(f"      ❌ Error removing {file_to_remove}: {e}")
        
        # Also cleanup old timestamped directories
        timestamped_dirs = []
        for d in os.listdir(repo_backup_dir):
            dir_path = os.path.join(repo_backup_dir, d)
            if os.path.isdir(dir_path) and d != '.git':
                mod_time = os.path.getmtime(dir_path)
                timestamped_dirs.append((d, mod_time))
        
        # Sort by modification time (newest first)
        timestamped_dirs.sort(key=lambda x: x[1], reverse=True)
        
        if len(timestamped_dirs) > self.max_backups:
            dirs_to_remove = timestamped_dirs[self.max_backups:]
            self.log(f"   🗑️  Removing {len(dirs_to_remove)} old backup directories")
            
            for dir_to_remove, _ in dirs_to_remove:
                dir_path = os.path.join(repo_backup_dir, dir_to_remove)
                try:
                    shutil.rmtree(dir_path)
                    self.log(f"      🗑️  Removed directory: {dir_to_remove}")
                except Exception as e:
                    self.log(f"      ❌ Error removing directory {dir_to_remove}: {e}")
    
    def send_email_notification(self, success=True):
        """Send email notification with backup report"""
        if not self.email_enabled or not self.notification_email:
            self.log("📧 Email notifications disabled or no recipient configured")
            return
        
        try:
            # Calculate statistics
            duration = self.backup_stats['end_time'] - self.backup_stats['start_time']
            success_rate = (self.backup_stats['successful_repos'] / max(self.backup_stats['total_repos'], 1)) * 100
            
            # Email subject
            status = "✅ SUCCESS" if success else "❌ FAILED"
            subject = f"Bitbucket Backup Report {status} - {self.timestamp}"
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_from
            msg['To'] = self.notification_email
            
            # Create HTML email body
            html_body = self.create_email_html_body(success, duration, success_rate)
            
            # Create plain text version
            text_body = self.create_email_text_body(success, duration, success_rate)
            
            # Attach both versions
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Attach log file if exists
            log_file = os.path.join(self.logs_dir, f'backup_{self.timestamp}.log')
            if os.path.exists(log_file):
                with open(log_file, 'rb') as f:
                    attachment = MIMEBase('application', 'octet-stream')
                    attachment.set_payload(f.read())
                    encoders.encode_base64(attachment)
                    attachment.add_header(
                        'Content-Disposition',
                        f'attachment; filename="backup_{self.timestamp}.log"'
                    )
                    msg.attach(attachment)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_username, self.email_password)
            
            text = msg.as_string()
            server.sendmail(self.email_from, self.notification_email, text)
            server.quit()
            
            self.log(f"📧 ✅ Email notification sent to {self.notification_email}")
            
        except Exception as e:
            self.log(f"📧 ❌ Failed to send email notification: {e}")
    
    def create_email_html_body(self, success, duration, success_rate):
        """Create HTML email body with backup report"""
        status_color = "#28a745" if success else "#dc3545"
        status_text = "SUCCESS" if success else "FAILED"
        
        # Repository details table
        repo_rows = ""
        for repo in self.backup_stats['repo_details']:
            status_icon = "✅" if repo['success'] else "❌"
            repo_rows += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{repo['name']}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{status_icon}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{repo.get('size', 'N/A')}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{repo.get('metadata_items', 'N/A')}</td>
            </tr>
            """
        
        # Error details
        error_section = ""
        if self.backup_stats['errors']:
            error_list = "\n".join([f"<li>{error}</li>" for error in self.backup_stats['errors'][:10]])  # Limit to 10 errors
            error_section = f"""
            <div style="margin: 20px 0; padding: 15px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px;">
                <h3 style="color: #721c24; margin-top: 0;">Errors Encountered:</h3>
                <ul style="margin: 0;">
                    {error_list}
                </ul>
                {f'<p><strong>... and {len(self.backup_stats["errors"]) - 10} more errors</strong></p>' if len(self.backup_stats['errors']) > 10 else ''}
            </div>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Bitbucket Backup Report</title>
        </head>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h1 style="color: {status_color}; text-align: center; margin-bottom: 30px;">
                    🔄 Bitbucket Backup Report - {status_text}
                </h1>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 4px; margin-bottom: 20px;">
                    <h2 style="margin-top: 0; color: #495057;">📊 Summary Statistics</h2>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div><strong>Backup Date:</strong> {self.backup_stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}</div>
                        <div><strong>Duration:</strong> {str(duration).split('.')[0]}</div>
                        <div><strong>Total Repositories:</strong> {self.backup_stats['total_repos']}</div>
                        <div><strong>Successful:</strong> {self.backup_stats['successful_repos']}</div>
                        <div><strong>Failed:</strong> {self.backup_stats['failed_repos']}</div>
                        <div><strong>Success Rate:</strong> {success_rate:.1f}%</div>
                    </div>
                </div>
                
                <div style="margin: 20px 0;">
                    <h2 style="color: #495057;">📁 Repository Details</h2>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                        <thead>
                            <tr style="background-color: #e9ecef;">
                                <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">Repository</th>
                                <th style="padding: 12px; border: 1px solid #ddd; text-align: center;">Status</th>
                                <th style="padding: 12px; border: 1px solid #ddd; text-align: right;">Size</th>
                                <th style="padding: 12px; border: 1px solid #ddd; text-align: center;">Metadata Items</th>
                            </tr>
                        </thead>
                        <tbody>
                            {repo_rows}
                        </tbody>
                    </table>
                </div>
                
                {error_section}
                
                <div style="margin-top: 30px; padding: 15px; background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 4px;">
                    <h3 style="color: #0c5460; margin-top: 0;">💾 Backup Configuration</h3>
                    <ul style="margin: 0;">
                        <li><strong>Workspace:</strong> {self.bitbucket_workspace}</li>
                        <li><strong>Backup Location:</strong> {self.backup_base_dir}</li>
                        <li><strong>Mirror Workspace:</strong> {self.backup_workspace}</li>
                        <li><strong>Retention:</strong> {self.max_backups} backups per repository</li>
                    </ul>
                </div>
                
                <div style="margin-top: 20px; text-align: center; color: #6c757d; font-size: 12px;">
                    <p>Generated by Bitbucket Backup System on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def create_email_text_body(self, success, duration, success_rate):
        """Create plain text email body with backup report"""
        status_text = "SUCCESS" if success else "FAILED"
        
        # Repository details
        repo_details = "\n".join([
            f"  - {repo['name']}: {'✅ Success' if repo['success'] else '❌ Failed'} ({repo.get('size', 'N/A')})"
            for repo in self.backup_stats['repo_details']
        ])
        
        # Error details
        error_section = ""
        if self.backup_stats['errors']:
            error_list = "\n".join([f"  - {error}" for error in self.backup_stats['errors'][:10]])
            error_section = f"""

Errors Encountered:
{error_list}
{f'... and {len(self.backup_stats["errors"]) - 10} more errors' if len(self.backup_stats['errors']) > 10 else ''}
"""
        
        text = f"""
Bitbucket Backup Report - {status_text}
{'=' * 50}

Summary Statistics:
- Backup Date: {self.backup_stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
- Duration: {str(duration).split('.')[0]}
- Total Repositories: {self.backup_stats['total_repos']}
- Successful: {self.backup_stats['successful_repos']}
- Failed: {self.backup_stats['failed_repos']}
- Success Rate: {success_rate:.1f}%

Repository Details:
{repo_details}
{error_section}

Backup Configuration:
- Workspace: {self.bitbucket_workspace}
- Backup Location: {self.backup_base_dir}
- Mirror Workspace: {self.backup_workspace}
- Retention: {self.max_backups} backups per repository

Generated by Bitbucket Backup System on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return text
    
    def backup_all_repositories(self):
        """Main function to backup and migrate all repositories"""
        if self.auto_discover_all:
            self.log("🚀 Starting Bitbucket AUTO-DISCOVERY MIGRATION process...")
            self.log("🔍 Will automatically discover ALL workspaces and repositories")
            self.log(f"📤 SOURCE ACCOUNT: {self.source_email}")
            if self.migration_mode:
                self.log(f"📥 DESTINATION ACCOUNT: {self.dest_email}")
            if self.workspace_include_patterns:
                self.log(f"   🎯 Include patterns: {', '.join(self.workspace_include_patterns)}")
            if self.workspace_exclude_patterns:
                self.log(f"   🚫 Exclude patterns: {', '.join(self.workspace_exclude_patterns)}")
        elif self.migration_mode:
            if self.multi_workspace_mode:
                self.log("🚀 Starting Bitbucket MULTI-WORKSPACE MIGRATION process...")
                workspace_pairs = self.get_workspace_pairs()
                self.log(f"📂 Workspace pairs to migrate: {len(workspace_pairs)}")
                for source_ws, dest_ws in workspace_pairs:
                    self.log(f"   📤 {source_ws} → 📥 {dest_ws}")
            else:
                self.log("🚀 Starting Bitbucket MIGRATION process...")
                self.log(f"📤 SOURCE: {self.source_workspace} ({self.source_email})")
                self.log(f"📥 DESTINATION: {self.dest_workspace} ({self.dest_email})")
        else:
            self.log("🚀 Starting Bitbucket backup process...")
        
        # Validate configuration
        if not self.validate_migration_config():
            self.log("\n" + "="*60)
            self.log("❌ CONFIGURATION VALIDATION FAILED")
            self.log("="*60)
            self.log("🔧 TROUBLESHOOTING GUIDE:")
            self.log("   1. Check your .env file configuration")
            self.log("   2. Verify API tokens have correct permissions:")
            self.log("      • Account: Read")
            self.log("      • Repositories: Read (Source) / Write (Destination)")
            self.log("   3. Confirm workspace names are correct")
            self.log("   4. Test API tokens at: https://bitbucket.org/account/settings/app-passwords/")
            self.log("   5. Ensure you have access to specified workspaces")
            self.log("="*60)
            return False
        
        # Determine repository discovery method
        repositories = []
        workspace_repositories = {}
        
        if self.auto_discover_all:
            # AUTO-DISCOVERY MODE: Find all workspaces and repositories automatically
            self.log("🔍 AUTO-DISCOVERY MODE: Discovering all accessible workspaces and repositories...")
            
            complete_structure = self.auto_discover_complete_structure()
            if not complete_structure:
                self.log("❌ Auto-discovery failed - no workspaces or repositories found")
                self.backup_stats['end_time'] = datetime.now()
                self.backup_stats['errors'].append("Auto-discovery failed")
                if self.email_enabled:
                    self.send_email_notification(success=False)
                return False
            
            # Create destination workspace structure
            if self.migration_mode:
                workspace_mapping = self.create_destination_workspace_structure(complete_structure)
                self.discovered_workspace_mapping = workspace_mapping
            
            # Convert auto-discovered structure to repository list for processing
            repositories = self.flatten_discovered_structure_to_repositories(complete_structure)
            workspace_repositories = complete_structure
            total_repos = len(repositories)
            
        elif self.multi_workspace_mode:
            # MANUAL MULTI-WORKSPACE MODE: Use configured workspace pairs
            workspace_repositories = self.get_all_workspaces_repositories()
            repositories = self.flatten_workspace_repositories(workspace_repositories)
            total_repos = len(repositories)
            
        else:
            # SINGLE WORKSPACE MODE: Use configured single workspace
            repositories = self.get_all_repositories()
            total_repos = len(repositories)
        
        if not repositories:
            self.log("❌ No repositories found to process")
            self.backup_stats['end_time'] = datetime.now()
            self.backup_stats['errors'].append("No repositories found")
            if self.email_enabled:
                self.send_email_notification(success=False)
            return False
        
        # Get existing repositories in DESTINATION (for migration mode)
        existing_dest_repos = {}
        if self.migration_mode:
            existing_dest_repos = self.get_destination_repositories()
        
        # Update statistics
        self.backup_stats['total_repos'] = len(repositories)
        success_count = 0
        migration_count = 0
        
        for repo in repositories:
            repo_name = repo['name']
            self.log(f"\n{'='*50}")
            self.log(f"Processing repository: {repo_name}")
            self.log(f"{'='*50}")
            
            repo_stats = {
                'name': repo_name,
                'success': False,
                'size': 'N/A',
                'metadata_items': 0
            }
            
            try:
                # 1. Backup metadata
                metadata_path = self.backup_repository_metadata(repo)
                
                # Count metadata items
                if metadata_path and os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            repo_stats['metadata_items'] = (
                                metadata.get('total_prs', 0) +
                                metadata.get('total_issues', 0) +
                                metadata.get('total_branches', 0) +
                                metadata.get('total_tags', 0) +
                                metadata.get('total_permissions', 0) +
                                metadata.get('total_webhooks', 0) +
                                metadata.get('total_deploy_keys', 0) +
                                metadata.get('total_branch_restrictions', 0)
                            )
                    except Exception:
                        pass
                
                # 2. Clone repository locally
                local_repo_path = self.clone_repository(repo)
                
                # 3. Create mirror repository
                mirror_repo = self.create_mirror_repository(repo)
                
                # 4. Push to mirror
                if local_repo_path and mirror_repo:
                    self.push_to_mirror(local_repo_path, mirror_repo)
                
                # 5. Restore collaboration metadata to destination repository
                if self.migration_mode and metadata_path and mirror_repo:
                    # Switch to destination auth for restoration
                    original_auth = self.auth
                    self.auth = self.dest_auth
                    
                    try:
                        dest_repo_name = mirror_repo.get('name', repo_name)
                        restoration_results = self.restore_repository_metadata(repo_name, metadata_path, dest_repo_name)
                        
                        # Track restoration in stats
                        if 'restoration_stats' not in repo_stats:
                            repo_stats['restoration_stats'] = restoration_results
                    except Exception as e:
                        self.log(f"⚠️ Error during metadata restoration: {e}")
                        repo_stats['restoration_error'] = str(e)
                    finally:
                        # Always switch back to source auth
                        self.auth = original_auth
                
                # 6. Create compressed backup
                backup_file = None
                if local_repo_path and metadata_path:
                    backup_file = self.create_compressed_backup(repo_name, local_repo_path, metadata_path, repo)
                
                # Calculate backup size
                if backup_file and os.path.exists(backup_file):
                    size_bytes = os.path.getsize(backup_file)
                    if size_bytes > 1024 * 1024:  # > 1MB
                        repo_stats['size'] = f"{size_bytes / (1024*1024):.1f} MB"
                    else:
                        repo_stats['size'] = f"{size_bytes / 1024:.1f} KB"
                    self.backup_stats['total_size'] += size_bytes
                
                # 7. Cleanup old backups
                self.cleanup_old_backups(repo_name)
                
                success_count += 1
                repo_stats['success'] = True
                self.log(f"✅ Successfully processed {repo_name}")
                
            except Exception as e:
                error_msg = f"Error processing {repo_name}: {e}"
                self.log(f"❌ {error_msg}")
                self.backup_stats['errors'].append(error_msg)
                continue
            finally:
                self.backup_stats['repo_details'].append(repo_stats)
            
            # Small delay to be nice to the API
            time.sleep(1)
        
        # Update final statistics
        self.backup_stats['successful_repos'] = success_count
        self.backup_stats['failed_repos'] = len(repositories) - success_count
        self.backup_stats['end_time'] = datetime.now()
        
        # Log final results
        overall_success = success_count == len(repositories)
        self.log(f"\n🎉 Backup completed! Successfully processed {success_count}/{len(repositories)} repositories")
        
        # Send email notification
        if self.email_enabled:
            self.send_email_notification(success=overall_success)
        
        return overall_success

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("""
🔄 Bitbucket Migration & Backup System

🚀 MIGRATION MODE - Dual Account Support:
For complete repository migration from one Bitbucket account to another:

SOURCE ACCOUNT (migrate FROM):
- SOURCE_ATLASSIAN_EMAIL: Source account email
- SOURCE_BITBUCKET_API_TOKEN: Source account API token
- SOURCE_BITBUCKET_USERNAME: Source account username
- SOURCE_BITBUCKET_WORKSPACE: Source workspace name

DESTINATION ACCOUNT (migrate TO):
- DEST_ATLASSIAN_EMAIL: Destination account email
- DEST_BITBUCKET_API_TOKEN: Destination account API token
- DEST_BITBUCKET_USERNAME: Destination account username
- DEST_BITBUCKET_WORKSPACE: Destination workspace name

MIGRATION SETTINGS:
- MIGRATION_MODE: Enable migration mode (true/false, default: true)
- PRESERVE_REPO_NAMES: Keep original names (true/false, default: true)
- REPO_NAME_PREFIX: Optional prefix for migrated repos (default: "")
- SKIP_EXISTING_REPOS: Skip existing repos (true/false, default: true)
- MIGRATION_BATCH_SIZE: Concurrent repo processing (default: 5)

📦 BACKUP CONFIGURATION:
- BACKUP_BASE_DIR: Local backup directory (default: /opt/bitbucket-backup)
- MAX_BACKUPS: Backup retention count (default: 5)
- CLONE_TIMEOUT: Git clone timeout in seconds (default: 1800)
- PUSH_TIMEOUT: Git push timeout in seconds (default: 3600)

📧 EMAIL NOTIFICATIONS (Optional):
- EMAIL_NOTIFICATIONS: Enable notifications (true/false, default: false)
- SMTP_SERVER: SMTP server (default: smtp.gmail.com)
- SMTP_PORT: SMTP port (default: 587)
- EMAIL_USERNAME: SMTP username
- EMAIL_PASSWORD: SMTP password (use app password for Gmail)
- NOTIFICATION_EMAIL: Recipient email address

🔧 LEGACY SUPPORT (backward compatibility):
- ATLASSIAN_EMAIL: Maps to SOURCE_ATLASSIAN_EMAIL
- BITBUCKET_API_TOKEN: Maps to SOURCE_BITBUCKET_API_TOKEN
- BITBUCKET_WORKSPACE: Maps to SOURCE_BITBUCKET_WORKSPACE
- BACKUP_WORKSPACE: Maps to DEST_BITBUCKET_WORKSPACE

📚 Documentation:
- Migration Guide: See MIGRATION-GUIDE.md
- Email Setup: See EMAIL-SETUP.md
- Recovery Guide: See RECOVERY.md

Usage:
    python3 bitbucket-backup.py
    
Examples:
    # Complete account migration
    MIGRATION_MODE=true python3 bitbucket-backup.py
    
    # Test configuration
    python3 bitbucket-backup.py --test-config
        """)
        return
    
    backup_system = BitbucketMigrationSystem()
    
    # Verify dual-account configuration
    if not all([backup_system.source_email, backup_system.source_api_token]):
        backup_system.log("❌ Missing required SOURCE account configuration!")
        backup_system.log("Required: SOURCE_ATLASSIAN_EMAIL, SOURCE_BITBUCKET_API_TOKEN")
        backup_system.log("For migration: DEST_ATLASSIAN_EMAIL, DEST_BITBUCKET_API_TOKEN")
        backup_system.log("Optional: SOURCE_BITBUCKET_USERNAME (for git authentication)")
        sys.exit(1)
    
    # Run backup
    success = backup_system.backup_all_repositories()
    sys.exit(0 if success else 1)

def test_configuration():
    """Test API configuration and connections without running backup/migration"""
    print("🧪 BITBUCKET CONFIGURATION TEST")
    print("="*50)
    
    backup_system = BitbucketMigrationSystem()
    
    # Test basic configuration loading
    print("📋 Configuration loaded:")
    print(f"   • Migration Mode: {'Yes' if backup_system.migration_mode else 'No'}")
    print(f"   • Auto-Discovery: {'Yes' if backup_system.auto_discover_all else 'No'}")
    print(f"   • Source Email: {backup_system.source_email or 'NOT SET'}")
    print(f"   • Source Workspace: {backup_system.source_workspace or 'NOT SET'}")
    if backup_system.migration_mode:
        print(f"   • Dest Email: {backup_system.dest_email or 'NOT SET'}")
        print(f"   • Dest Workspace: {backup_system.dest_workspace or 'NOT SET'}")
    
    # Run validation tests
    success = backup_system.validate_migration_config()
    
    print("\n" + "="*50)
    if success:
        print("✅ CONFIGURATION TEST PASSED")
        print("🚀 Your configuration is ready for backup/migration!")
    else:
        print("❌ CONFIGURATION TEST FAILED")
        print("🔧 Please fix the issues above before proceeding")
    
    return success

if __name__ == '__main__':
    import sys
    
    # Check if test mode is requested
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        success = test_configuration()
        sys.exit(0 if success else 1)
    else:
        main()