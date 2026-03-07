#!/usr/bin/env python3
"""
Script to create download icon PNG
Requires: pip install pillow
"""

from PIL import Image, ImageDraw

def create_download_icon(png_path, size=512):
    """Create download icon PNG with specified size"""
    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Scale factor
    scale = size / 24
    stroke_width = max(2, int(2 * scale))
    
    # Draw the download icon
    # Box at bottom
    box_top = int(15 * scale)
    box_bottom = int(21 * scale)
    box_left = int(3 * scale)
    box_right = int(21 * scale)
    corner_radius = int(2 * scale)
    
    # Draw rounded rectangle (box)
    draw.rounded_rectangle(
        [box_left, box_top, box_right, box_bottom],
        radius=corner_radius,
        outline=(0, 0, 0, 255),
        width=stroke_width
    )
    
    # Draw arrow shaft (vertical line)
    line_x = int(12 * scale)
    line_top = int(3 * scale)
    line_bottom = int(15 * scale)
    draw.line([(line_x, line_top), (line_x, line_bottom)], 
              fill=(0, 0, 0, 255), width=stroke_width)
    
    # Draw arrow head (two lines forming V)
    arrow_y = int(15 * scale)
    arrow_left_x = int(7 * scale)
    arrow_right_x = int(17 * scale)
    arrow_top_y = int(10 * scale)
    
    draw.line([(arrow_left_x, arrow_top_y), (line_x, arrow_y)], 
              fill=(0, 0, 0, 255), width=stroke_width)
    draw.line([(line_x, arrow_y), (arrow_right_x, arrow_top_y)], 
              fill=(0, 0, 0, 255), width=stroke_width)
    
    # Save
    img.save(png_path, 'PNG')
    print(f"✓ Created {png_path} ({size}x{size}px)")

if __name__ == "__main__":
    # Create different sizes
    create_download_icon("static/download-icon-512.png", 512)
    create_download_icon("static/download-icon-1024.png", 1024)
    
    print("\nDone! Files created:")
    print("- static/download-icon-512.png (512x512)")
    print("- static/download-icon-1024.png (1024x1024)")
