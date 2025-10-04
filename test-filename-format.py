#!/usr/bin/env python3
"""
Test script to demonstrate the improved tar.gz filename format
for the Bitbucket Migration System
"""

import os
import sys
from datetime import datetime

def demonstrate_filename_format():
    """Show examples of the new comprehensive filename format"""
    
    print("🔧 NEW TAR.GZ FILENAME FORMAT DEMONSTRATION")
    print("=" * 60)
    
    # Example scenarios
    scenarios = [
        {
            "workspace": "my-company",
            "repo_name": "web-frontend",
            "metadata_count": 47,
            "size_mb": 15.7,
            "timestamp": "2024-01-15_14-30-22"
        },
        {
            "workspace": "client-projects",
            "repo_name": "mobile-app-backend",
            "metadata_count": 123,
            "size_mb": 89.4,
            "timestamp": "2024-01-15_14-31-08"
        },
        {
            "workspace": "opensource",
            "repo_name": "python-utils",
            "metadata_count": 28,
            "size_mb": 2.1,
            "timestamp": "2024-01-15_14-32-45"
        },
        {
            "workspace": "data-science",
            "repo_name": "ml-models",
            "metadata_count": 95,
            "size_mb": 256.8,
            "timestamp": "2024-01-15_14-33-12"
        }
    ]
    
    print("\n📁 FILENAME FORMAT:")
    print("   WORKSPACE_REPO-NAME_YYYY-MM-DD_HH-MM-SS_metaCOUNT_SIZE.tar.gz")
    print("\n✨ EXAMPLES:")
    
    for i, scenario in enumerate(scenarios, 1):
        filename = f"{scenario['workspace']}_{scenario['repo_name']}_{scenario['timestamp']}_meta{scenario['metadata_count']}_{scenario['size_mb']}MB.tar.gz"
        
        print(f"\n{i}. {filename}")
        print(f"   📂 Workspace: {scenario['workspace']}")
        print(f"   📦 Repository: {scenario['repo_name']}")
        print(f"   📅 Created: {scenario['timestamp'].replace('_', ' ').replace('-', ':')}")
        print(f"   📊 Metadata items: {scenario['metadata_count']}")
        print(f"   💾 Size: {scenario['size_mb']} MB")
    
    print("\n🎯 BENEFITS OF NEW FORMAT:")
    print("   ✅ Workspace clearly identified")
    print("   ✅ Repository name always visible")
    print("   ✅ Precise timestamp (YYYY-MM-DD HH-MM-SS)")
    print("   ✅ Metadata count for quick assessment")
    print("   ✅ File size for storage planning")
    print("   ✅ Easy sorting by date/time")
    print("   ✅ Comprehensive backup info included")
    
    print("\n📋 BACKUP CONTENTS:")
    print("   📁 repository-{repo_name}/     <- Full repository clone")
    print("   📄 metadata-{repo_name}.json  <- All metadata (PRs, issues, etc.)")
    print("   📄 backup-info.json           <- Backup creation details")
    
    print("\n🔍 EASY IDENTIFICATION:")
    print("   • Instantly see which workspace/repo")
    print("   • Know when backup was created")
    print("   • Understand backup size and complexity")
    print("   • Perfect for organization and cleanup")
    
    print("\n🚀 MIGRATION READY:")
    print("   • Clear source workspace identification")
    print("   • Comprehensive metadata for reconstruction")
    print("   • Size information for planning")
    print("   • Timestamp for version tracking")

if __name__ == "__main__":
    demonstrate_filename_format()