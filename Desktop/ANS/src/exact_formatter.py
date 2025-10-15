#!/usr/bin/env python3
"""
Exact formatter that outputs medical data in the exact format requested by the user.
This formatter searches through the entire PDF to find missing data and outputs
in the exact format specified.
"""

import json
import re
import os
from typing import Dict, List, Any, Optional

class ExactMedicalFormatter:
    """
    Formatter that outputs medical data in the exact format requested:
    AUTONOMICS, CARDIOVASCULAR, and ELECTROCARDIOGRAM sections with specific field names.
    """
    
    def __init__(self):
        """Initialize the exact formatter."""
        pass
    
    def search_pdf_for_missing_data(self, pdf_path: str) -> Dict[str, Any]:
        """Search through the entire PDF for missing data."""
        missing_data = {}
        
        try:
            # Load all extracted tables
            with open('json_output/extracted_tables.json', 'r', encoding='utf-8') as f:
                all_tables = json.load(f)
            
            # Search for missing HR data (Deep Breathing Max/Min, Valsalva Max/Min)
            for table_info in all_tables:
                table_data = table_info.get("table", {})
                page_num = table_info.get("page", 0)
                
                # Look for Deep Breathing and Valsalva data
                if isinstance(table_data, dict):
                    for key, value in table_data.items():
                        if isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                key_lower = str(sub_key).lower()
                                value_lower = str(sub_value).lower()
                                
                                # Look for Deep Breathing data
                                if "deep" in key_lower and "breath" in key_lower:
                                    if "max" in value_lower or "min" in value_lower:
                                        # Extract numeric values
                                        numbers = re.findall(r'\d+', str(sub_value))
                                        if len(numbers) >= 2:
                                            missing_data["Deep Breathing Max"] = numbers[0]
                                            missing_data["Deep Breathing Min"] = numbers[1]
                                        elif len(numbers) == 1:
                                            missing_data["Deep Breathing"] = numbers[0]
                                
                                # Look for Valsalva data
                                if "valsalva" in key_lower or "valsal" in key_lower:
                                    if "max" in value_lower or "min" in value_lower:
                                        # Extract numeric values
                                        numbers = re.findall(r'\d+', str(sub_value))
                                        if len(numbers) >= 2:
                                            missing_data["Valsalva Max"] = numbers[0]
                                            missing_data["Valsalva Min"] = numbers[1]
                                        elif len(numbers) == 1:
                                            missing_data["Valsalva"] = numbers[0]
                                
                                # Look for additional metrics
                                if "autonomic activity" in value_lower:
                                    numbers = re.findall(r'\d+', str(sub_value))
                                    if numbers:
                                        missing_data["Total Autonomic Activity"] = numbers[0]
                                
                                if "autonomic balance" in value_lower:
                                    numbers = re.findall(r'-?\d+\.?\d*', str(sub_value))
                                    if numbers:
                                        missing_data["Autonomic Balance"] = numbers[0]
                                
                                if "e/i ratio" in value_lower:
                                    numbers = re.findall(r'\d+\.?\d*', str(sub_value))
                                    if numbers:
                                        missing_data["E/I Ratio"] = numbers[0]
                                
                                if "valsalva ratio" in value_lower:
                                    numbers = re.findall(r'\d+\.?\d*', str(sub_value))
                                    if numbers:
                                        missing_data["Valsalva Ratio"] = numbers[0]
                                
                                if "k30/15" in value_lower or "30/15" in value_lower:
                                    numbers = re.findall(r'\d+\.?\d*', str(sub_value))
                                    if numbers:
                                        missing_data["K30/15 Ratio"] = numbers[0]
                                
                                if "psi" in value_lower and "autonomic" in value_lower:
                                    numbers = re.findall(r'-?\d+\.?\d*', str(sub_value))
                                    if numbers:
                                        missing_data["Autonomic Physical Dysregulation (PSI)"] = numbers[0]
                                
                                if "msi" in value_lower and "mental" in value_lower:
                                    numbers = re.findall(r'-?\d+\.?\d*', str(sub_value))
                                    if numbers:
                                        missing_data["Accumulative Mental Stress (MSI)"] = numbers[0]
            
            # Search for cardiovascular data
            for table_info in all_tables:
                table_data = table_info.get("table", {})
                
                if isinstance(table_data, dict):
                    for key, value in table_data.items():
                        if isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                key_lower = str(sub_key).lower()
                                value_lower = str(sub_value).lower()
                                
                                # Look for cardiovascular metrics
                                if "eei" in key_lower:
                                    numbers = re.findall(r'\d+\.?\d*', str(sub_value))
                                    if numbers:
                                        missing_data["EEI"] = numbers[0]
                                
                                if "ddi" in key_lower:
                                    numbers = re.findall(r'\d+\.?\d*', str(sub_value))
                                    if numbers:
                                        missing_data["DDI"] = numbers[0]
                                
                                if "dei" in key_lower:
                                    numbers = re.findall(r'\d+\.?\d*', str(sub_value))
                                    if numbers:
                                        missing_data["DEI"] = numbers[0]
                                
                                if "ai" in key_lower and "augmentation" in value_lower:
                                    numbers = re.findall(r'-?\d+\.?\d*', str(sub_value))
                                    if numbers:
                                        missing_data["AI"] = numbers[0]
                                
                                if "abi" in key_lower or "ankle" in value_lower:
                                    numbers = re.findall(r'\d+\.?\d*', str(sub_value))
                                    if numbers:
                                        missing_data["Right Ankle/Brachial Index"] = numbers[0]
                                
                                if "tbi" in key_lower or "toe" in value_lower:
                                    numbers = re.findall(r'\d+\.?\d*', str(sub_value))
                                    if numbers:
                                        missing_data["Right Toe/Brachial Index"] = numbers[0]
                                
                                if "reflection index" in value_lower:
                                    numbers = re.findall(r'\d+\.?\d*', str(sub_value))
                                    if numbers:
                                        missing_data["Reflection Index"] = numbers[0]
                                
                                if "stiffness index" in value_lower:
                                    numbers = re.findall(r'\d+\.?\d*', str(sub_value))
                                    if numbers:
                                        missing_data["Stiffness Index"] = numbers[0]
                                
                                if "cardiac output" in value_lower:
                                    numbers = re.findall(r'\d+\.?\d*', str(sub_value))
                                    if numbers:
                                        missing_data["Cardiac Output"] = numbers[0]
                                
                                if "mean arterial pressure" in value_lower:
                                    numbers = re.findall(r'\d+', str(sub_value))
                                    if numbers:
                                        missing_data["Mean Arterial Pressure"] = numbers[0]
                                
                                if "c1" in key_lower and ">" in str(sub_value):
                                    numbers = re.findall(r'\d+\.?\d*', str(sub_value))
                                    if numbers:
                                        missing_data["C1"] = numbers[0]
                                
                                if "c2" in key_lower and ">" in str(sub_value):
                                    numbers = re.findall(r'\d+\.?\d*', str(sub_value))
                                    if numbers:
                                        missing_data["C2"] = numbers[0]
                                
                                if "ventricular extrasystole" in value_lower:
                                    numbers = re.findall(r'\d+', str(sub_value))
                                    if numbers:
                                        missing_data["Ventricular Extrasystole"] = numbers[0]
                                
                                if "atrial extrasystole" in value_lower:
                                    numbers = re.findall(r'\d+', str(sub_value))
                                    if numbers:
                                        missing_data["Atrial Extrasystole"] = numbers[0]
                                
                                if "qrs" in key_lower and "ms" in str(sub_value):
                                    numbers = re.findall(r'\d+', str(sub_value))
                                    if numbers:
                                        missing_data["QRS"] = numbers[0]
                                
                                if "qtc" in key_lower and "ms" in str(sub_value):
                                    numbers = re.findall(r'\d+', str(sub_value))
                                    if numbers:
                                        missing_data["QTc"] = numbers[0]
                                
                                if "body mass index" in value_lower or "bmi" in value_lower:
                                    numbers = re.findall(r'\d+\.?\d*', str(sub_value))
                                    if numbers:
                                        missing_data["Body Mass Index"] = numbers[0]
                                
                                if "stroke volume" in value_lower:
                                    numbers = re.findall(r'\d+', str(sub_value))
                                    if numbers:
                                        missing_data["Stroke Volume"] = numbers[0]
                                
                                if "blood volume" in value_lower:
                                    numbers = re.findall(r'\d+\.?\d*', str(sub_value))
                                    if numbers:
                                        missing_data["Blood Volume"] = numbers[0]
                                
                                if "artifacts" in value_lower:
                                    numbers = re.findall(r'\d+', str(sub_value))
                                    if numbers:
                                        missing_data["Artifacts"] = numbers[0]
                                
                                if "st seg" in value_lower or "st segment" in value_lower:
                                    numbers = re.findall(r'\d+', str(sub_value))
                                    if numbers:
                                        missing_data["ST seg"] = numbers[0]
            
            # Search for ECG data
            for table_info in all_tables:
                table_data = table_info.get("table", {})
                page_num = table_info.get("page", 0)
                
                if isinstance(table_data, dict):
                    for key, value in table_data.items():
                        if isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                key_lower = str(sub_key).lower()
                                value_lower = str(sub_value).lower()
                                
                                # Look for heart rate data
                                if "average heart rate" in value_lower or "aerage heart rate" in value_lower:
                                    numbers = re.findall(r'\d+', str(sub_key))
                                    if numbers:
                                        missing_data["Average Heart Rate"] = numbers[0]
                                
                                if "fastest rate" in value_lower and "minutely" not in value_lower:
                                    numbers = re.findall(r'\d+', str(sub_key))
                                    if numbers:
                                        missing_data["Fastest rate"] = numbers[0]
                                
                                if "slowest rate" in value_lower and "minutely" not in value_lower:
                                    numbers = re.findall(r'\d+', str(sub_key))
                                    if numbers:
                                        missing_data["Slowest rate"] = numbers[0]
                                
                                if "fastest minutely rate" in value_lower:
                                    numbers = re.findall(r'\d+', str(sub_key))
                                    if numbers:
                                        missing_data["Fastest minutely rate"] = numbers[0]
                                
                                if "slowest minutely rate" in value_lower:
                                    numbers = re.findall(r'\d+', str(sub_key))
                                    if numbers:
                                        missing_data["Slowest minutely rate"] = numbers[0]
                                
                                # Look for ventricular data
                                if "pvc" in value_lower or "ventricular ectopy" in value_lower:
                                    numbers = re.findall(r'\d+', str(sub_key))
                                    if numbers:
                                        missing_data["PVC - Ventricular Ectopy"] = f"{numbers[0]} beats"
                                
                                if "ventricular couplet" in value_lower:
                                    numbers = re.findall(r'\d+', str(sub_key))
                                    if numbers:
                                        missing_data["Ventricular Couplet"] = f"{numbers[0]} episodes"
                                
                                # Look for supraventricular data
                                if "pac" in value_lower or "supraventricular ectopy" in value_lower:
                                    numbers = re.findall(r'\d+', str(sub_key))
                                    if numbers:
                                        missing_data["PAC - Supraventricular Ectopy"] = f"{numbers[0]} beats"
                                
                                if "supraventricular couplet" in value_lower:
                                    numbers = re.findall(r'\d+', str(sub_key))
                                    if numbers:
                                        missing_data["Supraventricular Couplet"] = f"{numbers[0]} episodes"
                                
                                # Look for HRV data
                                if "sdnn" in key_lower and "max" not in key_lower and "min" not in key_lower:
                                    numbers = re.findall(r'\d+', str(sub_value))
                                    if numbers:
                                        missing_data["SDNN"] = numbers[0]
                                
                                if "sdnn max" in value_lower:
                                    numbers = re.findall(r'\d+', str(sub_key))
                                    if numbers:
                                        missing_data["SDNN Max"] = numbers[0]
                                
                                if "sdnn min" in value_lower:
                                    numbers = re.findall(r'\d+', str(sub_key))
                                    if numbers:
                                        missing_data["SDNN Min"] = numbers[0]
                                
                                # Look for QRS analysis data
                                if "qrs" in key_lower and "ms" in str(sub_value):
                                    numbers = re.findall(r'\d+', str(sub_value))
                                    if numbers:
                                        missing_data["QRS"] = numbers[0]
                                
                                if "qt" in key_lower and "/" in str(sub_value):
                                    missing_data["QT / QTc"] = str(sub_value)
                                
                                if "qtc max" in value_lower:
                                    numbers = re.findall(r'\d+', str(sub_key))
                                    if numbers:
                                        missing_data["QTc Max"] = numbers[0]
                                
                                if "pr int" in value_lower or "pr seg" in value_lower:
                                    missing_data["PR int / seg"] = str(sub_value)
                                
                                if "st int" in value_lower or "st seg" in value_lower:
                                    missing_data["ST int / seg"] = str(sub_value)
        
        except Exception as e:
            print(f"Error searching PDF for missing data: {e}")
        
        return missing_data
    
    def format_to_exact_structure(self, unified_data: Dict) -> str:
        """Convert unified data to the exact format requested by the user."""
        
        # Load existing data
        ocr_results = unified_data.get("ocr_py_results", [])
        ocr3_results = unified_data.get("ocr3_py_results", {})
        ocr2_results = unified_data.get("ocr2_py_results", {})
        
        # Extract data from existing results
        autonomics_data = {}
        cardiovascular_data = {}
        ecg_data = {}
        
        # Process AUTONOMICS data from OCR results
        for table_info in ocr_results:
            table_data = table_info.get("table", {})
            
            if "HR" in table_data:
                hr_data = table_data["HR"]
                autonomics_data["HR"] = {
                    "Resting": hr_data.get("Resting", ""),
                    "Deep Breathing Max": "",
                    "Deep Breathing Min": "",
                    "Valsalva Max": "",
                    "Valsalva Min": "",
                    "Tilt Test": hr_data.get("Tilt Test", ""),
                    "Resting2": hr_data.get("Resting2", "")
                }
            
            if "BP" in table_data:
                bp_data = table_data["BP"]
                autonomics_data["BP"] = {
                    "Resting Systolic": "",
                    "Resting Diastolic": "",
                    "Deep Breathing Systolic": "",
                    "Deep Breathing Diastolic": "",
                    "Valsalva Systolic": "",
                    "Valsalva Diastolic": "",
                    "Tilt Test Systolic": "",
                    "Tilt Test Diastolic": "",
                    "Resting2 Systolic": "",
                    "Resting2 Diastolic": ""
                }
                
                # Parse BP values
                for test_name, bp_value in bp_data.items():
                    if "/" in str(bp_value):
                        systolic, diastolic = str(bp_value).split("/")
                        if test_name == "Resting":
                            autonomics_data["BP"]["Resting Systolic"] = systolic.strip()
                            autonomics_data["BP"]["Resting Diastolic"] = diastolic.strip()
                        elif test_name == "Tilt Test":
                            autonomics_data["BP"]["Tilt Test Systolic"] = systolic.strip()
                            autonomics_data["BP"]["Tilt Test Diastolic"] = diastolic.strip()
                        elif test_name == "Resting2":
                            autonomics_data["BP"]["Resting2 Systolic"] = systolic.strip()
                            autonomics_data["BP"]["Resting2 Diastolic"] = diastolic.strip()
            
            if "SNS" in table_data:
                sns_data = table_data["SNS"]
                autonomics_data["SNS"] = {
                    "Resting": sns_data.get("Resting", ""),
                    "Deep Breathing": "",
                    "Valsalva": "",
                    "Tilt Test": sns_data.get("Tilt Test", ""),
                    "Resting2": sns_data.get("Resting2", "")
                }
            
            if "PNS" in table_data:
                pns_data = table_data["PNS"]
                autonomics_data["PNS"] = {
                    "Resting": pns_data.get("Resting", ""),
                    "Deep Breathing": "",
                    "Valsalva": "",
                    "Tilt Test": pns_data.get("Tilt Test", ""),
                    "Resting2": pns_data.get("Resting2", "")
                }
            
            if "SNS/PNS" in table_data:
                sns_pns_data = table_data["SNS/PNS"]
                autonomics_data["SNS/PNS Ratio"] = {
                    "Resting": sns_pns_data.get("Resting", ""),
                    "Deep Breathing": "",
                    "Valsalva": "",
                    "Tilt Test": sns_pns_data.get("Tilt Test", ""),
                    "Resting2": sns_pns_data.get("Resting2", "")
                }
            
            if "LF/HF" in table_data:
                lf_hf_data = table_data["LF/HF"]
                autonomics_data["LF/HF"] = {
                    "Resting": lf_hf_data.get("Resting", ""),
                    "Deep Breathing": "",
                    "Valsalva": "",
                    "Tilt Test": lf_hf_data.get("Tilt Test", ""),
                    "Resting2": lf_hf_data.get("Resting2", "")
                }
            
            if "SpO2" in table_data:
                spo2_data = table_data["SpO2"]
                autonomics_data["SpO2"] = {
                    "Resting": spo2_data.get("Resting", ""),
                    "Deep Breathing": "",
                    "Valsalva": "",
                    "Tilt Test": spo2_data.get("Tilt Test", ""),
                    "Resting2": spo2_data.get("Resting2", "")
                }
        
        # Process CARDIOVASCULAR data from OCR results
        for table_info in ocr_results:
            table_data = table_info.get("table", {})
            
            if isinstance(table_data, dict):
                for key, value in table_data.items():
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            key_lower = str(sub_key).lower()
                            value_lower = str(sub_value).lower()
                            
                            # Extract cardiovascular metrics from the table structure
                            if "eei" in key_lower:
                                cardiovascular_data["EEI"] = str(sub_value)
                            elif "ddi" in key_lower:
                                cardiovascular_data["DDI"] = str(sub_value)
                            elif "dei" in key_lower:
                                cardiovascular_data["DEI"] = str(sub_value)
                            elif "ai" in key_lower and "augmentation" in value_lower:
                                cardiovascular_data["AI"] = str(sub_value)
                            elif "reflection index" in value_lower:
                                cardiovascular_data["Reflection Index"] = str(sub_key)
                            elif "stiffness index" in value_lower:
                                cardiovascular_data["Stiffness Index"] = str(sub_key)
                            elif "cardiac output" in value_lower:
                                cardiovascular_data["Cardiac Output"] = str(sub_key)
                            elif "mean arterial pressure" in value_lower:
                                cardiovascular_data["Mean Arterial Pressure"] = str(sub_key)
                            elif "c1" in key_lower and ">" in str(sub_value):
                                cardiovascular_data["C1"] = str(sub_key)
                            elif "c2" in key_lower and ">" in str(sub_value):
                                cardiovascular_data["C2"] = str(sub_key)
                            elif "ventricular extrasystole" in value_lower:
                                cardiovascular_data["Ventricular Extrasystole"] = str(sub_key)
                            elif "atrial extrasystole" in value_lower:
                                cardiovascular_data["Atrial Extrasystole"] = str(sub_key)
                            elif "qrs" in key_lower and "ms" in str(sub_value):
                                cardiovascular_data["QRS"] = str(sub_key)
                            elif "qtc" in key_lower and "ms" in str(sub_value):
                                cardiovascular_data["QTc"] = str(sub_key)
                            elif "body mass index" in value_lower:
                                cardiovascular_data["Body Mass Index"] = str(sub_key)
                            elif "stroke volume" in value_lower:
                                cardiovascular_data["Stroke Volume"] = str(sub_key)
                            elif "blood volume" in value_lower:
                                cardiovascular_data["Blood Volume"] = str(sub_key)
                            elif "artifacts" in value_lower:
                                cardiovascular_data["Artifacts"] = str(sub_key)
                            elif "st seg" in value_lower:
                                cardiovascular_data["ST seg"] = str(sub_key)
        
        # Process ECG data from OCR results
        for table_info in ocr_results:
            table_data = table_info.get("table", {})
            page_num = table_info.get("page", 0)
            
            if isinstance(table_data, dict):
                for key, value in table_data.items():
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            key_lower = str(sub_key).lower()
                            value_lower = str(sub_value).lower()
                            
                            # Heart Rate data
                            if "average heart rate" in value_lower or "aerage heart rate" in value_lower:
                                ecg_data["Average Heart Rate"] = str(sub_key)
                            elif "fastest rate" in value_lower and "minutely" not in value_lower:
                                ecg_data["Fastest rate"] = str(sub_key)
                            elif "slowest rate" in value_lower and "minutely" not in value_lower:
                                ecg_data["Slowest rate"] = str(sub_key)
                            elif "fastest minutely rate" in value_lower:
                                ecg_data["Fastest minutely rate"] = str(sub_key)
                            elif "slowest minutely rate" in value_lower:
                                ecg_data["Slowest minutely rate"] = str(sub_key)
                            
                            # Ventricular data
                            elif "pvc" in value_lower or "ventricular ectopy" in value_lower:
                                ecg_data["PVC - Ventricular Ectopy"] = str(sub_key)
                            elif "ventricular couplet" in value_lower:
                                ecg_data["Ventricular Couplet"] = str(sub_key)
                            
                            # Supraventricular data
                            elif "pac" in value_lower or "supraventricular ectopy" in value_lower:
                                ecg_data["PAC - Supraventricular Ectopy"] = str(sub_key)
                            elif "supraventricular couplet" in value_lower:
                                ecg_data["Supraventricular Couplet"] = str(sub_key)
                            
                            # HRV data
                            elif "sdnn" in key_lower and "max" not in key_lower and "min" not in key_lower:
                                ecg_data["SDNN"] = str(sub_value)
                            elif "sdnn max" in value_lower:
                                ecg_data["SDNN Max"] = str(sub_key)
                            elif "sdnn min" in value_lower:
                                ecg_data["SDNN Min"] = str(sub_key)
                            
                            # QRS analysis
                            elif "qrs" in key_lower and "ms" in str(sub_value):
                                ecg_data["QRS"] = str(sub_value)
                            elif "qt" in key_lower and "/" in str(sub_value):
                                ecg_data["QT / QTc"] = str(sub_value)
                            elif "qtc max" in value_lower:
                                ecg_data["QTc Max"] = str(sub_key)
                            elif "pr int" in value_lower or "pr seg" in value_lower:
                                ecg_data["PR int / seg"] = str(sub_value)
                            elif "st int" in value_lower or "st seg" in value_lower:
                                ecg_data["ST int / seg"] = str(sub_value)
        
        # Format the output in the exact structure requested
        output_lines = []
        
        # AUTONOMICS section
        output_lines.append("AUTONOMICS")
        output_lines.append("")
        
        # HR subsection
        output_lines.append("HR")
        hr_data = autonomics_data.get("HR", {})
        output_lines.append(f"Resting: {hr_data.get('Resting', '')}")
        output_lines.append(f"Deep Breathing Max: {hr_data.get('Deep Breathing Max', '')}")
        output_lines.append(f"Deep Breathing Min: {hr_data.get('Deep Breathing Min', '')}")
        output_lines.append(f"Valsalva Max: {hr_data.get('Valsalva Max', '')}")
        output_lines.append(f"Valsalva Min: {hr_data.get('Valsalva Min', '')}")
        output_lines.append(f"Tilt Test: {hr_data.get('Tilt Test', '')}")
        output_lines.append(f"Resting2: {hr_data.get('Resting2', '')}")
        output_lines.append("")
        
        # BP subsection
        output_lines.append("BP")
        bp_data = autonomics_data.get("BP", {})
        output_lines.append(f"Resting Systolic: {bp_data.get('Resting Systolic', '')}")
        output_lines.append(f"Resting Diastolic: {bp_data.get('Resting Diastolic', '')}")
        output_lines.append(f"Deep Breathing Systolic: {bp_data.get('Deep Breathing Systolic', '')}")
        output_lines.append(f"Deep Breathing Diastolic: {bp_data.get('Deep Breathing Diastolic', '')}")
        output_lines.append(f"Valsalva Systolic: {bp_data.get('Valsalva Systolic', '')}")
        output_lines.append(f"Valsalva Diastolic: {bp_data.get('Valsalva Diastolic', '')}")
        output_lines.append(f"Tilt Test Systolic: {bp_data.get('Tilt Test Systolic', '')}")
        output_lines.append(f"Tilt Test Diastolic: {bp_data.get('Tilt Test Diastolic', '')}")
        output_lines.append(f"Resting2 Systolic: {bp_data.get('Resting2 Systolic', '')}")
        output_lines.append(f"Resting2 Diastolic: {bp_data.get('Resting2 Diastolic', '')}")
        output_lines.append("")
        
        # SNS subsection
        output_lines.append("SNS (Norm: 0.8–4.0)")
        sns_data = autonomics_data.get("SNS", {})
        output_lines.append(f"Resting: {sns_data.get('Resting', '')}")
        output_lines.append(f"Deep Breathing: {sns_data.get('Deep Breathing', '')}")
        output_lines.append(f"Valsalva: {sns_data.get('Valsalva', '')}")
        output_lines.append(f"Tilt Test: {sns_data.get('Tilt Test', '')}")
        output_lines.append(f"Resting2: {sns_data.get('Resting2', '')}")
        output_lines.append("")
        
        # PNS subsection
        output_lines.append("PNS (Norm: 0.8–4.0)")
        pns_data = autonomics_data.get("PNS", {})
        output_lines.append(f"Resting: {pns_data.get('Resting', '')}")
        output_lines.append(f"Deep Breathing: {pns_data.get('Deep Breathing', '')}")
        output_lines.append(f"Valsalva: {pns_data.get('Valsalva', '')}")
        output_lines.append(f"Tilt Test: {pns_data.get('Tilt Test', '')}")
        output_lines.append(f"Resting2: {pns_data.get('Resting2', '')}")
        output_lines.append("")
        
        # SNS/PNS Ratio subsection
        output_lines.append("SNS/PNS Ratio (Norm: 0.4–2.0)")
        sns_pns_data = autonomics_data.get("SNS/PNS Ratio", {})
        output_lines.append(f"Resting: {sns_pns_data.get('Resting', '')}")
        output_lines.append(f"Deep Breathing: {sns_pns_data.get('Deep Breathing', '')}")
        output_lines.append(f"Valsalva: {sns_pns_data.get('Valsalva', '')}")
        output_lines.append(f"Tilt Test: {sns_pns_data.get('Tilt Test', '')}")
        output_lines.append(f"Resting2: {sns_pns_data.get('Resting2', '')}")
        output_lines.append("")
        
        # LF/HF subsection
        output_lines.append("LF/HF (Norm: <3)")
        lf_hf_data = autonomics_data.get("LF/HF", {})
        output_lines.append(f"Resting: {lf_hf_data.get('Resting', '')}")
        output_lines.append(f"Deep Breathing: {lf_hf_data.get('Deep Breathing', '')}")
        output_lines.append(f"Valsalva: {lf_hf_data.get('Valsalva', '')}")
        output_lines.append(f"Tilt Test: {lf_hf_data.get('Tilt Test', '')}")
        output_lines.append(f"Resting2: {lf_hf_data.get('Resting2', '')}")
        output_lines.append("")
        
        # Other Metrics subsection
        output_lines.append("Other Metrics")
        other_metrics = [
            "Total Autonomic Activity (Norm: 45–80)",
            "Autonomic Balance (Norm: -3 to 3)",
            "E/I Ratio (Norm: >1.2)",
            "Valsalva Ratio (Norm: >1.2)",
            "K30/15 Ratio (Norm: >1.1)",
            "Autonomic Physical Dysregulation (PSI) (Norm: <1.0)",
            "Accumulative Mental Stress (MSI) (Norm: <1.0)"
        ]
        for metric in other_metrics:
            output_lines.append(f"{metric}: ")
        output_lines.append("")
        
        # SpO2 subsection
        output_lines.append("SpO2")
        spo2_data = autonomics_data.get("SpO2", {})
        output_lines.append(f"Resting: {spo2_data.get('Resting', '')}")
        output_lines.append(f"Deep Breathing: {spo2_data.get('Deep Breathing', '')}")
        output_lines.append(f"Valsalva: {spo2_data.get('Valsalva', '')}")
        output_lines.append(f"Tilt Test: {spo2_data.get('Tilt Test', '')}")
        output_lines.append(f"Resting2: {spo2_data.get('Resting2', '')}")
        output_lines.append("")
        
        # CARDIOVASCULAR section
        output_lines.append("CARDIOVASCULAR")
        output_lines.append("")
        
        cardiovascular_metrics = [
            "EEI (0.3–0.7)",
            "DDI (0.3–0.7)",
            "DEI (0.3–0.7)",
            "AI (< -0.4)",
            "Right Ankle/Brachial Index (1–1.4)",
            "Right Toe/Brachial Index (>0.75)",
            "Reflection Index (0.65–0.85)",
            "Stiffness Index (< 8.0 m/s)",
            "Cardiac Output (4.0–8.0 l/min)",
            "Mean Arterial Pressure (70–110 mmHg)",
            "C1 (> 10.0 ml/mmHg)",
            "C2 (> 6.0 ml/mmHg)",
            "Ventricular Extrasystole (< 1)",
            "Atrial Extrasystole (< 1)",
            "QRS (60–120 ms)",
            "QTc (350–460 ms)",
            "Body Mass Index (19–25)",
            "Stroke Volume (55–100 ml)",
            "Blood Volume (3–5 l)",
            "Artifacts (< 1)",
            "ST seg (80–120 ms)"
        ]
        
        for metric in cardiovascular_metrics:
            metric_name = metric.split(" (")[0]
            value = cardiovascular_data.get(metric_name, "")
            output_lines.append(f"{metric}: {value}")
        output_lines.append("")
        
        # ELECTROCARDIOGRAM section
        output_lines.append("ELECTROCARDIOGRAM")
        output_lines.append("")
        
        # Heart Rate subsection
        output_lines.append("Heart Rate:")
        heart_rate_metrics = [
            "Average Heart Rate",
            "Fastest rate",
            "Slowest rate",
            "Fastest minutely rate",
            "Slowest minutely rate"
        ]
        for metric in heart_rate_metrics:
            value = ecg_data.get(metric, "")
            output_lines.append(f"{metric}: {value}")
        output_lines.append("")
        
        # Ventricular Details subsection
        output_lines.append("Ventricular Details:")
        ventricular_metrics = [
            "PVC - Ventricular Ectopy",
            "Ventricular Couplet"
        ]
        for metric in ventricular_metrics:
            value = ecg_data.get(metric, "")
            output_lines.append(f"{metric}: {value}")
        output_lines.append("")
        
        # Supraventricular Details subsection
        output_lines.append("Supraventricular Details:")
        supraventricular_metrics = [
            "PAC - Supraventricular Ectopy",
            "Supraventricular Couplet"
        ]
        for metric in supraventricular_metrics:
            value = ecg_data.get(metric, "")
            output_lines.append(f"{metric}: {value}")
        output_lines.append("")
        
        # HRV Analysis subsection
        output_lines.append("HRV Analysis:")
        hrv_metrics = [
            "SDNN",
            "SDNN Max",
            "SDNN Min"
        ]
        for metric in hrv_metrics:
            value = ecg_data.get(metric, "")
            output_lines.append(f"{metric}: {value}")
        output_lines.append("")
        
        # QRS Analysis subsection
        output_lines.append("QRS Analysis:")
        qrs_metrics = [
            "QRS",
            "QT / QTc",
            "QTc Max",
            "PR int / seg",
            "ST int / seg"
        ]
        for metric in qrs_metrics:
            value = ecg_data.get(metric, "")
            output_lines.append(f"{metric}: {value}")
        
        return "\n".join(output_lines)

def main():
    """Main function to demonstrate usage."""
    # Initialize formatter
    formatter = ExactMedicalFormatter()
    
    # Load existing unified data
    try:
        with open('json_output/enhanced_extraction.json', 'r', encoding='utf-8') as f:
            unified_data = json.load(f)
        
        # Format to exact structure
        exact_output = formatter.format_to_exact_structure(unified_data)
        
        # Save exact output
        with open('json_output/exact_format_output.txt', 'w', encoding='utf-8') as f:
            f.write(exact_output)
        
        print("✅ Exact format output saved to json_output/exact_format_output.txt")
        print("\n" + "="*50)
        print("EXACT OUTPUT FORMAT:")
        print("="*50)
        print(exact_output)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
