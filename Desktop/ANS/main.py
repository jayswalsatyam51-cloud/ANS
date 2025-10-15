#!/usr/bin/env python3
"""
Main script for PDF table extraction
Supports extracting tables from any PDF file and any specific page
"""

import os
import sys
import json
from src.ocr import extract_tables_from_pdf

def print_usage():
    """Print usage instructions"""
    print("""
📖 PDF Table Extraction Tool

Usage:
    python main.py [PDF_PATH] [OUTPUT_PATH] [PAGE_NUMBER]

Arguments:
    PDF_PATH      - Path to the PDF file (optional, defaults to input/MP20010108_ANS_CV_25_06_17.pdf)
    OUTPUT_PATH   - Path for JSON output file (optional, defaults to json_out/extracted_tables.json)
    PAGE_NUMBER   - Specific page number to extract (optional, processes all pages if not specified)

Examples:
    # Extract all tables from default PDF
    python main.py
    
    # Extract all tables from specific PDF
    python main.py "path/to/your/document.pdf"
    
    # Extract tables from specific PDF and save to custom location
    python main.py "path/to/your/document.pdf" "output/my_tables.json"
    
    # Extract tables from page 2 only
    python main.py "path/to/your/document.pdf" "output/my_tables.json" 2
    
    # Extract from default PDF, page 1 only
    python main.py "" "" 1
""")

def ensure_output_directory(output_path):
    """Ensure the output directory exists"""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 Created output directory: {output_dir}")

def main():
    """Main function"""
    print("🚀 PDF Table Extraction Tool")
    print("=" * 50)
    
    # Parse command line arguments
    pdf_path = "input/MP20010108_ANS_CV_25_06_17.pdf"  # Default PDF
    output_path = "json_out/extracted_tables.json"     # Default output
    specific_page = None                               # Process all pages by default
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help", "help"]:
            print_usage()
            return 0
        pdf_path = sys.argv[1]
    
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    
    if len(sys.argv) > 3:
        try:
            specific_page = int(sys.argv[3])
            if specific_page < 1:
                print("❌ Page number must be positive")
                return 1
        except ValueError:
            print("❌ Invalid page number. Must be an integer.")
            return 1
    
    # Validate input file
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        print("💡 Make sure the file exists or provide the correct path")
        return 1
    
    # Ensure output directory exists
    ensure_output_directory(output_path)
    
    # Display configuration
    print(f"📄 Input PDF: {pdf_path}")
    print(f"💾 Output JSON: {output_path}")
    if specific_page:
        print(f"🎯 Processing page: {specific_page}")
    else:
        print(f"📖 Processing: All pages")
    print("-" * 50)
    
    try:
        # Extract tables
        print("🔄 Starting table extraction...")
        tables = extract_tables_from_pdf(
            pdf_path=pdf_path,
            json_output_path=output_path,
            specific_page=specific_page
        )
        
        # Display results
        print("\n" + "=" * 50)
        print("✅ EXTRACTION COMPLETE!")
        print("=" * 50)
        
        if tables:
            total_rows = sum(len(table["table"]) for table in tables)
            print(f"📊 Total tables extracted: {len(tables)}")
            print(f"📋 Total rows extracted: {total_rows}")
            print(f"💾 Results saved to: {output_path}")
            
            print("\n📋 Table Summary:")
            for i, table in enumerate(tables, 1):
                print(f"  {i}. Page {table['page']}, Table {table['table_index']}: {table['table_heading']} ({len(table['table'])} rows)")
            
            # Show sample data from first table
            if tables and tables[0]["table"]:
                print(f"\n🔍 Sample data from first table:")
                sample_row = tables[0]["table"][0]
                for key, value in list(sample_row.items())[:3]:  # Show first 3 fields
                    print(f"    {key}: {value}")
                if len(sample_row) > 3:
                    print(f"    ... and {len(sample_row) - 3} more fields")
        else:
            print("⚠️  No tables found in the specified page(s)")
            if specific_page:
                print(f"💡 Try processing all pages or check if page {specific_page} contains tables")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {str(e)}")
        return 1
    except ValueError as e:
        print(f"❌ Invalid input: {str(e)}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        print("💡 Please check your PDF file and try again")
        return 1

if __name__ == "__main__":
    exit(main())
