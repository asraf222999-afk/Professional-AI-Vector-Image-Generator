# mass_image_generator/multi_api_manager.py
"""
মাল্টি API ম্যানেজার - একাধিক ফ্রি API রোটেশন করে
"""

import os
import json
import time
import random
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import requests
import aiohttp
import asyncio

class APIManager:
    """API ম্যানেজার ক্লাস"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.apis = self.load_apis()
        self.api_stats = {}
        self.last_used_api = None
        self.rate_limits = {}
        
        # API keys লোড করুন
        self.api_keys = self.load_api_keys()
        
        # Initialize stats
        self.init_stats()
    
    def load_apis(self):
        """API গুলো লোড করুন"""
        
        apis = {
            "huggingface": {
                "name": "Hugging Face",
                "base_url": "https://api-inference.huggingface.co/models",
                "models": [
                    "stabilityai/stable-diffusion-2",
                    "runwayml/stable-diffusion-v1-5",
                    "CompVis/stable-diffusion-v1-4"
                ],
                "daily_limit": 100,
                "cost_per_call": 0,
                "requires_auth": True,
                "headers_template": {
                    "Authorization": "Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                "payload_template": {
                    "inputs": "{prompt}",
                    "parameters": {
                        "negative_prompt": "blurry, low quality, bad anatomy",
                        "num_inference_steps": 25,
                        "guidance_scale": 7.5,
                        "width": 512,
                        "height": 512
                    }
                }
            },
            
            "replicate": {
                "name": "Replicate",
                "base_url": "https://api.replicate.com/v1/predictions",
                "models": ["stability-ai/stable-diffusion"],
                "daily_limit": 50,
                "cost_per_call": 0.01,
                "requires_auth": True,
                "headers_template": {
                    "Authorization": "Token {api_key}",
                    "Content-Type": "application/json"
                },
                "payload_template": {
                    "version": "db21e45d3f7023abc2a46ee38a23973f6dce16bb082a930b0c49861f96d1e5bf",
                    "input": {
                        "prompt": "{prompt}",
                        "negative_prompt": "blurry",
                        "width": 512,
                        "height": 512,
                        "num_outputs": 1,
                        "num_inference_steps": 25
                    }
                }
            },
            
            "stability": {
                "name": "Stability AI",
                "base_url": "https://api.stability.ai/v1/generation",
                "models": ["stable-diffusion-xl-1024-v1-0"],
                "daily_limit": 25,
                "cost_per_call": 0,
                "requires_auth": True,
                "headers_template": {
                    "Authorization": "Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                "payload_template": {
                    "text_prompts": [
                        {
                            "text": "{prompt}",
                            "weight": 1
                        }
                    ],
                    "cfg_scale": 7,
                    "height": 512,
                    "width": 512,
                    "samples": 1,
                    "steps": 30
                }
            }
        }
        
        return apis
    
    def load_api_keys(self):
        """API keys লোড করুন"""
        api_keys = {}
        api_keys_dir = os.path.join(os.path.dirname(__file__), 'api_keys')
        
        # Create directory if not exists
        os.makedirs(api_keys_dir, exist_ok=True)
        
        # Load Hugging Face keys
        hf_file = os.path.join(api_keys_dir, 'huggingface_keys.json')
        if os.path.exists(hf_file):
            with open(hf_file, 'r') as f:
                api_keys['huggingface'] = json.load(f).get('keys', [])
        else:
            # Create sample file
            sample_keys = {
                "keys": ["hf_your_token_here"],
                "note": "Get free tokens from huggingface.co/settings/tokens"
            }
            with open(hf_file, 'w') as f:
                json.dump(sample_keys, f, indent=2)
            api_keys['huggingface'] = sample_keys['keys']
        
        # Load Replicate keys
        rep_file = os.path.join(api_keys_dir, 'replicate_keys.json')
        if os.path.exists(rep_file):
            with open(rep_file, 'r') as f:
                api_keys['replicate'] = json.load(f).get('keys', [])
        
        # Load Stability AI keys
        stab_file = os.path.join(api_keys_dir, 'stability_keys.json')
        if os.path.exists(stab_file):
            with open(stab_file, 'r') as f:
                api_keys['stability'] = json.load(f).get('keys', [])
        
        return api_keys
    
    def init_stats(self):
        """স্ট্যাটিস্টিক্স ইনিশিয়ালাইজ করুন"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        for api_name in self.apis.keys():
            self.api_stats[api_name] = {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'daily_calls': {today: 0},
                'last_used': None
            }
    
    def select_api(self):
        """সেরা API সিলেক্ট করুন"""
        
        available_apis = []
        
        for api_name, api_info in self.apis.items():
            # API enabled check
            if not api_info.get('enabled', True):
                continue
            
            # API keys available check
            if api_info['requires_auth']:
                if api_name not in self.api_keys or not self.api_keys[api_name]:
                    continue
            
            # Daily limit check
            today = datetime.now().strftime('%Y-%m-%d')
            daily_calls = self.api_stats[api_name]['daily_calls'].get(today, 0)
            
            if daily_calls < api_info['daily_limit']:
                available_apis.append(api_name)
        
        if not available_apis:
            # Reset daily counts if all limits reached
            self.reset_daily_counts_if_needed()
            return self.select_api()
        
        # Weighted selection based on remaining calls
        weights = []
        for api_name in available_apis:
            today = datetime.now().strftime('%Y-%m-%d')
            daily_calls = self.api_stats[api_name]['daily_calls'].get(today, 0)
            remaining = self.apis[api_name]['daily_limit'] - daily_calls
            weights.append(remaining)
        
        # Random selection with weights
        selected_api = random.choices(available_apis, weights=weights, k=1)[0]
        self.last_used_api = selected_api
        
        return selected_api
    
    def reset_daily_counts_if_needed(self):
        """ডেইলি কাউন্ট রিসেট করুন যদি নতুন দিন হয়ে থাকে"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        for api_name in self.apis.keys():
            days = list(self.api_stats[api_name]['daily_calls'].keys())
            if days and days[0] != today:
                # Old data, reset
                self.api_stats[api_name]['daily_calls'] = {today: 0}
    
    def get_api_key(self, api_name):
        """API key পাউন"""
        if api_name in self.api_keys and self.api_keys[api_name]:
            keys = self.api_keys[api_name]
            # Rotate through keys
            key_index = self.api_stats[api_name].get('key_index', 0)
            key = keys[key_index % len(keys)]
            
            # Update index for next time
            self.api_stats[api_name]['key_index'] = key_index + 1
            
            return key
        return None
    
    def generate_image(self, prompt):
        """ইমেজ জেনারেট করুন"""
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # API সিলেক্ট করুন
                api_name = self.select_api()
                api_info = self.apis[api_name]
                
                # API key নিন
                api_key = self.get_api_key(api_name)
                if not api_key and api_info['requires_auth']:
                    print(f"No API key for {api_name}, skipping...")
                    continue
                
                # Headers প্রিপেয়ার করুন
                headers = {}
                for key, value in api_info['headers_template'].items():
                    headers[key] = value.format(api_key=api_key)
                
                # Payload প্রিপেয়ার করুন
                payload = self.prepare_payload(api_info['payload_template'], prompt)
                
                # Model সিলেক্ট করুন
                model = random.choice(api_info['models'])
                
                # Request URL তৈরি করুন
                if api_name == "huggingface":
                    url = f"{api_info['base_url']}/{model}"
                elif api_name == "replicate":
                    url = api_info['base_url']
                elif api_name == "stability":
                    url = f"{api_info['base_url']}/{model}/text-to-image"
                else:
                    url = api_info['base_url']
                
                # Request সেন্ড করুন
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                
                # Response চেক করুন
                if response.status_code == 200:
                    # Update stats
                    self.update_stats(api_name, success=True)
                    
                    # Get image data
                    if api_name == "huggingface":
                        return response.content
                    elif api_name == "replicate":
                        # Replicate returns a JSON with get URL
                        result = response.json()
                        if 'urls' in result and 'get' in result['urls']:
                            get_url = result['urls']['get']
                            # Poll for result
                            return self.poll_replicate_result(get_url, headers)
                    elif api_name == "stability":
                        result = response.json()
                        if 'artifacts' in result and result['artifacts']:
                            import base64
                            image_data = base64.b64decode(result['artifacts'][0]['base64'])
                            return image_data
                
                else:
                    print(f"API {api_name} error: {response.status_code} - {response.text}")
                    self.update_stats(api_name, success=False)
                    
                    # Rate limit হলে delay করুন
                    if response.status_code == 429:
                        time.sleep(retry_delay * (attempt + 1))
                    
                    continue
                    
            except Exception as e:
                print(f"Error with API {api_name}: {str(e)}")
                if api_name in self.apis:
                    self.update_stats(api_name, success=False)
                time.sleep(retry_delay * (attempt + 1))
        
        return None
    
    def prepare_payload(self, template, prompt):
        """পেলোড প্রিপেয়ার করুন"""
        import json
        
        # Convert template to string and replace
        payload_str = json.dumps(template)
        payload_str = payload_str.replace("{prompt}", prompt)
        
        # Parse back to dict
        payload = json.loads(payload_str)
        
        return payload
    
    def poll_replicate_result(self, get_url, headers, max_attempts=30):
        """Replicate result পোল করুন"""
        
        for attempt in range(max_attempts):
            time.sleep(2)  # Wait 2 seconds between polls
            
            response = requests.get(get_url, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                
                if result['status'] == 'succeeded':
                    # Get output URL
                    if 'output' in result and result['output']:
                        output_url = result['output'][0] if isinstance(result['output'], list) else result['output']
                        
                        # Download image
                        image_response = requests.get(output_url)
                        if image_response.status_code == 200:
                            return image_response.content
                
                elif result['status'] == 'failed':
                    print(f"Replicate generation failed: {result.get('error', 'Unknown error')}")
                    return None
            
            # Still processing
            continue
        
        print("Replicate timeout after polling")
        return None
    
    def update_stats(self, api_name, success=True):
        """স্ট্যাটস আপডেট করুন"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        if api_name not in self.api_stats:
            self.api_stats[api_name] = {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'daily_calls': {today: 0},
                'last_used': None
            }
        
        # Update counts
        self.api_stats[api_name]['total_calls'] += 1
        self.api_stats[api_name]['daily_calls'][today] = \
            self.api_stats[api_name]['daily_calls'].get(today, 0) + 1
        
        if success:
            self.api_stats[api_name]['successful_calls'] += 1
        else:
            self.api_stats[api_name]['failed_calls'] += 1
        
        # Update last used time
        self.api_stats[api_name]['last_used'] = datetime.now().isoformat()
    
    def get_usage_stats(self):
        """ইউজেজ স্ট্যাটস গেট করুন"""
        stats = {}
        
        for api_name, api_stats in self.api_stats.items():
            stats[api_name] = {
                'total_calls': api_stats['total_calls'],
                'success_rate': (api_stats['successful_calls'] / api_stats['total_calls'] * 100 
                               if api_stats['total_calls'] > 0 else 0),
                'today_calls': api_stats['daily_calls'].get(datetime.now().strftime('%Y-%m-%d'), 0)
            }
        
        return stats
    
    def get_stats(self):
        """সম্পূর্ণ স্ট্যাটস গেট করুন"""
        return self.api_stats
    
    def save_stats(self):
        """স্ট্যাটস সেভ করুন"""
        stats_file = os.path.join('outputs', 'logs', 'api_stats.json')
        os.makedirs(os.path.dirname(stats_file), exist_ok=True)
        
        with open(stats_file, 'w') as f:
            json.dump(self.api_stats, f, indent=2, default=str)

# Async version for better performance
class AsyncAPIManager(APIManager):
    """Async API Manager"""
    
    async def generate_image_async(self, prompt):
        """Async ইমেজ জেনারেট করুন"""
        
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                api_name = self.select_api()
                api_info = self.apis[api_name]
                api_key = self.get_api_key(api_name)
                
                if not api_key and api_info['requires_auth']:
                    continue
                
                # Prepare request
                headers = {}
                for key, value in api_info['headers_template'].items():
                    headers[key] = value.format(api_key=api_key)
                
                payload = self.prepare_payload(api_info['payload_template'], prompt)
                model = random.choice(api_info['models'])
                
                # Build URL
                if api_name == "huggingface":
                    url = f"{api_info['base_url']}/{model}"
                elif api_name == "replicate":
                    url = api_info['base_url']
                elif api_name == "stability":
                    url = f"{api_info['base_url']}/{model}/text-to-image"
                else:
                    url = api_info['base_url']
                
                # Async request
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=payload, timeout=60) as response:
                        
                        if response.status == 200:
                            self.update_stats(api_name, success=True)
                            
                            if api_name == "huggingface":
                                return await response.read()
                            elif api_name == "replicate":
                                result = await response.json()
                                if 'urls' in result:
                                    get_url = result['urls']['get']
                                    return await self.poll_replicate_result_async(get_url, headers)
                            elif api_name == "stability":
                                result = await response.json()
                                if 'artifacts' in result:
                                    import base64
                                    image_data = base64.b64decode(result['artifacts'][0]['base64'])
                                    return image_data
                        
                        else:
                            error_text = await response.text()
                            print(f"API {api_name} error: {response.status} - {error_text}")
                            self.update_stats(api_name, success=False)
                            
                            if response.status == 429:
                                await asyncio.sleep(2 * (attempt + 1))
                            
                            continue
                            
            except Exception as e:
                print(f"Error with API {api_name}: {str(e)}")
                if api_name in self.apis:
                    self.update_stats(api_name, success=False)
                await asyncio.sleep(2 * (attempt + 1))
        
        return None
    
    async def poll_replicate_result_async(self, get_url, headers, max_attempts=30):
        """Async replicate result পোল করুন"""
        
        async with aiohttp.ClientSession() as session:
            for attempt in range(max_attempts):
                await asyncio.sleep(2)
                
                async with session.get(get_url, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if result['status'] == 'succeeded':
                            output_url = result['output'][0] if isinstance(result['output'], list) else result['output']
                            
                            # Download image
                            async with session.get(output_url) as img_response:
                                if img_response.status == 200:
                                    return await img_response.read()
                        
                        elif result['status'] == 'failed':
                            print(f"Replicate generation failed: {result.get('error', 'Unknown error')}")
                            return None
        
        print("Replicate timeout after polling")
        return None

if __name__ == "__main__":
    # টেস্ট করুন
    manager = APIManager()
    
    # Test API selection
    for _ in range(10):
        api = manager.select_api()
        print(f"Selected API: {api}")
    
    # Test stats
    print("\nAPI Stats:", json.dumps(manager.get_stats(), indent=2))