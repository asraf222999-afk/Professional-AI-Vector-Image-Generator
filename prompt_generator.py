# mass_image_generator/prompt_generator.py
"""
প্রম্পট জেনারেটর - হাজার হাজার ইউনিক প্রম্পট তৈরি করে
"""

import os
import json
import random
from typing import List, Dict
from datetime import datetime

class PromptFactory:
    """প্রম্পট ফ্যাক্টরি ক্লাস"""
    
    def __init__(self, config_file="config.json"):
        # লোড কনফিগারেশন
        config_path = os.path.join(os.path.dirname(__file__), config_file)
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # বাংলা এবং ইংলিশ ডেটা
        self.load_data()
        
    def load_data(self):
        """ডেটা লোড করুন"""
        # বিষয়বস্তু
        self.subjects_bn = [
            "বাংলাদেশের দৃশ্য", "সুন্দরবন", "পাহাড়", "নদী", "চা বাগান",
            "রিকশা", "নৌকা", "মসজিদ", "মন্দির", "ফুল", "পাখি", "মাছ",
            "গ্রামের দৃশ্য", "হাটবাজার", "ঐতিহ্যবাহী পোশাক", "নকশীকাঁথা",
            "আমের বাগান", "ধান ক্ষেত", "পদ্ম ফুল", "শাপলা", "কাক", "দোয়েল",
            "বাংলা বর্ণমালা", "ঐতিহাসিক স্থাপত্য", "সংশপ্তক", "জামদানি"
        ]
        
        self.subjects_en = [
            "cat", "dog", "tree", "mountain", "river", "building", "car",
            "flower", "bird", "person", "cityscape", "animal", "fantasy creature",
            "robot", "spaceship", "castle", "forest", "beach", "sunset",
            "abstract pattern", "geometric shape", "food", "instrument"
        ]
        
        # স্টাইল
        self.styles = [
            "vector art", "minimalist", "geometric", "line drawing",
            "flat design", "isometric", "pixel art", "watercolor",
            "oil painting", "sketch", "cartoon", "anime", "realistic",
            "abstract", "surreal", "impressionist", "art deco",
            "cyberpunk", "steampunk", "vintage"
        ]
        
        # রং
        self.colors = [
            "red", "blue", "green", "yellow", "purple", "orange",
            "monochrome", "pastel colors", "vibrant colors", "neon colors",
            "gradient", "rainbow", "gold and silver", "earth tones",
            "cool colors", "warm colors", "black and white"
        ]
        
        # বিশেষণ
        self.adjectives_bn = [
            "সুন্দর", "আকর্ষণীয়", "জটিল", "সহজ", "বিশাল", "ক্ষুদ্র",
            "রঙিন", "উজ্জ্বল", "মোহনীয়", "অদ্বিতীয়", "ঐতিহ্যবাহী",
            "আধুনিক", "প্রাচীন", "ভবিষ্যতের", "কল্পনাপ্রসূত", "বাস্তবিক"
        ]
        
        self.adjectives_en = [
            "beautiful", "stunning", "intricate", "simple", "massive",
            "tiny", "colorful", "bright", "mesmerizing", "unique",
            "traditional", "modern", "ancient", "futuristic", "fantastical",
            "realistic", "detailed", "epic", "majestic", "cute"
        ]
        
        # এডভার্বস
        self.adverbs = [
            "elegantly", "boldly", "gracefully", "powerfully", "delicately",
            "intricately", "simply", "complexly", "abstractly", "realistically"
        ]
        
        # মিডিয়া
        self.media = [
            "digital art", "illustration", "painting", "drawing",
            "3D render", "photograph", "engraving", "etching",
            "screen print", "woodcut", "mosaic", "stained glass"
        ]
        
        # লাইটিং
        self.lighting = [
            "dramatic lighting", "soft lighting", "backlit", "rim light",
            "golden hour", "blue hour", "studio lighting", "natural light",
            "moonlight", "sunlight", "neon lights", "bioluminescent"
        ]
        
        # কম্পোজিশন
        self.composition = [
            "close-up", "wide shot", "aerial view", "macro",
            "portrait", "landscape", "symmetrical", "rule of thirds",
            "centered", "dynamic angle", "bird's eye view", "worm's eye view"
        ]
    
    def generate_single_prompt(self, language="en"):
        """একটি প্রম্পট জেনারেট করুন"""
        
        if language == "bn":
            subject = random.choice(self.subjects_bn)
            adjective = random.choice(self.adjectives_bn)
            style = random.choice(self.styles)
            color = random.choice(self.colors)
            
            templates = [
                f"{adjective} {subject}, {style} স্টাইল, {color} রং",
                f"{style} শৈলীতে {subject}, {color} রঙের সমাহার",
                f"{adjective} {color} {subject}, {style} ডিজাইন",
                f"{subject} এর {style} চিত্রণ, {color} প্যালেট"
            ]
            
        else:  # English
            subject = random.choice(self.subjects_en)
            adjective = random.choice(self.adjectives_en)
            style = random.choice(self.styles)
            color = random.choice(self.colors)
            adverb = random.choice(self.adverbs)
            media = random.choice(self.media)
            light = random.choice(self.lighting)
            comp = random.choice(self.composition)
            
            templates = [
                f"{adjective} {subject}, {style} style, {color} colors, {media}",
                f"{style} {media} of {adjective} {subject}, {color} palette, {light}",
                f"{adverb} rendered {media} of {subject}, {style}, {color}, {comp}",
                f"{adjective} {style} {subject} with {color} colors, {light}, {comp}",
                f"{subject} in {style} style, {color} colors, {media}, {light}"
            ]
        
        return random.choice(templates)
    
    def generate_batch(self, count=1000, language="mixed"):
        """বহু সংখ্যক প্রম্পট জেনারেট করুন"""
        
        prompts = set()
        attempt = 0
        max_attempts = count * 2
        
        while len(prompts) < count and attempt < max_attempts:
            attempt += 1
            
            # ভাষা সিলেক্ট করুন
            if language == "mixed":
                current_lang = random.choice(["en", "bn", "en"])
            else:
                current_lang = language
            
            prompt = self.generate_single_prompt(current_lang)
            
            # ইউনিকনেস চেক করুন
            if prompt not in prompts:
                prompts.add(prompt)
            
            # প্রোগ্রেস শো করুন
            if attempt % 100 == 0:
                print(f"Generated {len(prompts)}/{count} unique prompts...")
        
        # যদি যথেষ্ট ইউনিক প্রম্পট না মেলে
        if len(prompts) < count:
            print(f"Warning: Could only generate {len(prompts)} unique prompts")
        
        return list(prompts)
    
    def generate_from_template(self, template_count=100):
        """টেম্পলেট থেকে প্রম্পট জেনারেট করুন"""
        
        templates = []
        template_file = os.path.join('prompts', 'prompt_templates.json')
        
        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                templates = json.load(f)
        
        if not templates:
            # ডিফল্ট টেম্পলেটস
            templates = [
                "{adjective} {subject} in {style} style with {color} colors",
                "{style} illustration of {adjective} {subject}, {media}",
                "{subject} {style} art, {color} palette, {lighting}",
                "{adjective} {media} of {subject}, {style}, {composition}"
            ]
        
        prompts = []
        for _ in range(template_count):
            template = random.choice(templates)
            
            # প্লেসহোল্ডার রিপ্লেস করুন
            prompt = template
            prompt = prompt.replace("{adjective}", random.choice(self.adjectives_en))
            prompt = prompt.replace("{subject}", random.choice(self.subjects_en))
            prompt = prompt.replace("{style}", random.choice(self.styles))
            prompt = prompt.replace("{color}", random.choice(self.colors))
            prompt = prompt.replace("{media}", random.choice(self.media))
            prompt = prompt.replace("{lighting}", random.choice(self.lighting))
            prompt = prompt.replace("{composition}", random.choice(self.composition))
            prompt = prompt.replace("{adverb}", random.choice(self.adverbs))
            
            prompts.append(prompt)
        
        return prompts
    
    def save_prompts(self, prompts, filename=None):
        """প্রম্পটস সেভ করুন"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"prompts_{len(prompts)}_{timestamp}.txt"
        
        # ফোল্ডার তৈরি করুন
        os.makedirs('prompts', exist_ok=True)
        filepath = os.path.join('prompts', filename)
        
        # সেভ করুন
        with open(filepath, 'w', encoding='utf-8') as f:
            for prompt in prompts:
                f.write(prompt + '\n')
        
        # JSON ভার্সনও সেভ করুন
        json_file = filepath.replace('.txt', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                "count": len(prompts),
                "generated_at": datetime.now().isoformat(),
                "prompts": prompts
            }, f, indent=2, ensure_ascii=False)
        
        print(f"Prompts saved to: {filepath}")
        print(f"JSON version: {json_file}")
        
        return filepath

# ইউটিলিটি ফাংশন
def create_sample_prompts():
    """স্যাম্পল প্রম্পটস তৈরি করুন"""
    factory = PromptFactory()
    
    # ছোট স্যাম্পল সেট
    print("Creating sample prompts...")
    prompts = factory.generate_batch(50, language="mixed")
    
    # সেভ করুন
    factory.save_prompts(prompts, "sample_prompts.txt")
    
    print(f"Created {len(prompts)} sample prompts")
    return prompts

if __name__ == "__main__":
    # টেস্ট করুন
    factory = PromptFactory()
    
    # একটি প্রম্পট জেনারেট করুন
    print("বাংলা প্রম্পট:", factory.generate_single_prompt("bn"))
    print("ইংরেজি প্রম্পট:", factory.generate_single_prompt("en"))
    
    # ১০টি প্রম্পট জেনারেট করুন
    # prompts = factory.generate_batch(10)
    # for i, prompt in enumerate(prompts, 1):
    #     print(f"{i}. {prompt}")