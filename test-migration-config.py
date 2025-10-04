#!/bin/bash
"""
Configuration Test Script for Bitbucket Migration System
Validates both source    # Validate source accoun    # Validate destination account (if migration mode)
    dest_success = True
    if migration_mode:
        if multi_workspace_mode:
            dest_workspaces_list = [ws.strip() for ws in dest_workspaces if ws.strip()] if dest_workspaces else []
            if not all([dest_email, dest_token]):
                print("\\n❌ DESTINATION multi-workspace configuration incomplete!")
                print("   Required for migration: DEST_ATLASSIAN_EMAIL, DEST_BITBUCKET_API_TOKEN")
                return False
            
            # For multi-workspace, we might create workspaces, so just test account access
            try:
                response = requests.get(
                    'https://api.bitbucket.org/2.0/user',
                    auth=(dest_email, dest_token),
                    timeout=30
                )
                if response.status_code == 200:
                    user_info = response.json()
                    print(f"\\n✅ DESTINATION account access validated")
                    print(f"   👤 User: {user_info.get('display_name', 'Unknown')}")
                    dest_success = True
                else:
                    print(f"\\n❌ DESTINATION account access failed: {response.status_code}")
                    dest_success = False
            except Exception as e:
                print(f"\\n❌ DESTINATION account test error: {e}")
                dest_success = False
        else:
            if not all([dest_email, dest_token, dest_workspace]):
                print("\\n❌ DESTINATION account configuration incomplete!")
                print("   Required for migration: DEST_ATLASSIAN_EMAIL, DEST_BITBUCKET_API_TOKEN, DEST_BITBUCKET_WORKSPACE")
                return False
                
            dest_success = test_account_access(dest_email, dest_token, dest_workspace, "DESTINATION") multi_workspace_mode:
        source_workspaces_list = [ws.strip() for ws in source_workspaces if ws.strip()]
        if not all([source_email, source_token]) or not source_workspaces_list:
            print("\\n❌ SOURCE multi-workspace configuration incomplete!")
            print("   Required: SOURCE_ATLASSIAN_EMAIL, SOURCE_BITBUCKET_API_TOKEN, SOURCE_BITBUCKET_WORKSPACES")
            return False
        
        # Test access to first workspace as sample
        test_workspace = source_workspaces_list[0]
        source_success = test_account_access(source_email, source_token, test_workspace, f"SOURCE ({test_workspace})")
        
        if source_success and len(source_workspaces_list) > 1:
            print(f"   ℹ️  Will process {len(source_workspaces_list)} workspaces total")
    else:
        if not all([source_email, source_token, source_workspace]):
            print("\\n❌ SOURCE account configuration incomplete!")
            print("   Required: SOURCE_ATLASSIAN_EMAIL, SOURCE_BITBUCKET_API_TOKEN, SOURCE_BITBUCKET_WORKSPACE")
            return False
            
        source_success = test_account_access(source_email, source_token, source_workspace, "SOURCE")stination account access before running migration
"""

import os
import sys
import requests
from datetime import datetime

def test_account_access(email, token, workspace, account_type):
    """Test API access for an account"""
    print(f"\n🧪 Testing {account_type} Account Access...")
    print(f"   Email: {email}")
    print(f"   Workspace: {workspace}")
    
    try:
        # Test basic API access
        response = requests.get(
            'https://api.bitbucket.org/2.0/user',
            auth=(email, token),
            timeout=30
        )
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"   ✅ Authentication successful")
            print(f"   👤 User: {user_info.get('display_name', 'Unknown')}")
        else:
            print(f"   ❌ Authentication failed: {response.status_code}")
            return False
            
        # Test workspace access
        response = requests.get(
            f'https://api.bitbucket.org/2.0/repositories/{workspace}',
            auth=(email, token),
            timeout=30
        )
        
        if response.status_code == 200:
            repos = response.json()
            repo_count = len(repos.get('values', []))
            print(f"   ✅ Workspace access successful")
            print(f"   📦 Found {repo_count} repositories")
            return True
        else:
            print(f"   ❌ Workspace access failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🔄 Bitbucket Migration System - Configuration Test")
    print("=" * 60)
    
    # Check migration mode
    migration_mode = os.environ.get('MIGRATION_MODE', 'true').lower() == 'true'
    multi_workspace_mode = os.environ.get('MULTI_WORKSPACE_MODE', 'false').lower() == 'true'
    print(f"Migration Mode: {'✅ ENABLED' if migration_mode else '❌ DISABLED'}")
    print(f"Multi-Workspace Mode: {'✅ ENABLED' if multi_workspace_mode else '❌ DISABLED'}")
    
    # Load source configuration
    source_email = os.environ.get('SOURCE_ATLASSIAN_EMAIL', os.environ.get('ATLASSIAN_EMAIL', ''))
    source_token = os.environ.get('SOURCE_BITBUCKET_API_TOKEN', os.environ.get('BITBUCKET_API_TOKEN', ''))
    
    # Multi-workspace configuration
    if multi_workspace_mode:
        source_workspaces = os.environ.get('SOURCE_BITBUCKET_WORKSPACES', '').split(',')
        dest_workspaces = os.environ.get('DEST_BITBUCKET_WORKSPACES', '').split(',')
        workspace_mapping = os.environ.get('WORKSPACE_MAPPING', '')
        
        print(f"\\n🏢 Multi-Workspace Configuration:")
        print(f"   Source workspaces: {len([ws for ws in source_workspaces if ws.strip()])}")
        for ws in source_workspaces:
            if ws.strip():
                print(f"     📤 {ws.strip()}")
        
        if dest_workspaces and dest_workspaces[0].strip():
            print(f"   Destination workspaces: {len([ws for ws in dest_workspaces if ws.strip()])}")
            for ws in dest_workspaces:
                if ws.strip():
                    print(f"     📥 {ws.strip()}")
        
        if workspace_mapping:
            print(f"   Custom mapping: {workspace_mapping}")
            
    else:
        source_workspace = os.environ.get('SOURCE_BITBUCKET_WORKSPACE', os.environ.get('BITBUCKET_WORKSPACE', ''))
        dest_workspace = os.environ.get('DEST_BITBUCKET_WORKSPACE', os.environ.get('BACKUP_WORKSPACE', ''))
    
    # Load destination configuration
    dest_email = os.environ.get('DEST_ATLASSIAN_EMAIL', '')
    dest_token = os.environ.get('DEST_BITBUCKET_API_TOKEN', '')
    
    # Validate source account
    if not all([source_email, source_token, source_workspace]):
        print("\n❌ SOURCE account configuration incomplete!")
        print("   Required: SOURCE_ATLASSIAN_EMAIL, SOURCE_BITBUCKET_API_TOKEN, SOURCE_BITBUCKET_WORKSPACE")
        return False
        
    source_success = test_account_access(source_email, source_token, source_workspace, "SOURCE")
    
    # Validate destination account (if migration mode)
    dest_success = True
    if migration_mode:
        if not all([dest_email, dest_token, dest_workspace]):
            print("\n❌ DESTINATION account configuration incomplete!")
            print("   Required for migration: DEST_ATLASSIAN_EMAIL, DEST_BITBUCKET_API_TOKEN, DEST_BITBUCKET_WORKSPACE")
            return False
            
        dest_success = test_account_access(dest_email, dest_token, dest_workspace, "DESTINATION")
    
    # Migration settings
    if migration_mode:
        print(f"\n⚙️  Migration Settings:")
        print(f"   Preserve repo names: {os.environ.get('PRESERVE_REPO_NAMES', 'true')}")
        print(f"   Repo name prefix: '{os.environ.get('REPO_NAME_PREFIX', '')}'")
        print(f"   Skip existing repos: {os.environ.get('SKIP_EXISTING_REPOS', 'true')}")
        print(f"   Batch size: {os.environ.get('MIGRATION_BATCH_SIZE', '5')}")
    
    # Performance settings
    print(f"\n⚡ Performance Settings:")
    print(f"   Clone timeout: {os.environ.get('CLONE_TIMEOUT', '1800')}s")
    print(f"   Push timeout: {os.environ.get('PUSH_TIMEOUT', '3600')}s")
    print(f"   Parallel jobs: {os.environ.get('PARALLEL_JOBS', '3')}")
    
    # Email configuration
    email_enabled = os.environ.get('EMAIL_NOTIFICATIONS', 'false').lower() == 'true'
    print(f"\n📧 Email Notifications: {'✅ ENABLED' if email_enabled else '❌ DISABLED'}")
    if email_enabled:
        notification_email = os.environ.get('NOTIFICATION_EMAIL', '')
        print(f"   Recipient: {notification_email if notification_email else '❌ NOT SET'}")
    
    # Final result
    print(f"\n" + "=" * 60)
    if source_success and dest_success:
        print("🎉 CONFIGURATION TEST PASSED!")
        print("✅ Ready to run migration")
        if migration_mode:
            print(f"\n🚀 To start migration:")
            print(f"   ./scripts/bitbucket-backup.sh --force")
        return True
    else:
        print("❌ CONFIGURATION TEST FAILED!")
        print("🔧 Please fix the issues above before running migration")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)