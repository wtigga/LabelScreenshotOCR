import base64
import json
import os
import PIL
from PIL import Image
import cv2
import easyocr

PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

#  this is a workaround for outdated EasyOCR library
# https://github.com/JaidedAI/EasyOCR/issues/1077

# Language of the text on your images
source_language = 'ru'

# Thresholds to ignore tiny text fields, input the smallest height and width in pixels
min_height = 12
min_width = 70

# Specify the folder path containing PNG files
folder_path = 'samples'


def find_text_regions(image_path):
    # Read the image using OpenCV
    image = cv2.imread(image_path)

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Initialize the EasyOCR reader
    reader = easyocr.Reader([source_language])  # Adjust the languages as per your requirements

    # Perform text detection using EasyOCR
    results = reader.readtext(gray)

    # Extract the bounding boxes and recognized text of the detected text regions
    text_regions = []
    for result in results:
        bbox = result[0]  # Get the bounding box coordinates
        x1, y1 = int(bbox[0][0]), int(bbox[0][1])
        x2, y2 = int(bbox[2][0]), int(bbox[2][1])
        points = [(x1, y1), (x2, y2)]
        height = abs(y2 - y1)
        width = abs(x2 - x1)
        if height >= min_height and width >= min_width:  # threshold to ignore tiny text fields
            text = result[1]  # Get the recognized text
            text_regions.append((points, text))

    # Combine overlapping rectangles into a single rectangle
    combined_regions = combine_overlapping_rectangles([region[0] for region in text_regions])

    # Update the combined regions with the recognized text
    final_regions = []
    for combined_region in combined_regions:
        text = ""
        for region in text_regions:
            if check_overlap(region[0], combined_region):
                text += region[1] + " "
        text = text.strip()
        final_regions.append((combined_region, text))

    return final_regions, image


def combine_overlapping_rectangles(rectangles):
    combined_rectangles = list(rectangles)  # Create a copy of the list

    while True:
        overlap_found = False

        for i in range(len(combined_rectangles)):
            rect1 = combined_rectangles[i]
            for j in range(i + 1, len(combined_rectangles)):
                rect2 = combined_rectangles[j]
                if check_overlap(rect1, rect2):
                    combined_rectangles[i] = combine_rectangles(rect1, rect2)
                    combined_rectangles.pop(j)
                    overlap_found = True
                    break

            if overlap_found:
                break

        if not overlap_found:
            break

    return combined_rectangles


def check_overlap(rect1, rect2):
    x1, y1 = rect1[0]
    x2, y2 = rect1[1]
    x3, y3 = rect2[0]
    x4, y4 = rect2[1]
    if x2 < x3 or x4 < x1 or y2 < y3 or y4 < y1:
        return False
    return True


def combine_rectangles(rect1, rect2):
    x1 = min(rect1[0][0], rect2[0][0])
    y1 = min(rect1[0][1], rect2[0][1])
    x2 = max(rect1[1][0], rect2[1][0])
    y2 = max(rect1[1][1], rect2[1][1])
    return [(x1, y1), (x2, y2)]


def escape_description(text):
    return json.dumps(text, ensure_ascii=False)[1:-1]

def save_definitions_as_txt(regions, output_file):
    with open(output_file, 'w', encoding='utf-8') as file:
        for region in regions:
            description = escape_description(region[1])
            file.write(f"{description}\n")


# Get a list of PNG files in the folder
file_list = [file for file in os.listdir(folder_path) if file.endswith('.png')]

# Process each file in the folder
for file in file_list:
    # Construct the input and output file paths
    image_path = os.path.join(folder_path, file)
    json_output_file = os.path.join(folder_path, file.replace('.png', '_JSON.json'))
    txt_output_file = os.path.join(folder_path, file.replace('.png', '_OCR_content.txt'))

    print(f"Processing image: {file}...")

    # Find text regions and get the image
    regions, image = find_text_regions(image_path)
    print("Text regions found:", len(regions))

    # Prepare the JSON output
    output = {
        "version": "4.5.6",
        "flags": {},
        "shapes": [],
        "imagePath": file,
        "imageData": "",
        "imageHeight": image.shape[0],
        "imageWidth": image.shape[1]
    }

    # Convert the regions to JSON format
    for i, region in enumerate(regions):
        shape = {
            "label": str(i + 1),  # Unique label starting from 1
            "points": region[0],
            "group_id": None,
            "description": escape_description(region[1]),  # Escape potentially dangerous characters
            "shape_type": "rectangle",
            "flags": {}
        }
        output["shapes"].append(shape)

    # Convert the image to base64 and update the imageData field
    retval, buffer = cv2.imencode('.png', image)
    image_data = base64.b64encode(buffer).decode()
    output["imageData"] = image_data

    # Save the JSON to a file with UTF-8 encoding
    with open(json_output_file, 'w', encoding='utf-8') as file:
        json.dump(output, file, ensure_ascii=False, indent=2, sort_keys=False)

    # Save the definitions as a TXT file
    save_definitions_as_txt(regions, txt_output_file)

    print(f"Output saved to {json_output_file} and {txt_output_file}")


