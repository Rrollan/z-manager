from PIL import Image

img = Image.open("src-tauri/icons/icon_master_squircle.png").convert("RGBA")
img = img.resize((32, 32))

for y in range(32):
    line = ""
    for x in range(32):
        r,g,b,a = img.getpixel((x,y))
        if a < 100:
            line += "."
        elif r>200 and g>200 and b>200:
            line += " "
        else:
            line += "#"
    print(line)
