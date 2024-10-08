from PIL import Image

# Open your image
image = Image.open("~/Downloads/frog-1.jpg")

# Resize the image (adjust size as needed)
image = image.resize((32, 32))

# Convert to 1-bit color (black and white)
image = image.convert("1")

# Get the byte data
byte_data = image.tobytes()

# Print the byte data as a formatted string for use in MicroPython
print("image_data = bytearray([")
print(", ".join([f"0x{b:02x}" for b in byte_data]))
print("])")