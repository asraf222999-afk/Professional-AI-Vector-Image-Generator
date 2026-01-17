# mass_image_generator/bulk_generator.py
"""
বাল্ক ইমেজ জেনারেটর - হাজার হাজার ইমেজ জেনারেট করে
"""

import os
import sys
import json
import time
import queue
import threading
import concurrent.futures
from datetime import datetime
from typing import List, Dict, Any
from tqdm import tqdm
from colorama import Fore, Style

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_api_manager import APIManager
from utils.image_utils import ImageProcessor

class MassImageGenerator:
    """মাস ইমেজ জেনারেটর ক্লাস"""
    
    def __init__(self, prompt_file=None, target_count=1000, config=None):
        self.prompt_file = prompt_file
        self.target_count = target_count
        self.config = config or self.load_default_config()
        
        # ইনিশিয়ালাইজ ম্যানেজার
        self.api_manager = APIManager(config=self.config)
        self.image_processor = ImageProcessor()
        
        # ট্র্যাকিং ভেরিয়েবল
        self.generated_count = 0
        self.failed_count = 0
        self.success_rate = 0
        self.start_time = None
        
        # থ্রেড সেফ কন্ট্রোল
        self.queue = queue.Queue()
        self.lock = threading.Lock()
        self.running = True
        
        # আউটপুট ডিরেক্টরি
        self.setup_output_directories()
        
    def load_default_config(self):
        """ডিফল্ট কনফিগারেশন লোড করুন"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def setup_output_directories(self):
        """আউটপুট ডিরেক্টরি সেটআপ করুন"""
        base_dir = self.config.get('output_settings', {}).get('base_dir', 'outputs')
        
        self.image_dir = os.path.join(base_dir, 'images', datetime.now().strftime('%Y%m%d'))
        self.metadata_dir = os.path.join(base_dir, 'metadata', datetime.now().strftime('%Y%m%d'))
        self.log_dir = os.path.join(base_dir, 'logs')
        
        for directory in [self.image_dir, self.metadata_dir, self.log_dir]:
            os.makedirs(directory, exist_ok=True)
    
    def load_prompts(self):
        """প্রম্পটস লোড করুন"""
        prompts = []
        
        if self.prompt_file and os.path.exists(self.prompt_file):
            with open(self.prompt_file, 'r', encoding='utf-8') as f:
                prompts = [line.strip() for line in f if line.strip()]
        else:
            # ডিফল্ট প্রম্পটস
            prompts = [
                "A beautiful landscape with mountains and river",
                "Abstract geometric pattern with vibrant colors",
                "Cute animal character in cartoon style",
                "Futuristic city with flying cars",
                "Minimalist logo design for a tech company"
            ]
        
        # টার্গেট কাউন্ট অনুযায়ী রিপিট করুন
        if len(prompts) < self.target_count:
            repeated_prompts = []
            while len(repeated_prompts) < self.target_count:
                for prompt in prompts:
                    if len(repeated_prompts) < self.target_count:
                        repeated_prompts.append(prompt)
                    else:
                        break
            prompts = repeated_prompts
        
        return prompts[:self.target_count]
    
    def generate_single_image(self, prompt, index):
        """একটি ইমেজ জেনারেট করুন"""
        
        try:
            # API থেকে ইমেজ জেনারেট করুন
            image_data = self.api_manager.generate_image(prompt)
            
            if image_data:
                # ফাইলনেম তৈরি করুন
                timestamp = datetime.now().strftime('%H%M%S')
                filename = f"image_{index:06d}_{timestamp}.png"
                filepath = os.path.join(self.image_dir, filename)
                
                # ইমেজ সেভ করুন
                self.image_processor.save_image(image_data, filepath)
                
                # মেটাডাটা সেভ করুন
                metadata = {
                    "prompt": prompt,
                    "filename": filename,
                    "generated_at": datetime.now().isoformat(),
                    "api_used": self.api_manager.last_used_api,
                    "index": index
                }
                
                metadata_file = os.path.join(self.metadata_dir, f"meta_{index:06d}.json")
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                # সাফল্য রেকর্ড করুন
                with self.lock:
                    self.generated_count += 1
                    self.update_progress()
                
                return True
            else:
                with self.lock:
                    self.failed_count += 1
                return False
                
        except Exception as e:
            # এরর লগ করুন
            error_log = os.path.join(self.log_dir, 'errors.log')
            with open(error_log, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now()} - Error generating image {index}: {str(e)}\n")
            
            with self.lock:
                self.failed_count += 1
            
            return False
    
    def worker(self, prompt_queue, progress_bar=None):
        """ওয়ার্কার থ্রেড"""
        while self.running:
            try:
                # কিউ থেকে প্রম্পট নিন
                prompt, index = prompt_queue.get(timeout=1)
                
                # ইমেজ জেনারেট করুন
                success = self.generate_single_image(prompt, index)
                
                # প্রোগ্রেস বার আপডেট করুন
                if progress_bar:
                    progress_bar.update(1)
                
                # টাস্ক কমপ্লিট মার্ক করুন
                prompt_queue.task_done()
                
            except queue.Empty:
                # কিউ খালি হলে ব্রেক করুন
                break
            except Exception as e:
                print(f"{Fore.RED}Worker error: {e}{Style.RESET_ALL}")
                continue
    
    def update_progress(self):
        """প্রোগ্রেস আপডেট করুন"""
        total = self.generated_count + self.failed_count
        if total > 0:
            self.success_rate = (self.generated_count / total) * 100
        
        # প্রতি ১০টি ইমেজে প্রোগ্রেস শো করুন
        if total % 10 == 0:
            elapsed = time.time() - self.start_time
            images_per_hour = (total / elapsed) * 3600 if elapsed > 0 else 0
            
            print(f"{Fore.CYAN}[Progress] {total}/{self.target_count} "
                  f"| Success: {self.success_rate:.1f}% "
                  f"| Speed: {images_per_hour:.1f}/hour{Style.RESET_ALL}")
    
    def start_generation(self):
        """জেনারেশন শুরু করুন"""
        
        print(f"{Fore.YELLOW}Starting mass image generation...{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Target: {self.target_count} images{Style.RESET_ALL}")
        
        # প্রম্পটস লোড করুন
        prompts = self.load_prompts()
        print(f"{Fore.GREEN}Loaded {len(prompts)} prompts{Style.RESET_ALL}")
        
        # কিউ তৈরি করুন
        prompt_queue = queue.Queue()
        for i, prompt in enumerate(prompts[:self.target_count]):
            prompt_queue.put((prompt, i))
        
        # প্রোগ্রেস বার
        progress_bar = tqdm(
            total=self.target_count,
            desc="Generating images",
            unit="img",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"
        )
        
        # থ্রেড পুল তৈরি করুন
        max_threads = self.config.get('settings', {}).get('max_threads', 4)
        threads = []
        
        self.start_time = time.time()
        
        try:
            # ওয়ার্কার থ্রেড শুরু করুন
            for _ in range(max_threads):
                thread = threading.Thread(
                    target=self.worker,
                    args=(prompt_queue, progress_bar)
                )
                thread.daemon = True
                thread.start()
                threads.append(thread)
            
            # সব টাস্ক কমপ্লিট হওয়ার জন্য অপেক্ষা করুন
            prompt_queue.join()
            
            # থ্রেড গুলো শেষ হওয়ার জন্য অপেক্ষা করুন
            for thread in threads:
                thread.join(timeout=5)
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Generation interrupted by user{Style.RESET_ALL}")
            self.running = False
        finally:
            # প্রোগ্রেস বার বন্ধ করুন
            progress_bar.close()
            
            # রিপোর্ট তৈরি করুন
            self.generate_report()
        
        return self.get_results()
    
    def generate_report(self):
        """রিপোর্ট তৈরি করুন"""
        report = {
            "total_target": self.target_count,
            "total_generated": self.generated_count,
            "total_failed": self.failed_count,
            "success_rate": self.success_rate,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_seconds": time.time() - self.start_time,
            "apis_used": self.api_manager.get_usage_stats(),
            "output_directory": os.path.abspath(self.image_dir)
        }
        
        # রিপোর্ট সেভ করুন
        report_file = os.path.join(self.log_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"{Fore.GREEN}Report saved to: {report_file}{Style.RESET_ALL}")
        
        # কনসোলে স্ট্যাটস প্রিন্ট করুন
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}🎉 Generation Complete!{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Total Images: {self.generated_count}/{self.target_count}")
        print(f"Success Rate: {self.success_rate:.1f}%")
        print(f"Failed: {self.failed_count}")
        print(f"Duration: {(time.time() - self.start_time)/60:.1f} minutes")
        print(f"Output: {self.image_dir}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    def get_results(self):
        """রেজাল্টস গেট করুন"""
        results = {
            "generated": self.generated_count,
            "failed": self.failed_count,
            "success_rate": self.success_rate,
            "image_dir": self.image_dir,
            "metadata_dir": self.metadata_dir
        }
        
        return results

# কমান্ড লাইন ইন্টারফেস
def main():
    """মেইন ফাংশন"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bulk Image Generator")
    parser.add_argument("--prompts", "-p", required=True, help="Prompt file")
    parser.add_argument("--count", "-c", type=int, default=100, help="Number of images")
    parser.add_argument("--threads", "-t", type=int, default=4, help="Number of threads")
    parser.add_argument("--output", "-o", default="outputs", help="Output directory")
    
    args = parser.parse_args()
    
    # কনফিগারেশন তৈরি করুন
    config = {
        "settings": {
            "target_images": args.count,
            "max_threads": args.threads
        },
        "output_settings": {
            "base_dir": args.output
        }
    }
    
    # জেনারেটর তৈরি করুন
    generator = MassImageGenerator(
        prompt_file=args.prompts,
        target_count=args.count,
        config=config
    )
    
    # জেনারেশন শুরু করুন
    generator.start_generation()

if __name__ == "__main__":
    main()