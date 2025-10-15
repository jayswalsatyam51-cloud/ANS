#!/usr/bin/env python3
"""
Enhanced Simple Exact Formatter
Reads from existing enhanced extraction JSON and outputs in the exact format requested by the user.
Now includes comprehensive PDF search for missing data.
"""

import json
import os
import re
import fitz  # PyMuPDF
from typing import Dict, Any

class SimpleExactFormatter:
    """
    Enhanced formatter that outputs medical data in the exact format requested:
    AUTONOMICS, CARDIOVASCULAR, and ELECTROCARDIOGRAM sections with specific field names.
    Now includes comprehensive PDF search for missing data.
    """
    
    def __init__(self):
        """Initialize the enhanced simple exact formatter."""
        pass
    
    def search_pdf_for_missing_data(self, pdf_path: str, missing_fields: Dict[str, str]) -> Dict[str, str]:
        """Search PDF for missing data using text extraction."""
        if not os.path.exists(pdf_path):
            return missing_fields
        
        try:
            doc = fitz.open(pdf_path)
            full_text = ""
            
            # Extract text from all pages
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                full_text += page.get_text() + " "
            
            doc.close()
            
            # Search patterns for different types of data
            search_patterns = {
                # HR patterns
                "Resting": [r'resting.*?hr.*?(\d+)', r'hr.*?resting.*?(\d+)', r'resting.*?(\d+).*?bpm'],
                "Deep Breathing Max": [r'deep.*?breathing.*?max.*?(\d+)', r'breathing.*?max.*?(\d+)'],
                "Deep Breathing Min": [r'deep.*?breathing.*?min.*?(\d+)', r'breathing.*?min.*?(\d+)'],
                "Valsalva Max": [r'valsalva.*?max.*?(\d+)', r'valsal.*?max.*?(\d+)'],
                "Valsalva Min": [r'valsalva.*?min.*?(\d+)', r'valsal.*?min.*?(\d+)'],
                "Tilt Test": [r'tilt.*?test.*?(\d+)', r'tilt.*?(\d+)'],
                "Resting2": [r'resting.*?2.*?(\d+)', r'resting2.*?(\d+)'],
                
                # BP patterns
                "Resting Systolic": [r'resting.*?systolic.*?(\d+)', r'resting.*?bp.*?(\d+)/'],
                "Resting Diastolic": [r'resting.*?diastolic.*?(\d+)', r'resting.*?bp.*?/(\d+)'],
                "Deep Breathing Systolic": [r'deep.*?breathing.*?systolic.*?(\d+)', r'breathing.*?(\d+)/'],
                "Deep Breathing Diastolic": [r'deep.*?breathing.*?diastolic.*?(\d+)', r'breathing.*?/(\d+)'],
                "Valsalva Systolic": [r'valsalva.*?systolic.*?(\d+)', r'valsal.*?(\d+)/'],
                "Valsalva Diastolic": [r'valsalva.*?diastolic.*?(\d+)', r'valsal.*?/(\d+)'],
                "Tilt Test Systolic": [r'tilt.*?test.*?systolic.*?(\d+)', r'tilt.*?(\d+)/'],
                "Tilt Test Diastolic": [r'tilt.*?test.*?diastolic.*?(\d+)', r'tilt.*?/(\d+)'],
                "Resting2 Systolic": [r'resting.*?2.*?systolic.*?(\d+)', r'resting2.*?(\d+)/'],
                "Resting2 Diastolic": [r'resting.*?2.*?diastolic.*?(\d+)', r'resting2.*?/(\d+)'],
                
                # Autonomic metrics
                "SNS Resting": [r'sns.*?resting.*?(-?\d+\.?\d*)', r'resting.*?sns.*?(-?\d+\.?\d*)'],
                "SNS Deep Breathing": [r'sns.*?deep.*?breathing.*?(-?\d+\.?\d*)', r'deep.*?breathing.*?sns.*?(-?\d+\.?\d*)'],
                "SNS Valsalva": [r'sns.*?valsalva.*?(-?\d+\.?\d*)', r'valsalva.*?sns.*?(-?\d+\.?\d*)'],
                "SNS Tilt Test": [r'sns.*?tilt.*?(-?\d+\.?\d*)', r'tilt.*?sns.*?(-?\d+\.?\d*)'],
                "SNS Resting2": [r'sns.*?resting.*?2.*?(-?\d+\.?\d*)', r'resting.*?2.*?sns.*?(-?\d+\.?\d*)'],
                
                "PNS Resting": [r'pns.*?resting.*?(-?\d+\.?\d*)', r'resting.*?pns.*?(-?\d+\.?\d*)'],
                "PNS Deep Breathing": [r'pns.*?deep.*?breathing.*?(-?\d+\.?\d*)', r'deep.*?breathing.*?pns.*?(-?\d+\.?\d*)'],
                "PNS Valsalva": [r'pns.*?valsalva.*?(-?\d+\.?\d*)', r'valsalva.*?pns.*?(-?\d+\.?\d*)'],
                "PNS Tilt Test": [r'pns.*?tilt.*?(-?\d+\.?\d*)', r'tilt.*?pns.*?(-?\d+\.?\d*)'],
                "PNS Resting2": [r'pns.*?resting.*?2.*?(-?\d+\.?\d*)', r'resting.*?2.*?pns.*?(-?\d+\.?\d*)'],
                
                # Other metrics
                "Total Autonomic Activity": [r'total.*?autonomic.*?activity.*?(-?\d+\.?\d*)', r'autonomic.*?activity.*?(-?\d+\.?\d*)'],
                "Autonomic Balance": [r'autonomic.*?balance.*?(-?\d+\.?\d*)', r'balance.*?(-?\d+\.?\d*)'],
                "E/I Ratio": [r'e/i.*?ratio.*?(-?\d+\.?\d*)', r'ei.*?ratio.*?(-?\d+\.?\d*)'],
                "Valsalva Ratio": [r'valsalva.*?ratio.*?(-?\d+\.?\d*)', r'valsal.*?ratio.*?(-?\d+\.?\d*)'],
                "K30/15 Ratio": [r'k30/15.*?ratio.*?(-?\d+\.?\d*)', r'k30.*?15.*?ratio.*?(-?\d+\.?\d*)'],
                "PSI": [r'psi.*?(-?\d+\.?\d*)', r'physical.*?dysregulation.*?(-?\d+\.?\d*)'],
                "MSI": [r'msi.*?(-?\d+\.?\d*)', r'mental.*?stress.*?(-?\d+\.?\d*)'],
                
                # SpO2
                "SpO2 Resting": [r'spo2.*?resting.*?(\d+)', r'resting.*?spo2.*?(\d+)'],
                "SpO2 Deep Breathing": [r'spo2.*?deep.*?breathing.*?(\d+)', r'deep.*?breathing.*?spo2.*?(\d+)'],
                "SpO2 Valsalva": [r'spo2.*?valsalva.*?(\d+)', r'valsalva.*?spo2.*?(\d+)'],
                "SpO2 Tilt Test": [r'spo2.*?tilt.*?(\d+)', r'tilt.*?spo2.*?(\d+)'],
                "SpO2 Resting2": [r'spo2.*?resting.*?2.*?(\d+)', r'resting.*?2.*?spo2.*?(\d+)'],
                
                # Cardiovascular
                "EEI": [r'eei.*?(-?\d+\.?\d*)', r'elasticity.*?index.*?(-?\d+\.?\d*)'],
                "DDI": [r'ddi.*?(-?\d+\.?\d*)', r'distensibility.*?index.*?(-?\d+\.?\d*)'],
                "DEI": [r'dei.*?(-?\d+\.?\d*)', r'distensibility.*?elasticity.*?(-?\d+\.?\d*)'],
                "AI": [r'ai.*?(-?\d+\.?\d*)', r'augmentation.*?index.*?(-?\d+\.?\d*)'],
                "ABI": [r'abi.*?(-?\d+\.?\d*)', r'ankle.*?brachial.*?(-?\d+\.?\d*)'],
                "TBI": [r'tbi.*?(-?\d+\.?\d*)', r'toe.*?brachial.*?(-?\d+\.?\d*)'],
                "Reflection Index": [r'reflection.*?index.*?(-?\d+\.?\d*)'],
                "Stiffness Index": [r'stiffness.*?index.*?(-?\d+\.?\d*)'],
                "Cardiac Output": [r'cardiac.*?output.*?(-?\d+\.?\d*)'],
                "Mean Arterial Pressure": [r'mean.*?arterial.*?pressure.*?(-?\d+\.?\d*)'],
                "C1": [r'c1.*?(-?\d+\.?\d*)'],
                "C2": [r'c2.*?(-?\d+\.?\d*)'],
                "Ventricular Extrasystole": [r'ventricular.*?extrasystole.*?(-?\d+\.?\d*)'],
                "Atrial Extrasystole": [r'atrial.*?extrasystole.*?(-?\d+\.?\d*)'],
                "QRS": [r'qrs.*?(-?\d+\.?\d*)'],
                "QTc": [r'qtc.*?(-?\d+\.?\d*)'],
                "Body Mass Index": [r'bmi.*?(-?\d+\.?\d*)', r'body.*?mass.*?index.*?(-?\d+\.?\d*)'],
                "Stroke Volume": [r'stroke.*?volume.*?(-?\d+\.?\d*)'],
                "Blood Volume": [r'blood.*?volume.*?(-?\d+\.?\d*)'],
                "Artifacts": [r'artifacts.*?(-?\d+\.?\d*)'],
                "ST seg": [r'st.*?seg.*?(-?\d+\.?\d*)', r'st.*?segment.*?(-?\d+\.?\d*)'],
                
                # ECG
                "Average Heart Rate": [r'average.*?heart.*?rate.*?(\d+)', r'mean.*?heart.*?rate.*?(\d+)'],
                "Fastest rate": [r'fastest.*?rate.*?(\d+)', r'maximum.*?heart.*?rate.*?(\d+)'],
                "Slowest rate": [r'slowest.*?rate.*?(\d+)', r'minimum.*?heart.*?rate.*?(\d+)'],
                "Fastest minutely rate": [r'fastest.*?minutely.*?rate.*?(\d+)'],
                "Slowest minutely rate": [r'slowest.*?minutely.*?rate.*?(\d+)'],
                "PVC - Ventricular Ectopy": [r'pvc.*?(\d+)', r'ventricular.*?ectopy.*?(\d+)'],
                "Ventricular Couplet": [r'ventricular.*?couplet.*?(\d+)'],
                "PAC - Supraventricular Ectopy": [r'pac.*?(\d+)', r'supraventricular.*?ectopy.*?(\d+)'],
                "Supraventricular Couplet": [r'supraventricular.*?couplet.*?(\d+)'],
                "SDNN": [r'sdnn.*?(-?\d+\.?\d*)'],
                "SDNN Max": [r'sdnn.*?max.*?(-?\d+\.?\d*)'],
                "SDNN Min": [r'sdnn.*?min.*?(-?\d+\.?\d*)'],
                "QT / QTc": [r'qt.*?qtc.*?(-?\d+\.?\d*)', r'qt/qtc.*?(-?\d+\.?\d*)'],
                "QTc Max": [r'qtc.*?max.*?(-?\d+\.?\d*)'],
                "PR int / seg": [r'pr.*?int.*?(-?\d+\.?\d*)', r'pr.*?seg.*?(-?\d+\.?\d*)'],
                "ST int / seg": [r'st.*?int.*?(-?\d+\.?\d*)', r'st.*?seg.*?(-?\d+\.?\d*)']
            }
            
            # Search for missing values
            for field_name, patterns in search_patterns.items():
                if field_name in missing_fields and not missing_fields[field_name]:
                    for pattern in patterns:
                        matches = re.findall(pattern, full_text, re.IGNORECASE)
                        if matches:
                            # Extract numeric value
                            numeric_match = re.search(r'-?\d+\.?\d*', str(matches[0]))
                            if numeric_match:
                                missing_fields[field_name] = numeric_match.group()
                                break
            
        except Exception as e:
            print(f"Error searching PDF for missing data: {e}")
        
        return missing_fields
    
    def get_norm(self, metric_name: str) -> str:
        """Get norm string for a metric."""
        norms = {
            "SNS": "0.8–4.0",
            "PNS": "0.8–4.0", 
            "SNS/PNS": "0.4–2.0",
            "LF/HF": "<3",
            "SpO2": "≥95"
        }
        return norms.get(metric_name, "")
    
    def organize_data_by_sections(self, enhanced_data: Dict) -> Dict[str, Any]:
        """Organize enhanced data into proper sections, moving misplaced data to correct sections."""
        
        # Initialize organized data structure
        organized_data = {
            "AUTONOMICS": {
                "HR": {},
                "BP": {},
                "SNS": {},
                "PNS": {},
                "SNS_PNS_Ratio": {},
                "SpO2": {},
                "LF_HF": {},
                "Other_Metrics": {}
            },
            "CARDIOVASCULAR": {},
            "ELECTROCARDIOGRAM": {
                "Heart_Rate": {},
                "Ventricular_Details": {},
                "Supraventricular_Details": {},
                "HRV_Analysis": {},
                "QRS_Analysis": {}
            }
        }
        
        # Define which metrics belong to which sections
        cardiovascular_metrics = [
            "EEI", "DDI", "DEI", "AI", "Right Ankle/Brachial Index", "Right Toe/Brachial Index",
            "Reflection Index", "Stiffness Index", "Cardiac Output", "Mean Arterial Pressure",
            "C1", "C2", "Ventricular Extrasystole", "Atrial Extrasystole", "QRS", "QTc",
            "Body Mass Index", "Stroke Volume", "Blood Volume", "Artifacts", "ST seg"
        ]
        
        # Define autonomic metrics that should stay in AUTONOMICS
        autonomic_metrics = [
            "Total Autonomic Activity", "Autonomic Balance", "E/I Ratio", "Valsalva Ratio", 
            "K30/15 Ratio", "Functional Age", "Autonomic Physical Dysregulation (PSI)", 
            "Accumulative Mental Stress (MSI)"
        ]
        
        # Process enhanced data and organize it
        autonomics = enhanced_data.get("AUTONOMICS", {})
        cardiovascular = enhanced_data.get("CARDIOVASCULAR", {})
        ecg = enhanced_data.get("ELECTROCARDIOGRAM", {})
        
        # Organize AUTONOMICS data
        for subsection_name, subsection_data in autonomics.items():
            if subsection_name in organized_data["AUTONOMICS"]:
                organized_data["AUTONOMICS"][subsection_name] = subsection_data
        
        # Organize CARDIOVASCULAR data
        organized_data["CARDIOVASCULAR"].update(cardiovascular)
        
        # Organize ELECTROCARDIOGRAM data
        for subsection_name, subsection_data in ecg.items():
            if subsection_name in organized_data["ELECTROCARDIOGRAM"]:
                organized_data["ELECTROCARDIOGRAM"][subsection_name] = subsection_data
        
        # Move any misplaced cardiovascular metrics to CARDIOVASCULAR section
        # and ensure autonomic metrics stay in AUTONOMICS
        for section_name, section_data in enhanced_data.items():
            if isinstance(section_data, dict):
                for metric_name, metric_value in section_data.items():
                    # Move cardiovascular metrics to CARDIOVASCULAR section
                    if metric_name in cardiovascular_metrics and metric_name not in organized_data["CARDIOVASCULAR"]:
                        organized_data["CARDIOVASCULAR"][metric_name] = metric_value
                    # Ensure autonomic metrics stay in AUTONOMICS Other_Metrics
                    elif metric_name in autonomic_metrics and metric_name not in organized_data["AUTONOMICS"]["Other_Metrics"]:
                        organized_data["AUTONOMICS"]["Other_Metrics"][metric_name] = metric_value
        
        return organized_data
    
    def format_to_exact_structure(self, enhanced_data: Dict, pdf_path: str = None) -> str:
        """Convert enhanced data to the exact format requested by the user."""
        
        # First organize the data properly
        organized_data = self.organize_data_by_sections(enhanced_data)
        
        # Extract sections from organized data
        autonomics = organized_data.get("AUTONOMICS", {})
        cardiovascular = organized_data.get("CARDIOVASCULAR", {})
        ecg = organized_data.get("ELECTROCARDIOGRAM", {})
        
        # Collect all missing fields for PDF search
        missing_fields = {}
        
        # Check HR data
        hr_data = autonomics.get("HR", {})
        for field in ["Resting", "Deep Breathing Max", "Deep Breathing Min", "Valsalva Max", "Valsalva Min", "Tilt Test", "Resting2"]:
            if not hr_data.get(field, ""):
                missing_fields[field] = ""
        
        # Check BP data
        bp_data = autonomics.get("BP", {})
        for field in ["Resting Systolic", "Resting Diastolic", "Deep Breathing Systolic", "Deep Breathing Diastolic", 
                     "Valsalva Systolic", "Valsalva Diastolic", "Tilt Test Systolic", "Tilt Test Diastolic", 
                     "Resting2 Systolic", "Resting2 Diastolic"]:
            if not bp_data.get(field, ""):
                missing_fields[field] = ""
        
        # Check autonomic metrics
        for metric in ["SNS", "PNS", "SNS/PNS", "LF/HF", "SpO2"]:
            metric_data = autonomics.get(f"{metric} (Norm: {self.get_norm(metric)})", {})
            for test in ["Resting", "Deep Breathing", "Valsalva", "Tilt Test", "Resting2"]:
                if not metric_data.get(test, ""):
                    missing_fields[f"{metric} {test}"] = ""
        
        # Check other metrics
        other_metrics = autonomics.get("Other Metrics", {})
        for field in ["Total Autonomic Activity", "Autonomic Balance", "E/I Ratio", "Valsalva Ratio", 
                     "K30/15 Ratio", "PSI", "MSI"]:
            if not other_metrics.get(field, ""):
                missing_fields[field] = ""
        
        # Check cardiovascular metrics
        cv_fields = ["EEI", "DDI", "DEI", "AI", "ABI", "TBI", "Reflection Index", "Stiffness Index", 
                    "Cardiac Output", "Mean Arterial Pressure", "C1", "C2", "Ventricular Extrasystole", 
                    "Atrial Extrasystole", "QRS", "QTc", "Body Mass Index", "Stroke Volume", 
                    "Blood Volume", "Artifacts", "ST seg"]
        for field in cv_fields:
            if not cardiovascular.get(field, ""):
                missing_fields[field] = ""
        
        # Check ECG data
        for section_name, section_data in ecg.items():
            if isinstance(section_data, dict):
                for field in section_data.keys():
                    if not section_data.get(field, ""):
                        missing_fields[field] = ""
        
        # Search PDF for missing data if PDF path is provided
        if pdf_path and missing_fields:
            print(f"Searching PDF for {len(missing_fields)} missing fields...")
            missing_fields = self.search_pdf_for_missing_data(pdf_path, missing_fields)
            
            # Update the data structures with found values
            # Update HR data
            for field in ["Resting", "Deep Breathing Max", "Deep Breathing Min", "Valsalva Max", "Valsalva Min", "Tilt Test", "Resting2"]:
                if field in missing_fields and missing_fields[field]:
                    if "HR" not in autonomics:
                        autonomics["HR"] = {}
                    autonomics["HR"][field] = missing_fields[field]
            
            # Update BP data
            for field in ["Resting Systolic", "Resting Diastolic", "Deep Breathing Systolic", "Deep Breathing Diastolic", 
                         "Valsalva Systolic", "Valsalva Diastolic", "Tilt Test Systolic", "Tilt Test Diastolic", 
                         "Resting2 Systolic", "Resting2 Diastolic"]:
                if field in missing_fields and missing_fields[field]:
                    if "BP" not in autonomics:
                        autonomics["BP"] = {}
                    autonomics["BP"][field] = missing_fields[field]
            
            # Update other metrics
            for field in ["Total Autonomic Activity", "Autonomic Balance", "E/I Ratio", "Valsalva Ratio", 
                         "K30/15 Ratio", "PSI", "MSI"]:
                if field in missing_fields and missing_fields[field]:
                    if "Other Metrics" not in autonomics:
                        autonomics["Other Metrics"] = {}
                    autonomics["Other Metrics"][field] = missing_fields[field]
            
            # Update cardiovascular metrics
            for field in cv_fields:
                if field in missing_fields and missing_fields[field]:
                    cardiovascular[field] = missing_fields[field]
            
            # Update ECG data
            for field_name, field_value in missing_fields.items():
                if field_value and field_name in ["Average Heart Rate", "Fastest rate", "Slowest rate", 
                                                 "Fastest minutely rate", "Slowest minutely rate"]:
                    if "Heart Rate" not in ecg:
                        ecg["Heart Rate"] = {}
                    ecg["Heart Rate"][field_name] = field_value
                elif field_value and field_name in ["PVC - Ventricular Ectopy", "Ventricular Couplet"]:
                    if "Ventricular Details" not in ecg:
                        ecg["Ventricular Details"] = {}
                    ecg["Ventricular Details"][field_name] = field_value
                elif field_value and field_name in ["PAC - Supraventricular Ectopy", "Supraventricular Couplet"]:
                    if "Supraventricular Details" not in ecg:
                        ecg["Supraventricular Details"] = {}
                    ecg["Supraventricular Details"][field_name] = field_value
                elif field_value and field_name in ["SDNN", "SDNN Max", "SDNN Min"]:
                    if "HRV Analysis" not in ecg:
                        ecg["HRV Analysis"] = {}
                    ecg["HRV Analysis"][field_name] = field_value
                elif field_value and field_name in ["QRS", "QT / QTc", "QTc Max", "PR int / seg", "ST int / seg"]:
                    if "QRS Analysis" not in ecg:
                        ecg["QRS Analysis"] = {}
                    ecg["QRS Analysis"][field_name] = field_value
        
        # Format the output in the exact structure requested
        output_lines = []
        
        # AUTONOMICS section
        output_lines.append("AUTONOMICS")
        output_lines.append("")
        
        # HR subsection
        output_lines.append("HR")
        hr_data = autonomics.get("HR", {})
        output_lines.append(f"Resting: {hr_data.get('Resting', '')}")
        output_lines.append(f"Deep Breathing Max: ")
        output_lines.append(f"Deep Breathing Min: ")
        output_lines.append(f"Valsalva Max: ")
        output_lines.append(f"Valsalva Min: ")
        output_lines.append(f"Tilt Test: {hr_data.get('Tilt Test', '')}")
        output_lines.append(f"Resting2: {hr_data.get('Resting2', '')}")
        output_lines.append("")
        
        # BP subsection
        output_lines.append("BP")
        bp_data = autonomics.get("BP", {})
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
        sns_data = autonomics.get("SNS (Norm: 0.8–4.0)", {})
        output_lines.append(f"Resting: {sns_data.get('Resting', '')}")
        output_lines.append(f"Deep Breathing: ")
        output_lines.append(f"Valsalva: ")
        output_lines.append(f"Tilt Test: {sns_data.get('Tilt Test', '')}")
        output_lines.append(f"Resting2: {sns_data.get('Resting2', '')}")
        output_lines.append("")
        
        # PNS subsection
        output_lines.append("PNS (Norm: 0.8–4.0)")
        pns_data = autonomics.get("PNS (Norm: 0.8–4.0)", {})
        output_lines.append(f"Resting: {pns_data.get('Resting', '')}")
        output_lines.append(f"Deep Breathing: ")
        output_lines.append(f"Valsalva: ")
        output_lines.append(f"Tilt Test: {pns_data.get('Tilt Test', '')}")
        output_lines.append(f"Resting2: {pns_data.get('Resting2', '')}")
        output_lines.append("")
        
        # SNS/PNS Ratio subsection
        output_lines.append("SNS/PNS Ratio (Norm: 0.4–2.0)")
        sns_pns_data = autonomics.get("SNS/PNS (Norm: 0.4–2.0)", {})
        output_lines.append(f"Resting: {sns_pns_data.get('Resting', '')}")
        output_lines.append(f"Deep Breathing: ")
        output_lines.append(f"Valsalva: ")
        output_lines.append(f"Tilt Test: {sns_pns_data.get('Tilt Test', '')}")
        output_lines.append(f"Resting2: {sns_pns_data.get('Resting2', '')}")
        output_lines.append("")
        
        # LF/HF subsection
        output_lines.append("LF/HF (Norm: <3)")
        lf_hf_data = autonomics.get("LF/HF (Norm: <3)", {})
        resting_value = lf_hf_data.get('Resting', '')
        if " | FLAG" in str(resting_value):
            resting_value = str(resting_value).replace(" | FLAG", "")
        tilt_value = lf_hf_data.get('Tilt Test', '')
        if " | FLAG" in str(tilt_value):
            tilt_value = str(tilt_value).replace(" | FLAG", "")
        resting2_value = lf_hf_data.get('Resting2', '')
        if " | FLAG" in str(resting2_value):
            resting2_value = str(resting2_value).replace(" | FLAG", "")
        output_lines.append(f"Resting: {resting_value}")
        output_lines.append(f"Deep Breathing: ")
        output_lines.append(f"Valsalva: ")
        output_lines.append(f"Tilt Test: {tilt_value}")
        output_lines.append(f"Resting2: {resting2_value}")
        output_lines.append("")
        
        # Other Metrics subsection
        output_lines.append("Other Metrics")
        other_metrics = autonomics.get("Other Metrics", {})
        
        # Extract values from the other metrics, handling different key formats
        total_activity = other_metrics.get('Total Autonomic Activity (Norm: 45–80)', '') or other_metrics.get('Total_Autonomic_Activity', '')
        autonomic_balance = other_metrics.get('Autonomic Balance (Norm: -3 to 3)', '') or other_metrics.get('Autonomic_Balance', '')
        ei_ratio = other_metrics.get('E/I Ratio (Norm: >1.2)', '') or other_metrics.get('E/I_Ratio', '')
        valsalva_ratio = other_metrics.get('Valsalva Ratio (Norm: >1.2)', '') or other_metrics.get('Valsalva_Ratio', '')
        k30_15_ratio = other_metrics.get('K30/15 Ratio (Norm: >1.1)', '') or other_metrics.get('K30/15_Ratio', '')
        psi = other_metrics.get('Autonomic Physical Dysregulation (PSI) (Norm: <1.0)', '') or other_metrics.get('PSI', '') or other_metrics.get('PSI (< 1.0)', '')
        msi = other_metrics.get('Accumulative Mental Stress (MSI) (Norm: <1.0)', '') or other_metrics.get('MSI', '') or other_metrics.get('MSI (< 1.0)', '')
        
        # Also check for EEI and DDI in Other Metrics
        eei_value = other_metrics.get('EEI (0.3 - 0.7)', '') or other_metrics.get('EEI', '')
        ddi_value = other_metrics.get('DDI (0.3 - 0.7)', '') or other_metrics.get('DDI', '')
        
        output_lines.append(f"Total Autonomic Activity (Norm: 45–80): {total_activity}")
        output_lines.append(f"Autonomic Balance (Norm: -3 to 3): {autonomic_balance}")
        output_lines.append(f"E/I Ratio (Norm: >1.2): {ei_ratio}")
        output_lines.append(f"Valsalva Ratio (Norm: >1.2): {valsalva_ratio}")
        output_lines.append(f"K30/15 Ratio (Norm: >1.1): {k30_15_ratio}")
        output_lines.append(f"Autonomic Physical Dysregulation (PSI) (Norm: <1.0): {psi}")
        output_lines.append(f"Accumulative Mental Stress (MSI) (Norm: <1.0): {msi}")
        output_lines.append("")
        
        # SpO2 subsection
        output_lines.append("SpO2")
        spo2_data = autonomics.get("SpO2 (Norm: ≥95)", {})
        resting_spo2 = spo2_data.get('Resting', '')
        if " %" in str(resting_spo2):
            resting_spo2 = str(resting_spo2).replace(" %", "")
        tilt_spo2 = spo2_data.get('Tilt Test', '')
        if " %" in str(tilt_spo2):
            tilt_spo2 = str(tilt_spo2).replace(" %", "")
        resting2_spo2 = spo2_data.get('Resting2', '')
        if " %" in str(resting2_spo2):
            resting2_spo2 = str(resting2_spo2).replace(" %", "")
        output_lines.append(f"Resting: {resting_spo2}")
        output_lines.append(f"Deep Breathing: ")
        output_lines.append(f"Valsalva: ")
        output_lines.append(f"Tilt Test: {tilt_spo2}")
        output_lines.append(f"Resting2: {resting2_spo2}")
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
            # Extract value from cardiovascular data, removing any flag text
            value = cardiovascular.get(metric, "")
            if " | FLAG" in str(value):
                value = str(value).replace(" | FLAG", "")
            # Also try alternative key formats
            if not value:
                metric_name = metric.split(" (")[0]
                value = cardiovascular.get(metric_name, "")
                if " | FLAG" in str(value):
                    value = str(value).replace(" | FLAG", "")
            
            # Special handling for specific metrics
            if metric == "EEI (0.3–0.7)" and not value:
                value = eei_value
            elif metric == "DDI (0.3–0.7)" and not value:
                value = ddi_value
            
            # Map specific cardiovascular metrics to their exact keys
            if metric == "DEI (0.3–0.7)" and not value:
                value = cardiovascular.get("DEI (Norm: 0.3–0.7)", "")
                if " | FLAG" in str(value):
                    value = str(value).replace(" | FLAG", "")
            elif metric == "AI (< -0.4)" and not value:
                value = cardiovascular.get("AI (Norm: < -0.4)", "")
                if " | FLAG" in str(value):
                    value = str(value).replace(" | FLAG", "")
            elif metric == "Reflection Index (0.65–0.85)" and not value:
                value = cardiovascular.get("Reflection Index (Norm: 0.65–0.85)", "")
                if " | FLAG" in str(value):
                    value = str(value).replace(" | FLAG", "")
            elif metric == "Stiffness Index (< 8.0 m/s)" and not value:
                value = cardiovascular.get("Stiffness Index (Norm: < 8.0)", "")
                if " | FLAG" in str(value):
                    value = str(value).replace(" | FLAG", "")
            elif metric == "Cardiac Output (4.0–8.0 l/min)" and not value:
                value = cardiovascular.get("Cardiac Output (Norm: 4.0–8.0)", "")
                if " | FLAG" in str(value):
                    value = str(value).replace(" | FLAG", "")
            elif metric == "Mean Arterial Pressure (70–110 mmHg)" and not value:
                value = cardiovascular.get("Mean Arterial Pressure (Norm: 70–110)", "")
                if " | FLAG" in str(value):
                    value = str(value).replace(" | FLAG", "")
            elif metric == "C1 (> 10.0 ml/mmHg)" and not value:
                value = cardiovascular.get("C1 (Norm: > 10.0)", "")
                if " | FLAG" in str(value):
                    value = str(value).replace(" | FLAG", "")
            elif metric == "C2 (> 6.0 ml/mmHg)" and not value:
                value = cardiovascular.get("C2 (Norm: > 6.0)", "")
                if " | FLAG" in str(value):
                    value = str(value).replace(" | FLAG", "")
            elif metric == "Ventricular Extrasystole (< 1)" and not value:
                value = cardiovascular.get("Ventricular Extrasystole (Norm: < 1)", "")
                if " | FLAG" in str(value):
                    value = str(value).replace(" | FLAG", "")
            elif metric == "Atrial Extrasystole (< 1)" and not value:
                value = cardiovascular.get("Atrial Extrasystole (Norm: < 1)", "")
                if " | FLAG" in str(value):
                    value = str(value).replace(" | FLAG", "")
            elif metric == "QRS (60–120 ms)" and not value:
                value = cardiovascular.get("QRS (Norm: 60–120)", "")
                if " | FLAG" in str(value):
                    value = str(value).replace(" | FLAG", "")
            elif metric == "QTc (350–460 ms)" and not value:
                value = cardiovascular.get("QTc (Norm: 350–460)", "")
                if " | FLAG" in str(value):
                    value = str(value).replace(" | FLAG", "")
            elif metric == "Body Mass Index (19–25)" and not value:
                value = cardiovascular.get("Body Mass Index (Norm: 19–25)", "")
                if " | FLAG" in str(value):
                    value = str(value).replace(" | FLAG", "")
            elif metric == "Stroke Volume (55–100 ml)" and not value:
                value = cardiovascular.get("Stroke Volume (Norm: 55–100)", "")
                if " | FLAG" in str(value):
                    value = str(value).replace(" | FLAG", "")
            elif metric == "Blood Volume (3–5 l)" and not value:
                value = cardiovascular.get("Blood Volume (Norm: 3–5)", "")
                if " | FLAG" in str(value):
                    value = str(value).replace(" | FLAG", "")
            elif metric == "Artifacts (< 1)" and not value:
                value = cardiovascular.get("Artifacts (Norm: < 1)", "")
                if " | FLAG" in str(value):
                    value = str(value).replace(" | FLAG", "")
            elif metric == "ST seg (80–120 ms)" and not value:
                value = cardiovascular.get("ST seg (Norm: 80–120)", "")
                if " | FLAG" in str(value):
                    value = str(value).replace(" | FLAG", "")
            
            output_lines.append(f"{metric}: {value}")
        output_lines.append("")
        
        # ELECTROCARDIOGRAM section
        output_lines.append("ELECTROCARDIOGRAM")
        output_lines.append("")
        
        # Heart Rate subsection
        output_lines.append("Heart Rate:")
        heart_rate_data = ecg.get("Heart Rate", {})
        heart_rate_metrics = [
            "Average Heart Rate",
            "Fastest rate",
            "Slowest rate",
            "Fastest minutely rate",
            "Slowest minutely rate"
        ]
        for metric in heart_rate_metrics:
            value = heart_rate_data.get(metric, "")
            output_lines.append(f"{metric}: {value}")
        output_lines.append("")
        
        # Ventricular Details subsection
        output_lines.append("Ventricular Details:")
        ventricular_data = ecg.get("Ventricular Details", {})
        ventricular_metrics = [
            "PVC - Ventricular Ectopy",
            "Ventricular Couplet"
        ]
        for metric in ventricular_metrics:
            value = ventricular_data.get(metric, "")
            output_lines.append(f"{metric}: {value}")
        output_lines.append("")
        
        # Supraventricular Details subsection
        output_lines.append("Supraventricular Details:")
        supraventricular_data = ecg.get("Supraventricular Details", {})
        supraventricular_metrics = [
            "PAC - Supraventricular Ectopy",
            "Supraventricular Couplet"
        ]
        for metric in supraventricular_metrics:
            value = supraventricular_data.get(metric, "")
            output_lines.append(f"{metric}: {value}")
        output_lines.append("")
        
        # HRV Analysis subsection
        output_lines.append("HRV Analysis:")
        hrv_data = ecg.get("HRV Analysis", {})
        hrv_metrics = [
            "SDNN",
            "SDNN Max",
            "SDNN Min"
        ]
        for metric in hrv_metrics:
            value = hrv_data.get(metric, "")
            output_lines.append(f"{metric}: {value}")
        output_lines.append("")
        
        # QRS Analysis subsection
        output_lines.append("QRS Analysis:")
        qrs_data = ecg.get("QRS Analysis", {})
        qrs_metrics = [
            "QRS",
            "QT / QTc",
            "QTc Max",
            "PR int / seg",
            "ST int / seg"
        ]
        for metric in qrs_metrics:
            value = qrs_data.get(metric, "")
            if " | FLAG" in str(value):
                value = str(value).replace(" | FLAG", "")
            output_lines.append(f"{metric}: {value}")
        
        return "\n".join(output_lines)

def main():
    """Main function to demonstrate usage."""
    # Initialize formatter
    formatter = SimpleExactFormatter()
    
    # Load existing enhanced data
    try:
        with open('json_output/enhanced_extraction.json', 'r', encoding='utf-8') as f:
            enhanced_data = json.load(f)
        
        # Format to exact structure
        exact_output = formatter.format_to_exact_structure(enhanced_data)
        
        # Save exact output
        with open('json_output/simple_exact_format_output.txt', 'w', encoding='utf-8') as f:
            f.write(exact_output)
        
        print("✅ Simple exact format output saved to json_output/simple_exact_format_output.txt")
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
