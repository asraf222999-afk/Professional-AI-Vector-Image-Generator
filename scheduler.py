# mass_image_generator/scheduler.py
"""
শিডিউলার - অটোমেটিক ইমেজ জেনারেশন শিডিউলার
"""

import os
import sys
import time
import json
import schedule
import threading
from datetime import datetime, timedelta
from colorama import Fore, Style

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompt_generator import PromptFactory
from bulk_generator import MassImageGenerator

class ImageScheduler:
    """ইমেজ শিডিউলার ক্লাস"""
    
    def __init__(self, daily_target=200, config_file="config.json"):
        self.daily_target = daily_target
        self.config_file = config_file
        self.running = False
        self.thread = None
        
        # Load config
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        # Initialize components
        self.prompt_factory = PromptFactory(config_file)
        self.generator = None
        
        # Statistics
        self.stats = {
            "total_generated": 0,
            "daily_target": daily_target,
            "last_run": None,
            "runs_today": 0,
            "success_rate": 0
        }
        
        # Create logs directory
        os.makedirs("outputs/logs", exist_ok=True)
    
    def load_stats(self):
        """স্ট্যাটস লোড করুন"""
        stats_file = "outputs/logs/scheduler_stats.json"
        if os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                loaded_stats = json.load(f)
                
                # Check if it's from today
                today = datetime.now().strftime("%Y-%m-%d")
                if loaded_stats.get("date") == today:
                    self.stats.update(loaded_stats)
    
    def save_stats(self):
        """স্ট্যাটস সেভ করুন"""
        stats_file = "outputs/logs/scheduler_stats.json"
        
        # Add current date
        self.stats["date"] = datetime.now().strftime("%Y-%m-%d")
        self.stats["last_updated"] = datetime.now().isoformat()
        
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
    
    def generate_daily_images(self):
        """দৈনিক ইমেজ জেনারেট করুন"""
        
        print(f"\n{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}🚀 Starting daily image generation{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Target: {self.daily_target} images{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
        
        try:
            # Step 1: Generate prompts
            print(f"{Fore.BLUE}[1/3] Generating prompts...{Style.RESET_ALL}")
            prompts = self.prompt_factory.generate_batch(self.daily_target)
            
            # Save prompts
            prompt_file = f"prompts/daily_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
            self.prompt_factory.save_prompts(prompts, prompt_file)
            
            print(f"{Fore.GREEN}✓ Generated {len(prompts)} prompts{Style.RESET_ALL}")
            
            # Step 2: Generate images
            print(f"{Fore.BLUE}[2/3] Generating images...{Style.RESET_ALL}")
            
            self.generator = MassImageGenerator(
                prompt_file=prompt_file,
                target_count=min(self.daily_target, len(prompts)),
                config=self.config
            )
            
            results = self.generator.start_generation()
            
            # Update statistics
            self.stats["total_generated"] += results["generated"]
            self.stats["runs_today"] += 1
            self.stats["last_run"] = datetime.now().isoformat()
            self.stats["success_rate"] = results["success_rate"]
            
            print(f"{Fore.GREEN}✓ Generated {results['generated']} images{Style.RESET_ALL}")
            
            # Step 3: Backup
            print(f"{Fore.BLUE}[3/3] Creating backup...{Style.RESET_ALL}")
            
            try:
                from backup_system import backup_images_daily
                backup_images_daily()
                print(f"{Fore.GREEN}✓ Backup completed{Style.RESET_ALL}")
            except ImportError:
                print(f"{Fore.YELLOW}⚠ Backup system not available{Style.RESET_ALL}")
            
            # Save statistics
            self.save_stats()
            
            print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}✅ Daily generation completed!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Total generated today: {self.stats['total_generated']}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
            
            return results
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error in daily generation: {str(e)}{Style.RESET_ALL}")
            
            # Log error
            error_log = "outputs/logs/scheduler_errors.log"
            with open(error_log, 'a') as f:
                f.write(f"{datetime.now()} - {str(e)}\n")
            
            return None
    
    def generate_nightly_batch(self):
        """রাতের ব্যাচ জেনারেট করুন"""
        print(f"\n{Fore.MAGENTA}🌙 Starting nightly batch generation...{Style.RESET_ALL}")
        
        # Smaller batch for night
        nightly_target = self.daily_target // 2
        
        prompts = self.prompt_factory.generate_batch(nightly_target)
        prompt_file = f"prompts/nightly_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        self.prompt_factory.save_prompts(prompts, prompt_file)
        
        generator = MassImageGenerator(
            prompt_file=prompt_file,
            target_count=nightly_target,
            config=self.config
        )
        
        results = generator.start_generation()
        
        # Update stats
        self.stats["total_generated"] += results["generated"]
        self.save_stats()
        
        print(f"{Fore.MAGENTA}🌙 Nightly batch completed: {results['generated']} images{Style.RESET_ALL}")
        
        return results
    
    def cleanup_old_files(self, days_to_keep=7):
        """পুরানো ফাইলস ক্লিনআপ করুন"""
        print(f"{Fore.BLUE}🧹 Cleaning up old files...{Style.RESET_ALL}")
        
        import shutil
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Cleanup old image directories
        base_dir = "outputs/images"
        if os.path.exists(base_dir):
            for folder in os.listdir(base_dir):
                folder_path = os.path.join(base_dir, folder)
                
                try:
                    # Try to parse date from folder name
                    folder_date = datetime.strptime(folder, "%Y%m%d")
                    
                    if folder_date < cutoff_date:
                        shutil.rmtree(folder_path)
                        print(f"  Deleted: {folder_path}")
                except:
                    pass
        
        print(f"{Fore.GREEN}✓ Cleanup completed{Style.RESET_ALL}")
    
    def setup_schedule(self):
        """শিডিউল সেটআপ করুন"""
        
        # Daily morning batch (8 AM)
        schedule.every().day.at("08:00").do(self.generate_daily_images)
        
        # Afternoon batch (2 PM)
        schedule.every().day.at("14:00").do(
            lambda: self.generate_small_batch(self.daily_target // 3)
        )
        
        # Evening batch (8 PM)
        schedule.every().day.at("20:00").do(
            lambda: self.generate_small_batch(self.daily_target // 3)
        )
        
        # Nightly batch (2 AM)
        schedule.every().day.at("02:00").do(self.generate_nightly_batch)
        
        # Weekly cleanup (Sunday at 3 AM)
        schedule.every().sunday.at("03:00").do(self.cleanup_old_files)
        
        # Hourly status check
        schedule.every().hour.do(self.print_status)
    
    def generate_small_batch(self, count=50):
        """ছোট ব্যাচ জেনারেট করুন"""
        print(f"\n{Fore.CYAN}🔄 Generating small batch ({count} images)...{Style.RESET_ALL}")
        
        prompts = self.prompt_factory.generate_batch(count)
        prompt_file = f"prompts/batch_{datetime.now().strftime('%H%M')}.txt"
        self.prompt_factory.save_prompts(prompts, prompt_file)
        
        generator = MassImageGenerator(
            prompt_file=prompt_file,
            target_count=count,
            config=self.config
        )
        
        results = generator.start_generation()
        
        # Update stats
        self.stats["total_generated"] += results["generated"]
        self.save_stats()
        
        return results
    
    def print_status(self):
        """স্ট্যাটাস প্রিন্ট করুন"""
        print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📊 Scheduler Status{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Total Generated: {self.stats['total_generated']}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Runs Today: {self.stats['runs_today']}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Success Rate: {self.stats.get('success_rate', 0):.1f}%{Style.RESET_ALL}")
        
        # Next run
        if schedule.jobs:
            next_run = schedule.next_run()
            if next_run:
                print(f"{Fore.WHITE}Next Run: {next_run.strftime('%H:%M')}{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    
    def run_continuously(self):
        """ক্রমাগত রান করুন"""
        self.running = True
        
        # Load stats
        self.load_stats()
        
        # Setup schedule
        self.setup_schedule()
        
        # Print initial status
        self.print_status()
        
        print(f"\n{Fore.GREEN}✅ Scheduler started!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Press Ctrl+C to stop{Style.RESET_ALL}")
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}🛑 Scheduler stopped by user{Style.RESET_ALL}")
            self.running = False
        
        except Exception as e:
            print(f"\n{Fore.RED}❌ Scheduler error: {str(e)}{Style.RESET_ALL}")
            self.running = False
        
        finally:
            # Save final stats
            self.save_stats()
            print(f"{Fore.GREEN}📁 Stats saved to scheduler_stats.json{Style.RESET_ALL}")
    
    def run_in_thread(self):
        """থ্রেডে রান করুন"""
        self.thread = threading.Thread(target=self.run_continuously, daemon=True)
        self.thread.start()
        return self.thread
    
    def stop(self):
        """স্টপ করুন"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)

# কমান্ড লাইন ইন্টারফেস
def main():
    """মেইন ফাংশন"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Image Generation Scheduler")
    parser.add_argument("--daily", "-d", type=int, default=200, help="Daily target images")
    parser.add_argument("--run-once", "-r", action="store_true", help="Run once and exit")
    parser.add_argument("--small-batch", "-s", type=int, help="Run a small batch")
    
    args = parser.parse_args()
    
    scheduler = ImageScheduler(daily_target=args.daily)
    
    if args.run_once:
        # Run once
        scheduler.generate_daily_images()
    
    elif args.small_batch:
        # Run small batch
        scheduler.generate_small_batch(args.small_batch)
    
    else:
        # Run continuously
        scheduler.run_continuously()

if __name__ == "__main__":
    main()