# mass_image_generator/backup_system.py
"""
ব্যাকআপ সিস্টেম - ডাটা ব্যাকআপ ও রিস্টোর
"""

import os
import sys
import json
import shutil
import zipfile
import hashlib
from datetime import datetime
from typing import List, Dict, Optional

class BackupManager:
    """ব্যাকআপ ম্যানেজার ক্লাস"""
    
    def __init__(self, backup_dir="backups"):
        self.backup_dir = backup_dir
        self.metadata_file = os.path.join(backup_dir, "backup_metadata.json")
        
        # Create backup directory
        os.makedirs(backup_dir, exist_ok=True)
        
        # Load metadata
        self.metadata = self.load_metadata()
    
    def load_metadata(self):
        """মেটাডাটা লোড করুন"""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {"backups": []}
    
    def save_metadata(self):
        """মেটাডাটা সেভ করুন"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def create_backup(self, source_dirs: List[str], backup_name: str = None):
        """ব্যাকআপ তৈরি করুন"""
        
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
        
        backup_path = os.path.join(self.backup_dir, backup_name + ".zip")
        
        # Create zip file
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            total_files = 0
            
            for source_dir in source_dirs:
                if os.path.exists(source_dir):
                    for root, dirs, files in os.walk(source_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, start=source_dir)
                            zipf.write(file_path, arcname)
                            total_files += 1
        
        # Calculate checksum
        checksum = self.calculate_checksum(backup_path)
        
        # Update metadata
        backup_info = {
            "name": backup_name,
            "path": backup_path,
            "created_at": datetime.now().isoformat(),
            "size_mb": os.path.getsize(backup_path) / (1024 * 1024),
            "files_count": total_files,
            "checksum": checksum,
            "source_dirs": source_dirs
        }
        
        self.metadata["backups"].append(backup_info)
        self.save_metadata()
        
        print(f"Backup created: {backup_name}")
        print(f"  Size: {backup_info['size_mb']:.2f} MB")
        print(f"  Files: {total_files}")
        print(f"  Path: {backup_path}")
        
        return backup_info
    
    def calculate_checksum(self, filepath: str, algorithm="sha256"):
        """চেকসাম ক্যালকুলেট করুন"""
        hash_func = hashlib.new(algorithm)
        
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    def list_backups(self):
        """ব্যাকআপ লিস্ট করুন"""
        return self.metadata.get("backups", [])
    
    def restore_backup(self, backup_name: str, target_dir: str = "."):
        """ব্যাকআপ রিস্টোর করুন"""
        
        # Find backup
        backup_info = None
        for backup in self.metadata["backups"]:
            if backup["name"] == backup_name:
                backup_info = backup
                break
        
        if not backup_info:
            raise ValueError(f"Backup not found: {backup_name}")
        
        backup_path = backup_info["path"]
        
        # Verify checksum
        current_checksum = self.calculate_checksum(backup_path)
        if current_checksum != backup_info["checksum"]:
            raise ValueError("Backup file corrupted: checksum mismatch")
        
        # Create target directory
        os.makedirs(target_dir, exist_ok=True)
        
        # Extract backup
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(target_dir)
        
        print(f"Backup restored: {backup_name} -> {target_dir}")
        
        return True
    
    def delete_backup(self, backup_name: str):
        """ব্যাকআপ ডিলিট করুন"""
        
        # Find and remove backup
        for i, backup in enumerate(self.metadata["backups"]):
            if backup["name"] == backup_name:
                # Delete file
                if os.path.exists(backup["path"]):
                    os.remove(backup["path"])
                
                # Remove from metadata
                self.metadata["backups"].pop(i)
                self.save_metadata()
                
                print(f"Backup deleted: {backup_name}")
                return True
        
        return False
    
    def auto_cleanup(self, max_backups=10, max_age_days=30):
        """অটো ক্লিনআপ করুন"""
        
        now = datetime.now()
        backups = self.list_backups()
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        
        deleted_count = 0
        
        for backup in backups[max_backups:]:
            # Delete if too many backups
            self.delete_backup(backup["name"])
            deleted_count += 1
        
        # Check age
        for backup in backups:
            if deleted_count >= len(backups) - max_backups:
                break
            
            created_date = datetime.fromisoformat(backup["created_at"])
            age_days = (now - created_date).days
            
            if age_days > max_age_days:
                self.delete_backup(backup["name"])
                deleted_count += 1
        
        return deleted_count

class IncrementalBackup(BackupManager):
    """ইনক্রিমেন্টাল ব্যাকআপ ক্লাস"""
    
    def __init__(self, backup_dir="backups"):
        super().__init__(backup_dir)
        self.change_log = os.path.join(backup_dir, "change_log.json")
        self.last_backup_time = None
        
        # Load change log
        self.changes = self.load_change_log()
    
    def load_change_log(self):
        """চেঞ্জ লগ লোড করুন"""
        if os.path.exists(self.change_log):
            with open(self.change_log, 'r') as f:
                return json.load(f)
        return {"changes": []}
    
    def save_change_log(self):
        """চেঞ্জ লগ সেভ করুন"""
        with open(self.change_log, 'w') as f:
            json.dump(self.changes, f, indent=2)
    
    def detect_changes(self, source_dir: str):
        """পরিবর্তন ডিটেক্ট করুন"""
        
        changes = []
        
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                
                # Get file stats
                stat = os.stat(file_path)
                modified_time = stat.st_mtime
                
                # Check if modified since last backup
                if (self.last_backup_time is None or 
                    modified_time > self.last_backup_time):
                    
                    changes.append({
                        "path": file_path,
                        "modified": datetime.fromtimestamp(modified_time).isoformat(),
                        "size": stat.st_size
                    })
        
        return changes
    
    def create_incremental_backup(self, source_dir: str):
        """ইনক্রিমেন্টাল ব্যাকআপ তৈরি করুন"""
        
        # Detect changes
        changes = self.detect_changes(source_dir)
        
        if not changes:
            print("No changes detected since last backup")
            return None
        
        # Create backup name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"incremental_{timestamp}"
        
        # Create backup
        backup_info = self.create_backup([source_dir], backup_name)
        
        # Record changes
        self.changes["changes"].extend(changes)
        self.save_change_log()
        
        # Update last backup time
        self.last_backup_time = datetime.now().timestamp()
        
        print(f"Incremental backup created with {len(changes)} changed files")
        
        return backup_info

# ইউটিলিটি ফাংশন
def backup_images_daily():
    """দৈনিক ইমেজ ব্যাকআপ"""
    manager = BackupManager()
    
    # Source directories
    sources = [
        "outputs/images",
        "outputs/metadata",
        "prompts"
    ]
    
    # Create backup
    manager.create_backup(sources)
    
    # Auto cleanup old backups
    manager.auto_cleanup(max_backups=7, max_age_days=7)
    
    print("Daily backup completed")

if __name__ == "__main__":
    # টেস্ট করুন
    manager = BackupManager()
    
    # Create a test backup
    test_sources = ["test_output"]
    os.makedirs("test_output", exist_ok=True)
    
    # Create some test files
    with open("test_output/test1.txt", "w") as f:
        f.write("Test file 1")
    
    with open("test_output/test2.txt", "w") as f:
        f.write("Test file 2")
    
    # Backup
    backup = manager.create_backup(test_sources, "test_backup")
    
    # List backups
    backups = manager.list_backups()
    print(f"Total backups: {len(backups)}")
    
    # Restore test
    manager.restore_backup("test_backup", "test_restore")
    
    print("Backup test completed successfully")