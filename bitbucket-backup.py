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

class BitbucketMetadataBackup:
    def __init__(self):
        # Configuration from environment
        self.atlassian_email = os.environ.get('ATLASSIAN_EMAIL', '')
        self.bitbucket_api_token = os.environ.get('BITBUCKET_API_TOKEN', '')
        self.bitbucket_workspace = os.environ.get('BITBUCKET_WORKSPACE', '')
        self.backup_workspace = os.environ.get('BACKUP_WORKSPACE', '')  # Target workspace for mirror repos
        
        # Local backup configuration
        self.backup_base_dir = os.environ.get('BACKUP_BASE_DIR', '/opt/bitbucket-backup')
        self.max_backups = int(os.environ.get('MAX_BACKUPS', '5'))
        
        # Bitbucket API setup
        self.base_url = 'https://api.bitbucket.org/2.0'
        self.auth = (self.atlassian_email, self.bitbucket_api_token)
        
        # Headers for API requests
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Setup directories
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.setup_directories()
        
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
        """Fetch all repositories from the workspace"""
        self.log("🔍 Fetching all repositories from workspace...")
        
        repos = self.fetch_paginated_data(f'repositories/{self.bitbucket_workspace}')
        self.log(f"Found {len(repos)} repositories")
        
        return repos
    
    def backup_repository_metadata(self, repo):
        """Backup metadata for a single repository"""
        repo_name = repo['name']
        self.log(f"📝 Backing up metadata for {repo_name}...")
        
        # Create repo-specific metadata directory
        repo_metadata_dir = os.path.join(self.metadata_dir, repo_name, self.timestamp)
        os.makedirs(repo_metadata_dir, exist_ok=True)
        
        metadata = {
            'repository_info': repo,
            'backup_timestamp': self.timestamp
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
        
        # Save metadata to JSON file
        metadata_file = os.path.join(repo_metadata_dir, 'metadata.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        return metadata_file
    
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
        
        # Construct authenticated URL using email and API token
        auth_url = clone_url.replace('https://', f'https://{self.atlassian_email}:{self.bitbucket_api_token}@')
        
        try:
            # Clone with better error handling and Ubuntu optimization
            
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
    
    def create_mirror_repository(self, repo):
        """Create a mirror repository in backup workspace"""
        repo_name = repo['name']
        mirror_name = f"{repo_name}-backup-mirror"
        
        self.log(f"🔄 Creating mirror repository: {mirror_name}")
        
        # Check if mirror repo already exists
        existing_repo = self.make_api_request(f'repositories/{self.backup_workspace}/{mirror_name}')
        
        if existing_repo:
            self.log(f"Mirror repository {mirror_name} already exists")
            return existing_repo
        
        # Create new mirror repository
        repo_data = {
            "name": mirror_name,
            "description": f"Automated backup mirror of {repo_name}",
            "is_private": True,
            "fork_policy": "no_public_forks",
            "has_issues": False,
            "has_wiki": False
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/repositories/{self.backup_workspace}/{mirror_name}",
                auth=self.auth,
                headers=self.headers,
                json=repo_data
            )
            response.raise_for_status()
            
            mirror_repo = response.json()
            self.log(f"✅ Created mirror repository: {mirror_name}")
            return mirror_repo
            
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Error creating mirror repository {mirror_name}: {e}")
            return None
    
    def push_to_mirror(self, local_repo_path, mirror_repo):
        """Push local repository to mirror"""
        if not local_repo_path or not mirror_repo:
            return False
        
        mirror_name = mirror_repo['name']
        
        # Find HTTPS clone URL for mirror
        clone_url = None
        for link in mirror_repo['links']['clone']:
            if link['name'] == 'https':
                clone_url = link['href']
                break
        
        if not clone_url:
            self.log(f"❌ No HTTPS clone URL found for mirror {mirror_name}")
            return False
        
        # Construct authenticated URL using email and API token
        auth_url = clone_url.replace('https://', f'https://{self.atlassian_email}:{self.bitbucket_api_token}@')
        
        try:
            mirror_git_dir = os.path.join(local_repo_path, 'repo.git')
            
            if os.path.exists(mirror_git_dir):
                self.log(f"🔄 Pushing to mirror {mirror_name}...")
                
                # Add mirror remote (suppress error if exists)
                subprocess.run([
                    'git', '-C', mirror_git_dir, 'remote', 'add', 'mirror', auth_url
                ], capture_output=True)
                
                # Push with timeout and better error handling
                push_result = subprocess.run([
                    'git', '-C', mirror_git_dir, 'push', '--mirror', 'mirror'
                ], capture_output=True, text=True, timeout=1800)  # 30 min timeout
                
                if push_result.returncode == 0:
                    self.log(f"✅ Successfully pushed to mirror {mirror_name}")
                    return True
                else:
                    self.log(f"❌ Push failed: {push_result.stderr}")
                    return False
            else:
                self.log(f"❌ Mirror git directory not found: {mirror_git_dir}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log(f"❌ Push timeout for mirror {mirror_name}")
            return False
        except Exception as e:
            self.log(f"❌ Error pushing to mirror {mirror_name}: {e}")
            return False
    
    def create_compressed_backup(self, repo_name, repo_path, metadata_path):
        """Create tar.gz backup for repository"""
        repo_backup_dir = os.path.join(self.repos_dir, repo_name)
        
        # Create tar.gz file
        backup_filename = f"{repo_name}_{self.timestamp}.tar.gz"
        backup_filepath = os.path.join(repo_backup_dir, backup_filename)
        
        self.log(f"📦 Creating compressed backup: {backup_filename}")
        
        try:
            with tarfile.open(backup_filepath, 'w:gz') as tar:
                # Add repository files
                if os.path.exists(repo_path):
                    tar.add(repo_path, arcname=f"repository_{self.timestamp}")
                
                # Add metadata file
                if os.path.exists(metadata_path):
                    tar.add(metadata_path, arcname=f"metadata_{self.timestamp}.json")
            
            self.log(f"✅ Created compressed backup: {backup_filepath}")
            return backup_filepath
            
        except Exception as e:
            self.log(f"❌ Error creating compressed backup: {e}")
            return None
    
    def cleanup_old_backups(self, repo_name):
        """Remove old backups keeping only the specified number"""
        repo_backup_dir = os.path.join(self.repos_dir, repo_name)
        
        if not os.path.exists(repo_backup_dir):
            return
        
        # Get all backup files
        backup_files = [f for f in os.listdir(repo_backup_dir) if f.endswith('.tar.gz')]
        backup_files.sort(reverse=True)  # Sort by name (timestamp descending)
        
        # Remove old backups
        if len(backup_files) > self.max_backups:
            files_to_remove = backup_files[self.max_backups:]
            
            for file_to_remove in files_to_remove:
                file_path = os.path.join(repo_backup_dir, file_to_remove)
                try:
                    os.remove(file_path)
                    self.log(f"🗑️  Removed old backup: {file_to_remove}")
                except Exception as e:
                    self.log(f"❌ Error removing {file_to_remove}: {e}")
        
        # Also cleanup old timestamped directories
        timestamped_dirs = [d for d in os.listdir(repo_backup_dir) 
                           if os.path.isdir(os.path.join(repo_backup_dir, d)) and d != '.git']
        timestamped_dirs.sort(reverse=True)
        
        if len(timestamped_dirs) > self.max_backups:
            dirs_to_remove = timestamped_dirs[self.max_backups:]
            
            for dir_to_remove in dirs_to_remove:
                dir_path = os.path.join(repo_backup_dir, dir_to_remove)
                try:
                    shutil.rmtree(dir_path)
                    self.log(f"🗑️  Removed old backup directory: {dir_to_remove}")
                except Exception as e:
                    self.log(f"❌ Error removing directory {dir_to_remove}: {e}")
    
    def backup_all_repositories(self):
        """Main function to backup all repositories"""
        self.log("🚀 Starting Bitbucket backup process...")
        
        # Get all repositories
        repositories = self.get_all_repositories()
        
        if not repositories:
            self.log("❌ No repositories found or error fetching repositories")
            return False
        
        success_count = 0
        
        for repo in repositories:
            repo_name = repo['name']
            self.log(f"\n{'='*50}")
            self.log(f"Processing repository: {repo_name}")
            self.log(f"{'='*50}")
            
            try:
                # 1. Backup metadata
                metadata_path = self.backup_repository_metadata(repo)
                
                # 2. Clone repository locally
                local_repo_path = self.clone_repository(repo)
                
                # 3. Create mirror repository
                mirror_repo = self.create_mirror_repository(repo)
                
                # 4. Push to mirror
                if local_repo_path and mirror_repo:
                    self.push_to_mirror(local_repo_path, mirror_repo)
                
                # 5. Create compressed backup
                if local_repo_path and metadata_path:
                    self.create_compressed_backup(repo_name, local_repo_path, metadata_path)
                
                # 6. Cleanup old backups
                self.cleanup_old_backups(repo_name)
                
                success_count += 1
                self.log(f"✅ Successfully processed {repo_name}")
                
            except Exception as e:
                self.log(f"❌ Error processing {repo_name}: {e}")
                continue
            
            # Small delay to be nice to the API
            time.sleep(1)
        
        self.log(f"\n🎉 Backup completed! Successfully processed {success_count}/{len(repositories)} repositories")
        return success_count == len(repositories)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("""
Bitbucket Backup System

Environment Variables Required:
- ATLASSIAN_EMAIL: Your Atlassian account email
- BITBUCKET_API_TOKEN: Your Bitbucket API token (not app password)
- BITBUCKET_WORKSPACE: Source workspace to backup
- BACKUP_WORKSPACE: Target workspace for mirror repositories
- BACKUP_BASE_DIR: Local directory for backups (default: /opt/bitbucket-backup)
- MAX_BACKUPS: Number of backups to retain (default: 5)

Usage:
    python3 bitbucket-backup.py
        """)
        return
    
    backup_system = BitbucketMetadataBackup()
    
    # Verify configuration
    if not all([backup_system.atlassian_email, backup_system.bitbucket_api_token, 
                backup_system.bitbucket_workspace, backup_system.backup_workspace]):
        backup_system.log("❌ Missing required environment variables!")
        backup_system.log("Required: ATLASSIAN_EMAIL, BITBUCKET_API_TOKEN, BITBUCKET_WORKSPACE, BACKUP_WORKSPACE")
        sys.exit(1)
    
    # Run backup
    success = backup_system.backup_all_repositories()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()