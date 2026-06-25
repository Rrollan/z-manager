from PIL import Image

img = Image.open("src-tauri/icons/icon_master_squircle.png").convert("RGBA")
width, height = img.size

# Find the background color of the squircle
# Start from center, go UP until we hit something or stay on the background color
bg_color = None
for y in range(height//2, 0, -1):
    r,g,b,a = img.getpixel((width//2, y))
    # the logo is in the very center, let's just pick a pixel half-way between center and top edge
    pass

bg_color = img.getpixel((width//2, int(height*0.2)))
print(f"Background color chosen: {bg_color}")

# Create a new image filled with the background color
new_img = Image.new("RGBA", (width, height), bg_color)
# Paste the original on top, using it as a mask so transparent pixels get the background color
new_img.paste(img, (0, 0), img)
new_img.save("public/icon.png")
new_img.save("src-tauri/icons/icon.png")
print("Saved filled icon")
