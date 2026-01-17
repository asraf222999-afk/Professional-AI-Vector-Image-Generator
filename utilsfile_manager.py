# mass_image_generator/utils/file_manager.py
"""
ফাইল ম্যানেজার - ফাইল অপারেশন ইউটিলিটি
"""

import os
import shutil
import json
import csv
from datetime import datetime
from typing import List, Dict, Any

class FileManager:
    """ফাইল ম্যানেজার ক্লাস"""
    
    @staticmethod
    def ensure_directory(directory: str):
        """ডিরেক্টরি নিশ্চিত করুন"""
        os.makedirs(directory, exist_ok=True)
        return directory
    
    @staticmethod
    def get_file_size(filepath: str):
        """ফাইল সাইজ পান"""
        if os.path.exists(filepath):
            return os.path.getsize(filepath)
        return 0
    
    @staticmethod
    def get_directory_size(directory: str):
        """ডিরেক্টরি সাইজ পান"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        return total_size
    
    @staticmethod
    def count_files(directory: str, extensions=None):
        """ফাইল কাউন্ট করুন"""
        if extensions is None:
            extensions = ['.png', '.jpg', '.jpeg']
        
        count = 0
        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    count += 1
        return count
    
    @staticmethod
    def organize_images_by_date(source_dir: str, target_dir: str = None):
        """ইমেজ তারিখ অনুযায়ী অর্গানাইজ করুন"""
        if target_dir is None:
            target_dir = source_dir
        
        for filename in os.listdir(source_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                filepath = os.path.join(source_dir, filename)
                
                try:
                    # Get creation date
                    stat = os.stat(filepath)
                    create_date = datetime.fromtimestamp(stat.st_ctime)
                    date_str = create_date.strftime("%Y%m%d")
                    
                    # Create date directory
                    date_dir = os.path.join(target_dir, date_str)
                    os.makedirs(date_dir, exist_ok=True)
                    
                    # Move file
                    shutil.move(filepath, os.path.join(date_dir, filename))
                    
                except Exception as e:
                    print(f"Error organizing {filename}: {e}")
        
        return True
    
    @staticmethod
    def save_json(data: Any, filepath: str, indent=2):
        """JSON সেভ করুন"""
        FileManager.ensure_directory(os.path.dirname(filepath))
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        
        return filepath
    
    @staticmethod
    def load_json(filepath: str):
        """JSON লোড করুন"""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    @staticmethod
    def save_csv(data: List[Dict], filepath: str):
        """CSV সেভ করুন"""
        if not data:
            return
        
        FileManager.ensure_directory(os.path.dirname(filepath))
        
        # Get fieldnames from first item
        fieldnames = list(data[0].keys())
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        return filepath
    
    @staticmethod
    def find_duplicate_images(directory: str, method='hash'):
        """ডুপ্লিকেট ইমেজ খুঁজুন"""
        import hashlib
        from PIL import Image
        
        hashes = {}
        duplicates = []
        
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    filepath = os.path.join(root, filename)
                    
                    try:
                        if method == 'hash':
                            # Calculate file hash
                            with open(filepath, 'rb') as f:
                                file_hash = hashlib.md5(f.read()).hexdigest()
                        else:
                            # Calculate image hash
                            img = Image.open(filepath)
                            img_hash = hashlib.md5(img.tobytes()).hexdigest()
                            file_hash = img_hash
                        
                        if file_hash in hashes:
                            duplicates.append({
                                'original': hashes[file_hash],
                                'duplicate': filepath,
                                'hash': file_hash
                            })
                        else:
                            hashes[file_hash] = filepath
                    
                    except Exception as e:
                        print(f"Error processing {filename}: {e}")
        
        return duplicates
    
    @staticmethod
    def create_readme(directory: str, content: Dict):
        """README ফাইল তৈরি করুন"""
        readme_file = os.path.join(directory, "README.md")
        
        lines = [
            "# Image Collection",
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Statistics",
            f"- Total Images: {content.get('total_images', 0)}",
            f"- Generated Date: {content.get('generation_date', 'Unknown')}",
            f"- Success Rate: {content.get('success_rate', 0):.1f}%",
            "",
            "## Generation Details",
            f"- Prompts Used: {content.get('prompt_count', 0)}",
            f"- APIs Used: {', '.join(content.get('apis_used', []))}",
            "",
            "## Usage",
            "These images were generated using AI and are free to use for personal projects.",
            "",
            "## Notes",
            content.get('notes', '')
        ]
        
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return readme_file