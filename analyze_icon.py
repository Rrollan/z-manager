from PIL import Image

img = Image.open("public/icon.png").convert("RGBA")
img = img.resize((32, 32))

for y in range(32):
    line = ""
    for x in range(32):
        r,g,b,a = img.getpixel((x,y))
        # if bright, print ' ', if dark print '#'
        if r>200 and g>200 and b>200:
            line += " "
        else:
            line += "#"
    print(line)
