import sys
from PIL import Image

img = Image.open(sys.argv[1]).convert("RGBA")
img = img.resize((32, 32))

for y in range(32):
    line = ""
    for x in range(32):
        r,g,b,a = img.getpixel((x,y))
        if a < 100:
            line += "."
        elif r>240 and g>240 and b>240:
            line += "W"
        else:
            line += "#"
    print(line)
