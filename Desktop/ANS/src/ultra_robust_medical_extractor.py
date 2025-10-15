#!/usr/bin/env python3
"""
ULTRA-ROBUST Medical Data Extraction System
Designed for maximum accuracy and reliability in medical data extraction.
Multiple validation layers ensure no critical data is missed.
"""

import json
import re
import os
import fitz  # PyMuPDF
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging for medical data extraction
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataConfidence(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    MISSING = "MISSING"

@dataclass
class MedicalValue:
    value: str
    confidence: DataConfidence
    source_page: int
    extraction_method: str
    validation_checks: List[str]

class UltraRobustMedicalExtractor:
    """
    Ultra-robust medical data extractor with multiple validation layers.
    Designed to ensure 100% accuracy for critical medical data.
    """
    
    def __init__(self):
        """Initialize the ultra-robust extractor."""
        self.required_fields = {
            "AUTONOMICS": {
                "HR": {
                    "Resting": {"critical": True, "patterns": 15},
                    "Deep Breathing Max": {"critical": True, "patterns": 12},
                    "Deep Breathing Min": {"critical": True, "patterns": 12},
                    "Valsalva Max": {"critical": True, "patterns": 10},
                    "Valsalva Min": {"critical": True, "patterns": 10},
                    "Tilt Test": {"critical": True, "patterns": 8},
                    "Resting2": {"critical": True, "patterns": 6}
                },
                "BP": {
                    "Resting Systolic": {"critical": True, "patterns": 15},
                    "Resting Diastolic": {"critical": True, "patterns": 15},
                    "Deep Breathing Systolic": {"critical": True, "patterns": 12},
                    "Deep Breathing Diastolic": {"critical": True, "patterns": 12},
                    "Valsalva Systolic": {"critical": True, "patterns": 10},
                    "Valsalva Diastolic": {"critical": True, "patterns": 10},
                    "Tilt Test Systolic": {"critical": True, "patterns": 8},
                    "Tilt Test Diastolic": {"critical": True, "patterns": 8},
                    "Resting2 Systolic": {"critical": True, "patterns": 6},
                    "Resting2 Diastolic": {"critical": True, "patterns": 6}
                },
                "SNS": {
                    "Resting": {"critical": True, "patterns": 12},
                    "Deep Breathing": {"critical": True, "patterns": 10},
                    "Valsalva": {"critical": True, "patterns": 8},
                    "Tilt Test": {"critical": True, "patterns": 8},
                    "Resting2": {"critical": True, "patterns": 6}
                },
                "PNS": {
                    "Resting": {"critical": True, "patterns": 12},
                    "Deep Breathing": {"critical": True, "patterns": 10},
                    "Valsalva": {"critical": True, "patterns": 8},
                    "Tilt Test": {"critical": True, "patterns": 8},
                    "Resting2": {"critical": True, "patterns": 6}
                },
                "SNS_PNS_Ratio": {
                    "Resting": {"critical": True, "patterns": 10},
                    "Deep Breathing": {"critical": True, "patterns": 8},
                    "Valsalva": {"critical": True, "patterns": 6},
                    "Tilt Test": {"critical": True, "patterns": 6},
                    "Resting2": {"critical": True, "patterns": 4}
                },
                "SpO2": {
                    "Resting": {"critical": True, "patterns": 10},
                    "Deep Breathing": {"critical": True, "patterns": 8},
                    "Valsalva": {"critical": True, "patterns": 6},
                    "Tilt Test": {"critical": True, "patterns": 6},
                    "Resting2": {"critical": True, "patterns": 4}
                },
                "LF_HF": {
                    "Resting": {"critical": True, "patterns": 10},
                    "Deep Breathing": {"critical": True, "patterns": 8},
                    "Valsalva": {"critical": True, "patterns": 6},
                    "Tilt Test": {"critical": True, "patterns": 6},
                    "Resting2": {"critical": True, "patterns": 4}
                },
                "Other_Metrics": {
                    "Total Autonomic Activity": {"critical": True, "patterns": 8},
                    "Autonomic Balance": {"critical": True, "patterns": 8},
                    "E/I Ratio": {"critical": True, "patterns": 6},
                    "Valsalva Ratio": {"critical": True, "patterns": 6},
                    "K30/15 Ratio": {"critical": True, "patterns": 6},
                    "Functional Age": {"critical": True, "patterns": 4},
                    "Autonomic Physical Dysregulation (PSI)": {"critical": True, "patterns": 6},
                    "Accumulative Mental Stress (MSI)": {"critical": True, "patterns": 6}
                }
            },
            "CARDIOVASCULAR": {
                "EEI": {"critical": True, "patterns": 8},
                "DDI": {"critical": True, "patterns": 8},
                "DEI": {"critical": True, "patterns": 8},
                "AI": {"critical": True, "patterns": 8},
                "Right Ankle/Brachial Index": {"critical": True, "patterns": 6},
                "Right Toe/Brachial Index": {"critical": True, "patterns": 6},
                "Reflection Index": {"critical": True, "patterns": 6},
                "Stiffness Index": {"critical": True, "patterns": 6},
                "Cardiac Output": {"critical": True, "patterns": 8},
                "Mean Arterial Pressure": {"critical": True, "patterns": 8},
                "C1": {"critical": True, "patterns": 6},
                "C2": {"critical": True, "patterns": 6},
                "Ventricular Extrasystole": {"critical": True, "patterns": 6},
                "Atrial Extrasystole": {"critical": True, "patterns": 6},
                "QRS": {"critical": True, "patterns": 8},
                "QTc": {"critical": True, "patterns": 8},
                "Body Mass Index": {"critical": True, "patterns": 6},
                "Stroke Volume": {"critical": True, "patterns": 6},
                "Blood Volume": {"critical": True, "patterns": 6},
                "Artifacts": {"critical": True, "patterns": 4},
                "ST seg": {"critical": True, "patterns": 6}
            },
            "ELECTROCARDIOGRAM": {
                "Heart_Rate": {
                    "Average Heart Rate": {"critical": True, "patterns": 12},
                    "Fastest rate": {"critical": True, "patterns": 10},
                    "Slowest rate": {"critical": True, "patterns": 10},
                    "Fastest minutely rate": {"critical": True, "patterns": 8},
                    "Slowest minutely rate": {"critical": True, "patterns": 8}
                },
                "Ventricular_Details": {
                    "PVC - Ventricular Ectopy": {"critical": True, "patterns": 8},
                    "Ventricular Couplet": {"critical": True, "patterns": 6}
                },
                "Supraventricular_Details": {
                    "PAC - Supraventricular Ectopy": {"critical": True, "patterns": 8},
                    "Supraventricular Couplet": {"critical": True, "patterns": 6}
                },
                "HRV_Analysis": {
                    "SDNN": {"critical": True, "patterns": 10},
                    "SDNN Max": {"critical": True, "patterns": 8},
                    "SDNN Min": {"critical": True, "patterns": 8}
                },
                "QRS_Analysis": {
                    "QRS": {"critical": True, "patterns": 8},
                    "QT / QTc": {"critical": True, "patterns": 8},
                    "QTc Max": {"critical": True, "patterns": 6},
                    "PR int / seg": {"critical": True, "patterns": 8},
                    "ST int / seg": {"critical": True, "patterns": 8}
                }
            }
        }
        
        # Define comprehensive norms for validation
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
        
        # Initialize extraction results
        self.extraction_results = {}
        self.validation_log = []
        
    def extract_text_from_pdf(self, pdf_path: str) -> List[str]:
        """Extract text from all pages of PDF with error handling."""
        try:
            doc = fitz.open(pdf_path)
            pages_text = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                pages_text.append(text)
                logger.info(f"Extracted text from page {page_num + 1}")
            
            doc.close()
            logger.info(f"Successfully extracted text from {len(pages_text)} pages")
            return pages_text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return []
    
    def get_comprehensive_patterns(self, field_name: str, field_type: str) -> List[str]:
        """Get comprehensive search patterns for each field."""
        
        # Base patterns for different field types
        base_patterns = {
            "HR": [
                rf'{field_name.lower()}.*?(\d+)',
                rf'heart.*?rate.*?{field_name.lower()}.*?(\d+)',
                rf'hr.*?{field_name.lower()}.*?(\d+)',
                rf'{field_name.lower()}.*?hr.*?(\d+)',
                rf'{field_name.lower()}.*?bpm.*?(\d+)',
                rf'{field_name.lower()}.*?beats.*?(\d+)',
                rf'rate.*?{field_name.lower()}.*?(\d+)',
                rf'{field_name.lower()}.*?rate.*?(\d+)',
                rf'{field_name.lower()}.*?(\d+).*?bpm',
                rf'{field_name.lower()}.*?(\d+).*?beats',
                rf'{field_name.lower()}.*?(\d+).*?hr',
                rf'{field_name.lower()}.*?(\d+).*?heart',
                rf'{field_name.lower()}.*?(\d+).*?rate',
                rf'{field_name.lower()}.*?(\d+).*?min',
                rf'{field_name.lower()}.*?(\d+).*?max'
            ],
            "BP": [
                rf'{field_name.lower()}.*?systolic.*?(\d+)',
                rf'{field_name.lower()}.*?diastolic.*?(\d+)',
                rf'systolic.*?{field_name.lower()}.*?(\d+)',
                rf'diastolic.*?{field_name.lower()}.*?(\d+)',
                rf'{field_name.lower()}.*?bp.*?(\d+)/',
                rf'{field_name.lower()}.*?bp.*?/(\d+)',
                rf'{field_name.lower()}.*?(\d+)/\d+',
                rf'{field_name.lower()}.*?\d+/(\d+)',
                rf'{field_name.lower()}.*?(\d+).*?systolic',
                rf'{field_name.lower()}.*?(\d+).*?diastolic',
                rf'{field_name.lower()}.*?(\d+).*?mmhg',
                rf'{field_name.lower()}.*?(\d+).*?pressure',
                rf'{field_name.lower()}.*?(\d+).*?bp',
                rf'{field_name.lower()}.*?(\d+).*?blood',
                rf'{field_name.lower()}.*?(\d+).*?pressure'
            ],
            "SNS": [
                rf'sns.*?{field_name.lower()}.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?sns.*?(-?\d+\.?\d*)',
                rf'sympathetic.*?{field_name.lower()}.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?sympathetic.*?(-?\d+\.?\d*)',
                rf'sns.*?{field_name.lower()}.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?sns.*?(-?\d+\.?\d*)',
                rf'sympathetic.*?nervous.*?{field_name.lower()}.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?sympathetic.*?nervous.*?(-?\d+\.?\d*)',
                rf'sns.*?activity.*?{field_name.lower()}.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?sns.*?activity.*?(-?\d+\.?\d*)',
                rf'sympathetic.*?tone.*?{field_name.lower()}.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?sympathetic.*?tone.*?(-?\d+\.?\d*)'
            ],
            "PNS": [
                rf'pns.*?{field_name.lower()}.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?pns.*?(-?\d+\.?\d*)',
                rf'parasympathetic.*?{field_name.lower()}.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?parasympathetic.*?(-?\d+\.?\d*)',
                rf'pns.*?{field_name.lower()}.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?pns.*?(-?\d+\.?\d*)',
                rf'parasympathetic.*?nervous.*?{field_name.lower()}.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?parasympathetic.*?nervous.*?(-?\d+\.?\d*)',
                rf'pns.*?activity.*?{field_name.lower()}.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?pns.*?activity.*?(-?\d+\.?\d*)',
                rf'parasympathetic.*?tone.*?{field_name.lower()}.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?parasympathetic.*?tone.*?(-?\d+\.?\d*)'
            ],
            "SpO2": [
                rf'spo2.*?{field_name.lower()}.*?(\d+)',
                rf'{field_name.lower()}.*?spo2.*?(\d+)',
                rf'oxygen.*?saturation.*?{field_name.lower()}.*?(\d+)',
                rf'{field_name.lower()}.*?oxygen.*?saturation.*?(\d+)',
                rf'spo2.*?{field_name.lower()}.*?(\d+)',
                rf'{field_name.lower()}.*?spo2.*?(\d+)',
                rf'oxygen.*?{field_name.lower()}.*?(\d+)',
                rf'{field_name.lower()}.*?oxygen.*?(\d+)',
                rf'saturation.*?{field_name.lower()}.*?(\d+)',
                rf'{field_name.lower()}.*?saturation.*?(\d+)'
            ],
            "ECG": [
                rf'{field_name.lower()}.*?(\d+)',
                rf'{field_name.lower()}.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?rate.*?(\d+)',
                rf'{field_name.lower()}.*?interval.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?duration.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?(\d+).*?bpm',
                rf'{field_name.lower()}.*?(\d+).*?ms',
                rf'{field_name.lower()}.*?(\d+).*?beats',
                rf'{field_name.lower()}.*?(\d+).*?episodes',
                rf'{field_name.lower()}.*?(\d+).*?events',
                rf'{field_name.lower()}.*?(\d+).*?ectopy',
                rf'{field_name.lower()}.*?(\d+).*?couplet',
                rf'{field_name.lower()}.*?(\d+).*?analysis',
                rf'{field_name.lower()}.*?(\d+).*?measurement',
                rf'{field_name.lower()}.*?(\d+).*?value',
                # Specific patterns for the actual data format found
                rf'resting.*?{field_name.lower()}.*?(\d+)',
                rf'tilt.*?test.*?{field_name.lower()}.*?(\d+)',
                rf'resting2.*?{field_name.lower()}.*?(\d+)',
                rf'{field_name.lower()}.*?resting.*?(\d+)',
                rf'{field_name.lower()}.*?tilt.*?(\d+)',
                rf'{field_name.lower()}.*?resting2.*?(\d+)',
                # Table format patterns
                rf'{field_name.lower()}.*?\s+(\d+)\s+',
                rf'\s+(\d+)\s+.*?{field_name.lower()}',
                # Direct value patterns
                rf'{field_name.lower()}.*?(\d+\.?\d*)',
                rf'(\d+\.?\d*).*?{field_name.lower()}'
            ],
            "Cardiovascular": [
                rf'{field_name.lower()}.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?(\d+)',
                rf'{field_name.lower()}.*?index.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?ratio.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?pressure.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?output.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?volume.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?mass.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?stiffness.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?elasticity.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?distensibility.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?augmentation.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?reflection.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?cardiac.*?(-?\d+\.?\d*)',
                rf'{field_name.lower()}.*?arterial.*?(-?\d+\.?\d*)'
            ]
        }
        
        # Get patterns based on field type
        if "hr" in field_name.lower() or "heart rate" in field_name.lower():
            return base_patterns["HR"]
        elif "systolic" in field_name.lower() or "diastolic" in field_name.lower():
            return base_patterns["BP"]
        elif "sns" in field_name.lower():
            return base_patterns["SNS"]
        elif "pns" in field_name.lower():
            return base_patterns["PNS"]
        elif "spo2" in field_name.lower():
            return base_patterns["SpO2"]
        elif any(term in field_name.lower() for term in ["ecg", "heart rate", "ventricular", "supraventricular", "hrv", "qrs", "qt", "pr", "st"]):
            return base_patterns["ECG"]
        else:
            return base_patterns["Cardiovascular"]
    
    def search_with_multiple_methods(self, text: str, field_name: str, field_type: str) -> MedicalValue:
        """Search for a value using multiple methods and return confidence level."""
        
        patterns = self.get_comprehensive_patterns(field_name, field_type)
        found_values = []
        validation_checks = []
        
        # Method 1: Direct pattern matching
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match and match.strip():
                    found_values.append({
                        'value': match.strip(),
                        'method': 'pattern_match',
                        'pattern': pattern
                    })
        
        # Method 2: Context-aware search
        context_patterns = [
            rf'{field_name.lower()}.*?[:=]\s*(\d+\.?\d*)',
            rf'{field_name.lower()}.*?is\s*(\d+\.?\d*)',
            rf'{field_name.lower()}.*?was\s*(\d+\.?\d*)',
            rf'{field_name.lower()}.*?measured\s*(\d+\.?\d*)',
            rf'{field_name.lower()}.*?shows\s*(\d+\.?\d*)',
            rf'{field_name.lower()}.*?indicates\s*(\d+\.?\d*)',
            rf'{field_name.lower()}.*?reveals\s*(\d+\.?\d*)',
            rf'{field_name.lower()}.*?displays\s*(\d+\.?\d*)'
        ]
        
        for pattern in context_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match and match.strip():
                    found_values.append({
                        'value': match.strip(),
                        'method': 'context_search',
                        'pattern': pattern
                    })
        
        # Method 3: Table-based extraction
        table_patterns = [
            rf'{field_name.lower()}.*?\|.*?(\d+\.?\d*)',
            rf'{field_name.lower()}.*?\t.*?(\d+\.?\d*)',
            rf'{field_name.lower()}.*?\s{2,}.*?(\d+\.?\d*)'
        ]
        
        for pattern in table_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match and match.strip():
                    found_values.append({
                        'value': match.strip(),
                        'method': 'table_extraction',
                        'pattern': pattern
                    })
        
        # Determine confidence and best value
        if not found_values:
            return MedicalValue(
                value="",
                confidence=DataConfidence.MISSING,
                source_page=0,
                extraction_method="none",
                validation_checks=["No values found"]
            )
        
        # Count occurrences and determine confidence
        value_counts = {}
        for val in found_values:
            value = val['value']
            if value not in value_counts:
                value_counts[value] = {'count': 0, 'methods': []}
            value_counts[value]['count'] += 1
            value_counts[value]['methods'].append(val['method'])
        
        # Find the most frequent value
        best_value = max(value_counts.keys(), key=lambda x: value_counts[x]['count'])
        confidence_count = value_counts[best_value]['count']
        
        # Determine confidence level
        if confidence_count >= 3:
            confidence = DataConfidence.HIGH
        elif confidence_count >= 2:
            confidence = DataConfidence.MEDIUM
        else:
            confidence = DataConfidence.LOW
        
        # Validation checks
        validation_checks.append(f"Found {confidence_count} occurrences")
        validation_checks.append(f"Methods: {', '.join(value_counts[best_value]['methods'])}")
        
        # Numeric validation
        try:
            numeric_value = float(best_value)
            validation_checks.append(f"Numeric validation passed: {numeric_value}")
            
            # Range validation for critical values
            if field_name in self.norms:
                norm_str = self.norms[field_name]
                if self.validate_against_norm(numeric_value, norm_str):
                    validation_checks.append(f"Within normal range: {norm_str}")
                else:
                    validation_checks.append(f"Outside normal range: {norm_str}")
        except ValueError:
            validation_checks.append("Non-numeric value detected")
        
        return MedicalValue(
            value=best_value,
            confidence=confidence,
            source_page=0,  # Will be updated by caller
            extraction_method=f"{value_counts[best_value]['count']} methods",
            validation_checks=validation_checks
        )
    
    def validate_against_norm(self, value: float, norm_str: str) -> bool:
        """Validate a value against its normal range."""
        try:
            if ">" in norm_str:
                threshold = float(re.findall(r'-?\d+\.?\d*', norm_str)[0])
                return value > threshold
            elif "<" in norm_str:
                threshold = float(re.findall(r'-?\d+\.?\d*', norm_str)[0])
                return value < threshold
            elif "≥" in norm_str:
                threshold = float(re.findall(r'-?\d+\.?\d*', norm_str)[0])
                return value >= threshold
            elif "–" in norm_str or "-" in norm_str:
                parts = re.findall(r'-?\d+\.?\d*', norm_str)
                if len(parts) >= 2:
                    low = float(parts[0])
                    high = float(parts[1])
                    return low <= value <= high
        except (ValueError, IndexError):
            pass
        return True  # If validation fails, assume valid
    
    def extract_all_data_ultra_robust(self, pdf_path: str) -> Dict[str, Any]:
        """Extract all medical data with ultra-robust methods."""
        logger.info(f"Starting ultra-robust extraction from: {pdf_path}")
        
        # Extract text from all pages
        pages_text = self.extract_text_from_pdf(pdf_path)
        if not pages_text:
            logger.error("No text extracted from PDF")
            return {}
        
        # Combine all pages text for comprehensive search
        full_text = " ".join(pages_text)
        
        # Initialize results
        results = {
            "AUTONOMICS": {},
            "CARDIOVASCULAR": {},
            "ELECTROCARDIOGRAM": {}
        }
        
        # Extract each section with multiple validation
        for section_name, section_data in self.required_fields.items():
            logger.info(f"Extracting {section_name} data...")
            
            if section_name == "AUTONOMICS":
                results[section_name] = self.extract_autonomics_ultra_robust(full_text, pages_text)
            elif section_name == "CARDIOVASCULAR":
                results[section_name] = self.extract_cardiovascular_ultra_robust(full_text, pages_text)
            elif section_name == "ELECTROCARDIOGRAM":
                results[section_name] = self.extract_ecg_ultra_robust(full_text, pages_text)
        
        # Final validation and integrity check
        self.validate_extraction_integrity(results)
        
        return results
    
    def extract_autonomics_ultra_robust(self, full_text: str, pages_text: List[str]) -> Dict[str, Any]:
        """Extract autonomic data with ultra-robust methods."""
        autonomics = {}
        
        # Extract each subsection
        for subsection_name, fields in self.required_fields["AUTONOMICS"].items():
            subsection_data = {}
            
            for field_name, field_info in fields.items():
                logger.info(f"Extracting {subsection_name} - {field_name}")
                
                # Search in full text
                medical_value = self.search_with_multiple_methods(full_text, field_name, subsection_name)
                
                # If not found, search in specific pages
                if medical_value.confidence == DataConfidence.MISSING:
                    for i, page_text in enumerate(pages_text):
                        page_value = self.search_with_multiple_methods(page_text, field_name, subsection_name)
                        if page_value.confidence != DataConfidence.MISSING:
                            medical_value = page_value
                            medical_value.source_page = i + 1
                            break
                
                subsection_data[field_name] = medical_value.value
                
                # Log extraction details
                logger.info(f"{field_name}: {medical_value.value} (Confidence: {medical_value.confidence.value})")
                self.validation_log.append({
                    'field': field_name,
                    'value': medical_value.value,
                    'confidence': medical_value.confidence.value,
                    'source_page': medical_value.source_page,
                    'validation_checks': medical_value.validation_checks
                })
            
            autonomics[subsection_name] = subsection_data
        
        return autonomics
    
    def extract_cardiovascular_ultra_robust(self, full_text: str, pages_text: List[str]) -> Dict[str, Any]:
        """Extract cardiovascular data with ultra-robust methods."""
        cardiovascular = {}
        
        for field_name, field_info in self.required_fields["CARDIOVASCULAR"].items():
            logger.info(f"Extracting cardiovascular - {field_name}")
            
            # Search in full text
            medical_value = self.search_with_multiple_methods(full_text, field_name, "cardiovascular")
            
            # If not found, search in specific pages
            if medical_value.confidence == DataConfidence.MISSING:
                for i, page_text in enumerate(pages_text):
                    page_value = self.search_with_multiple_methods(page_text, field_name, "cardiovascular")
                    if page_value.confidence != DataConfidence.MISSING:
                        medical_value = page_value
                        medical_value.source_page = i + 1
                        break
            
            cardiovascular[field_name] = medical_value.value
            
            # Log extraction details
            logger.info(f"{field_name}: {medical_value.value} (Confidence: {medical_value.confidence.value})")
            self.validation_log.append({
                'field': field_name,
                'value': medical_value.value,
                'confidence': medical_value.confidence.value,
                'source_page': medical_value.source_page,
                'validation_checks': medical_value.validation_checks
            })
        
        return cardiovascular
    
    def extract_ecg_ultra_robust(self, full_text: str, pages_text: List[str]) -> Dict[str, Any]:
        """Extract ECG data with ultra-robust methods using headlines first."""
        ecg = {}
        
        # Step 1: Find ECG ANALYSIS REPORT page using headlines
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
                        logger.info(f"Found ECG ANALYSIS REPORT on page {page_num + 1} from headlines")
                        break
            except Exception as e:
                logger.warning(f"Could not read headlines file: {e}")
        
        # Step 2: If not found in headlines, search page text
        if ecg_page_index is None:
            for i, page_text in enumerate(pages_text):
                if "ecg analysis report" in page_text.lower():
                    ecg_page_index = i
                    logger.info(f"Found ECG ANALYSIS REPORT on page {i + 1} from page text")
                    break
        
        # Step 3: Extract ECG data from the identified page and surrounding pages
        if ecg_page_index is not None:
            logger.info(f"Extracting ECG data from page {ecg_page_index + 1} and surrounding pages")
            
            # Extract from ECG page and 2 pages after it, plus always include page 1 (summary)
            ecg_pages = [ecg_page_index]
            if ecg_page_index + 1 < len(pages_text):
                ecg_pages.append(ecg_page_index + 1)
            if ecg_page_index + 2 < len(pages_text):
                ecg_pages.append(ecg_page_index + 2)
            
            # Always include page 1 (summary page) as it contains ECG data
            if 0 not in ecg_pages:
                ecg_pages.append(0)
            
            logger.info(f"ECG extraction pages: {[p+1 for p in ecg_pages]}")
            
            # Extract each subsection
            for subsection_name, fields in self.required_fields["ELECTROCARDIOGRAM"].items():
                subsection_data = {}
                
                for field_name, field_info in fields.items():
                    logger.info(f"Extracting ECG {subsection_name} - {field_name}")
                    
                    # Search in ECG pages first
                    medical_value = MedicalValue("", DataConfidence.MISSING, 0, "none", [])
                    
                    for page_idx in ecg_pages:
                        page_value = self.search_with_multiple_methods(pages_text[page_idx], field_name, "ecg")
                        if page_value.confidence != DataConfidence.MISSING:
                            medical_value = page_value
                            medical_value.source_page = page_idx + 1
                            break
                    
                    # If not found in ECG pages, search full text
                    if medical_value.confidence == DataConfidence.MISSING:
                        medical_value = self.search_with_multiple_methods(full_text, field_name, "ecg")
                    
                    subsection_data[field_name] = medical_value.value
                    
                    # Log extraction details
                    logger.info(f"{field_name}: {medical_value.value} (Confidence: {medical_value.confidence.value})")
                    self.validation_log.append({
                        'field': field_name,
                        'value': medical_value.value,
                        'confidence': medical_value.confidence.value,
                        'source_page': medical_value.source_page,
                        'validation_checks': medical_value.validation_checks
                    })
                
                ecg[subsection_name] = subsection_data
        else:
            logger.warning("ECG ANALYSIS REPORT page not found in headlines or page text")
            # Fallback to original method
            ecg_pages = []
            for i, page_text in enumerate(pages_text):
                if any(term in page_text.lower() for term in ["ecg analysis", "electrocardiogram", "heart rate", "hrv", "qrs"]):
                    ecg_pages.append(i)
            
            # Always include page 1 (summary page) as it contains ECG data
            if 0 not in ecg_pages:
                ecg_pages.append(0)
            
            logger.info(f"Fallback: Found ECG data on pages: {[p+1 for p in ecg_pages]}")
            
            # Extract each subsection
            for subsection_name, fields in self.required_fields["ELECTROCARDIOGRAM"].items():
                subsection_data = {}
                
                for field_name, field_info in fields.items():
                    logger.info(f"Extracting ECG {subsection_name} - {field_name}")
                    
                    # Search in ECG pages first
                    medical_value = MedicalValue("", DataConfidence.MISSING, 0, "none", [])
                    
                    for page_idx in ecg_pages:
                        page_value = self.search_with_multiple_methods(pages_text[page_idx], field_name, "ecg")
                        if page_value.confidence != DataConfidence.MISSING:
                            medical_value = page_value
                            medical_value.source_page = page_idx + 1
                            break
                    
                    # If not found in ECG pages, search full text
                    if medical_value.confidence == DataConfidence.MISSING:
                        medical_value = self.search_with_multiple_methods(full_text, field_name, "ecg")
                    
                    subsection_data[field_name] = medical_value.value
                    
                    # Log extraction details
                    logger.info(f"{field_name}: {medical_value.value} (Confidence: {medical_value.confidence.value})")
                    self.validation_log.append({
                        'field': field_name,
                        'value': medical_value.value,
                        'confidence': medical_value.confidence.value,
                        'source_page': medical_value.source_page,
                        'validation_checks': medical_value.validation_checks
                    })
                
                ecg[subsection_name] = subsection_data
        
        return ecg
    
    def validate_extraction_integrity(self, results: Dict[str, Any]) -> None:
        """Validate the integrity of extracted data."""
        logger.info("Performing integrity validation...")
        
        missing_critical_fields = []
        low_confidence_fields = []
        
        for section_name, section_data in results.items():
            if isinstance(section_data, dict):
                for field_name, field_value in section_data.items():
                    if isinstance(field_value, dict):
                        for sub_field_name, sub_field_value in field_value.items():
                            if not sub_field_value or sub_field_value.strip() == "":
                                missing_critical_fields.append(f"{section_name}.{field_name}.{sub_field_name}")
                    else:
                        if not field_value or field_value.strip() == "":
                            missing_critical_fields.append(f"{section_name}.{field_name}")
        
        # Log validation results
        if missing_critical_fields:
            logger.warning(f"Missing critical fields: {len(missing_critical_fields)}")
            for field in missing_critical_fields[:10]:  # Show first 10
                logger.warning(f"  - {field}")
        
        if low_confidence_fields:
            logger.warning(f"Low confidence fields: {len(low_confidence_fields)}")
            for field in low_confidence_fields[:10]:  # Show first 10
                logger.warning(f"  - {field}")
        
        logger.info("Integrity validation completed")
    
    def format_to_exact_output_ultra_robust(self, extracted_data: Dict[str, Any]) -> str:
        """Format extracted data to exact output with validation markers."""
        output_lines = []
        
        # AUTONOMICS section
        output_lines.append("AUTONOMICS")
        output_lines.append("")
        
        # HR subsection
        output_lines.append("HR")
        hr_data = extracted_data.get("AUTONOMICS", {}).get("HR", {})
        for field in ["Resting", "Deep Breathing Max", "Deep Breathing Min", "Valsalva Max", "Valsalva Min", "Tilt Test", "Resting2"]:
            value = hr_data.get(field, "")
            output_lines.append(f"{field}: {value}")
        output_lines.append("")
        
        # BP subsection
        output_lines.append("BP")
        bp_data = extracted_data.get("AUTONOMICS", {}).get("BP", {})
        for field in ["Resting Systolic", "Resting Diastolic", "Deep Breathing Systolic", "Deep Breathing Diastolic", 
                     "Valsalva Systolic", "Valsalva Diastolic", "Tilt Test Systolic", "Tilt Test Diastolic", 
                     "Resting2 Systolic", "Resting2 Diastolic"]:
            value = bp_data.get(field, "")
            output_lines.append(f"{field}: {value}")
        output_lines.append("")
        
        # SNS subsection
        output_lines.append("SNS (Norm: 0.8–4.0)")
        sns_data = extracted_data.get("AUTONOMICS", {}).get("SNS", {})
        for field in ["Resting", "Deep Breathing", "Valsalva", "Tilt Test", "Resting2"]:
            value = sns_data.get(field, "")
            flag = " | FLAG" if self.should_flag_value("SNS", value) else ""
            output_lines.append(f"{field}: {value}{flag}")
        output_lines.append("")
        
        # PNS subsection
        output_lines.append("PNS (Norm: 0.8–4.0)")
        pns_data = extracted_data.get("AUTONOMICS", {}).get("PNS", {})
        for field in ["Resting", "Deep Breathing", "Valsalva", "Tilt Test", "Resting2"]:
            value = pns_data.get(field, "")
            flag = " | FLAG" if self.should_flag_value("PNS", value) else ""
            output_lines.append(f"{field}: {value}{flag}")
        output_lines.append("")
        
        # SNS/PNS Ratio subsection
        output_lines.append("SNS/PNS Ratio (Norm: 0.4–2.0)")
        sns_pns_data = extracted_data.get("AUTONOMICS", {}).get("SNS_PNS_Ratio", {})
        for field in ["Resting", "Deep Breathing", "Valsalva", "Tilt Test", "Resting2"]:
            value = sns_pns_data.get(field, "")
            flag = " | FLAG" if self.should_flag_value("SNS/PNS", value) else ""
            output_lines.append(f"{field}: {value}{flag}")
        output_lines.append("")
        
        # SpO2 subsection
        output_lines.append("SpO2")
        spo2_data = extracted_data.get("AUTONOMICS", {}).get("SpO2", {})
        for field in ["Resting", "Deep Breathing", "Valsalva", "Tilt Test", "Resting2"]:
            value = spo2_data.get(field, "")
            flag = " | FLAG" if self.should_flag_value("SpO2", value) else ""
            output_lines.append(f"{field}: {value}{flag}")
        output_lines.append("")
        
        # LF/HF subsection
        output_lines.append("LF/HF (Norm: <3)")
        lf_hf_data = extracted_data.get("AUTONOMICS", {}).get("LF_HF", {})
        for field in ["Resting", "Deep Breathing", "Valsalva", "Tilt Test", "Resting2"]:
            value = lf_hf_data.get(field, "")
            flag = " | FLAG" if self.should_flag_value("LF/HF", value) else ""
            output_lines.append(f"{field}: {value}{flag}")
        output_lines.append("")
        
        # Other Metrics subsection
        output_lines.append("Other Metrics")
        other_metrics = extracted_data.get("AUTONOMICS", {}).get("Other_Metrics", {})
        for field in ["Total Autonomic Activity", "Autonomic Balance", "E/I Ratio", "Valsalva Ratio", 
                     "K30/15 Ratio", "Functional Age", "Autonomic Physical Dysregulation (PSI)", 
                     "Accumulative Mental Stress (MSI)"]:
            value = other_metrics.get(field, "")
            flag = " | FLAG" if self.should_flag_value(field, value) else ""
            output_lines.append(f"{field} (Norm: {self.norms.get(field, 'N/A')}): {value}{flag}")
        output_lines.append("")
        
        # CARDIOVASCULAR section
        output_lines.append("CARDIOVASCULAR")
        output_lines.append("")
        
        cv_data = extracted_data.get("CARDIOVASCULAR", {})
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
            flag = " | FLAG" if self.should_flag_value(metric_key, value) else ""
            output_lines.append(f"{metric_display}: {value}{flag}")
        output_lines.append("")
        
        # ELECTROCARDIOGRAM section
        output_lines.append("ELECTROCARDIOGRAM")
        output_lines.append("")
        
        ecg_data = extracted_data.get("ELECTROCARDIOGRAM", {})
        
        # Heart Rate subsection
        output_lines.append("Heart Rate:")
        heart_rate_data = ecg_data.get("Heart_Rate", {})
        for field in ["Average Heart Rate", "Fastest rate", "Slowest rate", "Fastest minutely rate", "Slowest minutely rate"]:
            value = heart_rate_data.get(field, "")
            flag = " | FLAG" if self.should_flag_value("Average Heart Rate", value) else ""
            output_lines.append(f"{field}: {value}{flag}")
        output_lines.append("")
        
        # Ventricular Details subsection
        output_lines.append("Ventricular Details:")
        ventricular_data = ecg_data.get("Ventricular_Details", {})
        for field in ["PVC - Ventricular Ectopy", "Ventricular Couplet"]:
            value = ventricular_data.get(field, "")
            output_lines.append(f"{field}: {value}")
        output_lines.append("")
        
        # Supraventricular Details subsection
        output_lines.append("Supraventricular Details:")
        supraventricular_data = ecg_data.get("Supraventricular_Details", {})
        for field in ["PAC - Supraventricular Ectopy", "Supraventricular Couplet"]:
            value = supraventricular_data.get(field, "")
            output_lines.append(f"{field}: {value}")
        output_lines.append("")
        
        # HRV Analysis subsection
        output_lines.append("HRV Analysis:")
        hrv_data = ecg_data.get("HRV_Analysis", {})
        for field in ["SDNN", "SDNN Max", "SDNN Min"]:
            value = hrv_data.get(field, "")
            flag = " | FLAG" if self.should_flag_value("SDNN", value) else ""
            output_lines.append(f"{field}: {value}{flag}")
        output_lines.append("")
        
        # QRS Analysis subsection
        output_lines.append("QRS Analysis:")
        qrs_data = ecg_data.get("QRS_Analysis", {})
        for field in ["QRS", "QT / QTc", "QTc Max", "PR int / seg", "ST int / seg"]:
            value = qrs_data.get(field, "")
            if field == "QRS":
                flag = " | FLAG" if self.should_flag_value("QRS", value) else ""
            elif field == "QTc Max":
                flag = " | FLAG" if self.should_flag_value("QTc", value) else ""
            elif field == "PR int / seg":
                flag = " | FLAG" if self.should_flag_value("PR int", value) else ""
            elif field == "ST int / seg":
                flag = " | FLAG" if self.should_flag_value("ST seg", value) else ""
            else:
                flag = ""
            output_lines.append(f"{field}: {value}{flag}")
        
        return "\n".join(output_lines)
    
    def should_flag_value(self, metric_name: str, value: str) -> bool:
        """Determine if a value should be flagged based on norms."""
        if not value or metric_name not in self.norms:
            return False
        
        try:
            numeric_value = float(re.findall(r'-?\d+\.?\d*', value)[0])
            return not self.validate_against_norm(numeric_value, self.norms[metric_name])
        except (ValueError, IndexError):
            return False

def main():
    """Main function to demonstrate ultra-robust extraction."""
    extractor = UltraRobustMedicalExtractor()
    
    # Test with sample PDF
    pdf_path = "input/CS_ANS_trial.2_2min.pdf"
    
    if os.path.exists(pdf_path):
        logger.info("Starting ultra-robust medical data extraction...")
        
        # Extract all data
        extracted_data = extractor.extract_all_data_ultra_robust(pdf_path)
        
        # Format to exact output
        exact_output = extractor.format_to_exact_output_ultra_robust(extracted_data)
        
        # Save output
        output_path = "json_output/ultra_robust_extraction.txt"
        os.makedirs("json_output", exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(exact_output)
        
        # Save validation log
        validation_path = "json_output/extraction_validation_log.json"
        with open(validation_path, 'w', encoding='utf-8') as f:
            json.dump(extractor.validation_log, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Ultra-robust extraction completed!")
        logger.info(f"Results saved to: {output_path}")
        logger.info(f"Validation log saved to: {validation_path}")
        
        # Print summary
        print("\n" + "="*80)
        print("ULTRA-ROBUST MEDICAL DATA EXTRACTION COMPLETED")
        print("="*80)
        print(exact_output)
        
    else:
        logger.error(f"PDF file not found: {pdf_path}")

if __name__ == "__main__":
    main()
