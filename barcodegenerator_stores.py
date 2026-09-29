from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import os

# ================= SETTINGS =================
N_BINS = 30                     # Change only this
OUTPUT_FOLDER = "Engineering_Store_Barcodes"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Label size (50 x 25 mm @300 DPI)
DPI = 300
LABEL_WIDTH = int(50 * DPI / 25.4)     # 591 px
LABEL_HEIGHT = int(25 * DPI / 25.4)    # 295 px

barcode_options = {
    "module_width": 0.22,
    "module_height": 18,
    "quiet_zone": 5,
    "write_text": False,
    "dpi": DPI
}

# Load bold font
font = None
for p in [
    "C:/Windows/Fonts/arialbd.ttf",
    "arialbd.ttf",
]:
    try:
        font = ImageFont.truetype(p, 46)
        break
    except:
        pass

if font is None:
    font = ImageFont.load_default()

count = 0

for rack in ["A", "B", "C"]:
    for partition in range(1, 4):
        for layer in range(1, 5):
            for bin_no in range(1, N_BINS + 1):

                location = f"{rack}/P{partition}/L{layer}/B{bin_no}"

                # Generate barcode
                barcode = Code128(location, writer=ImageWriter())
                barcode_img = barcode.render(writer_options=barcode_options)

                barcode_width = LABEL_WIDTH - 30
                barcode_height = 165

                barcode_img = barcode_img.resize(
                    (barcode_width, barcode_height),
                    Image.LANCZOS
                )

                # Coordinates FIRST (needed for border)
                x_bar = (LABEL_WIDTH - barcode_width) // 2
                y_bar = 12

                # Create label
                label = Image.new("RGB", (LABEL_WIDTH, LABEL_HEIGHT), "white")
                draw = ImageDraw.Draw(label)

                # Paste barcode
                label.paste(barcode_img, (x_bar, y_bar))

                # Draw text
                bbox = draw.textbbox((0, 0), location, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                x_text = (LABEL_WIDTH - text_width) // 2
                y_text = barcode_height + 18   # moved upward

                draw.text((x_text, y_text), location, fill="black", font=font)

                # Tight border around barcode + text
                padding = 10
                left = x_bar - padding
                top = y_bar - padding
                right = x_bar + barcode_width + padding
                bottom = y_text + text_height + 10

                draw.rectangle(
                    [(left, top), (right, bottom)],
                    outline="black",
                    width=3
                )

                filename = os.path.join(
                    OUTPUT_FOLDER,
                    location.replace("/", "_") + ".png"
                )

                label.save(filename, dpi=(300, 300))
                count += 1

print(f"{count} labels generated successfully.")
print("Saved in:", OUTPUT_FOLDER)