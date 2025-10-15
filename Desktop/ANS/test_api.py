#!/usr/bin/env python3
"""
Test script for the PDF Medical Data Extraction API
"""

import requests
import json
import os
import time

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_upload_pdf():
    """Test PDF upload endpoint"""
    print("\n🔍 Testing PDF upload...")
    
    # Check if test PDF exists
    test_pdf_path = "input/MP20010108_ANS_CV_25_06_17.pdf"
    if not os.path.exists(test_pdf_path):
        print(f"❌ Test PDF not found: {test_pdf_path}")
        return False
    
    try:
        with open(test_pdf_path, 'rb') as f:
            files = {'file': ('test.pdf', f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/upload-pdf", files=files)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ PDF upload successful")
                print(f"   File: {result['data']['filename']}")
                return result['data']['file_path']
            else:
                print(f"❌ Upload failed: {result['message']}")
                return None
        else:
            print(f"❌ Upload failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None

def test_crop_processing(file_path):
    """Test crop processing endpoint"""
    print("\n🔍 Testing crop processing...")
    
    try:
        data = {
            "pdf_path": file_path,
            "rectangle_coords": [175, 0, 550, 60],
            "output_dir": "cropped_output"
        }
        
        response = requests.post(f"{BASE_URL}/process-crop", json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ Crop processing successful")
                print(f"   Images generated: {result['data']['image_count']}")
                return True
            else:
                print(f"❌ Crop processing failed: {result['message']}")
                return False
        else:
            print(f"❌ Crop processing failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Crop processing error: {e}")
        return False

def test_headings_processing():
    """Test headings processing endpoint"""
    print("\n🔍 Testing headings processing...")
    
    try:
        data = {
            "image_dir": "cropped_output",
            "output_json_path": "json_output/extracted_headlines.json"
        }
        
        response = requests.post(f"{BASE_URL}/process-headings", json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ Headings processing successful")
                print(f"   Pages processed: {result['data']['page_count']}")
                return True
            else:
                print(f"❌ Headings processing failed: {result['message']}")
                return False
        else:
            print(f"❌ Headings processing failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Headings processing error: {e}")
        return False

def test_ocr_processing(file_path):
    """Test OCR processing endpoint"""
    print("\n🔍 Testing OCR processing...")
    
    try:
        data = {
            "pdf_path": file_path,
            "json_output_path": "json_output/extracted_tables.json",
            "specific_page": 1,
            "grouped_format": True
        }
        
        response = requests.post(f"{BASE_URL}/process-ocr", json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ OCR processing successful")
                print(f"   Tables extracted: {result['data']['table_count']}")
                return True
            else:
                print(f"❌ OCR processing failed: {result['message']}")
                return False
        else:
            print(f"❌ OCR processing failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ OCR processing error: {e}")
        return False

def test_coordinate_validation():
    """Test coordinate validation"""
    print("\n🔍 Testing coordinate validation...")
    
    # Test valid coordinates
    valid_coords = [175, 0, 550, 60]
    try:
        response = requests.post(f"{BASE_URL}/process-crop", json={
            "pdf_path": "test.pdf",
            "rectangle_coords": valid_coords,
            "output_dir": "test_output"
        })
        if response.status_code == 400 and "Invalid coordinates" in response.json().get("detail", ""):
            print("✅ Coordinate validation working (correctly rejected invalid PDF path)")
        else:
            print("⚠️ Coordinate validation response unexpected")
    except Exception as e:
        print(f"❌ Coordinate validation error: {e}")
    
    # Test invalid coordinates
    invalid_coords = [550, 0, 175, 60]  # x0 > x1
    try:
        response = requests.post(f"{BASE_URL}/process-crop", json={
            "pdf_path": "test.pdf",
            "rectangle_coords": invalid_coords,
            "output_dir": "test_output"
        })
        if response.status_code == 400:
            print("✅ Invalid coordinates correctly rejected")
        else:
            print("❌ Invalid coordinates not rejected")
    except Exception as e:
        print(f"❌ Coordinate validation error: {e}")

def test_default_coordinates():
    """Test getting default coordinates"""
    print("\n🔍 Testing default coordinates endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/default-coordinates")
        if response.status_code == 200:
            data = response.json()
            print("✅ Default coordinates retrieved")
            print(f"   Default crop coords: {data['default_crop_coords']}")
            print(f"   OCR3 definitions: {len(data['default_crop_definitions']['ocr3'])}")
            print(f"   OCR2 definitions: {len(data['default_crop_definitions']['ocr2'])}")
            return True
        else:
            print(f"❌ Default coordinates failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Default coordinates error: {e}")
        return False

def test_complete_pipeline():
    """Test the complete processing pipeline"""
    print("\n🔍 Testing complete pipeline...")
    
    # Check if test PDF exists
    test_pdf_path = "input/MP20010108_ANS_CV_25_06_17.pdf"
    if not os.path.exists(test_pdf_path):
        print(f"❌ Test PDF not found: {test_pdf_path}")
        return False
    
    try:
        with open(test_pdf_path, 'rb') as f:
            files = {'file': ('test.pdf', f, 'application/pdf')}
            data = {
                'specific_page': '1'
            }
            response = requests.post(f"{BASE_URL}/process-complete", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ Complete pipeline successful")
                print(f"   Original file: {result['data']['original_file']}")
                print(f"   Cropped images: {result['data']['cropped_images']}")
                print(f"   OCR tables: {result['data']['ocr_tables']}")
                return True
            else:
                print(f"❌ Complete pipeline failed: {result['message']}")
                if result.get('errors'):
                    print(f"   Errors: {result['errors']}")
                return False
        else:
            print(f"❌ Complete pipeline failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Complete pipeline error: {e}")
        return False

def test_download_endpoints():
    """Test download endpoints"""
    print("\n🔍 Testing download endpoints...")
    
    endpoints = ['headlines', 'tables', 'enhanced']
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}/download/{endpoint}")
            if response.status_code == 200:
                print(f"✅ Download {endpoint} successful")
            else:
                print(f"⚠️ Download {endpoint} failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Download {endpoint} error: {e}")

def test_document_conversion():
    """Test document conversion endpoint"""
    print("\n🔍 Testing document conversion...")
    
    try:
        data = {
            'json_file_path': 'json_out/enhanced_extraction.json',
            'output_format': 'docx',
            'patient_name': 'Test Patient',
            'output_dir': 'documents'
        }
        
        response = requests.post(f"{BASE_URL}/convert-to-document", data=data)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ Document conversion successful")
                print(f"   Output file: {result['data']['output_file']}")
                print(f"   Format: {result['data']['format']}")
                return True
            else:
                print(f"❌ Document conversion failed: {result['message']}")
                return False
        else:
            print(f"❌ Document conversion failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Document conversion error: {e}")
        return False

def test_cleanup():
    """Test cleanup endpoint"""
    print("\n🔍 Testing cleanup...")
    
    try:
        response = requests.post(f"{BASE_URL}/cleanup")
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ Cleanup successful")
                return True
            else:
                print(f"❌ Cleanup failed: {result['message']}")
                return False
        else:
            print(f"❌ Cleanup failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting API Tests")
    print("=" * 50)
    
    # Test health check first
    if not test_health_check():
        print("\n❌ API is not running. Please start the server first:")
        print("   python app.py")
        return
    
    # Test coordinate functionality
    test_coordinate_validation()
    test_default_coordinates()
    
    # Test individual endpoints
    file_path = test_upload_pdf()
    if file_path:
        test_crop_processing(file_path)
        test_headings_processing()
        test_ocr_processing(file_path)
    
    # Test complete pipeline
    test_complete_pipeline()
    
    # Test download endpoints
    test_download_endpoints()
    
    # Test document conversion
    test_document_conversion()
    
    # Test cleanup
    test_cleanup()
    
    print("\n" + "=" * 50)
    print("🎉 API testing completed!")

if __name__ == "__main__":
    main()
