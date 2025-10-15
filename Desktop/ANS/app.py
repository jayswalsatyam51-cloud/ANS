#!/usr/bin/env python3
"""
FastAPI application for PDF table extraction
Integrates crop.py, heading.py, ocr.py, and enhanced_formatter.py
"""

import os
import json
import tempfile
import shutil
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Import our modules
from src.crop import save_cropped_images_from_all_pages
from src.heading import extract_headlines_from_images
from src.ocr import extract_tables_from_pdf, extract_and_save_aggregated_tables, extract_and_save_separate_tables, process_unified_format, process_cardiovascular_tables
from src.enhanced_formatter import EnhancedMedicalFormatter
from src.exact_formatter import ExactMedicalFormatter
from src.simple_exact_formatter import SimpleExactFormatter
from src.comprehensive_medical_extractor import ComprehensiveMedicalExtractor
from src.ultra_robust_medical_extractor import UltraRobustMedicalExtractor
from src.doc_util import MedicalDocumentConverter
from src.uploadToS3 import upload_to_s3

app = FastAPI(
    title="PDF Medical Data Extraction API",
    description="Extract and format medical data from PDF files",
    version="1.0.0"
)

# Mount static files for HTML interface
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount documents directory for generated documents
app.mount("/documents", StaticFiles(directory="documents"), name="documents")

# Global variables for processing
PROCESSING_DIR = "processing_temp"
CROPPED_DIR = "cropped_output"
JSON_OUTPUT_DIR = "json_output"

class ProcessingResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None


def ensure_directories():
    """Ensure all required directories exist"""
    directories = [PROCESSING_DIR, CROPPED_DIR, JSON_OUTPUT_DIR, "json_out"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def cleanup_temp_files():
    """Clean up temporary files"""
    if os.path.exists(PROCESSING_DIR):
        shutil.rmtree(PROCESSING_DIR)
    if os.path.exists(CROPPED_DIR):
        shutil.rmtree(CROPPED_DIR)

def validate_coordinates(coords):
    """Validate coordinate format and values"""
    if not isinstance(coords, (list, tuple)):
        return False, "Coordinates must be a list or tuple"
    
    if len(coords) != 4:
        return False, "Coordinates must have exactly 4 values (x0, y0, x1, y1)"
    
    try:
        x0, y0, x1, y1 = [float(coord) for coord in coords]
        
        if x0 >= x1:
            return False, "x0 must be less than x1"
        
        if y0 >= y1:
            return False, "y0 must be less than y1"
        
        if any(coord < 0 for coord in [x0, y0, x1, y1]):
            return False, "All coordinates must be non-negative"
        
        return True, "Valid coordinates"
    
    except (ValueError, TypeError):
        return False, "All coordinates must be numeric values"

def get_default_crop_definitions():
    """Get default crop definitions"""
    return {
        "ocr3": [
            {
                "name": "Autonomic_Balance_Metrics",
                "coords": (0, 380, 611, 425),
                "parser": "process_unified_format"
            },
            {
                "name": "Valsalva_And_Tilt_Metrics",
                "coords": (0, 420, 611, 475),
                "parser": "process_unified_format"
            },
        ],
        "ocr2": [
            {
                "name": "Cardiovascular_Metrics",
                "coords": (0, 482, 611, 685),
                "parser": "process_cardiovascular_tables"
            },
            {
                "name": "Additional_Cardiovascular_Metrics",
                "coords": (0, 685, 611, 750),
                "parser": "process_cardiovascular_tables"
            },
        ]
    }

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML interface"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
            <head><title>PDF Medical Data Extraction</title></head>
            <body>
                <h1>PDF Medical Data Extraction API</h1>
                <p>API is running! Please check the static/index.html file.</p>
                <p><a href="/docs">API Documentation</a></p>
            </body>
        </html>
        """)

@app.post("/upload-pdf", response_model=ProcessingResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF file for processing"""
    try:
        ensure_directories()
        
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Save uploaded file
        file_path = os.path.join(PROCESSING_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return ProcessingResponse(
            success=True,
            message=f"PDF uploaded successfully: {file.filename}",
            data={"file_path": file_path, "filename": file.filename}
        )
    
    except Exception as e:
        return ProcessingResponse(
            success=False,
            message="Failed to upload PDF",
            errors=[str(e)]
        )






@app.post("/process-complete", response_model=ProcessingResponse)
async def process_complete(file: UploadFile = File(...)):
    """Complete processing pipeline: upload -> crop -> headings -> ocr -> enhanced formatting -> DOCX conversion"""
    try:
        ensure_directories()
        
        # Step 1: Upload PDF
        file_path = os.path.join(PROCESSING_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Step 2: Use fixed default crop coordinates
        crop_coords_list = [175, 0, 550, 60]  # Fixed coordinates - not editable
        
        # Crop images
        save_cropped_images_from_all_pages(
            pdf_path=file_path,
            rect=tuple(crop_coords_list),
            output_dir=CROPPED_DIR
        )
        
        # Step 3: Extract headings
        headlines_path = os.path.join(JSON_OUTPUT_DIR, "extracted_headlines.json")
        extract_headlines_from_images(
            image_dir=CROPPED_DIR,
            output_json_path=headlines_path
        )
        
        # Step 4: OCR extraction
        ocr_output_path = os.path.join(JSON_OUTPUT_DIR, "extracted_tables.json")
        tables = extract_tables_from_pdf(
            pdf_path=file_path,
            json_output_path=ocr_output_path,
            specific_page=None,
            grouped_format=True
        )
        
        # Step 5: Enhanced formatting
        formatter = EnhancedMedicalFormatter()
        
        # Create unified data structure
        unified_data = {
            "ocr_py_results": tables,
            "ocr3_py_results": {},
            "ocr2_py_results": {}
        }
        
        # Add OCR3 and OCR2 results if available
        try:
            # Use default crop definitions
            crop_definitions = get_default_crop_definitions()
            
            # OCR3 processing
            ocr3_crop_definitions = []
            for definition in crop_definitions.get("ocr3", []):
                ocr3_def = {
                    "name": definition["name"],
                    "coords": tuple(definition["coords"]),
                    "parser": process_unified_format
                }
                ocr3_crop_definitions.append(ocr3_def)
            
            if ocr3_crop_definitions:
                ocr3_results = extract_and_save_aggregated_tables(
                    pdf_path=file_path,
                    json_output_path=None,
                    specific_page=1,
                    crop_definitions=ocr3_crop_definitions
                )
                
                if ocr3_results and ocr3_results.get("results"):
                    unified_data["ocr3_py_results"] = ocr3_results["results"]
            
            # OCR2 processing
            ocr2_crop_definitions = []
            for definition in crop_definitions.get("ocr2", []):
                ocr2_def = {
                    "name": definition["name"],
                    "coords": tuple(definition["coords"]),
                    "parser": process_cardiovascular_tables
                }
                ocr2_crop_definitions.append(ocr2_def)
            
            if ocr2_crop_definitions:
                ocr2_results = extract_and_save_separate_tables(
                    pdf_path=file_path,
                    json_output_dir=None,
                    specific_page=1,
                    crop_definitions=ocr2_crop_definitions
                )
                
                if ocr2_results:
                    unified_data["ocr2_py_results"] = ocr2_results
        
        except Exception as e:
            print(f"Warning: Could not extract OCR3/OCR2 results: {e}")
        
        # Format to target structure
        formatted_data = formatter.format_to_target_structure(unified_data)
        
        # Save enhanced data
        enhanced_output_path = os.path.join(JSON_OUTPUT_DIR, "enhanced_extraction.json")
        with open(enhanced_output_path, 'w', encoding='utf-8') as f:
            json.dump(formatted_data, f, indent=4, ensure_ascii=False)
        
        # Step 6: Convert to DOCX
        converter = MedicalDocumentConverter()
        docx_output_path = converter.convert_json_file(
            json_file_path=enhanced_output_path,
            output_format="docx",
            patient_name="Patient",
            output_dir="documents"
        )
        
        # Step 7: Upload DOCX to S3
        s3_url = None
        s3_filename = None
        try:
            s3_url, s3_filename = upload_to_s3(docx_output_path, prefix="medical-documents/")
        except Exception as s3_error:
            print(f"Warning: Failed to upload to S3: {s3_error}")
        
        return ProcessingResponse(
            success=True,
            message="Complete processing pipeline finished successfully - DOCX document generated and uploaded to S3",
            data={
                "original_file": file.filename,
                "cropped_images": len([f for f in os.listdir(CROPPED_DIR) if f.endswith('.png')]),
                "headlines_file": headlines_path,
                "ocr_tables": len(tables),
                "enhanced_output": enhanced_output_path,
                "docx_output": docx_output_path,
                "s3_url": s3_url,
                "s3_filename": s3_filename,
                "formatted_data": formatted_data
            }
        )
    
    except Exception as e:
        return ProcessingResponse(
            success=False,
            message="Failed to complete processing pipeline",
            errors=[str(e)]
        )

@app.post("/upload-to-s3", response_model=ProcessingResponse)
async def upload_file_to_s3(
    file: UploadFile = File(...),
    prefix: str = Form("uploads/")
):
    """Upload any file directly to S3"""
    try:
        # Save uploaded file temporarily
        temp_file_path = os.path.join(PROCESSING_DIR, file.filename)
        ensure_directories()
        
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Upload to S3
        s3_url, s3_filename = upload_to_s3(temp_file_path, prefix=prefix)
        
        return ProcessingResponse(
            success=True,
            message=f"File uploaded to S3 successfully",
            data={
                "original_filename": file.filename,
                "s3_url": s3_url,
                "s3_filename": s3_filename,
                "prefix": prefix
            }
        )
    
    except Exception as e:
        return ProcessingResponse(
            success=False,
            message="Failed to upload file to S3",
            errors=[str(e)]
        )

@app.post("/convert-to-document", response_model=ProcessingResponse)
async def convert_to_document(
    json_file_path: str = Form("json_out/enhanced_extraction.json"),
    output_format: str = Form("html"),
    patient_name: str = Form("Patient"),
    output_dir: str = Form("documents"),
    upload_to_s3_flag: bool = Form(False),
    s3_prefix: str = Form("converted-documents/")
):
    """Convert JSON medical data to formatted document"""
    try:
        if not os.path.exists(json_file_path):
            raise HTTPException(status_code=404, detail="JSON file not found")
        
        # Initialize converter
        converter = MedicalDocumentConverter()
        
        # Convert to document
        output_path = converter.convert_json_file(
            json_file_path=json_file_path,
            output_format=output_format,
            patient_name=patient_name,
            output_dir=output_dir
        )
        
        # Optionally upload to S3
        s3_url = None
        s3_filename = None
        if upload_to_s3_flag:
            try:
                s3_url, s3_filename = upload_to_s3(output_path, prefix=s3_prefix)
            except Exception as s3_error:
                print(f"Warning: Failed to upload to S3: {s3_error}")
        
        return ProcessingResponse(
            success=True,
            message=f"Document converted successfully to {output_format.upper()}",
            data={
                "output_file": output_path,
                "format": output_format,
                "patient_name": patient_name,
                "s3_url": s3_url,
                "s3_filename": s3_filename
            }
        )
    
    except Exception as e:
        return ProcessingResponse(
            success=False,
            message="Failed to convert document",
            errors=[str(e)]
        )


@app.post("/cleanup")
async def cleanup():
    """Clean up temporary files"""
    try:
        cleanup_temp_files()
        return ProcessingResponse(
            success=True,
            message="Cleanup completed successfully"
        )
    except Exception as e:
        return ProcessingResponse(
            success=False,
            message="Failed to cleanup",
            errors=[str(e)]
        )


@app.post("/extract-exact-format", response_model=ProcessingResponse)
async def extract_exact_format(file: UploadFile = File(...)):
    """Extract medical data and return in the exact format requested by the user"""
    try:
        ensure_directories()
        
        # Step 1: Upload PDF
        file_path = os.path.join(PROCESSING_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Step 2: Use fixed default crop coordinates
        crop_coords_list = [175, 0, 550, 60]  # Fixed coordinates - not editable
        
        # Crop images
        save_cropped_images_from_all_pages(
            pdf_path=file_path,
            rect=tuple(crop_coords_list),
            output_dir=CROPPED_DIR
        )
        
        # Step 3: Extract headings
        headlines_path = os.path.join(JSON_OUTPUT_DIR, "extracted_headlines.json")
        extract_headlines_from_images(
            image_dir=CROPPED_DIR,
            output_json_path=headlines_path
        )
        
        # Step 4: OCR extraction
        ocr_output_path = os.path.join(JSON_OUTPUT_DIR, "extracted_tables.json")
        tables = extract_tables_from_pdf(
            pdf_path=file_path,
            json_output_path=ocr_output_path,
            specific_page=None,
            grouped_format=True
        )
        
        # Step 5: Enhanced formatting
        formatter = EnhancedMedicalFormatter()
        
        # Create unified data structure
        unified_data = {
            "ocr_py_results": tables,
            "ocr3_py_results": {},
            "ocr2_py_results": {}
        }
        
        # Add OCR3 and OCR2 results if available
        try:
            # Use default crop definitions
            crop_definitions = get_default_crop_definitions()
            
            # OCR3 processing
            ocr3_crop_definitions = []
            for definition in crop_definitions.get("ocr3", []):
                ocr3_def = {
                    "name": definition["name"],
                    "coords": tuple(definition["coords"]),
                    "parser": process_unified_format
                }
                ocr3_crop_definitions.append(ocr3_def)
            
            if ocr3_crop_definitions:
                ocr3_results = extract_and_save_aggregated_tables(
                    pdf_path=file_path,
                    json_output_path=None,
                    specific_page=1,
                    crop_definitions=ocr3_crop_definitions
                )
                
                if ocr3_results and ocr3_results.get("results"):
                    unified_data["ocr3_py_results"] = ocr3_results["results"]
            
            # OCR2 processing
            ocr2_crop_definitions = []
            for definition in crop_definitions.get("ocr2", []):
                ocr2_def = {
                    "name": definition["name"],
                    "coords": tuple(definition["coords"]),
                    "parser": process_cardiovascular_tables
                }
                ocr2_crop_definitions.append(ocr2_def)
            
            if ocr2_crop_definitions:
                ocr2_results = extract_and_save_separate_tables(
                    pdf_path=file_path,
                    json_output_dir=None,
                    specific_page=1,
                    crop_definitions=ocr2_crop_definitions
                )
                
                if ocr2_results:
                    unified_data["ocr2_py_results"] = ocr2_results
        
        except Exception as e:
            print(f"Warning: Could not extract OCR3/OCR2 results: {e}")
        
        # Step 6: Use simple exact formatter to get the exact format requested
        simple_exact_formatter = SimpleExactFormatter()
        
        # First get the enhanced data
        formatted_data = formatter.format_to_target_structure(unified_data)
        
        # Then format to exact structure
        exact_output = simple_exact_formatter.format_to_exact_structure(formatted_data, file_path)
        
        # Save exact output
        exact_output_path = os.path.join(JSON_OUTPUT_DIR, "exact_format_output.txt")
        with open(exact_output_path, 'w', encoding='utf-8') as f:
            f.write(exact_output)
        
        return ProcessingResponse(
            success=True,
            message="Medical data extracted in exact format successfully",
            data={
                "original_file": file.filename,
                "exact_format_output": exact_output,
                "output_file": exact_output_path
            }
        )
    
    except Exception as e:
        return ProcessingResponse(
            success=False,
            message="Failed to extract data in exact format",
            errors=[str(e)]
        )

@app.post("/extract-comprehensive", response_model=ProcessingResponse)
async def extract_comprehensive(file: UploadFile = File(...)):
    """Extract medical data using comprehensive PDF search and return in exact format"""
    try:
        ensure_directories()
        
        # Step 1: Upload PDF
        file_path = os.path.join(PROCESSING_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Step 2: Use comprehensive extractor to search entire PDF
        extractor = ComprehensiveMedicalExtractor()
        
        # Extract all data from PDF
        extracted_data = extractor.extract_all_data_from_pdf(file_path)
        
        # Format to exact output structure
        exact_output = extractor.format_to_exact_output(extracted_data)
        
        # Save exact output
        exact_output_path = os.path.join(JSON_OUTPUT_DIR, "comprehensive_exact_format_output.txt")
        with open(exact_output_path, 'w', encoding='utf-8') as f:
            f.write(exact_output)
        
        return ProcessingResponse(
            success=True,
            message="Medical data extracted comprehensively from entire PDF in exact format",
            data={
                "original_file": file.filename,
                "exact_format_output": exact_output,
                "output_file": exact_output_path,
                "extracted_fields": len([k for k, v in extracted_data.get("AUTONOMICS", {}).items() if v]) + 
                                      len([k for k, v in extracted_data.get("CARDIOVASCULAR", {}).items() if v]) +
                                      len([k for k, v in extracted_data.get("ELECTROCARDIOGRAM", {}).items() if v])
            }
        )
    
    except Exception as e:
        return ProcessingResponse(
            success=False,
            message="Failed to extract data comprehensively",
            errors=[str(e)]
        )

@app.post("/extract-ultra-robust", response_model=ProcessingResponse)
async def extract_ultra_robust(file: UploadFile = File(...)):
    """Extract medical data using ultra-robust methods with multiple validation layers"""
    try:
        ensure_directories()
        
        # Step 1: Upload PDF
        file_path = os.path.join(PROCESSING_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Step 2: Use ultra-robust extractor with multiple validation layers
        extractor = UltraRobustMedicalExtractor()
        
        # Extract all data with ultra-robust methods
        extracted_data = extractor.extract_all_data_ultra_robust(file_path)
        
        # Format to exact output structure
        exact_output = extractor.format_to_exact_output_ultra_robust(extracted_data)
        
        # Save exact output
        exact_output_path = os.path.join(JSON_OUTPUT_DIR, "ultra_robust_exact_format_output.txt")
        with open(exact_output_path, 'w', encoding='utf-8') as f:
            f.write(exact_output)
        
        # Save validation log
        validation_log_path = os.path.join(JSON_OUTPUT_DIR, "ultra_robust_validation_log.json")
        with open(validation_log_path, 'w', encoding='utf-8') as f:
            json.dump(extractor.validation_log, f, indent=4, ensure_ascii=False)
        
        # Calculate statistics
        missing_fields = [log for log in extractor.validation_log if log['confidence'] == 'MISSING']
        low_confidence_fields = [log for log in extractor.validation_log if log['confidence'] == 'LOW']
        high_confidence_fields = [log for log in extractor.validation_log if log['confidence'] == 'HIGH']
        
        return ProcessingResponse(
            success=True,
            message="Ultra-robust medical data extraction completed with maximum validation",
            data={
                "original_file": file.filename,
                "exact_format_output": exact_output,
                "output_file": exact_output_path,
                "validation_log_file": validation_log_path,
                "extraction_method": "ultra_robust_multiple_validation",
                "confidence_level": "maximum",
                "validation_statistics": {
                    "total_fields_processed": len(extractor.validation_log),
                    "high_confidence_fields": len(high_confidence_fields),
                    "low_confidence_fields": len(low_confidence_fields),
                    "missing_fields": len(missing_fields),
                    "success_rate": f"{((len(high_confidence_fields) + len(low_confidence_fields)) / len(extractor.validation_log) * 100):.1f}%"
                },
                "critical_missing_fields": [log['field'] for log in missing_fields[:10]]  # First 10 missing fields
            }
        )
    
    except Exception as e:
        return ProcessingResponse(
            success=False,
            message="Failed to extract data with ultra-robust methods",
            errors=[str(e)]
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "PDF Medical Data Extraction API is running"}

if __name__ == "__main__":
    # Ensure directories exist on startup
    ensure_directories()
    
    # Run the application
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
