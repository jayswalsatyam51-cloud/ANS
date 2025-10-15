import os
import pymupdf # Need to import the library used inside your function

# Define the function (as provided in the prompt)
def save_cropped_images_from_all_pages(pdf_path, rect, output_dir):
    """
    Crops a specific rectangle from all pages of a PDF and saves as PNG images.
    """
    # NOTE: The original function snippet implies 'pymupdf' is being used (due to Rect, get_pixmap, etc.)
    # If the function is not defined in your environment, you must include it.

    os.makedirs(output_dir, exist_ok=True)
    try:
        doc = pymupdf.open(pdf_path)
        for page_number in range(len(doc)):
            page = doc[page_number]
            # rect is already a tuple (x0, y0, x1, y1)
            clip = pymupdf.Rect(rect)
            pix = page.get_pixmap(clip=clip)
            image_data = pix.tobytes("png")

            output_path = os.path.join(output_dir, f"page_{page_number + 1}.png")
            with open(output_path, "wb") as f:
                f.write(image_data)

        doc.close()
        print(f"✅ Images saved in '{output_dir}'")
    except Exception as e:
        print(f"❌ Error while cropping images: {e}")

# --- FUNCTION CALL SETUP ---

# Default configuration - can be overridden by function parameters
DEFAULT_PDF_PATH = "input/MP20010108_ANS_CV_25_06_17.pdf"
DEFAULT_OUTPUT_DIR = "cropped_output"
DEFAULT_RECTANGLE_COORDS = (175, 0, 550, 60)  # Default: top portion of page

# 3. Call the function with default values
if __name__ == "__main__":
    if os.path.exists(DEFAULT_PDF_PATH):
        print(f"Cropping PDF: {DEFAULT_PDF_PATH} with rectangle {DEFAULT_RECTANGLE_COORDS}")
        save_cropped_images_from_all_pages(
            pdf_path=DEFAULT_PDF_PATH,
            rect=DEFAULT_RECTANGLE_COORDS,
            output_dir=DEFAULT_OUTPUT_DIR
        )
    else:
        print(f"❌ Error: PDF file not found at {DEFAULT_PDF_PATH}")
        print("💡 Please ensure the PDF file exists or update the DEFAULT_PDF_PATH variable")
      