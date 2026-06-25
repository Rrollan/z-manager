from PIL import Image

img = Image.open("src-tauri/icons/icon_master_squircle.png").convert("RGBA")
width, height = img.size

# Pick a pixel just inside the top edge
color = img.getpixel((width//2, int(height*0.05)))
print(f"Top edge color: {color}")

# Pick a pixel near the left edge
color2 = img.getpixel((int(width*0.05), height//2))
print(f"Left edge color: {color2}")
