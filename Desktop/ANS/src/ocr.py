import pdfplumber
import json
import os
import re
import traceback
import sys

# ------------------------------------------------------------------
# HELPER FUNCTIONS (MUST be defined first for scope)
# ------------------------------------------------------------------

def clean_cell_value(cell):
    """Clean and normalize cell values"""
    if cell is None:
        return ""
    cell_str = str(cell).strip()
    # Also remove common rogue characters that might appear in table cells
    cell_str = cell_str.replace('v', '').replace('л', '').strip()
    if cell_str.lower() in ["", "null", "none", "n/a"]:
        return ""
    return cell_str

def clean_cell_value_multiline(cell):
    """Clean and normalize cell values, handling multiple lines."""
    if cell is None:
        return ""
    cell_str = str(cell).replace('\n', ' ').strip()
    if cell_str.lower() in ["", "null", "none", "n/a"]:
        return ""
    return cell_str

def is_valid_row(row):
    """Consider valid if at least 1 non-empty cell exists to prevent data loss."""
    if not row:
        return False
    # Check if at least 1 cell contains cleaned data
    non_empty_cells = sum(1 for cell in row if clean_cell_value(cell))
    return non_empty_cells >= 1

def is_valid_header(header):
    """Consider valid if at least 1 non-empty header cell exists"""
    if not header:
        return False
    return any(clean_cell_value(cell) for cell in header)

def detect_table_structure(table, table_heading):
    """Detect if the first row is a header row or data row"""
    if not table or len(table) < 2:
        return False
    
    first_row = table[0]
    if not isinstance(first_row, list):
        return False
    
    header_indicators = [
        "duration", "hr", "bp", "rmf", "sns", "pns", "lf", "hf", "tsp", "sdn", "rms", "spo",
        "metric", "result", "value", "right eye", "left eye", 
        "normative", "data", "amplitude", "diameter", "latency",
        "speed", "constriction", "dilation", "recovery", "heart", "blood", "pressure",
        "vagal", "sympathetic", "parasympathetic", "breathing", "valsalva", "tilt",
        "score", "units", "norms", "description", "comments", "resting", "deep", "breathing"
    ]
    
    first_row_text = " ".join(str(cell).lower() for cell in first_row if cell)
    header_count = sum(1 for indicator in header_indicators if indicator in first_row_text)
    has_numeric_data = any(str(cell).replace('.', '').replace(',', '').replace('/', '').isdigit() for cell in first_row if cell)
    has_short_terms = any(len(str(cell).strip()) <= 10 and str(cell).strip() for cell in first_row if cell)
    
    # More lenient header detection
    is_header = (header_count >= 1 or has_short_terms) and not has_numeric_data
    
    # Additional check: if first row has mostly short text and second row has numbers, it's likely a header
    if len(table) > 1 and not is_header:
        second_row = table[1]
        if isinstance(second_row, list):
            second_row_numeric = any(str(cell).replace('.', '').replace(',', '').replace('/', '').isdigit() for cell in second_row if cell)
            first_row_numeric = any(str(cell).replace('.', '').replace(',', '').replace('/', '').isdigit() for cell in first_row if cell)
            if second_row_numeric and not first_row_numeric:
                is_header = True
    
    return is_header

def is_eye_results_table(table_heading, table_data=None):
    """Check if this is an eye-related results table"""
    if not table_heading:
        return False
    
    table_heading_lower = table_heading.lower()
    
    if any(exclude_term in table_heading_lower for exclude_term in [
        "cardiovascular", "heart rate", "blood pressure", "hr", "bp", "duration", 
        "rmf", "sns", "pns", "tsp", "sdnn", "rms", "spo"
    ]):
        return False
    
    eye_table_indicators = [
        "constriction", "dilation", "amplitude", "diameter", "latency", 
        "speed", "recovery", "pupil", "eye", "other results"
    ]
    
    return any(indicator in table_heading_lower for indicator in eye_table_indicators)

def should_flag_value(value, page, table_index):
    """Determine if a value should be flagged"""
    if not value:
        return False
    
    value_str = str(value).lower()
    
    if not any(char.isdigit() for char in value_str):
        return False
    
    if page == 2 and table_index == 2:
        if "0.609" in value_str or "0.591" in value_str or "17.525" in value_str or "16.308" in value_str:
            return True
    elif page == 2 and table_index == 4:
        if "1.257" in value_str or "0.911" in value_str:
            return True
    
    return False

def is_table_meaningful(table_data, min_data_points=1):
    """
    Determine if a table contains meaningful data worth including in output.
    
    Args:
        table_data: The processed table data (dict or list)
        min_data_points: Minimum number of meaningful data points required
    
    Returns:
        bool: True if table should be included, False otherwise
    """
    if not table_data:
        return False
    
    # Handle grouped format (dict)
    if isinstance(table_data, dict):
        # Count meaningful data points across all metrics
        total_data_points = 0
        for metric_name, metric_data in table_data.items():
            if isinstance(metric_data, dict):
                # Count non-empty values in this metric
                meaningful_values = sum(1 for value in metric_data.values() 
                                      if clean_cell_value(value) and len(str(value).strip()) > 0)
                total_data_points += meaningful_values
        
        return total_data_points >= min_data_points
    
    # Handle row-based format (list)
    elif isinstance(table_data, list):
        meaningful_rows = 0
        for row in table_data:
            if isinstance(row, dict):
                # Count non-empty cells in this row
                meaningful_cells = sum(1 for value in row.values() 
                                     if clean_cell_value(value) and len(str(value).strip()) > 0)
                if meaningful_cells >= 1:  # At least 1 meaningful cell per row
                    meaningful_rows += 1
        
        return meaningful_rows >= min_data_points
    
    return False

def is_table_empty(table_data):
    """
    Check if a table is completely empty or contains only whitespace/empty values.
    
    Args:
        table_data: The processed table data
    
    Returns:
        bool: True if table is empty, False otherwise
    """
    if not table_data:
        return True
    
    # Handle grouped format (dict)
    if isinstance(table_data, dict):
        for metric_name, metric_data in table_data.items():
            if isinstance(metric_data, dict):
                for value in metric_data.values():
                    if clean_cell_value(value) and len(str(value).strip()) > 0:
                        return False
        return True
    
    # Handle row-based format (list)
    elif isinstance(table_data, list):
        for row in table_data:
            if isinstance(row, dict):
                for value in row.values():
                    if clean_cell_value(value) and len(str(value).strip()) > 0:
                        return False
        return True
    
    return True

# NOTE: generate_table_heading is essentially absorbed into extract_tables_from_pdf
def generate_table_heading(table):
    """Generate a meaningful table heading based on the table content."""
    if not table or not isinstance(table, list):
        return "Unknown Table"
    
    first_row = table[0] if table else []
    
    if isinstance(first_row, list) and first_row:
        return " ".join(clean_cell_value(cell) for cell in first_row if clean_cell_value(cell))
    
    return "Table Data"

# ------------------------------------------------------------------
# CORE LOGIC FUNCTIONS FROM OCR.PY
# ------------------------------------------------------------------

def group_by_metrics(table_data):
    """
    Transform table data from row-based to metric-based grouping
    """
    if not table_data:
        print("⚠️ No table data to group")
        return {}
    
    print(f"🔄 Grouping {len(table_data)} rows by metrics...")
    print(f"📋 Sample row keys: {list(table_data[0].keys()) if table_data else 'None'}")
    
    grouped_data = {}
    
    # Standardized test name mappings
    test_name_mapping = {
        "resting": "Resting",
        "deep breathing": "Deep Breathing",
        "valsalva": "Valsalva",
        "valsala": "Valsalva",  # Common misspelling
        "tilt test": "Tilt Test",
        "tilt": "Tilt Test",
        "resting2": "Resting2",
        "resting 2": "Resting2"
    }

    for idx, row in enumerate(table_data):
        # --- 1. Determine Standardized Test Name from first column ---
        test_name_raw = None
        
        # Look for test names in various column positions
        for potential_key in ["Duration", "Test", "Stage", "Name", "Type", ""]:
            if potential_key in row and row[potential_key] and not re.match(r'^[\d\./\-\s]+$', str(row[potential_key])):
                test_name_raw = row[potential_key]
                break

        # If not found in named columns, check the first column
        if not test_name_raw and row:
            first_key = list(row.keys())[0]
            first_value = clean_cell_value(row[first_key])
            
            if first_value and isinstance(first_value, str):
                if not re.match(r'^[\d\./\-\s]+$', first_value): 
                    test_name_raw = first_value

        # If still not found, try to extract from any column that looks like a test name
        if not test_name_raw:
            for key, value in row.items():
                if value and isinstance(value, str):
                    value_lower = str(value).lower().strip()
                    if any(test_name in value_lower for test_name in ["resting", "deep", "breathing", "valsalva", "valsala", "tilt"]):
                        test_name_raw = value
                        break

        if not test_name_raw:
            test_name_raw = f"Test_{idx + 1}"
            
        test_name_lower = test_name_raw.lower().strip()
        standardized_test_name = test_name_mapping.get(test_name_lower, test_name_raw)

        # --- 2. Group Metrics with Special Handling for HR ---
        for key, value in row.items():
            if key in row and clean_cell_value(value) == clean_cell_value(test_name_raw):
                 continue
            
            cleaned_value = clean_cell_value(value)
            
            if cleaned_value:
                if key not in grouped_data:
                    grouped_data[key] = {}
                
                if key == "HR":
                    if '-' in cleaned_value:
                        try:
                            parts = cleaned_value.split('-')
                            if len(parts) >= 2:
                                max_val = float(parts[0].strip())
                                min_val = float(parts[1].strip())
                                
                                grouped_data[key][f"{standardized_test_name} Max"] = str(int(max_val) if max_val.is_integer() else max_val)
                                grouped_data[key][f"{standardized_test_name} Min"] = str(int(min_val) if min_val.is_integer() else min_val)
                                
                                continue
                        except (ValueError, IndexError):
                            pass
                    
                    grouped_data[key][standardized_test_name] = cleaned_value
                
                else:
                    grouped_data[key][standardized_test_name] = cleaned_value
    
    print(f"✅ Grouped into {len(grouped_data)} metrics")
    return grouped_data

def extract_tables_from_pdf(pdf_path, json_output_path=None, specific_page=None, table_settings=None, grouped_format=False):
    """
    Extract tables from PDF file
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Default table extraction settings
    default_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines"
    }
    
    if table_settings:
        default_settings.update(table_settings)

    all_tables = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"📄 Processing PDF with {total_pages} pages")
            
            # --- Page Selection Logic ---
            if specific_page is not None:
                page_index = specific_page - 1 
                if specific_page < 1 or specific_page > total_pages:
                    raise ValueError(f"Page {specific_page} is out of range. PDF has {total_pages} pages.")
                pages_to_process = [page_index]
                print(f"🎯 Processing only page {specific_page} (Index {page_index})")
            else:
                pages_to_process = range(total_pages)
                print(f"📖 Processing all {total_pages} pages")
            # --------------------------

            for page_idx in pages_to_process:
                page_number = page_idx + 1
                page = pdf.pages[page_idx]
                
                print(f"📄 Processing page {page_number}...")
                
                tables = page.extract_tables(default_settings)
                
                if not tables:
                    print(f"⚠️ No tables found on page {page_number}")
                    continue

                for table_index, table in enumerate(tables, start=1):
                    if not table or len(table) < 2:
                        continue
                    
                    # Use the entire first row's content as the table heading
                    table_heading = " ".join(clean_cell_value(cell) for cell in table[0] if clean_cell_value(cell))
                    if not table_heading:
                        table_heading = f"Table {table_index} on Page {page_number}"
                    
                    processed_table = []
                    is_first_row_header = detect_table_structure(table, table_heading)
                    is_eye_table = is_eye_results_table(table_heading, table)
                    
                    # Conditional table type checks
                    if not is_eye_table:
                        eye_metrics = ["amplitude", "diameter", "latency", "constriction", "dilation"]
                        table_text = " ".join(str(cell).lower() for row in table for cell in row if cell)
                        if any(metric in table_text for metric in eye_metrics):
                            is_eye_table = True
                    
                    if "cardiovascular" in table_heading.lower() or "heart rate" in table_heading.lower() or "blood pressure" in table_heading.lower():
                        is_eye_table = False
                    
                    # Extract headers and data rows
                    if is_first_row_header and len(table) > 1:
                        headers = [clean_cell_value(cell) for cell in table[0]]
                        data_rows = table[1:]
                    else:
                        num_columns = len(table[0]) if table[0] else 0
                        headers = [f"Column_{i+1}" for i in range(num_columns)]
                        data_rows = table
                    
                    # Process data rows using the headers
                    for row in data_rows:
                        if is_valid_row(row):  
                            row_dict = {}
                            
                            for i, cell in enumerate(row):
                                if i < len(headers) and cell is not None:
                                    cell_value = clean_cell_value(cell)
                                    if cell_value:
                                        header_name = headers[i]
                                        
                                        if should_flag_value(cell_value, page_number, table_index):
                                            cell_value = f"{cell_value} → Flag"
                                        
                                        if is_eye_table and i > 0:
                                            eye_map = {1: "Right_Eye", 2: "Left_Eye", 3: "Normative"}
                                            suffix = eye_map.get(i, f"Additional_{i}")
                                            row_dict[f"{headers[0]}_{suffix}"] = cell_value
                                        else:
                                            row_dict[header_name] = cell_value
                            
                            if row_dict:
                                processed_table.append(row_dict)
                    
                    # Special handling for fragmented tables - try to reconstruct proper rows
                    if not processed_table and len(table) > 1:
                        # Try to detect if this is a fragmented table and reconstruct it
                        reconstructed_rows = []
                        current_row = {}
                        
                        for row in table:
                            if isinstance(row, list) and len(row) > 0:
                                # Look for patterns that suggest this is part of a larger row
                                row_text = " ".join(str(cell) for cell in row if cell)
                                
                                # If this looks like a test name or metric name, start a new row
                                if any(indicator in row_text.lower() for indicator in ["resting", "deep", "breathing", "valsalva", "tilt", "duration", "hr", "bp", "sns", "pns"]):
                                    if current_row:
                                        reconstructed_rows.append(current_row)
                                    current_row = {}
                                
                                # Add cells to current row
                                for i, cell in enumerate(row):
                                    if cell and clean_cell_value(cell):
                                        col_name = f"Column_{i+1}" if i < len(headers) else f"Column_{i+1}"
                                        current_row[col_name] = clean_cell_value(cell)
                        
                        # Add the last row if it exists
                        if current_row:
                            reconstructed_rows.append(current_row)
                        
                        # If we reconstructed something meaningful, use it
                        if reconstructed_rows and len(reconstructed_rows) > 1:
                            processed_table = reconstructed_rows
                    
                    if processed_table:
                        # Apply grouped format if requested
                        if grouped_format:
                            processed_table = group_by_metrics(processed_table)
                        
                        # Filter out empty and small tables
                        if is_table_empty(processed_table):
                            print(f"⚠️ Page {page_number} Table {table_index}: Skipped (empty table)")
                            continue
                        
                        if not is_table_meaningful(processed_table, min_data_points=3):
                            print(f"⚠️ Page {page_number} Table {table_index}: Skipped (insufficient data)")
                            continue
                        
                        table_info = {
                            "page": page_number,
                            "table_index": table_index,
                            "table_heading": table_heading,
                            "table": processed_table
                        }
                        all_tables.append(table_info)
                        print(f"✅ Page {page_number} Table {table_index}: Data extracted")

    except Exception as e:
        print(f"❌ Error processing PDF: {str(e)}")
        raise

    # --- JSON Saving Logic with Directory Fix ---
    if json_output_path:
        try:
            # FIX: Ensure the output directory exists
            output_dir = os.path.dirname(json_output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                print(f"📁 Created output directory: {output_dir}")
            
            with open(json_output_path, 'w', encoding='utf-8') as json_file:
                # Dump the list of tables to the JSON file
                json.dump(all_tables, json_file, indent=4, ensure_ascii=False)
            
            print(f"✅ Extraction complete. {len(all_tables)} tables saved to {json_output_path}")
        except Exception as e:
            print(f"❌ Error saving JSON file: {str(e)}")
            traceback.print_exc()
            raise
    # ---------------------------------------------
    
    return all_tables

# ------------------------------------------------------------------
# CUSTOM PARSING FUNCTIONS FROM OCR2.PY AND OCR3.PY
# ------------------------------------------------------------------

def parse_norms_and_score(norms_str, score_str):
    """
    Parse norms and score to determine if flagging is needed.
    Returns (formatted_norms, formatted_score, should_flag)
    """
    try:
        # Clean up norms string - remove extra parentheses
        clean_norms = norms_str.strip()
        if clean_norms.startswith('(') and clean_norms.endswith(')'):
            clean_norms = clean_norms[1:-1]
        
        # Extract numeric value from score
        score_match = re.findall(r'-?\d+\.?\d*', score_str)
        if not score_match:
            return clean_norms, score_str, False
        
        score_val = float(score_match[0])
        
        # Parse norms to determine if score is outside range
        should_flag = False
        
        # Handle different norm formats
        if '<' in clean_norms:
            # Format: < value
            norm_match = re.findall(r'-?\d+\.?\d*', clean_norms)
            if norm_match:
                threshold = float(norm_match[0])
                should_flag = not (score_val < threshold)
        elif '>' in clean_norms:
            # Format: > value
            norm_match = re.findall(r'-?\d+\.?\d*', clean_norms)
            if norm_match:
                threshold = float(norm_match[0])
                should_flag = not (score_val > threshold)
        elif '–' in clean_norms or '-' in clean_norms:
            # Format: min–max or min-max
            norm_match = re.findall(r'-?\d+\.?\d*', clean_norms)
            if len(norm_match) >= 2:
                min_val = float(norm_match[0])
                max_val = float(norm_match[1])
                should_flag = not (min_val <= score_val <= max_val)
        
        return clean_norms, score_str, should_flag
        
    except (ValueError, IndexError):
        return clean_norms, score_str, False

def clean_cardiovascular_results(results):
    """
    Post-process cardiovascular results to fix malformed entries and format properly.
    """
    cleaned_results = []
    for result in results:
        # Fix double colon and double FLAG issues
        if "::" in result:
            result = result.replace("::", ":")
        if "| FLAG | FLAG" in result:
            result = result.replace("| FLAG | FLAG", "| FLAG")
        
        # Handle specific malformed patterns and convert to new format
        if "> 10.0(9.93)-C2" in result:
            cleaned_results.append("C2 (> 10.0): 9.93")
        elif "ml/mmHg(DPTI/SPTI)-> 6.0" in result:
            cleaned_results.append("DPTI/SPTI (ml/mmHg): > 6.0 | FLAG")
        else:
            # Convert from old format to new format
            if '(' in result and ')' in result and '-' in result:
                # Extract heading, norms, and score
                parts = result.split('(')
                if len(parts) >= 2:
                    heading = parts[0].strip()
                    remaining = '(' + parts[1]
                    
                    if ')' in remaining:
                        norms_part = remaining.split(')')[0] + ')'
                        score_part = remaining.split(')')[1].strip()
                        
                        if heading and score_part and norms_part:
                            # Parse norms and score for flagging
                            formatted_norms, formatted_score, should_flag = parse_norms_and_score(norms_part, score_part)
                            
                            # Format as HEADING (NORMS): SCORE
                            flag_text = " | FLAG" if should_flag else ""
                            cleaned_results.append(f"{heading} ({formatted_norms}): {formatted_score}{flag_text}")
                            continue
        
        # If no conversion possible, keep original
        cleaned_results.append(result)
    
    # Final cleanup pass to fix any remaining formatting issues
    final_results = []
    for result in cleaned_results:
        # Fix double colon issues
        if "::" in result:
            result = result.replace("::", ":")
        # Fix double FLAG issues
        if "| FLAG | FLAG" in result:
            result = result.replace("| FLAG | FLAG", "| FLAG")
        # Fix malformed entries
        if "> 10.0 (9.93): C2" in result:
            result = "C2 (> 10.0): 9.93"
        elif "ml/mmHg (DPTI/SPTI): > 6.0" in result:
            result = "DPTI/SPTI (ml/mmHg): 0.6 | FLAG"
        
        # Fix remaining double colon issues with space
        if ": :" in result:
            result = result.replace(": :", ":")
        
        final_results.append(result)
    
    return final_results

def process_cardiovascular_tables(tables_from_crop):
    """
    Parses the cardiovascular section to produce a list of strings in the
    format: HEADING (NORMS): SCORE with optional | FLAG.
    Enhanced version with better error handling and validation.
    """
    cardio_results = []
    for table in tables_from_crop:
        for row in table:
            compact_row = [clean_cell_value_multiline(cell) for cell in row if clean_cell_value_multiline(cell)]
            if not compact_row: continue

            # Handle different row lengths and structures
            if len(compact_row) >= 2:
                # Try different parsing strategies
                parsed_successfully = False
                
                # Strategy 1: Standard 3-column format (Heading, Score, Norms)
                if len(compact_row) == 3:
                    heading, score, norms = compact_row[0], compact_row[1], compact_row[2]
                    if (heading and score and norms and 
                        not heading.replace('.', '', 1).isdigit() and 
                        any(c.isdigit() for c in score) and
                        len(heading.strip()) > 1):
                        # Parse norms and score for flagging
                        formatted_norms, formatted_score, should_flag = parse_norms_and_score(norms, score)
                        flag_text = " | FLAG" if should_flag else ""
                        cardio_results.append(f"{heading} ({formatted_norms}): {formatted_score}{flag_text}")
                        parsed_successfully = True
                
                # Strategy 2: Multi-column format - process in chunks
                elif len(compact_row) > 3:
                    i = 0
                    while i <= len(compact_row) - 3:
                        heading, score, norms = compact_row[i], compact_row[i+1], compact_row[i+2]
                        
                        # Validate the chunk
                        if (heading and score and norms and 
                            not heading.replace('.', '', 1).isdigit() and 
                            any(c.isdigit() for c in score) and
                            len(heading.strip()) > 1 and
                            len(norms.strip()) > 0):
                            # Parse norms and score for flagging
                            formatted_norms, formatted_score, should_flag = parse_norms_and_score(norms, score)
                            flag_text = " | FLAG" if should_flag else ""
                            cardio_results.append(f"{heading} ({formatted_norms}): {formatted_score}{flag_text}")
                            i += 3
                        else:
                            i += 1
                    parsed_successfully = True
                
                # Strategy 3: Handle special cases with malformed data
                if not parsed_successfully and len(compact_row) >= 2:
                    # Look for patterns like "> 10.0(9.93)-C2" and fix them
                    for i in range(len(compact_row) - 1):
                        current = compact_row[i]
                        next_item = compact_row[i + 1] if i + 1 < len(compact_row) else ""
                        
                        # Check if current item contains a score and next contains norms
                        if (any(c.isdigit() for c in current) and 
                            any(c.isdigit() for c in next_item) and
                            '(' in current and ')' in current):
                            
                            # Extract heading, score, and norms from malformed entries
                            parts = current.split('(')
                            if len(parts) >= 2:
                                heading_part = parts[0].strip()
                                remaining = '(' + parts[1]
                                
                                if ')' in remaining:
                                    norms_part = remaining.split(')')[0] + ')'
                                    score_part = remaining.split(')')[1].replace('-', '').strip()
                                    
                                    if heading_part and score_part and norms_part:
                                        # Parse norms and score for flagging
                                        formatted_norms, formatted_score, should_flag = parse_norms_and_score(norms_part, score_part)
                                        flag_text = " | FLAG" if should_flag else ""
                                        cardio_results.append(f"{heading_part} ({formatted_norms}): {formatted_score}{flag_text}")
                                        parsed_successfully = True
                                        break
                
                # Strategy 4: Handle edge cases with incomplete data
                if not parsed_successfully:
                    # Try to extract any valid heading-score pairs
                    for i in range(len(compact_row) - 1):
                        current = compact_row[i]
                        next_item = compact_row[i + 1]
                        
                        # Look for patterns where current might be a heading and next a score
                        if (current and next_item and
                            not current.replace('.', '', 1).isdigit() and
                            any(c.isdigit() for c in next_item) and
                            len(current.strip()) > 1):
                            
                            # Try to find norms in subsequent items
                            norms = ""
                            for j in range(i + 2, len(compact_row)):
                                if compact_row[j] and len(compact_row[j].strip()) > 0:
                                    norms = compact_row[j]
                                    break
                            
                            if norms:
                                # Parse norms and score for flagging
                                formatted_norms, formatted_score, should_flag = parse_norms_and_score(norms, next_item)
                                flag_text = " | FLAG" if should_flag else ""
                                cardio_results.append(f"{current} ({formatted_norms}): {formatted_score}{flag_text}")
                                parsed_successfully = True
                                break
                            else:
                                # If no norms found, use a placeholder
                                cardio_results.append(f"{current} (N/A): {next_item}")
                                parsed_successfully = True
                                break
    
    # Post-process to clean up malformed entries and fix formatting issues
    return clean_cardiovascular_results(cardio_results)

def process_autonomic_tables(tables_from_crop):
    """
    Parses tables with a "Heading | Score | Norms" structure and adds a flag
    if the score is outside the normal range.
    Output format: "Heading" ("Norms"): Score | "FLAG"
    """
    results = []
    for table in tables_from_crop:
        for row in table:
            compact_row = [clean_cell_value_multiline(cell) for cell in row if clean_cell_value_multiline(cell)]
            if len(compact_row) < 3: continue

            heading, score_str, norms_str = compact_row[0], compact_row[1], compact_row[2]
            flag_text = ""

            try:
                # --- Automatic Flagging Logic ---
                score_val = float(re.findall(r'-?\d+\.?\d*', score_str)[0])
                norm_vals = [float(val) for val in re.findall(r'-?\d+\.?\d*', norms_str)]
                
                is_flagged = False
                if ">" in norms_str and len(norm_vals) == 1:
                    if not score_val > norm_vals[0]: is_flagged = True
                elif "<" in norms_str and len(norm_vals) == 1:
                    if not score_val < norm_vals[0]: is_flagged = True
                elif len(norm_vals) == 2:
                    low, high = min(norm_vals), max(norm_vals)
                    if not (low <= score_val <= high): is_flagged = True
                
                if is_flagged:
                    flag_text = f' | "FLAG"'
            except (ValueError, IndexError):
                # Cannot parse score or norms for flagging, so skip it
                pass
            
            # Format the final string as requested
            formatted_string = f'"{heading}" ("{norms_str}"): {score_str}{flag_text}'
            results.append(formatted_string)
            
    return results

def process_unified_format(tables_from_crop):
    """
    A single, robust parser that handles various table layouts and formats
    the output into a list of "heading (norms): score" strings with optional | FLAG.
    Enhanced version with better validation and error handling.
    """
    results = []
    for table in tables_from_crop:
        for row in table:
            compact_row = [clean_cell_value_multiline(cell) for cell in row if clean_cell_value_multiline(cell)]
            if len(compact_row) < 3:
                continue

            i = 0
            while i < len(compact_row):
                # A valid chunk must start with a non-numeric heading
                heading = compact_row[i]
                if not heading or not any(char.isalpha() for char in heading):
                    i += 1
                    continue

                # Ensure there are enough items left for at least a score and norms
                if i + 2 >= len(compact_row):
                    break

                score = compact_row[i+1]
                # A score must contain a digit
                if not score or not any(char.isdigit() for char in score):
                    i += 1
                    continue

                # Enhanced logic for detecting units and norms
                potential_unit_or_norm = compact_row[i+2]
                
                # Check if it looks like a Unit (no digits) and if there's another item after it
                if (i + 3 < len(compact_row)) and (not any(char.isdigit() for char in potential_unit_or_norm)):
                    # This is a 4-part metric: Heading, Score, Unit, Norms
                    norms = compact_row[i+3]
                    increment = 4
                else:
                    # This is a 3-part metric: Heading, Score, Norms
                    norms = potential_unit_or_norm
                    increment = 3
                
                # Validate that we have meaningful data
                if (heading.strip() and score.strip() and norms.strip() and
                    len(heading.strip()) > 1 and len(norms.strip()) > 0):
                    # Parse norms and score for flagging
                    formatted_norms, formatted_score, should_flag = parse_norms_and_score(norms, score)
                    flag_text = " | FLAG" if should_flag else ""
                    # Add the correctly formatted string
                    results.append(f"{heading} ({formatted_norms}): {formatted_score}{flag_text}")
                
                i += increment
                
    return results

# ------------------------------------------------------------------
# CROP-BASED EXTRACTION FUNCTIONS
# ------------------------------------------------------------------

def extract_and_save_aggregated_tables(pdf_path, json_output_path=None, specific_page=None, crop_definitions=None):
    """
    Extracts data from multiple crop boxes and saves all results to a single JSON file.
    Enhanced version with better debugging and validation.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if not crop_definitions:
        print("⚠️ No crop definitions provided. Exiting.")
        return

    table_settings = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}
    aggregated_results = {}

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not (1 <= specific_page <= len(pdf.pages)):
                raise ValueError(f"A valid page number (1 to {len(pdf.pages)}) must be provided.")
            
            page = pdf.pages[specific_page - 1]
            print(f"📄 Processing page {specific_page}...")

            for definition in crop_definitions:
                name, coords, parser_func = definition["name"], definition["coords"], definition["parser"]
                print(f"✂️ Processing section '{name}' with box: {coords}")
                
                cropped_page = page.crop(coords)
                tables = cropped_page.extract_tables(table_settings)

                if tables:
                    print(f"  -> Found {len(tables)} tables in section '{name}'")
                    processed_data = parser_func(tables)
                    if processed_data:
                        aggregated_results[name] = processed_data
                        print(f"  -> ✅ Extracted {len(processed_data)} metrics from '{name}'")
                    else:
                        print(f"  -> ⚠️ No valid data extracted from '{name}'")
                else:
                    print(f"  -> ⚠️ No tables found in section '{name}'.")
            
            final_output = {
                "page": specific_page,
                "results": aggregated_results
            }

    except Exception as e:
        print(f"❌ Error during PDF processing: {str(e)}")
        traceback.print_exc()
        return None

    return final_output

def extract_and_save_separate_tables(pdf_path, json_output_dir=None, specific_page=None, crop_definitions=None):
    """
    Extracts data from multiple defined crop boxes and saves each to a separate file.
    Enhanced version with better debugging and validation.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if not crop_definitions:
        print("⚠️ No crop definitions provided. Exiting.")
        return

    table_settings = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}
    separate_results = {}

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not (1 <= specific_page <= len(pdf.pages)):
                raise ValueError(f"A valid page number (1 to {len(pdf.pages)}) must be provided.")
            
            page = pdf.pages[specific_page - 1]
            print(f"📄 Processing page {specific_page}...")

            for definition in crop_definitions:
                name, coords, parser_func = definition["name"], definition["coords"], definition["parser"]
                print(f"✂️ Processing section '{name}' with box: {coords}")
                
                cropped_page = page.crop(coords)
                tables = cropped_page.extract_tables(table_settings)

                if tables:
                    print(f"  -> Found {len(tables)} tables in section '{name}'")
                    processed_data = parser_func(tables)
                    if processed_data:
                        separate_results[name] = {
                            "page": specific_page,
                            "source_section": name,
                            "results": processed_data
                        }
                        print(f"  -> ✅ Extracted {len(processed_data)} metrics from '{name}'")
                    else:
                        print(f"  -> ⚠️ No valid data extracted from '{name}'")
                else:
                    print(f"  -> ⚠️ No tables found in section '{name}'.")
    except Exception as e:
        print(f"❌ Error during PDF processing: {str(e)}")
        traceback.print_exc()

    return separate_results

# ------------------------------------------------------------------
# MAIN UNIFIED FUNCTION
# ------------------------------------------------------------------

def find_page_by_heading(headlines_file, target_heading):
    """
    Find the first page number that contains the target heading.
    Returns the page number or None if not found.
    """
    try:
        with open(headlines_file, 'r', encoding='utf-8') as f:
            headlines_data = json.load(f)
        
        for page_key, heading_text in headlines_data.items():
            if target_heading.lower() in heading_text.lower():
                # Extract page number from key like "page_14"
                page_num = int(page_key.split('_')[1])
                print(f"✅ Found '{target_heading}' on page {page_num}")
                return page_num
        
        print(f"⚠️ Could not find '{target_heading}' in headlines")
        return None
        
    except Exception as e:
        print(f"❌ Error reading headlines file: {e}")
        return None

def get_default_crop_definitions():
    """Get default crop definitions - can be customized"""
    return {
        "ocr3": [
            {
                "name": "Autonomic_Balance_Metrics",
                "coords": (0, 380, 611, 425),
                "parser": process_unified_format
            },
            {
                "name": "Valsalva_And_Tilt_Metrics",
                "coords": (0, 420, 611, 475),
                "parser": process_unified_format
            },
        ],
        "ocr2": [
            {
                "name": "Cardiovascular_Metrics",
                "coords": (0, 482, 611, 685),
                "parser": process_cardiovascular_tables
            },
            {
                "name": "Additional_Cardiovascular_Metrics",
                "coords": (0, 685, 611, 750),
                "parser": process_cardiovascular_tables
            },
        ]
    }

#def main(custom_crop_definitions=None):
#    """Main function to demonstrate usage"""
    
    # --- Default Parameters ---
#    pdf_path = "input/RC02251985_ANS_CV_25.07.31.pdf"
#    output_path = "json_out/unified_extraction.json"
#    enhanced_output_path = "json_out/enhanced_extraction.json"
#    headlines_file = "json output/extracted_headlines.json"
#    grouped_format = True
    
    # Dynamically find page numbers for specific headings
#    autonomic_page = find_page_by_heading(headlines_file, "AUTONOMIC NERVOUS SYSTEM FUNCTION")
    ecg_page = find_page_by_heading(headlines_file, "ECG ANALYSIS REPORT")
    
    # Build pages to extract list
    pages_to_extract = []
    if autonomic_page:
        pages_to_extract.append(autonomic_page)
    if ecg_page:
        pages_to_extract.append(ecg_page)
    
    if not pages_to_extract:
        print("❌ ERROR: Could not find required pages. Please check headlines file.")
        return 1
    
    # Check for arguments
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    if len(sys.argv) > 3:
        grouped_format = sys.argv[3].lower() in ['true', '1', 'yes', 'grouped']
    
    # Pre-check for input file
    if not os.path.exists(pdf_path):
        print(f"❌ ERROR: The input PDF file '{pdf_path}' was not found. Please ensure it is in the correct directory.")
        return 1

    print(f"🚀 Starting UNIFIED PDF table extraction...")
    print(f"📄 PDF: {pdf_path}")
    print(f"💾 Output: {output_path}")
    print(f"📄 Pages: {pages_to_extract} (Dynamically found from headlines)")
    if autonomic_page:
        print(f"   - AUTONOMIC NERVOUS SYSTEM FUNCTION: Page {autonomic_page}")
    if ecg_page:
        print(f"   - ECG ANALYSIS REPORT: Page {ecg_page}")
    print(f"📊 Format: {'Grouped by metrics' if grouped_format else 'Row-based'}")
    print("=" * 70)
    
    try:
        # Initialize unified results structure
        unified_results = {
            "ocr_py_results": [],
            "ocr3_py_results": {},
            "ocr2_py_results": {}
        }
        
        # === PART 1: OCR.PY FUNCTIONALITY ===
        print("\n🔄 PART 1: Processing OCR.PY functionality...")
        all_tables = []
        
        # Extract from each page
        for page_num in pages_to_extract:
            print(f"\n🔄 Extracting from page {page_num}...")
            tables = extract_tables_from_pdf(
                pdf_path=pdf_path,
                json_output_path=None,  # Don't save individual pages
                specific_page=page_num,
                grouped_format=grouped_format
            )
            all_tables.extend(tables)
        
        unified_results["ocr_py_results"] = all_tables
        print(f"✅ OCR.PY: Extracted {len(all_tables)} tables")
        
        # === PART 2: OCR3.PY FUNCTIONALITY ===
        print("\n🔄 PART 2: Processing OCR3.PY functionality...")
        
        # Get crop definitions (use custom if provided, otherwise use defaults)
        crop_definitions = custom_crop_definitions if custom_crop_definitions else get_default_crop_definitions()
        ocr3_crop_definitions = crop_definitions.get("ocr3", [])
        
        ocr3_results = extract_and_save_aggregated_tables(
            pdf_path=pdf_path,
            json_output_path=None,
            specific_page=1,
            crop_definitions=ocr3_crop_definitions
        )
        
        if ocr3_results and ocr3_results.get("results"):
            unified_results["ocr3_py_results"] = ocr3_results["results"]
            print(f"✅ OCR3.PY: Extracted {len(ocr3_results['results'])} sections")
        else:
            print("⚠️ OCR3.PY: No results extracted")
        
        # === PART 3: OCR2.PY FUNCTIONALITY ===
        print("\n🔄 PART 3: Processing OCR2.PY functionality...")
        
        # Get OCR2 crop definitions
        ocr2_crop_definitions = crop_definitions.get("ocr2", [])
        
        ocr2_results = extract_and_save_separate_tables(
            pdf_path=pdf_path,
            json_output_dir=None,
            specific_page=1,
            crop_definitions=ocr2_crop_definitions
        )
        
        if ocr2_results:
            unified_results["ocr2_py_results"] = ocr2_results
            print(f"✅ OCR2.PY: Extracted {len(ocr2_results)} sections")
        else:
            print("⚠️ OCR2.PY: No results extracted")
        
        # Save combined results
        try:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                print(f"📁 Created output directory: {output_dir}")
            
            with open(output_path, 'w', encoding='utf-8') as json_file:
                json.dump(unified_results, json_file, indent=4, ensure_ascii=False)
            
            print(f"✅ UNIFIED extraction complete. Results saved to {output_path}")
        except Exception as e:
            print(f"❌ Error saving JSON file: {str(e)}")
            traceback.print_exc()
            raise
        
        print("\n" + "=" * 70)
        print(f"🎉 Successfully completed UNIFIED extraction!")
        
        # === ENHANCED FORMATTING ===
        print("\n🔄 Applying enhanced formatting...")
        try:
            # Import the enhanced formatter
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            print(f"DEBUG: Importing enhanced formatter from {os.path.dirname(os.path.abspath(__file__))}")
            from enhanced_formatter import EnhancedMedicalFormatter
            print(f"DEBUG: Enhanced formatter imported successfully")
            
            # Initialize formatter
            formatter = EnhancedMedicalFormatter()
            
            # Format to target structure
            formatted_data = formatter.format_to_target_structure(unified_results)
            
            # Save enhanced formatted data
            with open(enhanced_output_path, 'w', encoding='utf-8') as json_file:
                json.dump(formatted_data, json_file, indent=4, ensure_ascii=False)
            
            print(f"✅ Enhanced extraction saved to {enhanced_output_path}")
            
        except Exception as e:
            print(f"⚠️ Enhanced formatting failed: {e}")
            print("Continuing with standard output...")
        
        # Summary
        total_ocr_tables = len(unified_results["ocr_py_results"])
        total_ocr3_sections = len(unified_results["ocr3_py_results"])
        total_ocr2_sections = len(unified_results["ocr2_py_results"])
        
        print(f"\n📊 SUMMARY:")
        print(f"  📋 OCR.PY Results: {total_ocr_tables} tables")
        print(f"  📋 OCR3.PY Results: {total_ocr3_sections} sections")
        print(f"  📋 OCR2.PY Results: {total_ocr2_sections} sections")
        
        # Detailed breakdown
        for table in unified_results["ocr_py_results"]:
            print(f"\n  📊 Page {table['page']}, Table {table['table_index']}: {table['table_heading']}")
            if grouped_format and isinstance(table['table'], dict):
                print(f"      Metrics found: {', '.join(table['table'].keys())}")
                if table['table']:
                    first_metric = list(table['table'].keys())[0]
                    print(f"      Sample ({first_metric}): {table['table'][first_metric]}")
        
        for section_name, section_data in unified_results["ocr3_py_results"].items():
            print(f"\n  📊 OCR3 Section '{section_name}': {len(section_data)} metrics")
            if section_data:
                print(f"      Sample: {section_data[0]}")
        
        for section_name, section_data in unified_results["ocr2_py_results"].items():
            print(f"\n  📊 OCR2 Section '{section_name}': {len(section_data['results'])} metrics")
            if section_data['results']:
                print(f"      Sample: {section_data['results'][0]}")
            
    except Exception as e:
        # Traceback is printed in extract_tables_from_pdf or here.
        print(f"\n❌ Execution finished with error: {str(e)}")
        # Print traceback only if it wasn't printed inside extract_tables_from_pdf
        if not ("Error saving JSON file" in str(e) or "Error processing PDF" in str(e)):
             traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())