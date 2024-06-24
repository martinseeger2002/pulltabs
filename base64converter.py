import base64
import os

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def save_base64_to_file(base64_data, output_path):
    with open(output_path, "w") as file:
        file.write(base64_data)

# List of image files to convert
image_files = [
    "pulltab.png",
    "back.png",
    "tab.png",
    "rip1.png",
    "rip2.png",
    "rip3.png",
    "win.png",
    "1.png",
    "2.png",
    "3.png",
    "4.png",
    "5.png",
    "6.png",
    "7.png"
]

# Directory containing the images
image_directory = "./images/"

# Output directory for base64 text files
output_directory = "./base64/"

# Ensure the output directory exists
os.makedirs(output_directory, exist_ok=True)

for image_file in image_files:
    image_path = os.path.join(image_directory, image_file)
    base64_data = image_to_base64(image_path)
    output_path = os.path.join(output_directory, f"{os.path.splitext(image_file)[0]}.txt")
    save_base64_to_file(base64_data, output_path)
    print(f"Converted {image_file} to {output_path}")

print("All images have been converted to base64 and saved as text files.")
