from PIL import Image

img = Image.open("src-tauri/icons/icon.png").convert("RGBA")
width, height = img.size

# Find the background color of the squircle by checking a pixel near the edge but inside the squircle
# Let's say center-top but down a bit
bg_color = img.getpixel((width//2, int(height*0.1)))

# Create a new image filled with the background color
new_img = Image.new("RGBA", (width, height), bg_color)
new_img.paste(img, (0, 0), img)
new_img.save("src-tauri/icons/icon.png")
new_img.save("public/icon.png")

print(f"Filled background with {bg_color}")
