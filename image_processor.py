# mass_image_generator/image_processor.py
"""
ইমেজ প্রসেসর - ইমেজ প্রসেসিং ইউটিলিটি ফাংশন
"""

import os
import io
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
from typing import Optional, Tuple, List

class ImageProcessor:
    """ইমেজ প্রসেসর ক্লাস"""
    
    def __init__(self, default_quality=85):
        self.default_quality = default_quality
        
    def save_image(self, image_data, filepath, format='PNG', quality=None):
        """ইমেজ সেভ করুন"""
        
        # Create directory if not exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        if isinstance(image_data, bytes):
            # Save bytes directly
            with open(filepath, 'wb') as f:
                f.write(image_data)
        elif isinstance(image_data, Image.Image):
            # Save PIL Image
            if quality is None:
                quality = self.default_quality
            
            image_data.save(filepath, format=format, quality=quality, optimize=True)
        else:
            raise ValueError("Unsupported image data type")
        
        return filepath
    
    def load_image(self, filepath):
        """ইমেজ লোড করুন"""
        return Image.open(filepath)
    
    def resize_image(self, image, size=(512, 512), keep_aspect=True):
        """ইমেজ রিসাইজ করুন"""
        if keep_aspect:
            image.thumbnail(size, Image.Resampling.LANCZOS)
        else:
            image = image.resize(size, Image.Resampling.LANCZOS)
        
        return image
    
    def optimize_image(self, image, max_size_kb=500):
        """ইমেজ অপ্টিমাইজ করুন"""
        # Convert to RGB if RGBA
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        
        # Optimize quality
        quality = 95
        while True:
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=quality, optimize=True)
            size_kb = len(buffer.getvalue()) / 1024
            
            if size_kb <= max_size_kb or quality <= 50:
                break
            
            quality -= 5
        
        return image, quality
    
    def create_thumbnail(self, image, size=(256, 256)):
        """থাম্বনেইল তৈরি করুন"""
        return self.resize_image(image.copy(), size)
    
    def batch_process(self, input_dir, output_dir, process_func, **kwargs):
        """ব্যাচ প্রসেস করুন"""
        os.makedirs(output_dir, exist_ok=True)
        
        processed = 0
        for filename in os.listdir(input_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                input_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, filename)
                
                try:
                    image = self.load_image(input_path)
                    processed_image = process_func(image, **kwargs)
                    processed_image.save(output_path)
                    processed += 1
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
        
        return processed
    
    def extract_colors(self, image, num_colors=5):
        """রং এক্সট্র্যাক্ট করুন"""
        # Reduce colors
        image = image.convert('P', palette=Image.ADAPTIVE, colors=num_colors)
        palette = image.getpalette()
        
        colors = []
        for i in range(num_colors):
            idx = i * 3
            colors.append((palette[idx], palette[idx+1], palette[idx+2]))
        
        return colors
    
    def add_watermark(self, image, watermark_text="AI Generated"):
        """ওয়াটারমার্ক যোগ করুন"""
        from PIL import ImageDraw, ImageFont
        
        # Create a copy
        result = image.copy()
        
        try:
            # Try to load font
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            # Use default font
            font = ImageFont.load_default()
        
        # Create drawing context
        draw = ImageDraw.Draw(result)
        
        # Calculate text size and position
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Position at bottom-right
        margin = 10
        position = (
            image.width - text_width - margin,
            image.height - text_height - margin
        )
        
        # Draw semi-transparent background
        bg_bbox = (
            position[0] - 5,
            position[1] - 3,
            position[0] + text_width + 5,
            position[1] + text_height + 3
        )
        draw.rectangle(bg_bbox, fill=(0, 0, 0, 128))
        
        # Draw text
        draw.text(position, watermark_text, font=font, fill=(255, 255, 255, 200))
        
        return result
    
    def create_collage(self, images, grid_size=(3, 3), output_size=(1024, 1024)):
        """কলাজ তৈরি করুন"""
        if len(images) > grid_size[0] * grid_size[1]:
            images = images[:grid_size[0] * grid_size[1]]
        
        # Calculate cell size
        cell_width = output_size[0] // grid_size[1]
        cell_height = output_size[1] // grid_size[0]
        
        # Create blank canvas
        collage = Image.new('RGB', output_size, (255, 255, 255))
        
        # Paste images
        for i, img in enumerate(images):
            if isinstance(img, str):
                img = self.load_image(img)
            
            # Resize image to fit cell
            img = self.resize_image(img, (cell_width, cell_height))
            
            # Calculate position
            row = i // grid_size[1]
            col = i % grid_size[1]
            position = (col * cell_width, row * cell_height)
            
            # Paste image
            collage.paste(img, position)
        
        return collage

# ইউটিলিটি ফাংশন
def compress_images_in_folder(folder_path, quality=85, max_width=1024):
    """ফোল্ডারে সব ইমেজ কম্প্রেস করুন"""
    processor = ImageProcessor()
    
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            input_path = os.path.join(folder_path, filename)
            
            try:
                # Load image
                img = processor.load_image(input_path)
                
                # Resize if too large
                if img.width > max_width:
                    new_height = int(img.height * (max_width / img.width))
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                # Optimize and save
                img_optimized, actual_quality = processor.optimize_image(img)
                
                # Save with optimized quality
                output_path = os.path.join(folder_path, f"compressed_{filename}")
                img_optimized.save(output_path, quality=actual_quality, optimize=True)
                
                print(f"Compressed: {filename} -> quality: {actual_quality}")
                
            except Exception as e:
                print(f"Error compressing {filename}: {e}")

if __name__ == "__main__":
    # টেস্ট করুন
    processor = ImageProcessor()
    
    # Create a test image
    test_image = Image.new('RGB', (512, 512), color='red')
    
    # Save it
    processor.save_image(test_image, 'test_output/test_image.png')
    print("Test image saved")
    
    # Test thumbnail
    thumb = processor.create_thumbnail(test_image, (100, 100))
    processor.save_image(thumb, 'test_output/thumbnail.png')
    print("Thumbnail created")