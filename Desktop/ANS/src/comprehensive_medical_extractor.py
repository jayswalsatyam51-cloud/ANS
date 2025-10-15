#!/usr/bin/env python3
"""
Comprehensive Medical Data Extractor
Searches through entire PDF to extract all required medical data in exact format
"""

import json
import re
import os
from typing import Dict, List, Any, Optional
import fitz  # PyMuPDF

class ComprehensiveMedicalExtractor:
    """
    Comprehensive extractor that searches through entire PDF to find all required medical data
    and outputs in the exact format requested by the user.
    """
    
    def __init__(self):
        """Initialize the comprehensive extractor."""
        self.required_fields = {
            "AUTONOMICS": {
                "HR": {
                    "Resting": "",
                    "Deep Breathing Max": "",
                    "Deep Breathing Min": "",
                    "Valsalva Max": "",
                    "Valsalva Min": "",
                    "Tilt Test": "",
                    "Resting2": ""
                },
                "BP": {
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
                },
                "SNS": {
                    "Resting": "",
                    "Deep Breathing": "",
                    "Valsalva": "",
                    "Tilt Test": "",
                    "Resting2": ""
                },
                "PNS": {
                    "Resting": "",
                    "Deep Breathing": "",
                    "Valsalva": "",
                    "Tilt Test": "",
                    "Resting2": ""
                },
                "SNS_PNS_Ratio": {
                    "Resting": "",
                    "Deep Breathing": "",
                    "Valsalva": "",
                    "Tilt Test": "",
                    "Resting2": ""
                },
                "LF_HF": {
                    "Resting": "",
                    "Deep Breathing": "",
                    "Valsalva": "",
                    "Tilt Test": "",
                    "Resting2": ""
                },
                "Other_Metrics": {
                    "Total Autonomic Activity": "",
                    "Autonomic Balance": "",
                    "E/I Ratio": "",
                    "Valsalva Ratio": "",
                    "K30/15 Ratio": "",
                    "Autonomic Physical Dysregulation (PSI)": "",
                    "Accumulative Mental Stress (MSI)": ""
                },
                "SpO2": {
                    "Resting": "",
                    "Deep Breathing": "",
                    "Valsalva": "",
                    "Tilt Test": "",
                    "Resting2": ""
                }
            },
            "CARDIOVASCULAR": {
                "EEI": "",
                "DDI": "",
                "DEI": "",
                "AI": "",
                "Right Ankle/Brachial Index": "",
                "Right Toe/Brachial Index": "",
                "Reflection Index": "",
                "Stiffness Index": "",
                "Cardiac Output": "",
                "Mean Arterial Pressure": "",
                "C1": "",
                "C2": "",
                "Ventricular Extrasystole": "",
                "Atrial Extrasystole": "",
                "QRS": "",
                "QTc": "",
                "Body Mass Index": "",
                "Stroke Volume": "",
                "Blood Volume": "",
                "Artifacts": "",
                "ST seg": ""
            },
            "ELECTROCARDIOGRAM": {
                "Heart_Rate": {
                    "Average Heart Rate": "",
                    "Fastest rate": "",
                    "Slowest rate": "",
                    "Fastest minutely rate": "",
                    "Slowest minutely rate": ""
                },
                "Ventricular_Details": {
                    "PVC - Ventricular Ectopy": "",
                    "Ventricular Couplet": ""
                },
                "Supraventricular_Details": {
                    "PAC - Supraventricular Ectopy": "",
                    "Supraventricular Couplet": ""
                },
                "HRV_Analysis": {
                    "SDNN": "",
                    "SDNN Max": "",
                    "SDNN Min": ""
                },
                "QRS_Analysis": {
                    "QRS": "",
                    "QT / QTc": "",
                    "QTc Max": "",
                    "PR int / seg": "",
                    "ST int / seg": ""
                }
            }
        }
        
        # Define norms for flagging
        self.norms = {
            "SNS": "0.8–4.0",
            "PNS": "0.8–4.0", 
            "SNS/PNS": "0.4–2.0",
            "LF/HF": "<3",
            "SpO2": "≥95",
            "Total Autonomic Activity": "45–80",
            "Autonomic Balance": "-3 to 3",
            "E/I Ratio": ">1.2",
            "Valsalva Ratio": ">1.2",
            "K30/15 Ratio": ">1.1",
            "PSI": "<1.0",
            "MSI": "<1.0",
            "EEI": "0.3–0.7",
            "DDI": "0.3–0.7",
            "DEI": "0.3–0.7",
            "AI": "< -0.4",
            "ABI": "1–1.4",
            "TBI": ">0.75",
            "Reflection Index": "0.65–0.85",
            "Stiffness Index": "< 8.0",
            "Cardiac Output": "4.0–8.0",
            "Mean Arterial Pressure": "70–110",
            "C1": "> 10.0",
            "C2": "> 6.0",
            "Ventricular Extrasystole": "< 1",
            "Atrial Extrasystole": "< 1",
            "QRS": "60–120",
            "QTc": "350–460",
            "Body Mass Index": "19–25",
            "Stroke Volume": "55–100",
            "Blood Volume": "3–5",
            "Artifacts": "< 1",
            "ST seg": "80–120",
            "Average Heart Rate": "60–100",
            "SDNN": "20–50"
        }
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[str]:
        """Extract text from all pages of PDF."""
        try:
            doc = fitz.open(pdf_path)
            pages_text = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                pages_text.append(text)
            
            doc.close()
            return pages_text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return []
    
    def search_for_value_in_text(self, text: str, patterns: List[str]) -> str:
        """Search for a value using multiple patterns in text."""
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Return the first match, cleaned up
                value = matches[0]
                # Extract numeric value if it's a complex string
                numeric_match = re.search(r'-?\d+\.?\d*', str(value))
                if numeric_match:
                    return numeric_match.group()
                return str(value).strip()
        return ""
    
    def extract_hr_data(self, pages_text: List[str]) -> Dict[str, str]:
        """Extract HR data from PDF text."""
        hr_data = {}
        
        # Combine all pages text
        full_text = " ".join(pages_text)
        
        # Patterns for different HR measurements
        hr_patterns = {
            "Resting": [
                r'resting.*?hr.*?(\d+)',
                r'hr.*?resting.*?(\d+)',
                r'resting.*?(\d+).*?bpm',
                r'resting.*?(\d+).*?hr'
            ],
            "Deep Breathing Max": [
                r'deep.*?breathing.*?max.*?(\d+)',
                r'deep.*?breathing.*?(\d+).*?max',
                r'breathing.*?max.*?(\d+)'
            ],
            "Deep Breathing Min": [
                r'deep.*?breathing.*?min.*?(\d+)',
                r'deep.*?breathing.*?(\d+).*?min',
                r'breathing.*?min.*?(\d+)'
            ],
            "Valsalva Max": [
                r'valsalva.*?max.*?(\d+)',
                r'valsalva.*?(\d+).*?max',
                r'valsal.*?max.*?(\d+)'
            ],
            "Valsalva Min": [
                r'valsalva.*?min.*?(\d+)',
                r'valsalva.*?(\d+).*?min',
                r'valsal.*?min.*?(\d+)'
            ],
            "Tilt Test": [
                r'tilt.*?test.*?(\d+)',
                r'tilt.*?(\d+)',
                r'tilt.*?test.*?hr.*?(\d+)'
            ],
            "Resting2": [
                r'resting.*?2.*?(\d+)',
                r'resting2.*?(\d+)',
                r'resting.*?second.*?(\d+)'
            ]
        }
        
        for metric, patterns in hr_patterns.items():
            hr_data[metric] = self.search_for_value_in_text(full_text, patterns)
        
        return hr_data
    
    def extract_bp_data(self, pages_text: List[str]) -> Dict[str, str]:
        """Extract BP data from PDF text."""
        bp_data = {}
        
        # Combine all pages text
        full_text = " ".join(pages_text)
        
        # Patterns for BP measurements
        bp_patterns = {
            "Resting Systolic": [
                r'resting.*?systolic.*?(\d+)',
                r'resting.*?bp.*?(\d+)/',
                r'resting.*?(\d+)/\d+'
            ],
            "Resting Diastolic": [
                r'resting.*?diastolic.*?(\d+)',
                r'resting.*?bp.*?/(\d+)',
                r'resting.*?\d+/(\d+)'
            ],
            "Deep Breathing Systolic": [
                r'deep.*?breathing.*?systolic.*?(\d+)',
                r'deep.*?breathing.*?bp.*?(\d+)/',
                r'breathing.*?(\d+)/\d+'
            ],
            "Deep Breathing Diastolic": [
                r'deep.*?breathing.*?diastolic.*?(\d+)',
                r'deep.*?breathing.*?bp.*?/(\d+)',
                r'breathing.*?\d+/(\d+)'
            ],
            "Valsalva Systolic": [
                r'valsalva.*?systolic.*?(\d+)',
                r'valsalva.*?bp.*?(\d+)/',
                r'valsal.*?(\d+)/\d+'
            ],
            "Valsalva Diastolic": [
                r'valsalva.*?diastolic.*?(\d+)',
                r'valsalva.*?bp.*?/(\d+)',
                r'valsal.*?\d+/(\d+)'
            ],
            "Tilt Test Systolic": [
                r'tilt.*?test.*?systolic.*?(\d+)',
                r'tilt.*?test.*?bp.*?(\d+)/',
                r'tilt.*?(\d+)/\d+'
            ],
            "Tilt Test Diastolic": [
                r'tilt.*?test.*?diastolic.*?(\d+)',
                r'tilt.*?test.*?bp.*?/(\d+)',
                r'tilt.*?\d+/(\d+)'
            ],
            "Resting2 Systolic": [
                r'resting.*?2.*?systolic.*?(\d+)',
                r'resting2.*?bp.*?(\d+)/',
                r'resting.*?2.*?(\d+)/\d+'
            ],
            "Resting2 Diastolic": [
                r'resting.*?2.*?diastolic.*?(\d+)',
                r'resting2.*?bp.*?/(\d+)',
                r'resting.*?2.*?\d+/(\d+)'
            ]
        }
        
        for metric, patterns in bp_patterns.items():
            bp_data[metric] = self.search_for_value_in_text(full_text, patterns)
        
        return bp_data
    
    def extract_autonomic_metrics(self, pages_text: List[str]) -> Dict[str, Dict[str, str]]:
        """Extract autonomic metrics (SNS, PNS, etc.) from PDF text."""
        autonomic_data = {}
        
        # Combine all pages text
        full_text = " ".join(pages_text)
        
        # Patterns for autonomic metrics
        metric_patterns = {
            "SNS": {
                "Resting": [r'sns.*?resting.*?(-?\d+\.?\d*)', r'resting.*?sns.*?(-?\d+\.?\d*)'],
                "Deep Breathing": [r'sns.*?deep.*?breathing.*?(-?\d+\.?\d*)', r'deep.*?breathing.*?sns.*?(-?\d+\.?\d*)'],
                "Valsalva": [r'sns.*?valsalva.*?(-?\d+\.?\d*)', r'valsalva.*?sns.*?(-?\d+\.?\d*)'],
                "Tilt Test": [r'sns.*?tilt.*?(-?\d+\.?\d*)', r'tilt.*?sns.*?(-?\d+\.?\d*)'],
                "Resting2": [r'sns.*?resting.*?2.*?(-?\d+\.?\d*)', r'resting.*?2.*?sns.*?(-?\d+\.?\d*)']
            },
            "PNS": {
                "Resting": [r'pns.*?resting.*?(-?\d+\.?\d*)', r'resting.*?pns.*?(-?\d+\.?\d*)'],
                "Deep Breathing": [r'pns.*?deep.*?breathing.*?(-?\d+\.?\d*)', r'deep.*?breathing.*?pns.*?(-?\d+\.?\d*)'],
                "Valsalva": [r'pns.*?valsalva.*?(-?\d+\.?\d*)', r'valsalva.*?pns.*?(-?\d+\.?\d*)'],
                "Tilt Test": [r'pns.*?tilt.*?(-?\d+\.?\d*)', r'tilt.*?pns.*?(-?\d+\.?\d*)'],
                "Resting2": [r'pns.*?resting.*?2.*?(-?\d+\.?\d*)', r'resting.*?2.*?pns.*?(-?\d+\.?\d*)']
            },
            "SNS_PNS_Ratio": {
                "Resting": [r'sns/pns.*?resting.*?(-?\d+\.?\d*)', r'resting.*?sns/pns.*?(-?\d+\.?\d*)'],
                "Deep Breathing": [r'sns/pns.*?deep.*?breathing.*?(-?\d+\.?\d*)', r'deep.*?breathing.*?sns/pns.*?(-?\d+\.?\d*)'],
                "Valsalva": [r'sns/pns.*?valsalva.*?(-?\d+\.?\d*)', r'valsalva.*?sns/pns.*?(-?\d+\.?\d*)'],
                "Tilt Test": [r'sns/pns.*?tilt.*?(-?\d+\.?\d*)', r'tilt.*?sns/pns.*?(-?\d+\.?\d*)'],
                "Resting2": [r'sns/pns.*?resting.*?2.*?(-?\d+\.?\d*)', r'resting.*?2.*?sns/pns.*?(-?\d+\.?\d*)']
            },
            "LF_HF": {
                "Resting": [r'lf/hf.*?resting.*?(-?\d+\.?\d*)', r'resting.*?lf/hf.*?(-?\d+\.?\d*)'],
                "Deep Breathing": [r'lf/hf.*?deep.*?breathing.*?(-?\d+\.?\d*)', r'deep.*?breathing.*?lf/hf.*?(-?\d+\.?\d*)'],
                "Valsalva": [r'lf/hf.*?valsalva.*?(-?\d+\.?\d*)', r'valsalva.*?lf/hf.*?(-?\d+\.?\d*)'],
                "Tilt Test": [r'lf/hf.*?tilt.*?(-?\d+\.?\d*)', r'tilt.*?lf/hf.*?(-?\d+\.?\d*)'],
                "Resting2": [r'lf/hf.*?resting.*?2.*?(-?\d+\.?\d*)', r'resting.*?2.*?lf/hf.*?(-?\d+\.?\d*)']
            },
            "SpO2": {
                "Resting": [r'spo2.*?resting.*?(\d+)', r'resting.*?spo2.*?(\d+)'],
                "Deep Breathing": [r'spo2.*?deep.*?breathing.*?(\d+)', r'deep.*?breathing.*?spo2.*?(\d+)'],
                "Valsalva": [r'spo2.*?valsalva.*?(\d+)', r'valsalva.*?spo2.*?(\d+)'],
                "Tilt Test": [r'spo2.*?tilt.*?(\d+)', r'tilt.*?spo2.*?(\d+)'],
                "Resting2": [r'spo2.*?resting.*?2.*?(\d+)', r'resting.*?2.*?spo2.*?(\d+)']
            }
        }
        
        for metric_type, test_patterns in metric_patterns.items():
            autonomic_data[metric_type] = {}
            for test_name, patterns in test_patterns.items():
                autonomic_data[metric_type][test_name] = self.search_for_value_in_text(full_text, patterns)
        
        return autonomic_data
    
    def extract_other_metrics(self, pages_text: List[str]) -> Dict[str, str]:
        """Extract other autonomic metrics from PDF text."""
        other_metrics = {}
        
        # Combine all pages text
        full_text = " ".join(pages_text)
        
        # Patterns for other metrics
        other_patterns = {
            "Total Autonomic Activity": [
                r'total.*?autonomic.*?activity.*?(-?\d+\.?\d*)',
                r'autonomic.*?activity.*?(-?\d+\.?\d*)',
                r'total.*?activity.*?(-?\d+\.?\d*)',
                r'activity.*?(-?\d+\.?\d*)'
            ],
            "Autonomic Balance": [
                r'autonomic.*?balance.*?(-?\d+\.?\d*)',
                r'balance.*?(-?\d+\.?\d*)',
                r'balance.*?index.*?(-?\d+\.?\d*)'
            ],
            "E/I Ratio": [
                r'e/i.*?ratio.*?(-?\d+\.?\d*)',
                r'ei.*?ratio.*?(-?\d+\.?\d*)',
                r'e/i.*?(-?\d+\.?\d*)',
                r'expiration.*?inspiration.*?ratio.*?(-?\d+\.?\d*)'
            ],
            "Valsalva Ratio": [
                r'valsalva.*?ratio.*?(-?\d+\.?\d*)',
                r'valsal.*?ratio.*?(-?\d+\.?\d*)',
                r'valsalva.*?maneuver.*?ratio.*?(-?\d+\.?\d*)'
            ],
            "K30/15 Ratio": [
                r'k30/15.*?ratio.*?(-?\d+\.?\d*)',
                r'k30.*?15.*?ratio.*?(-?\d+\.?\d*)',
                r'30.*?15.*?ratio.*?(-?\d+\.?\d*)'
            ],
            "Functional Age": [
                r'functional.*?age.*?(-?\d+\.?\d*)',
                r'biological.*?age.*?(-?\d+\.?\d*)',
                r'age.*?(-?\d+\.?\d*)'
            ],
            "Autonomic Physical Dysregulation (PSI)": [
                r'psi.*?(-?\d+\.?\d*)',
                r'physical.*?dysregulation.*?(-?\d+\.?\d*)',
                r'autonomic.*?physical.*?dysregulation.*?(-?\d+\.?\d*)',
                r'physical.*?stress.*?index.*?(-?\d+\.?\d*)'
            ],
            "Accumulative Mental Stress (MSI)": [
                r'msi.*?(-?\d+\.?\d*)',
                r'mental.*?stress.*?(-?\d+\.?\d*)',
                r'accumulative.*?mental.*?stress.*?(-?\d+\.?\d*)',
                r'mental.*?stress.*?index.*?(-?\d+\.?\d*)'
            ]
        }
        
        for metric, patterns in other_patterns.items():
            other_metrics[metric] = self.search_for_value_in_text(full_text, patterns)
        
        return other_metrics
    
    def extract_cardiovascular_metrics(self, pages_text: List[str]) -> Dict[str, str]:
        """Extract cardiovascular metrics from PDF text."""
        cv_metrics = {}
        
        # Combine all pages text
        full_text = " ".join(pages_text)
        
        # Patterns for cardiovascular metrics
        cv_patterns = {
            "EEI": [r'eei.*?(-?\d+\.?\d*)', r'elasticity.*?index.*?(-?\d+\.?\d*)'],
            "DDI": [r'ddi.*?(-?\d+\.?\d*)', r'distensibility.*?index.*?(-?\d+\.?\d*)'],
            "DEI": [r'dei.*?(-?\d+\.?\d*)', r'distensibility.*?elasticity.*?(-?\d+\.?\d*)'],
            "AI": [r'ai.*?(-?\d+\.?\d*)', r'augmentation.*?index.*?(-?\d+\.?\d*)'],
            "Right Ankle/Brachial Index": [r'abi.*?(-?\d+\.?\d*)', r'ankle.*?brachial.*?(-?\d+\.?\d*)'],
            "Right Toe/Brachial Index": [r'tbi.*?(-?\d+\.?\d*)', r'toe.*?brachial.*?(-?\d+\.?\d*)'],
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
            "ST seg": [r'st.*?seg.*?(-?\d+\.?\d*)', r'st.*?segment.*?(-?\d+\.?\d*)']
        }
        
        for metric, patterns in cv_patterns.items():
            cv_metrics[metric] = self.search_for_value_in_text(full_text, patterns)
        
        return cv_metrics
    
    def extract_ecg_data(self, pages_text: List[str]) -> Dict[str, Dict[str, str]]:
        """Extract ECG data from PDF text, specifically from ECG ANALYSIS REPORT page."""
        ecg_data = {}
        
        # Step 1: Find ECG ANALYSIS REPORT page using headlines first
        ecg_page_index = None
        headlines_file = "json_output/extracted_headlines.json"
        
        if os.path.exists(headlines_file):
            try:
                with open(headlines_file, 'r', encoding='utf-8') as f:
                    headlines = json.load(f)
                
                # Find the first page with "ECG ANALYSIS REPORT"
                for page_key, page_title in headlines.items():
                    if "ecg analysis report" in page_title.lower():
                        page_num = int(page_key.split('_')[1]) - 1  # Convert to 0-based index
                        ecg_page_index = page_num
                        print(f"DEBUG: Found ECG ANALYSIS REPORT on page {page_num + 1} from headlines")
                        break
            except Exception as e:
                print(f"DEBUG: Could not read headlines file: {e}")
        
        # Step 2: If not found in headlines, search page text
        if ecg_page_index is None:
            for i, page_text in enumerate(pages_text):
                if "ecg analysis report" in page_text.lower():
                    ecg_page_index = i
                    print(f"DEBUG: Found ECG ANALYSIS REPORT on page {i + 1} from page text")
                    break
        
        # Step 3: If still not found, try alternative patterns
        if ecg_page_index is None:
            for i, page_text in enumerate(pages_text):
                if "ecg analysis" in page_text.lower() and "report" in page_text.lower():
                    ecg_page_index = i
                    print(f"DEBUG: Found ECG ANALYSIS on page {i + 1}")
                    break
        
        if ecg_page_index is None:
            print("DEBUG: ECG ANALYSIS REPORT page not found")
            return ecg_data
        
        # Extract text from ECG page and surrounding pages
        ecg_text = pages_text[ecg_page_index]
        if ecg_page_index + 1 < len(pages_text):
            ecg_text += " " + pages_text[ecg_page_index + 1]
        if ecg_page_index + 2 < len(pages_text):
            ecg_text += " " + pages_text[ecg_page_index + 2]
        
        print(f"DEBUG: Extracting ECG data from page {ecg_page_index + 1} and surrounding pages")
        
        # Heart Rate patterns - look for specific ECG patterns
        hr_patterns = {
            "Average Heart Rate": [
                r'average.*?heart.*?rate.*?(\d+)', 
                r'mean.*?heart.*?rate.*?(\d+)',
                r'hr.*?(\d+).*?bpm',
                r'heart.*?rate.*?(\d+)'
            ],
            "Fastest rate": [
                r'fastest.*?rate.*?(\d+)', 
                r'maximum.*?heart.*?rate.*?(\d+)',
                r'max.*?hr.*?(\d+)',
                r'peak.*?heart.*?rate.*?(\d+)'
            ],
            "Slowest rate": [
                r'slowest.*?rate.*?(\d+)', 
                r'minimum.*?heart.*?rate.*?(\d+)',
                r'min.*?hr.*?(\d+)',
                r'lowest.*?heart.*?rate.*?(\d+)'
            ],
            "Fastest minutely rate": [
                r'fastest.*?minutely.*?rate.*?(\d+)',
                r'max.*?minutely.*?(\d+)',
                r'peak.*?minutely.*?(\d+)'
            ],
            "Slowest minutely rate": [
                r'slowest.*?minutely.*?rate.*?(\d+)',
                r'min.*?minutely.*?(\d+)',
                r'lowest.*?minutely.*?(\d+)'
            ]
        }
        
        ecg_data["Heart_Rate"] = {}
        for metric, patterns in hr_patterns.items():
            ecg_data["Heart_Rate"][metric] = self.search_for_value_in_text(ecg_text, patterns)
        
        # Ventricular Details patterns
        ventricular_patterns = {
            "PVC - Ventricular Ectopy": [
                r'pvc.*?(\d+)', 
                r'ventricular.*?ectopy.*?(\d+)',
                r'ventricular.*?premature.*?(\d+)',
                r'vpc.*?(\d+)'
            ],
            "Ventricular Couplet": [
                r'ventricular.*?couplet.*?(\d+)',
                r'ventricular.*?pair.*?(\d+)',
                r'couplet.*?(\d+)'
            ]
        }
        
        ecg_data["Ventricular_Details"] = {}
        for metric, patterns in ventricular_patterns.items():
            ecg_data["Ventricular_Details"][metric] = self.search_for_value_in_text(ecg_text, patterns)
        
        # Supraventricular Details patterns
        supraventricular_patterns = {
            "PAC - Supraventricular Ectopy": [
                r'pac.*?(\d+)', 
                r'supraventricular.*?ectopy.*?(\d+)',
                r'atrial.*?premature.*?(\d+)',
                r'apc.*?(\d+)'
            ],
            "Supraventricular Couplet": [
                r'supraventricular.*?couplet.*?(\d+)',
                r'atrial.*?couplet.*?(\d+)',
                r'supraventricular.*?pair.*?(\d+)'
            ]
        }
        
        ecg_data["Supraventricular_Details"] = {}
        for metric, patterns in supraventricular_patterns.items():
            ecg_data["Supraventricular_Details"][metric] = self.search_for_value_in_text(ecg_text, patterns)
        
        # HRV Analysis patterns
        hrv_patterns = {
            "SDNN": [
                r'sdnn.*?(-?\d+\.?\d*)',
                r'standard.*?deviation.*?nn.*?(-?\d+\.?\d*)',
                r'hrv.*?sdnn.*?(-?\d+\.?\d*)'
            ],
            "SDNN Max": [
                r'sdnn.*?max.*?(-?\d+\.?\d*)',
                r'max.*?sdnn.*?(-?\d+\.?\d*)',
                r'peak.*?sdnn.*?(-?\d+\.?\d*)'
            ],
            "SDNN Min": [
                r'sdnn.*?min.*?(-?\d+\.?\d*)',
                r'min.*?sdnn.*?(-?\d+\.?\d*)',
                r'lowest.*?sdnn.*?(-?\d+\.?\d*)'
            ]
        }
        
        ecg_data["HRV_Analysis"] = {}
        for metric, patterns in hrv_patterns.items():
            ecg_data["HRV_Analysis"][metric] = self.search_for_value_in_text(ecg_text, patterns)
        
        # QRS Analysis patterns
        qrs_patterns = {
            "QRS": [
                r'qrs.*?(-?\d+\.?\d*)',
                r'qrs.*?duration.*?(-?\d+\.?\d*)',
                r'qrs.*?width.*?(-?\d+\.?\d*)'
            ],
            "QT / QTc": [
                r'qt.*?qtc.*?(-?\d+\.?\d*)', 
                r'qt/qtc.*?(-?\d+\.?\d*)',
                r'qt.*?interval.*?(-?\d+\.?\d*)'
            ],
            "QTc Max": [
                r'qtc.*?max.*?(-?\d+\.?\d*)',
                r'max.*?qtc.*?(-?\d+\.?\d*)',
                r'peak.*?qtc.*?(-?\d+\.?\d*)'
            ],
            "PR int / seg": [
                r'pr.*?int.*?(-?\d+\.?\d*)', 
                r'pr.*?seg.*?(-?\d+\.?\d*)',
                r'pr.*?interval.*?(-?\d+\.?\d*)'
            ],
            "ST int / seg": [
                r'st.*?int.*?(-?\d+\.?\d*)', 
                r'st.*?seg.*?(-?\d+\.?\d*)',
                r'st.*?segment.*?(-?\d+\.?\d*)'
            ]
        }
        
        ecg_data["QRS_Analysis"] = {}
        for metric, patterns in qrs_patterns.items():
            ecg_data["QRS_Analysis"][metric] = self.search_for_value_in_text(ecg_text, patterns)
        
        # Debug output
        print(f"DEBUG: ECG data extracted from page {ecg_page_index + 1}:")
        for section_name, section_data in ecg_data.items():
            if isinstance(section_data, dict):
                for metric_name, value in section_data.items():
                    if value:
                        print(f"  {section_name} - {metric_name}: {value}")
        
        return ecg_data
    
    def should_flag_value(self, metric_name: str, value: str) -> bool:
        """Determine if a value should be flagged based on norms."""
        if not value or metric_name not in self.norms:
            return False
        
        try:
            # Extract numeric value
            numeric_value = float(re.findall(r'-?\d+\.?\d*', value)[0])
            norm_str = self.norms[metric_name]
            
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
    
    def format_value_with_flag(self, metric_name: str, value: str) -> str:
        """Format a value with flag if needed."""
        if not value:
            return ""
        
        flag_text = " | FLAG" if self.should_flag_value(metric_name, value) else ""
        return f"{value}{flag_text}"
    
    def extract_all_data_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extract all required medical data from PDF."""
        print(f"Extracting data from PDF: {pdf_path}")
        
        # Extract text from all pages
        pages_text = self.extract_text_from_pdf(pdf_path)
        if not pages_text:
            print("No text extracted from PDF")
            return {}
        
        print(f"Extracted text from {len(pages_text)} pages")
        
        # Extract all data sections
        extracted_data = {
            "AUTONOMICS": {
                "HR": self.extract_hr_data(pages_text),
                "BP": self.extract_bp_data(pages_text),
                **self.extract_autonomic_metrics(pages_text),
                "Other_Metrics": self.extract_other_metrics(pages_text)
            },
            "CARDIOVASCULAR": self.extract_cardiovascular_metrics(pages_text),
            "ELECTROCARDIOGRAM": self.extract_ecg_data(pages_text)
        }
        
        return extracted_data
    
    def organize_data_by_sections(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Organize extracted data into proper sections, moving misplaced data to correct sections."""
        
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
        
        # Process extracted data and organize it
        for section_name, section_data in extracted_data.items():
            if section_name == "AUTONOMICS":
                # Keep autonomic data in AUTONOMICS section
                for subsection_name, subsection_data in section_data.items():
                    if subsection_name in organized_data["AUTONOMICS"]:
                        organized_data["AUTONOMICS"][subsection_name] = subsection_data
            elif section_name == "CARDIOVASCULAR":
                # Keep cardiovascular data in CARDIOVASCULAR section
                organized_data["CARDIOVASCULAR"].update(section_data)
            elif section_name == "ELECTROCARDIOGRAM":
                # Keep ECG data in ELECTROCARDIOGRAM section
                for subsection_name, subsection_data in section_data.items():
                    if subsection_name in organized_data["ELECTROCARDIOGRAM"]:
                        organized_data["ELECTROCARDIOGRAM"][subsection_name] = subsection_data
        
        # Move any misplaced cardiovascular metrics to CARDIOVASCULAR section
        # and ensure autonomic metrics stay in AUTONOMICS
        for section_name, section_data in extracted_data.items():
            if isinstance(section_data, dict):
                for metric_name, metric_value in section_data.items():
                    # Move cardiovascular metrics to CARDIOVASCULAR section
                    if metric_name in cardiovascular_metrics and metric_name not in organized_data["CARDIOVASCULAR"]:
                        organized_data["CARDIOVASCULAR"][metric_name] = metric_value
                    # Ensure autonomic metrics stay in AUTONOMICS Other_Metrics
                    elif metric_name in autonomic_metrics and metric_name not in organized_data["AUTONOMICS"]["Other_Metrics"]:
                        organized_data["AUTONOMICS"]["Other_Metrics"][metric_name] = metric_value
        
        return organized_data
    
    def format_to_exact_output(self, extracted_data: Dict[str, Any]) -> str:
        """Format extracted data to exact output format requested."""
        
        # First organize the data properly
        organized_data = self.organize_data_by_sections(extracted_data)
        
        output_lines = []
        
        # AUTONOMICS section
        output_lines.append("AUTONOMICS")
        output_lines.append("")
        
        # HR subsection
        output_lines.append("HR")
        hr_data = organized_data.get("AUTONOMICS", {}).get("HR", {})
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
        bp_data = organized_data.get("AUTONOMICS", {}).get("BP", {})
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
        sns_data = organized_data.get("AUTONOMICS", {}).get("SNS", {})
        output_lines.append(f"Resting: {self.format_value_with_flag('SNS', sns_data.get('Resting', ''))}")
        output_lines.append(f"Deep Breathing: {self.format_value_with_flag('SNS', sns_data.get('Deep Breathing', ''))}")
        output_lines.append(f"Valsalva: {self.format_value_with_flag('SNS', sns_data.get('Valsalva', ''))}")
        output_lines.append(f"Tilt Test: {self.format_value_with_flag('SNS', sns_data.get('Tilt Test', ''))}")
        output_lines.append(f"Resting2: {self.format_value_with_flag('SNS', sns_data.get('Resting2', ''))}")
        output_lines.append("")
        
        # PNS subsection
        output_lines.append("PNS (Norm: 0.8–4.0)")
        pns_data = organized_data.get("AUTONOMICS", {}).get("PNS", {})
        output_lines.append(f"Resting: {self.format_value_with_flag('PNS', pns_data.get('Resting', ''))}")
        output_lines.append(f"Deep Breathing: {self.format_value_with_flag('PNS', pns_data.get('Deep Breathing', ''))}")
        output_lines.append(f"Valsalva: {self.format_value_with_flag('PNS', pns_data.get('Valsalva', ''))}")
        output_lines.append(f"Tilt Test: {self.format_value_with_flag('PNS', pns_data.get('Tilt Test', ''))}")
        output_lines.append(f"Resting2: {self.format_value_with_flag('PNS', pns_data.get('Resting2', ''))}")
        output_lines.append("")
        
        # SNS/PNS Ratio subsection
        output_lines.append("SNS/PNS Ratio (Norm: 0.4–2.0)")
        sns_pns_data = organized_data.get("AUTONOMICS", {}).get("SNS_PNS_Ratio", {})
        output_lines.append(f"Resting: {self.format_value_with_flag('SNS/PNS', sns_pns_data.get('Resting', ''))}")
        output_lines.append(f"Deep Breathing: {self.format_value_with_flag('SNS/PNS', sns_pns_data.get('Deep Breathing', ''))}")
        output_lines.append(f"Valsalva: {self.format_value_with_flag('SNS/PNS', sns_pns_data.get('Valsalva', ''))}")
        output_lines.append(f"Tilt Test: {self.format_value_with_flag('SNS/PNS', sns_pns_data.get('Tilt Test', ''))}")
        output_lines.append(f"Resting2: {self.format_value_with_flag('SNS/PNS', sns_pns_data.get('Resting2', ''))}")
        output_lines.append("")
        
        # SpO2 subsection
        output_lines.append("SpO2")
        spo2_data = organized_data.get("AUTONOMICS", {}).get("SpO2", {})
        output_lines.append(f"Resting: {self.format_value_with_flag('SpO2', spo2_data.get('Resting', ''))}")
        output_lines.append(f"Deep Breathing: {self.format_value_with_flag('SpO2', spo2_data.get('Deep Breathing', ''))}")
        output_lines.append(f"Valsalva: {self.format_value_with_flag('SpO2', spo2_data.get('Valsalva', ''))}")
        output_lines.append(f"Tilt Test: {self.format_value_with_flag('SpO2', spo2_data.get('Tilt Test', ''))}")
        output_lines.append(f"Resting2: {self.format_value_with_flag('SpO2', spo2_data.get('Resting2', ''))}")
        output_lines.append("")
        
        # LF/HF subsection
        output_lines.append("LF/HF (Norm: <3)")
        lf_hf_data = organized_data.get("AUTONOMICS", {}).get("LF_HF", {})
        output_lines.append(f"Resting: {self.format_value_with_flag('LF/HF', lf_hf_data.get('Resting', ''))}")
        output_lines.append(f"Deep Breathing: {self.format_value_with_flag('LF/HF', lf_hf_data.get('Deep Breathing', ''))}")
        output_lines.append(f"Valsalva: {self.format_value_with_flag('LF/HF', lf_hf_data.get('Valsalva', ''))}")
        output_lines.append(f"Tilt Test: {self.format_value_with_flag('LF/HF', lf_hf_data.get('Tilt Test', ''))}")
        output_lines.append(f"Resting2: {self.format_value_with_flag('LF/HF', lf_hf_data.get('Resting2', ''))}")
        output_lines.append("")
        
        # Other Metrics subsection
        output_lines.append("Other Metrics")
        other_metrics = organized_data.get("AUTONOMICS", {}).get("Other_Metrics", {})
        output_lines.append(f"Total Autonomic Activity (Norm: 45–80): {self.format_value_with_flag('Total Autonomic Activity', other_metrics.get('Total Autonomic Activity', ''))}")
        output_lines.append(f"Autonomic Balance (Norm: -3 to 3): {self.format_value_with_flag('Autonomic Balance', other_metrics.get('Autonomic Balance', ''))}")
        output_lines.append(f"E/I Ratio (Norm: >1.2): {self.format_value_with_flag('E/I Ratio', other_metrics.get('E/I Ratio', ''))}")
        output_lines.append(f"Valsalva Ratio (Norm: >1.2): {self.format_value_with_flag('Valsalva Ratio', other_metrics.get('Valsalva Ratio', ''))}")
        output_lines.append(f"K30/15 Ratio (Norm: >1.1): {self.format_value_with_flag('K30/15 Ratio', other_metrics.get('K30/15 Ratio', ''))}")
        output_lines.append(f"Autonomic Physical Dysregulation (PSI) (Norm: <1.0): {self.format_value_with_flag('PSI', other_metrics.get('Autonomic Physical Dysregulation (PSI)', ''))}")
        output_lines.append(f"Accumulative Mental Stress (MSI) (Norm: <1.0): {self.format_value_with_flag('MSI', other_metrics.get('Accumulative Mental Stress (MSI)', ''))}")
        output_lines.append("")
        
        # CARDIOVASCULAR section
        output_lines.append("CARDIOVASCULAR")
        output_lines.append("")
        
        cv_data = organized_data.get("CARDIOVASCULAR", {})
        cv_metrics = [
            ("EEI (0.3–0.7)", "EEI"),
            ("DDI (0.3–0.7)", "DDI"),
            ("DEI (0.3–0.7)", "DEI"),
            ("AI (< -0.4)", "AI"),
            ("Right Ankle/Brachial Index (1–1.4)", "Right Ankle/Brachial Index"),
            ("Right Toe/Brachial Index (>0.75)", "Right Toe/Brachial Index"),
            ("Reflection Index (0.65–0.85)", "Reflection Index"),
            ("Stiffness Index (< 8.0 m/s)", "Stiffness Index"),
            ("Cardiac Output (4.0–8.0 l/min)", "Cardiac Output"),
            ("Mean Arterial Pressure (70–110 mmHg)", "Mean Arterial Pressure"),
            ("C1 (> 10.0 ml/mmHg)", "C1"),
            ("C2 (> 6.0 ml/mmHg)", "C2"),
            ("Ventricular Extrasystole (< 1)", "Ventricular Extrasystole"),
            ("Atrial Extrasystole (< 1)", "Atrial Extrasystole"),
            ("QRS (60–120 ms)", "QRS"),
            ("QTc (350–460 ms)", "QTc"),
            ("Body Mass Index (19–25)", "Body Mass Index"),
            ("Stroke Volume (55–100 ml)", "Stroke Volume"),
            ("Blood Volume (3–5 l)", "Blood Volume"),
            ("Artifacts (< 1)", "Artifacts"),
            ("ST seg (80–120 ms)", "ST seg")
        ]
        
        for metric_display, metric_key in cv_metrics:
            value = cv_data.get(metric_key, "")
            output_lines.append(f"{metric_display}: {self.format_value_with_flag(metric_key, value)}")
        output_lines.append("")
        
        # ELECTROCARDIOGRAM section
        output_lines.append("ELECTROCARDIOGRAM")
        output_lines.append("")
        
        ecg_data = organized_data.get("ELECTROCARDIOGRAM", {})
        
        # Heart Rate subsection
        output_lines.append("Heart Rate:")
        heart_rate_data = ecg_data.get("Heart_Rate", {})
        heart_rate_metrics = [
            "Average Heart Rate",
            "Fastest rate",
            "Slowest rate",
            "Fastest minutely rate",
            "Slowest minutely rate"
        ]
        for metric in heart_rate_metrics:
            value = heart_rate_data.get(metric, "")
            output_lines.append(f"{metric}: {self.format_value_with_flag('Average Heart Rate', value)}")
        output_lines.append("")
        
        # Ventricular Details subsection
        output_lines.append("Ventricular Details:")
        ventricular_data = ecg_data.get("Ventricular_Details", {})
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
        supraventricular_data = ecg_data.get("Supraventricular_Details", {})
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
        hrv_data = ecg_data.get("HRV_Analysis", {})
        hrv_metrics = [
            "SDNN",
            "SDNN Max",
            "SDNN Min"
        ]
        for metric in hrv_metrics:
            value = hrv_data.get(metric, "")
            output_lines.append(f"{metric}: {self.format_value_with_flag('SDNN', value)}")
        output_lines.append("")
        
        # QRS Analysis subsection
        output_lines.append("QRS Analysis:")
        qrs_data = ecg_data.get("QRS_Analysis", {})
        qrs_metrics = [
            "QRS",
            "QT / QTc",
            "QTc Max",
            "PR int / seg",
            "ST int / seg"
        ]
        for metric in qrs_metrics:
            value = qrs_data.get(metric, "")
            if metric == "QRS":
                output_lines.append(f"{metric}: {self.format_value_with_flag('QRS', value)}")
            elif metric == "QTc Max":
                output_lines.append(f"{metric}: {self.format_value_with_flag('QTc', value)}")
            elif metric == "PR int / seg":
                output_lines.append(f"{metric}: {self.format_value_with_flag('PR int', value)}")
            elif metric == "ST int / seg":
                output_lines.append(f"{metric}: {self.format_value_with_flag('ST seg', value)}")
            else:
                output_lines.append(f"{metric}: {value}")
        
        return "\n".join(output_lines)

def main():
    """Main function to demonstrate usage."""
    extractor = ComprehensiveMedicalExtractor()
    
    # Test with a sample PDF
    pdf_path = "input/CS_ANS_trial.2_2min.pdf"
    
    if os.path.exists(pdf_path):
        # Extract all data
        extracted_data = extractor.extract_all_data_from_pdf(pdf_path)
        
        # Format to exact output
        exact_output = extractor.format_to_exact_output(extracted_data)
        
        # Save output
        output_path = "json_output/comprehensive_extraction.txt"
        os.makedirs("json_output", exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(exact_output)
        
        print(f"✅ Comprehensive extraction saved to {output_path}")
        print("\n" + "="*50)
        print("EXACT OUTPUT FORMAT:")
        print("="*50)
        print(exact_output)
        
    else:
        print(f"❌ PDF file not found: {pdf_path}")

if __name__ == "__main__":
    main()
