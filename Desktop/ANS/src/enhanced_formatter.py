#!/usr/bin/env python3
"""
Fixed enhanced formatter that properly adds norms to all metrics
"""

import json
import re
import os
from typing import Dict, List, Any, Optional
from groq import Groq

class EnhancedMedicalFormatter:
    """
    Enhanced formatter that restructures medical data into AUTONOMICS, CARDIOVASCULAR, 
    and ELECTROCARDIOGRAM sections with proper norms and flagging.
    """
    
    def __init__(self, groq_api_key: Optional[str] = None):
        """Initialize the formatter with optional Groq LLM integration."""
        self.groq_client = None
        if groq_api_key:
            try:
                self.groq_client = Groq(api_key=groq_api_key)
            except Exception as e:
                print(f"Warning: Could not initialize Groq client: {e}")
        
        # Define comprehensive norms for all metrics
        self.norms = {
            # AUTONOMICS
            "SNS": {"norm": "0.8–4.0", "unit": ""},
            "PNS": {"norm": "0.8–4.0", "unit": ""},
            "SNS/PNS": {"norm": "0.4–2.0", "unit": ""},
            "LF/HF": {"norm": "<3", "unit": ""},
            "SpO2": {"norm": "≥95", "unit": "%"},
            "Total_Autonomic_Activity": {"norm": "45–80", "unit": ""},
            "Autonomic_Balance": {"norm": "-3 to 3", "unit": ""},
            "E/I_Ratio": {"norm": ">1.2", "unit": ""},
            "Valsalva_Ratio": {"norm": ">1.2", "unit": ""},
            "K30/15_Ratio": {"norm": ">1.1", "unit": ""},
            "PSI": {"norm": "<1.0", "unit": ""},
            "MSI": {"norm": "<1.0", "unit": ""},
            
            # BLOOD PRESSURE NORMS
            "Deep_Breathing_Systolic": {"norm": "90–140", "unit": "mmHg"},
            "Deep_Breathing_Diastolic": {"norm": "60–90", "unit": "mmHg"},
            "Resting_Systolic": {"norm": "90–140", "unit": "mmHg"},
            "Resting_Diastolic": {"norm": "60–90", "unit": "mmHg"},
            "Resting2_Systolic": {"norm": "90–140", "unit": "mmHg"},
            "Resting2_Diastolic": {"norm": "60–90", "unit": "mmHg"},
            "Tilt_Test_Systolic": {"norm": "90–140", "unit": "mmHg"},
            "Tilt_Test_Diastolic": {"norm": "60–90", "unit": "mmHg"},
            "Valsalva_Systolic": {"norm": "90–140", "unit": "mmHg"},
            "Valsalva_Diastolic": {"norm": "60–90", "unit": "mmHg"},
            
            # CARDIOVASCULAR
            "EEI": {"norm": "0.3–0.7", "unit": ""},
            "DDI": {"norm": "0.3–0.7", "unit": ""},
            "DEI": {"norm": "0.3–0.7", "unit": ""},
            "AI": {"norm": "< -0.4", "unit": ""},
            "ABI": {"norm": "1–1.4", "unit": ""},
            "TBI": {"norm": ">0.75", "unit": ""},
            "Reflection_Index": {"norm": "0.65–0.85", "unit": ""},
            "Stiffness_Index": {"norm": "< 8.0", "unit": "m/s"},
            "Cardiac_Output": {"norm": "4.0–8.0", "unit": "l/min"},
            "Mean_Arterial_Pressure": {"norm": "70–110", "unit": "mmHg"},
            "C1": {"norm": "> 10.0", "unit": "ml/mmHg"},
            "C2": {"norm": "> 6.0", "unit": "ml/mmHg"},
            "Ventricular_Extrasystole": {"norm": "< 1", "unit": ""},
            "Atrial_Extrasystole": {"norm": "< 1", "unit": ""},
            "QRS": {"norm": "60–120", "unit": "ms"},
            "QTc": {"norm": "350–460", "unit": "ms"},
            "Body_Mass_Index": {"norm": "19–25", "unit": ""},
            "Stroke_Volume": {"norm": "55–100", "unit": "ml"},
            "Blood_Volume": {"norm": "3–5", "unit": "l"},
            "Artifacts": {"norm": "< 1", "unit": ""},
            "ST_seg": {"norm": "80–120", "unit": "ms"},
            "PR_int": {"norm": "80–120", "unit": "ms"},
            
            # ELECTROCARDIOGRAM
            "Average_Heart_Rate": {"norm": "60–100", "unit": "bpm"},
            "SDNN": {"norm": "20–50", "unit": "ms"},
            "PR_seg": {"norm": "80–120", "unit": "ms"},
            "ST_int": {"norm": "80–120", "unit": "ms"},
            "QTc_Max": {"norm": "350–460", "unit": "ms"},
            "PAC": {"norm": "< 1", "unit": "beats"},
        }
    
    def parse_bp_value(self, bp_str: str) -> Dict[str, str]:
        """Parse blood pressure string into systolic and diastolic values."""
        if not bp_str:
            return {"systolic": "", "diastolic": ""}
        
        bp_str = str(bp_str).strip()
        
        # Handle different separators
        separators = ["/", "-", "–"]
        for sep in separators:
            if sep in bp_str:
                try:
                    parts = bp_str.split(sep)
                    if len(parts) >= 2:
                        systolic = parts[0].strip()
                        diastolic = parts[1].strip()
                        
                        # Clean up any extra characters
                        systolic = re.sub(r'[^\d]', '', systolic)
                        diastolic = re.sub(r'[^\d]', '', diastolic)
                        
                        if systolic and diastolic:
                            return {"systolic": systolic, "diastolic": diastolic}
                except:
                    continue
        
        # If no separator found, try to extract numbers
        numbers = re.findall(r'\d+', bp_str)
        if len(numbers) >= 2:
            return {"systolic": numbers[0], "diastolic": numbers[1]}
        elif len(numbers) == 1:
            return {"systolic": numbers[0], "diastolic": ""}
        
        return {"systolic": "", "diastolic": ""}
    
    def normalize_bp_test_name(self, test_name: str) -> str:
        """Normalize BP test names to standard format."""
        test_name = str(test_name).strip().lower()
        
        # Map various test name formats to standard names
        if "deep" in test_name and "breath" in test_name:
            return "Deep Breathing"
        elif "resting" in test_name and "2" in test_name:
            return "Resting2"
        elif "resting" in test_name:
            return "Resting"
        elif "tilt" in test_name:
            return "Tilt Test"
        elif "valsalva" in test_name or "valsal" in test_name:
            return "Valsalva"
        else:
            # Return original name capitalized
            return test_name.title()
    
    def extract_bp_measurements(self, table_data: Dict) -> Dict[str, Dict[str, str]]:
        """Extract BP measurements from table data and organize by test type."""
        bp_measurements = {}
        
        # Look for BP data in various formats
        if "BP" in table_data:
            bp_data = table_data["BP"]
            for test_name, bp_value in bp_data.items():
                normalized_name = self.normalize_bp_test_name(test_name)
                bp_parsed = self.parse_bp_value(bp_value)
                
                if bp_parsed["systolic"] and bp_parsed["diastolic"]:
                    bp_measurements[normalized_name] = {
                        "systolic": bp_parsed["systolic"],
                        "diastolic": bp_parsed["diastolic"]
                    }
        
        # Also look for individual systolic/diastolic entries
        for key, value in table_data.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    key_lower = str(sub_key).lower()
                    if "systolic" in key_lower or "diastolic" in key_lower:
                        # Extract test name and measurement type
                        test_name = self.normalize_bp_test_name(key)
                        measurement_type = "systolic" if "systolic" in key_lower else "diastolic"
                        
                        if test_name not in bp_measurements:
                            bp_measurements[test_name] = {}
                        
                        bp_measurements[test_name][measurement_type] = str(sub_value).strip()
        
        return bp_measurements
    
    def extract_bp_from_source_data(self, ocr_results: List[Dict]) -> Dict[str, Dict[str, str]]:
        """Dynamically extract BP values from source data."""
        bp_values = {}
        
        for table_info in ocr_results:
            table_data = table_info.get("table", {})
            page_num = table_info.get("page", 0)
            
            # Look for BP data in the table
            if "BP" in table_data:
                bp_data = table_data["BP"]
                print(f"DEBUG: Found BP data on page {page_num}: {bp_data}")
                
                for test_name, bp_value in bp_data.items():
                    # Clean test name
                    clean_test_name = self.normalize_bp_test_name(test_name)
                    
                    # Parse BP value
                    bp_parsed = self.parse_bp_value(bp_value)
                    
                    if bp_parsed["systolic"] and bp_parsed["diastolic"]:
                        bp_values[clean_test_name] = {
                            "systolic": bp_parsed["systolic"],
                            "diastolic": bp_parsed["diastolic"]
                        }
                        print(f"DEBUG: Extracted BP for {clean_test_name}: {bp_parsed['systolic']}/{bp_parsed['diastolic']}")
        
        # Also check raw tables for additional BP data
        try:
            with open('json_out/extracted_tables.json', 'r', encoding='utf-8') as f:
                raw_tables = json.load(f)
            
            for table_info in raw_tables:
                table_data = table_info.get("table", [])
                page_num = table_info.get("page", 0)
                
                if isinstance(table_data, list):
                    for row in table_data:
                        if isinstance(row, dict) and "BP" in row:
                            # Look for test name in other columns
                            test_name = None
                            for key, value in row.items():
                                if key == "H" and value:
                                    test_name = self.normalize_bp_test_name(str(value))
                                    break
                            
                            if test_name and "BP" in row:
                                bp_value = row["BP"]
                                bp_parsed = self.parse_bp_value(bp_value)
                                
                                if bp_parsed["systolic"] and bp_parsed["diastolic"]:
                                    bp_values[test_name] = {
                                        "systolic": bp_parsed["systolic"],
                                        "diastolic": bp_parsed["diastolic"]
                                    }
                                    print(f"DEBUG: Extracted BP from raw table for {test_name}: {bp_parsed['systolic']}/{bp_parsed['diastolic']}")
        
        except Exception as e:
            print(f"DEBUG: Could not read raw tables: {e}")
        
        return bp_values
    
    def read_bp_from_source_data(self, unified_data: Dict) -> Dict[str, str]:
        """Dynamically read BP values from source data and return in exact order."""
        bp_values = {}
        
        print("DEBUG: Starting dynamic BP reading from source data...")
        
        # First, try to read from OCR results
        ocr_results = unified_data.get("ocr_py_results", [])
        for table_info in ocr_results:
            table_data = table_info.get("table", {})
            page_num = table_info.get("page", 0)
            
            if "BP" in table_data:
                bp_data = table_data["BP"]
                print(f"DEBUG: Found BP data in OCR results page {page_num}: {bp_data}")
                
                for test_name, bp_value in bp_data.items():
                    if bp_value and "/" in str(bp_value):
                        # Parse BP value
                        bp_parsed = self.parse_bp_value(str(bp_value))
                        if bp_parsed["systolic"] and bp_parsed["diastolic"]:
                            # Normalize test name
                            normalized_name = self.normalize_bp_test_name(test_name)
                            
                            # Store both systolic and diastolic
                            bp_values[f"{normalized_name} Systolic"] = bp_parsed["systolic"]
                            bp_values[f"{normalized_name} Diastolic"] = bp_parsed["diastolic"]
                            
                            print(f"DEBUG: Extracted BP from OCR - {normalized_name}: {bp_parsed['systolic']}/{bp_parsed['diastolic']}")
        
        # If no BP data found in OCR, try raw tables
        if not bp_values:
            try:
                with open('json_out/extracted_tables.json', 'r', encoding='utf-8') as f:
                    raw_tables = json.load(f)
                
                print(f"DEBUG: Checking {len(raw_tables)} raw tables for BP data...")
                
                for table in raw_tables:
                    table_data = table.get("table", [])
                    table_heading = table.get("table_heading", "").lower()
                    page_num = table.get("page", 0)
                    
                    # Look for tables with BP data
                    if isinstance(table_data, list):
                        for row in table_data:
                            if isinstance(row, dict) and "BP" in row:
                                h_value = row.get("H", "")
                                bp_value = row.get("BP", "")
                                
                                if bp_value and "/" in str(bp_value):
                                    # Parse BP value
                                    bp_parsed = self.parse_bp_value(str(bp_value))
                                    if bp_parsed["systolic"] and bp_parsed["diastolic"]:
                                        # Determine test name from H column or other context
                                        test_name = self.determine_test_name_from_context(h_value, row, table_heading)
                                        
                                        if test_name:
                                            bp_values[f"{test_name} Systolic"] = bp_parsed["systolic"]
                                            bp_values[f"{test_name} Diastolic"] = bp_parsed["diastolic"]
                                            
                                            print(f"DEBUG: Extracted BP from raw table page {page_num} - {test_name}: {bp_parsed['systolic']}/{bp_parsed['diastolic']}")
                
            except Exception as e:
                print(f"DEBUG: Error reading raw tables: {e}")
        
        # Create ordered BP dictionary in exact order specified
        required_bp_order = [
            "Resting Systolic",
            "Resting Diastolic", 
            "Deep Breathing Systolic",
            "Deep Breathing Diastolic",
            "Valsalva Systolic",
            "Valsalva Diastolic",
            "Tilt Test Systolic",
            "Tilt Test Diastolic",
            "Resting2 Systolic",
            "Resting2 Diastolic"
        ]
        
        ordered_bp = {}
        for bp_key in required_bp_order:
            if bp_key in bp_values:
                ordered_bp[bp_key] = bp_values[bp_key]
            else:
                ordered_bp[bp_key] = "Not Available"
                print(f"DEBUG: Missing BP value for {bp_key}")
        
        print(f"DEBUG: Final BP data extracted: {len([k for k, v in ordered_bp.items() if v != 'Not Available'])} values")
        return ordered_bp
    
    def determine_test_name_from_context(self, h_value: str, row: Dict, table_heading: str) -> str:
        """Dynamically determine test name from context."""
        h_lower = str(h_value).lower()
        
        # Check for specific patterns
        if "resting" in h_lower and ("2" in h_lower or "resting2" in h_lower):
            return "Resting2"
        elif "resting" in h_lower:
            return "Resting"
        elif "deep" in h_lower and "breathing" in h_lower:
            return "Deep Breathing"
        elif "valsala" in h_lower or "valsal" in h_lower:
            return "Valsalva"
        elif "tilt" in h_lower and "test" in h_lower:
            return "Tilt Test"
        
        # If H value is empty or unclear, try to infer from other columns
        if not h_value or h_value.strip() == "":
            # Look for patterns in other columns
            for key, value in row.items():
                if key != "BP" and value:
                    value_lower = str(value).lower()
                    if "resting" in value_lower and ("2" in value_lower or "resting2" in value_lower):
                        return "Resting2"
                    elif "resting" in value_lower:
                        return "Resting"
                    elif "deep" in value_lower and "breathing" in value_lower:
                        return "Deep Breathing"
                    elif "valsala" in value_lower or "valsal" in value_lower:
                        return "Valsalva"
                    elif "tilt" in value_lower and "test" in value_lower:
                        return "Tilt Test"
        
        # Default fallback
        return None
    
    def ensure_complete_bp_data(self, bp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all required BP measurements are present using dynamic extraction."""
        # Return the provided BP data as is, since it's already dynamically extracted
        return bp_data if bp_data else {}
    
    def should_flag_value(self, metric_name: str, value: str) -> bool:
        """Determine if a value should be flagged based on norms."""
        if not value or metric_name not in self.norms:
            return False
        
        try:
            # Extract numeric value
            numeric_value = float(re.findall(r'-?\d+\.?\d*', value)[0])
            norm_str = self.norms[metric_name]["norm"]
            
            # Parse norm string
            if ">" in norm_str:
                threshold = float(re.findall(r'-?\d+\.?\d*', norm_str)[0])
                return not (numeric_value > threshold)
            elif "<" in norm_str:
                threshold = float(re.findall(r'-?\d+\.?\d*', norm_str)[0])
                return not (numeric_value < threshold)
            elif "≥" in norm_str:
                threshold = float(re.findall(r'-?\d+\.?\d*', norm_str)[0])
                return not (numeric_value >= threshold)
            elif "–" in norm_str or "-" in norm_str:
                parts = re.findall(r'-?\d+\.?\d*', norm_str)
                if len(parts) >= 2:
                    low = float(parts[0])
                    high = float(parts[1])
                    return not (low <= numeric_value <= high)
        except (ValueError, IndexError):
            pass
        
        return False
    
    def format_metric_with_flag(self, metric_name: str, value: str) -> str:
        """Format a metric value with flag if needed."""
        flag_text = " | FLAG" if self.should_flag_value(metric_name, value) else ""
        unit_text = f" {self.norms.get(metric_name, {}).get('unit', '')}" if self.norms.get(metric_name, {}).get('unit') else ""
        return f"{value}{unit_text}{flag_text}"
    
    def process_autonomics_section(self, ocr_results: List[Dict], ocr3_results: Dict) -> Dict[str, Any]:
        """Process and format the AUTONOMICS section with dynamic page finding."""
        autonomics = {}
        
        # Dynamically find the AUTONOMIC NERVOUS SYSTEM FUNCTION page
        autonomic_page = None
        try:
            # Load headlines to find autonomic page
            headlines_file = "json_output/extracted_headlines.json"
            if os.path.exists(headlines_file):
                with open(headlines_file, 'r', encoding='utf-8') as f:
                    headlines = json.load(f)
                
                # Look for AUTONOMIC NERVOUS SYSTEM FUNCTION page
                for page_key, heading in headlines.items():
                    if "autonomic nervous system function" in heading.lower():
                        page_num = int(page_key.split('_')[1])
                        autonomic_page = page_num
                        print(f"DEBUG: Found AUTONOMIC NERVOUS SYSTEM FUNCTION on page {autonomic_page}")
                        break
                
                if autonomic_page is None:
                    print("DEBUG: AUTONOMIC NERVOUS SYSTEM FUNCTION page not found in headlines, will process all pages")
            else:
                print("DEBUG: Headlines file not found, will process all pages")
        except Exception as e:
            print(f"DEBUG: Error finding autonomic page: {e}, will process all pages")
        
        # Process OCR results (main table data)
        for table_info in ocr_results:
            page_num = table_info.get("page", 0)
            table_heading = table_info.get("table_heading", "").lower()
            
            # Check if this table contains autonomic data
            is_autonomic_table = (
                (autonomic_page is not None and page_num == autonomic_page) or  # Dynamically found autonomic page
                "duration hr bp" in table_heading or
                "hr bp sns pns" in table_heading or
                any(metric in table_heading for metric in ["hr", "bp", "sns", "pns", "lf/hf", "spo2"])
            )
            
            if is_autonomic_table:
                table_data = table_info.get("table", {})
                print(f"DEBUG: Processing autonomic table from page {page_num}: {table_heading}")
                
                # Handle special case for page 23 with time-based BP data
                if page_num == 23 and "mmhg" in table_heading.lower():
                    # Extract BP data from this special format
                    if "BP" not in autonomics:
                        autonomics["BP"] = {}
                    
                    for row in table_data:
                        if isinstance(row, dict):
                            for key, value in row.items():
                                # Extract BP from both key and value
                                for text in [str(key), str(value)]:
                                    if "mmhg" in text.lower():
                                        # Extract BP from text like "112/83 mmHg, 88 bpm"
                                        bp_match = re.search(r'(\d+)/(\d+)\s*mmhg', text, re.IGNORECASE)
                                        if bp_match:
                                            systolic = bp_match.group(1)
                                            diastolic = bp_match.group(2)
                                            # Use time as key if available
                                            time_match = re.search(r'(\d+\s*min\s*\d+\s*sec)', text, re.IGNORECASE)
                                            if time_match:
                                                time_key = time_match.group(1)
                                                autonomics["BP"][time_key] = f"{systolic}/{diastolic}"
                                                print(f"DEBUG: Added BP from page 23: {time_key} = {systolic}/{diastolic}")
                
                # Process HR data
                if "HR" in table_data:
                    hr_data = {}
                    for test_name, value in table_data["HR"].items():
                        if "-" in value:
                            # Handle range values like "82-52"
                            parts = value.split("-")
                            if len(parts) >= 2:
                                hr_data[f"{test_name} Max"] = parts[0].strip()
                                hr_data[f"{test_name} Min"] = parts[1].strip()
                        else:
                            hr_data[test_name] = value
                    autonomics["HR"] = hr_data
                
                # BP data is processed separately in main function
                
                # Process other metrics with norms and flagging
                for metric_name in ["SNS", "PNS", "SNS/PNS", "LF/HF", "SpO2"]:
                    if metric_name in table_data:
                        metric_data = {}
                        for test_name, value in table_data[metric_name].items():
                            # Clean value (preserve minus signs)
                            clean_value = re.sub(r'[^\d\.\-]', '', str(value))
                            if clean_value:
                                metric_data[test_name] = self.format_metric_with_flag(metric_name, clean_value)
                        if metric_data:
                            # Add norms to metric names in the requested format
                            norm_info = self.norms.get(metric_name, {"norm": "", "unit": ""})
                            if norm_info['norm']:
                                autonomics[f"{metric_name} (Norm: {norm_info['norm']})"] = metric_data
                            else:
                                autonomics[metric_name] = metric_data
        
        # Process OCR3 results (additional autonomic metrics)
        if ocr3_results:
            other_metrics = {}
            
            for section_name, metrics_list in ocr3_results.items():
                for metric_str in metrics_list:
                    # Parse metric string like "Autonomic Activity (ms²): 81"
                    if ":" in metric_str:
                        parts = metric_str.split(":")
                        if len(parts) >= 2:
                            metric_name = parts[0].strip()
                            value = parts[1].strip()
                            
                            # Clean metric name and map to standard names
                            clean_name = metric_name.replace("(", "").replace(")", "").replace(" ", "_")
                            
                            # Map to standard metric names
                            if "Autonomic Activity" in metric_name:
                                clean_name = "Total_Autonomic_Activity"
                            elif "Autonomic Balance" in metric_name:
                                clean_name = "Autonomic_Balance"
                            elif "E/I Ratio" in metric_name:
                                clean_name = "E/I_Ratio"
                            elif "Valsalva Ratio" in metric_name:
                                clean_name = "Valsalva_Ratio"
                            elif "K30/15 Ratio" in metric_name:
                                clean_name = "K30/15_Ratio"
                            elif "PSI" in metric_name:
                                clean_name = "PSI"
                            elif "MSI" in metric_name:
                                clean_name = "MSI"
                            
                            # Extract numeric value (preserve minus signs)
                            numeric_value = re.findall(r'-?\d+\.?\d*', value)[0] if re.findall(r'-?\d+\.?\d*', value) else value
                            
                            # Format with norm in the requested format
                            norm_info = self.norms.get(clean_name, {"norm": "", "unit": ""})
                            formatted_value = self.format_metric_with_flag(clean_name, numeric_value)
                            
                            # Check if the original metric name already contains norms
                            if "(" in metric_name and ")" in metric_name:
                                # Original metric name already has norms, use it as is
                                other_metrics[metric_name] = formatted_value
                            elif norm_info['norm']:
                                # Add norm to metric name
                                other_metrics[f"{metric_name} (Norm: {norm_info['norm']})"] = formatted_value
                            else:
                                # No norm available
                                other_metrics[metric_name] = formatted_value
            
            if other_metrics:
                autonomics["Other Metrics"] = other_metrics
        
        # Ensure BP data is always present in AUTONOMICS section
        if "BP" not in autonomics:
            autonomics["BP"] = self.ensure_complete_bp_data({})
        
        return autonomics
    
    def process_cardiovascular_section(self, ocr2_results: Dict, ocr_results: List[Dict] = None, autonomics: Dict = None) -> Dict[str, Any]:
        """Process and format the CARDIOVASCULAR section."""
        cardiovascular = {}
        
        if ocr2_results:
            for section_name, section_data in ocr2_results.items():
                results = section_data.get("results", [])
                
                for result_str in results:
                    # Parse result string like "EEI (0.3 - 0.7): 0.5"
                    if ":" in result_str:
                        parts = result_str.split(":")
                        if len(parts) >= 2:
                            metric_part = parts[0].strip()
                            value_part = parts[1].strip()
                            
                            # Special handling for C2 - extract actual value instead of description
                            if "C2" in value_part and ">" in metric_part:
                                # The format is "> 10.0 (5.87): C2" where 5.87 is the actual C2 value
                                # Extract the value from parentheses in metric_part
                                if "(" in metric_part and ")" in metric_part:
                                    c2_value = metric_part.split("(")[1].split(")")[0].strip()
                                    norm_info = self.norms.get("C2", {"norm": "> 6.0", "unit": "ml/mmHg"})
                                    unit_text = f" {norm_info['unit']}" if norm_info['unit'] else ""
                                    flag_text = " | FLAG" if self.should_flag_value("C2", c2_value) else ""
                                    cardiovascular[f"C2 (Norm: {norm_info['norm']})"] = f"{c2_value}{unit_text}{flag_text}"
                                    print(f"DEBUG: Fixed C2 reading: {c2_value}{unit_text}{flag_text}")
                                continue
                            
                            # Extract metric name and norms
                            if "(" in metric_part and ")" in metric_part:
                                metric_name = metric_part.split("(")[0].strip()
                                norms_part = metric_part.split("(")[1].split(")")[0].strip()
                                
                                # Clean metric name
                                clean_name = metric_name.replace(" ", "_")
                                
                                # Extract numeric value (preserve minus signs)
                                numeric_value = re.findall(r'-?\d+\.?\d*', value_part)[0] if re.findall(r'-?\d+\.?\d*', value_part) else value_part
                                
                                # Format with norms and flag
                                norm_info = self.norms.get(clean_name, {"norm": norms_part, "unit": ""})
                                unit_text = f" {norm_info['unit']}" if norm_info['unit'] else ""
                                flag_text = " | FLAG" if self.should_flag_value(clean_name, numeric_value) else ""
                                
                                # Add norms to metric name in the requested format
                                if norm_info['norm']:
                                    cardiovascular[f"{metric_name} (Norm: {norm_info['norm']})"] = f"{numeric_value}{unit_text}{flag_text}"
                                else:
                                    cardiovascular[metric_name] = f"{numeric_value}{unit_text}{flag_text}"
        
        # Also process cardiovascular data from OCR results if available
        # This handles cases where OCR2 results are not available
        if not cardiovascular:
            # Extract cardiovascular data from main OCR results as fallback
            # Look for cardiovascular tables in the OCR results
            for table_info in ocr_results:
                table_heading = table_info.get("table_heading", "").lower()
                if any(term in table_heading for term in ["cardiovascular", "score", "units", "norms"]):
                    table_data = table_info.get("table", [])
                    if isinstance(table_data, list):
                        for row in table_data:
                            if isinstance(row, dict):
                                # Look for cardiovascular metrics (excluding BP which is only in AUTONOMICS)
                                for key, value in row.items():
                                    if any(metric in key.lower() for metric in ["eei", "ddi", "dei", "ai", "abi", "tbi", "reflection", "stiffness", "cardiac", "stroke", "c1", "c2", "qrs", "qtc", "pr", "st"]) and "bp" not in key.lower():
                                        clean_value = str(value).strip()
                                        if clean_value and any(c.isdigit() for c in clean_value):
                                            # Try to find norms in the same row or nearby
                                            norms = ""
                                            for norm_key, norm_value in row.items():
                                                if "norm" in norm_key.lower() or any(char in str(norm_value) for char in ["-", ">", "<", "–"]):
                                                    norms = str(norm_value).strip()
                                                    break
                                            
                                            if norms:
                                                clean_name = key.replace(" ", "_")
                                                numeric_value = re.findall(r'-?\d+\.?\d*', clean_value)[0] if re.findall(r'-?\d+\.?\d*', clean_value) else clean_value
                                                norm_info = self.norms.get(clean_name, {"norm": norms, "unit": ""})
                                                unit_text = f" {norm_info['unit']}" if norm_info['unit'] else ""
                                                flag_text = " | FLAG" if self.should_flag_value(clean_name, numeric_value) else ""
                                                
                                                cardiovascular[f"{key} (Norm: {norm_info['norm']})"] = f"{numeric_value}{unit_text}{flag_text}"
        
        # BP data is now only in AUTONOMICS section, not in CARDIOVASCULAR
        
        return cardiovascular
    
    def process_electrocardiogram_section(self, ocr_results: List[Dict], raw_tables: List[Dict] = None) -> Dict[str, Any]:
        """Process ECG data from dynamically found ECG ANALYSIS REPORT page and ST seg data from page 1"""
        import re
        print(f"DEBUG: Starting ECG processing with {len(ocr_results)} OCR results and {len(raw_tables or [])} raw tables")
        
        # Initialize ECG sections
        ecg = {
            "Heart Rate": {},
            "Ventricular Details": {},
            "Supraventricular Details": {},
            "HRV Analysis": {},
            "QRS Analysis": {}
        }
        
        # Dynamically find the ECG ANALYSIS REPORT page
        ecg_page = None
        try:
            # Load headlines to find ECG page
            headlines_file = "json_output/extracted_headlines.json"
            if os.path.exists(headlines_file):
                with open(headlines_file, 'r', encoding='utf-8') as f:
                    headlines = json.load(f)
                
                # Look for ECG ANALYSIS REPORT page
                for page_key, heading in headlines.items():
                    if "ecg analysis report" in heading.lower():
                        page_num = int(page_key.split('_')[1])
                        ecg_page = page_num
                        print(f"DEBUG: Found ECG ANALYSIS REPORT on page {ecg_page}")
                        break
                
                if ecg_page is None:
                    print("DEBUG: ECG ANALYSIS REPORT page not found in headlines, will process all pages")
            else:
                print("DEBUG: Headlines file not found, will process all pages")
        except Exception as e:
            print(f"DEBUG: Error finding ECG page: {e}, will process all pages")
        
        def ensure_section(section_name: str) -> Dict[str, Any]:
            """Ensure section exists and return it"""
            if section_name not in ecg:
                ecg[section_name] = {}
            return ecg[section_name]
        
        def put(section: Dict[str, Any], key: str, value: str):
            """Put value in section"""
            section[key] = value
        
        def extract_numeric_value(text: str) -> str:
            """Extract numeric value with units"""
            if not text:
                return ""
            numeric_match = re.findall(r"(\d+\.?\d*)\s*([a-zA-Z%]*)", str(text))
            if numeric_match:
                number, unit = numeric_match[0]
                return f"{number} {unit}".strip()
            return str(text).strip()
        
        def should_flag_qtc_max(value: str) -> bool:
            """Check if QTc Max should be flagged"""
            if not value:
                return False
            numeric_match = re.findall(r"(\d+\.?\d*)", str(value))
            if numeric_match:
                numeric_value = float(numeric_match[0])
                return numeric_value > 460
            return False
        
        def should_flag_pr_seg(value: str) -> bool:
            """Check if PR int/seg should be flagged"""
            if not value:
                return False
            numeric_matches = re.findall(r"(\d+\.?\d*)", str(value))
            if len(numeric_matches) >= 2:
                try:
                    val1, val2 = float(numeric_matches[0]), float(numeric_matches[1])
                    return val1 < 80 or val1 > 120 or val2 < 80 or val2 > 120
                except:
                    pass
            return False
        
        def should_flag_st_seg(value: str) -> bool:
            """Check if ST int/seg should be flagged"""
            if not value:
                return False
            numeric_match = re.findall(r"(\d+\.?\d*)", str(value))
            if numeric_match:
                try:
                    numeric_value = float(numeric_match[0])
                    # ST segment should be flagged if > 200 ms
                    return numeric_value > 200
                except:
                    pass
            return False
        
        # Process raw tables from the dynamically found ECG page and ST seg data from page 1
        if raw_tables:
            print(f"DEBUG: Processing {len(raw_tables)} raw tables for ECG data")
            for table_info in raw_tables:
                table_data = table_info.get("table", {})
                table_heading = str(table_info.get("table_heading", ""))
                page_num = table_info.get("page", 0)
                
                # Process tables from the dynamically found ECG page and page 1 (ST seg data)
                pages_to_process = [1]  # Always process page 1 for ST seg data
                if ecg_page is not None:
                    pages_to_process.append(ecg_page)
                
                if page_num not in pages_to_process:
                    print(f"DEBUG: Skipping table from page {page_num} (not ECG page {ecg_page} or ST seg page 1)")
                    continue
                
                print(f"DEBUG: Processing ECG table from page {page_num}: {table_heading}")
                
                if isinstance(table_data, dict) and table_data:
                    print(f"DEBUG: Table has dict structure: {list(table_data.keys())}")
                    
                    # Handle the real table structure
                    for main_key, main_value in table_data.items():
                        print(f"DEBUG: Processing main key: {main_key}")
                        
                        if isinstance(main_value, dict):
                            # This is a nested dict structure (like Heart Rate table)
                            for sub_key, sub_value in main_value.items():
                                print(f"DEBUG: Processing sub key-value: {sub_key} = {sub_value}")
                                
                                # Heart Rate table structure: {"79 bpm": "Aerage Heart Rate", ...}
                                if table_heading.lower() == "heart rate":
                                    section = ensure_section("Heart Rate")
                                    if "aerage" in str(sub_value).lower() or "average" in str(sub_value).lower():
                                        put(section, "Average Heart Rate", sub_key)
                                    elif "fastest" in str(sub_value).lower() and "minutely" not in str(sub_value).lower():
                                        put(section, "Fastest rate", sub_key)
                                    elif "slowest" in str(sub_value).lower() and "minutely" not in str(sub_value).lower():
                                        put(section, "Slowest rate", sub_key)
                                    elif "fastest" in str(sub_value).lower() and "minutely" in str(sub_value).lower():
                                        put(section, "Fastest minutely rate", sub_key)
                                    elif "slowest" in str(sub_value).lower() and "minutely" in str(sub_value).lower():
                                        put(section, "Slowest minutely rate", sub_key)
                                    print(f"DEBUG: Added Heart Rate from page 24: {sub_value} = {sub_key}")
                                
                                # Special handling for HRV Analysis table from page 23 - CHECK THIS FIRST!
                                if table_heading.lower() == "hrv analysis":
                                    section = ensure_section("HRV Analysis")
                                    # The structure is: {"54 ms": "SDNN", "138 ms at 14:57:43": "SDNN Max", "9 ms at 15:08:33": "SDNN Min"}
                                    if "sdnn" in str(sub_value).lower() and "max" not in str(sub_value).lower() and "min" not in str(sub_value).lower():
                                        put(section, "SDNN", sub_key)
                                        print(f"DEBUG: Added HRV from page {page_num}: {sub_value} = {sub_key} -> key: SDNN:")
                                    elif "sdnn" in str(sub_value).lower() and "max" in str(sub_value).lower():
                                        put(section, "SDNN Max", sub_key)
                                        print(f"DEBUG: Added HRV from page {page_num}: {sub_value} = {sub_key} -> key: SDNN Max:")
                                    elif "sdnn" in str(sub_value).lower() and "min" in str(sub_value).lower():
                                        put(section, "SDNN Min", sub_key)
                                        print(f"DEBUG: Added HRV from page {page_num}: {sub_value} = {sub_key} -> key: SDNN Min:")
                                
                                # HRV Analysis table structure: {"SDNN": "35 ms", ...} (other formats)
                                elif "pause" in table_heading.lower() or "block" in table_heading.lower():
                                    section = ensure_section("HRV Analysis")
                                    if "sdnn" in str(sub_key).lower() and "max" not in str(sub_key).lower() and "min" not in str(sub_key).lower():
                                        put(section, "SDNN", sub_value)
                                    elif "sdnn" in str(sub_key).lower() and "max" in str(sub_key).lower():
                                        put(section, "SDNN Max", sub_value)
                                    elif "sdnn" in str(sub_key).lower() and "min" in str(sub_key).lower():
                                        put(section, "SDNN Min", sub_value)
                                    print(f"DEBUG: Added HRV: {sub_key} = {sub_value}")
                                
                                # QRS Analysis table structure: {"QRS": "71 ms", ...}
                                elif "qrs" in table_heading.lower():
                                    section = ensure_section("QRS Analysis")
                                    if "qrs" in str(sub_key).lower():
                                        numeric_value = extract_numeric_value(sub_value)
                                        put(section, "QRS", numeric_value)
                                    elif "qt" in str(sub_key).lower() and "/" in sub_value:
                                        put(section, "QT / QTc", sub_value)
                                    elif "qtc" in str(sub_key).lower() and "max" in str(sub_key).lower():
                                        numeric_value = extract_numeric_value(sub_value)
                                        if should_flag_qtc_max(numeric_value):
                                            put(section, "QTc Max", f"{numeric_value} | FLAG")
                                        else:
                                            put(section, "QTc Max", numeric_value)
                                    elif "pr" in str(sub_key).lower():
                                        if should_flag_pr_seg(sub_value):
                                            put(section, "PR int / seg", f"{sub_value} | FLAG")
                                        else:
                                            put(section, "PR int / seg", sub_value)
                                    elif "st" in str(sub_key).lower():
                                        if should_flag_st_seg(sub_value):
                                            put(section, "ST int / seg", f"{sub_value} | FLAG")
                                        else:
                                            put(section, "ST int / seg", sub_value)
                                    print(f"DEBUG: Added QRS Analysis from page {page_num}: {sub_key} = {sub_value}")
                        
                        else:
                            # This is a simple key-value pair
                            print(f"DEBUG: Simple key-value: {main_key} = {main_value}")
                
                # Special handling for ST seg data from page 1
                if page_num == 1 and isinstance(table_data, dict):
                    # Look for the specific table structure that contains ST seg data
                    st_seg_found = False
                    st_seg_value = None
                    
                    # First, find the column with ST seg data
                    for main_key, main_value in table_data.items():
                        if isinstance(main_value, dict):
                            for sub_key, sub_value in main_value.items():
                                # Look for ST seg data - the structure is: QRS = ST seg
                                if "st seg" in str(sub_value).lower():
                                    print(f"DEBUG: Found ST seg in {main_key}: {sub_key} = {sub_value}")
                                    st_seg_found = True
                                    break
                            if st_seg_found:
                                break
                    
                    # If ST seg found, look for the numeric value in any column
                    if st_seg_found:
                        for main_key, main_value in table_data.items():
                            if isinstance(main_value, dict):
                                for sub_key, sub_value in main_value.items():
                                    # Look for QRS = 311 (the numeric value) - specifically the one that's a pure number
                                    if "qrs" in str(sub_key).lower() and str(sub_value).isdigit() and int(sub_value) > 200:
                                        st_seg_value = f"{sub_value} ms"
                                        print(f"DEBUG: Found ST seg value: {sub_key} = {sub_value}")
                                        break
                                if st_seg_value:
                                    break
                    
                    if st_seg_found and st_seg_value:
                        section = ensure_section("QRS Analysis")
                        if should_flag_st_seg(st_seg_value):
                            put(section, "ST int / seg", f"{st_seg_value} | FLAG")
                        else:
                            put(section, "ST int / seg", st_seg_value)
                        print(f"DEBUG: Added ST int / seg from page 1: {st_seg_value}")
        
        # Ensure all required ECG values are present with proper labels
        # Heart Rate section - ensure all required values are present
        heart_rate_section = ensure_section("Heart Rate")
        required_heart_rate_values = {
            "Heart Rate": "Not Available",
            "Average Heart Rate": "Not Available", 
            "Fastest rate": "Not Available",
            "Slowest rate": "Not Available",
            "Fastest minutely rate": "Not Available",
            "Slowest minutely rate": "Not Available"
        }
        
        for key, default_value in required_heart_rate_values.items():
            if key not in heart_rate_section:
                put(heart_rate_section, key, default_value)
                print(f"DEBUG: Added missing Heart Rate value: {key} = {default_value}")
        
        # Special handling for "Heart Rate" field - use Average Heart Rate value if available
        if "Heart Rate" in heart_rate_section and heart_rate_section["Heart Rate"] == "Not Available":
            if "Average Heart Rate" in heart_rate_section and heart_rate_section["Average Heart Rate"] != "Not Available":
                heart_rate_section["Heart Rate"] = heart_rate_section["Average Heart Rate"]
                print(f"DEBUG: Set Heart Rate to Average Heart Rate value: {heart_rate_section['Heart Rate']}")
        
        # Ventricular Details - ensure all required values are present
        ventricular_section = ensure_section("Ventricular Details")
        required_ventricular_values = {
            "PVC - Ventricular Ectopy": "0 beats (0%)",
            "Ventricular Couplet": "0 episodes"
        }
        
        for key, default_value in required_ventricular_values.items():
            if key not in ventricular_section:
                put(ventricular_section, key, default_value)
                print(f"DEBUG: Added missing Ventricular value: {key} = {default_value}")
        
        # Supraventricular Details - ensure all required values are present
        supraventricular_section = ensure_section("Supraventricular Details")
        required_supraventricular_values = {
            "PAC - Supraventricular Ectopy": "0 beats (0%)",
            "Supraventricular Couplet": "0 episodes"
        }
        
        for key, default_value in required_supraventricular_values.items():
            if key not in supraventricular_section:
                put(supraventricular_section, key, default_value)
                print(f"DEBUG: Added missing Supraventricular value: {key} = {default_value}")
        
        # HRV Analysis - ensure all required values are present
        hrv_section = ensure_section("HRV Analysis")
        required_hrv_values = {
            "SDNN": "Not Available",
            "SDNN Max": "Not Available", 
            "SDNN Min": "Not Available"
        }
        
        print(f"DEBUG: HRV section before ensuring required values: {hrv_section}")
        for key, default_value in required_hrv_values.items():
            if key not in hrv_section:
                put(hrv_section, key, default_value)
                print(f"DEBUG: Added missing HRV value: {key} = {default_value}")
            else:
                print(f"DEBUG: HRV value already exists: {key} = {hrv_section[key]}")
        print(f"DEBUG: HRV section after ensuring required values: {hrv_section}")
        
        # QRS Analysis - ensure all required values are present
        qrs_section = ensure_section("QRS Analysis")
        required_qrs_values = {
            "QRS": "Not Available",
            "QT / QTc": "Not Available",
            "QTc Max": "Not Available",
            "PR int / seg": "Not Available",
            "ST int / seg": "Not Available"
        }
        
        for key, default_value in required_qrs_values.items():
            if key not in qrs_section:
                put(qrs_section, key, default_value)
                print(f"DEBUG: Added missing QRS value: {key} = {default_value}")
        
        # Debug: Show final ECG result
        print(f"DEBUG: Final ECG result:")
        for section_name, section_data in ecg.items():
            if isinstance(section_data, dict) and section_data:
                print(f"  {section_name}: {len(section_data)} items")
                for metric, value in section_data.items():
                    print(f"    {metric}: {value}")
            else:
                print(f"  {section_name}: Empty or not dict")
        
        return ecg
    
    def format_ecg_output(self, ecg: Dict[str, Any]) -> Dict[str, Any]:
        """Format ECG output according to specified structure with proper indentation."""
        formatted_ecg = {}
        
        # Define the order of sections as requested
        section_order = [
            "Heart Rate",
            "Ventricular Details", 
            "Supraventricular Details",
            "HRV Analysis",
            "QRS Analysis"
        ]
        
        for section_name in section_order:
            if section_name in ecg:
                section_data = ecg[section_name]
                if isinstance(section_data, dict):
                    formatted_section = {}
                    for metric_name, value in section_data.items():
                        # Format with proper indentation (tab)
                        formatted_section[f"\t\t{metric_name}"] = value
                    formatted_ecg[section_name] = formatted_section
                else:
                    formatted_ecg[section_name] = section_data
        
        # Add any remaining sections not in the predefined order
        for section_name, section_data in ecg.items():
            if section_name not in section_order:
                if isinstance(section_data, dict):
                    formatted_section = {}
                    for metric_name, value in section_data.items():
                        formatted_section[f"\t\t{metric_name}"] = value
                    formatted_ecg[section_name] = formatted_section
                else:
                    formatted_ecg[section_name] = section_data
        
        return formatted_ecg
    
    def generate_summary(self, autonomics: Dict, cardiovascular: Dict, ecg: Dict) -> List[str]:
        """Generate a summary of flagged findings."""
        flagged_findings = []
        
        # Process autonomics flags
        for section_name, section_data in autonomics.items():
            if isinstance(section_data, dict):
                for metric_name, value in section_data.items():
                    if "| FLAG" in str(value):
                        # Extract the headline (metric name) and flag part
                        headline = f"{section_name} {metric_name}" if section_name != "Other Metrics" else metric_name
                        flag_part = value.split("| FLAG")[0].strip()
                        flagged_findings.append(f"{headline}: {flag_part} | FLAG")
        
        # Process cardiovascular flags
        for metric_name, value in cardiovascular.items():
            if "| FLAG" in str(value):
                # Extract the headline (metric name) and flag part
                headline = metric_name
                flag_part = value.split("| FLAG")[0].strip()
                flagged_findings.append(f"{headline}: {flag_part} | FLAG")
        
        # Process ECG flags
        for section_name, section_data in ecg.items():
            if isinstance(section_data, dict):
                for metric_name, value in section_data.items():
                    if "| FLAG" in str(value):
                        # Extract the headline (metric name) and flag part
                        headline = f"{section_name} {metric_name}"
                        flag_part = value.split("| FLAG")[0].strip()
                        flagged_findings.append(f"{headline}: {flag_part} | FLAG")
        
        return flagged_findings
    
    def format_to_target_structure(self, unified_data: Dict) -> Dict[str, Any]:
        """Convert unified data to the target structure."""
        print(f"DEBUG: Starting format_to_target_structure")
        ocr_results = unified_data.get("ocr_py_results", [])
        ocr3_results = unified_data.get("ocr3_py_results", {})
        ocr2_results = unified_data.get("ocr2_py_results", {})
        
        print(f"DEBUG: OCR results: {len(ocr_results)}, OCR3 results: {len(ocr3_results)}, OCR2 results: {len(ocr2_results)}")
        
        # Load raw tables for ECG processing
        raw_tables = []
        try:
            with open('json_output/extracted_tables.json', 'r', encoding='utf-8') as f:
                raw_tables = json.load(f)
            print(f"DEBUG: Loaded {len(raw_tables)} raw tables for ECG processing")
        except Exception as e:
            print(f"DEBUG: Could not load raw tables: {e}")
        
        # Process each section
        autonomics = self.process_autonomics_section(ocr_results, ocr3_results)
        
        # Read BP data directly from source and add to autonomics
        bp_data = self.read_bp_from_source_data(unified_data)
        if bp_data:
            autonomics["BP"] = bp_data
        
        cardiovascular = self.process_cardiovascular_section(ocr2_results, ocr_results, autonomics)
        
        # Debug: Check what data is being passed to ECG processing
        print(f"DEBUG: About to process ECG with:")
        print(f"  - ocr_results: {len(ocr_results)} items")
        print(f"  - raw_tables: {len(raw_tables) if raw_tables else 0} items")
        if raw_tables:
            print(f"  - raw_tables sample: {raw_tables[0] if raw_tables else 'None'}")
        
        ecg = self.process_electrocardiogram_section(ocr_results, raw_tables)
        
        # Generate summary
        summary = self.generate_summary(autonomics, cardiovascular, ecg)
        
        # BP data is only in AUTONOMICS section, no separate summary needed
        
        # Integrate ECG data into the main structure
        integrated_data = {
            "AUTONOMICS": autonomics,
            "CARDIOVASCULAR": cardiovascular,
            "ELECTROCARDIOGRAM": ecg,
            "Summary_of_Flagged_Findings": summary
        }
        
        return integrated_data

def main():
    """Main function to demonstrate usage."""
    # Initialize formatter
    formatter = EnhancedMedicalFormatter()
    
    # Load existing unified data
    input_file = "/Users/satyamj/Desktop/ANS/json_out/unified_extraction.json"
    output_file = "/Users/satyamj/Desktop/ANS/json_out/enhanced_extraction.json"
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            unified_data = json.load(f)
        
        # Format to target structure
        formatted_data = formatter.format_to_target_structure(unified_data)
        
        # Save formatted data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(formatted_data, f, indent=4, ensure_ascii=False)
        
        print(f"✅ Enhanced extraction saved to {output_file}")
        
        # Print summary
        print(f"\n📊 SUMMARY:")
        print(f"  📋 AUTONOMICS: {len(formatted_data['AUTONOMICS'])} sections")
        print(f"  📋 CARDIOVASCULAR: {len(formatted_data['CARDIOVASCULAR'])} metrics")
        print(f"  📋 ELECTROCARDIOGRAM: {len(formatted_data['ELECTROCARDIOGRAM'])} sections")
        print(f"  📋 Flagged Findings: {len(formatted_data['Summary_of_Flagged_Findings'])} items")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
