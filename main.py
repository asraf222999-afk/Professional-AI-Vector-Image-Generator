# mass_image_generator/main.py
#!/usr/bin/env python3
"""
মেইন প্রোগ্রাম - হাজার হাজার ইমেজ জেনারেটর
Author: AI Assistant
Version: 2.0.0
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from prompt_generator import PromptFactory
from bulk_generator import MassImageGenerator
from multi_api_manager import APIManager
from scheduler import ImageScheduler
from utils.file_manager import FileManager

class MassImageGeneratorCLI:
    """মেইন CLI ক্লাস"""
    
    def __init__(self):
        self.config = self.load_config()
        self.file_manager = FileManager()
        self.api_manager = APIManager()
        self.prompt_factory = PromptFactory()
        self.generator = None
        
    def load_config(self):
        """কনফিগারেশন লোড করুন"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def print_banner(self):
        """ব্যানার প্রিন্ট করুন"""
        banner = f"""
{Fore.CYAN}{'='*60}
{Fore.YELLOW}    ███╗   ███╗ █████╗ ███████╗███████╗    ██╗███╗   ███╗
{Fore.YELLOW}    ████╗ ████║██╔══██╗██╔════╝██╔════╝    ██║████╗ ████║
{Fore.YELLOW}    ██╔████╔██║███████║███████╗███████╗    ██║██╔████╔██║
{Fore.YELLOW}    ██║╚██╔╝██║██╔══██║╚════██║╚════██║    ██║██║╚██╔╝██║
{Fore.YELLOW}    ██║ ╚═╝ ██║██║  ██║███████║███████║    ██║██║ ╚═╝ ██║
{Fore.YELLOW}    ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝    ╚═╝╚═╝     ╚═╝
{Fore.GREEN}          হাজার হাজার ফ্রি AI ইমেজ জেনারেটর
{Fore.CYAN}{'='*60}
{Fore.WHITE}Version: 2.0.0 | Date: {datetime.now().strftime('%Y-%m-%d')}
{Fore.CYAN}{'='*60}{Style.RESET_ALL}
        """
        print(banner)
    
    def setup_environment(self):
        """এনভায়রনমেন্ট সেটআপ করুন"""
        print(f"{Fore.YELLOW}[1/5] এনভায়রনমেন্ট চেক করছি...{Style.RESET_ALL}")
        
        # Create directories
        dirs = ['outputs/images', 'outputs/metadata', 'outputs/logs', 
                'prompts', 'api_keys', 'utils']
        
        for directory in dirs:
            os.makedirs(directory, exist_ok=True)
            print(f"{Fore.GREEN}  ✓ {directory}{Style.RESET_ALL}")
        
        # Check requirements
        try:
            import requests
            import pillow
            import tqdm
            print(f"{Fore.GREEN}  ✓ সব লাইব্রেরি ঠিক আছে{Style.RESET_ALL}")
        except ImportError as e:
            print(f"{Fore.RED}  ✗ লাইব্রেরি মিসিং: {e}{Style.RESET_ALL}")
            self.install_requirements()
    
    def install_requirements(self):
        """রিকোয়ারমেন্টস ইনস্টল করুন"""
        print(f"{Fore.YELLOW}লাইব্রেরি ইনস্টল করছি...{Style.RESET_ALL}")
        os.system(f"{sys.executable} -m pip install -r requirements.txt")
    
    def generate_prompts(self, count=1000):
        """প্রম্পট জেনারেট করুন"""
        print(f"{Fore.YELLOW}[2/5] {count}টি প্রম্পট জেনারেট করছি...{Style.RESET_ALL}")
        
        prompts = self.prompt_factory.generate_batch(count)
        
        # Save prompts
        prompt_file = os.path.join('prompts', f'prompts_{count}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
        with open(prompt_file, 'w', encoding='utf-8') as f:
            for prompt in prompts:
                f.write(prompt + '\n')
        
        print(f"{Fore.GREEN}  ✓ {len(prompts)}টি প্রম্পট সেভ করা হয়েছে: {prompt_file}{Style.RESET_ALL}")
        return prompt_file
    
    def generate_images(self, prompt_file, target_count):
        """ইমেজ জেনারেট করুন"""
        print(f"{Fore.YELLOW}[3/5] {target_count}টি ইমেজ জেনারেট করছি...{Style.RESET_ALL}")
        
        self.generator = MassImageGenerator(
            prompt_file=prompt_file,
            target_count=target_count,
            config=self.config
        )
        
        results = self.generator.start_generation()
        
        print(f"{Fore.GREEN}  ✓ {len(results)}টি ইমেজ জেনারেট করা হয়েছে!{Style.RESET_ALL}")
        return results
    
    def start_scheduler(self, daily_target=200):
        """শিডিউলার শুরু করুন"""
        print(f"{Fore.YELLOW}[4/5] অটোমেটিক শিডিউলার শুরু করছি...{Style.RESET_ALL}")
        
        scheduler = ImageScheduler(daily_target=daily_target)
        scheduler.run_continuously()
    
    def show_stats(self):
        """স্ট্যাটিস্টিক্স দেখান"""
        print(f"{Fore.YELLOW}[5/5] রিপোর্ট তৈরি করছি...{Style.RESET_ALL}")
        
        stats_file = os.path.join('outputs', 'stats.json')
        stats = {
            "total_images": self.generator.generated_count if self.generator else 0,
            "success_rate": self.generator.success_rate if self.generator else 0,
            "apis_used": self.api_manager.get_stats(),
            "timestamp": datetime.now().isoformat(),
            "output_directory": os.path.abspath('outputs/images')
        }
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}🎉 সম্পূর্ণ হয়েছে!{Style.RESET_ALL}")
        print(f"{Fore.WHITE}মোট ইমেজ: {stats['total_images']}")
        print(f"সফলতার হার: {stats['success_rate']:.1f}%")
        print(f"আউটপুট ফোল্ডার: {stats['output_directory']}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    def run(self, args):
        """মেইন রান ফাংশন"""
        self.print_banner()
        self.setup_environment()
        
        if args.mode == "single":
            # Single batch generation
            prompt_file = self.generate_prompts(args.count)
            self.generate_images(prompt_file, args.count)
            self.show_stats()
            
        elif args.mode == "bulk":
            # Bulk generation
            prompt_file = self.generate_prompts(args.count)
            self.generate_images(prompt_file, args.count)
            self.show_stats()
            
        elif args.mode == "auto":
            # Automatic scheduler
            self.start_scheduler(args.daily_target)
            
        elif args.mode == "prompts":
            # Only generate prompts
            self.generate_prompts(args.count)
            
        else:
            print(f"{Fore.RED}অজানা মোড: {args.mode}{Style.RESET_ALL}")

def main():
    """মেইন এন্ট্রি পয়েন্ট"""
    parser = argparse.ArgumentParser(
        description="হাজার হাজার ফ্রি AI ইমেজ জেনারেটর",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
উদাহরণ:
  python main.py single --count 100
  python main.py bulk --count 1000
  python main.py auto --daily-target 200
  python main.py prompts --count 5000
        """
    )
    
    parser.add_argument(
        "mode",
        choices=["single", "bulk", "auto", "prompts"],
        help="জেনারেশন মোড"
    )
    
    parser.add_argument(
        "--count", "-c",
        type=int,
        default=100,
        help="কতগুলো ইমেজ/প্রম্পট জেনারেট করতে চান"
    )
    
    parser.add_argument(
        "--daily-target", "-d",
        type=int,
        default=200,
        help="দৈনিক টার্গেট (auto মোডের জন্য)"
    )
    
    parser.add_argument(
        "--threads", "-t",
        type=int,
        default=4,
        help="কতগুলো থ্রেড ব্যবহার করবেন"
    )
    
    args = parser.parse_args()
    
    # Run the generator
    generator = MassImageGeneratorCLI()
    generator.run(args)

if __name__ == "__main__":
    main()