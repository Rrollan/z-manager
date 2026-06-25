from PIL import Image, ImageChops

def trim_white_border(image_path, output_path):
    img = Image.open(image_path).convert("RGBA")
    
    # Create a white background image of the same size
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    diff = ImageChops.difference(img, bg)
    
    # Alternatively, find bounding box of non-white
    # Convert diff to grayscale
    diff = diff.convert("L")
    bbox = diff.getbbox()
    
    if bbox:
        # crop the image
        img = img.crop(bbox)
        
        # pad it slightly if needed, or make it square
        width, height = img.size
        size = max(width, height)
        # add 5% padding
        pad = int(size * 0.05)
        new_size = size + 2 * pad
        
        new_img = Image.new("RGBA", (new_size, new_size), (255, 255, 255, 0))
        
        # paste the cropped image into the center
        paste_x = (new_size - width) // 2
        paste_y = (new_size - height) // 2
        new_img.paste(img, (paste_x, paste_y))
        
        new_img.save(output_path)
        print(f"Cropped and saved {output_path}")
    else:
        print("Could not find bounding box")

trim_white_border("public/icon.png", "public/icon.png")
trim_white_border("src-tauri/icons/icon.png", "src-tauri/icons/icon.png")

