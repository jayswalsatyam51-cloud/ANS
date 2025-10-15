import os
import json
from PIL import Image
import pytesseract

# You MUST ensure this path is the EXACT output of 'which tesseract' in your terminal
TESSERACT_PATH = r'/usr/local/bin/tesseract' 

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def extract_headlines_from_images(image_dir, output_json_path):
    """
    Extracts text from cropped images using pytesseract and saves it as a JSON.
    The output JSON is guaranteed to be sorted by ascending page number.
    """
    extracted_data = {}

    # Verify Tesseract installation
    try:
        pytesseract.get_tesseract_version()
    except Exception as e:
        print("❌ Tesseract is not properly installed or configured.")
        print(f"Current path configured: {pytesseract.pytesseract.tesseract_cmd}")
        print("\n**macOS Solution:**")
        print("1. Install Tesseract using Homebrew: `brew install tesseract`")
        print("2. Set the correct path in the script (e.g., `/usr/local/bin/tesseract` or `/opt/homebrew/bin/tesseract`)")
        raise Exception("Tesseract configuration error") from e

    # Define common unwanted characters for stripping
    UNWANTED_CHARS = "‘”\"'"

    # Step 1: Process all images into the dictionary
    for filename in sorted(os.listdir(image_dir)):
        if filename.endswith(".png"):
            try:
                # Extract page number as an integer for accurate sorting later
                page_num = int(filename.split('_')[1].split('.')[0])
                image_path = os.path.join(image_dir, filename)
                image = Image.open(image_path)
                
                text = pytesseract.image_to_string(image)
                
                # --- FIX: NLP/CLEANING STEP ---
                # 1. Strip whitespace
                # 2. Strip common unwanted quotation marks/apostrophes from the ends
                cleaned_text = text.strip().strip(UNWANTED_CHARS)
                
                # Store data using the integer page number as the key for easy sorting
                extracted_data[page_num] = cleaned_text
                print(f"✅ Processed headline for page {page_num}")
            except Exception as e:
                print(f"⚠️ Error processing {filename}: {e}")

    # Step 2: Sort the data and write to JSON
    
    # Get all page numbers (keys) and sort them numerically
    sorted_page_numbers = sorted(extracted_data.keys())
    
    # Create the final ordered dictionary structure
    sorted_data_for_json = {
        f"page_{page_num}": extracted_data[page_num] 
        for page_num in sorted_page_numbers
    }

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(sorted_data_for_json, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Headlines saved to {output_json_path}")


# --- FUNCTION CALL ---

#extract_headlines_from_images(image_dir="cropped_output", output_json_path="json_out/extracted_headlines.json")
