# PDF Medical Data Extraction API

A comprehensive FastAPI application that extracts and formats medical data from PDF files using advanced OCR and AI processing.

## Features

- **PDF Upload**: Upload PDF files for processing
- **Image Cropping**: Extract specific regions from PDF pages
- **Heading Extraction**: Extract headings using OCR
- **Table Extraction**: Extract tables with advanced OCR processing
- **Enhanced Formatting**: Format data into structured medical reports
- **Web Interface**: Beautiful HTML interface for easy use
- **API Documentation**: Interactive API docs with Swagger UI

## Architecture

The application integrates four main modules in the correct processing order:

1. **crop.py** - Crops specific regions from PDF pages
2. **heading.py** - Extracts headings using OCR
3. **ocr.py** - Extracts tables and structured data
4. **enhanced_formatter.py** - Formats data into medical report structure

## Installation

### Prerequisites

- Python 3.8+
- Tesseract OCR installed on your system

### System Dependencies

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### Python Dependencies

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Starting the Server

```bash
python app.py
```

The server will start on `http://localhost:8000`

### Web Interface

Open your browser and go to `http://localhost:8000` to access the web interface.

### API Endpoints

#### Core Endpoints

- `GET /` - Web interface
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

#### Processing Endpoints

- `POST /upload-pdf` - Upload a PDF file
- `POST /process-crop` - Crop images from PDF with custom coordinates
- `POST /process-headings` - Extract headings from cropped images
- `POST /process-ocr` - Extract tables using OCR
- `POST /process-enhanced` - Apply enhanced formatting
- `POST /process-complete` - Run complete pipeline with dynamic coordinates

#### Configuration Endpoints

- `POST /configure-crop-definitions` - Configure custom crop definitions
- `GET /default-coordinates` - Get default coordinate configurations

#### Document Conversion Endpoints

- `POST /convert-to-document` - Convert JSON medical data to formatted documents (HTML, Markdown, Text)

#### Utility Endpoints

- `GET /download/{file_type}` - Download processed files
- `POST /cleanup` - Clean up temporary files

### Example Usage

#### Using the Web Interface

1. Open `http://localhost:8000`
2. Upload a PDF file
3. Optionally specify a specific page
4. Optionally add custom crop definitions for advanced processing
5. Click "Process Complete Pipeline"
6. Download results when processing is complete

#### Using the API Directly

```python
import requests

# Upload PDF and process
with open('your_file.pdf', 'rb') as f:
    files = {'file': ('your_file.pdf', f, 'application/pdf')}
    data = {'specific_page': '1'}  # Optional: specify page number
    response = requests.post('http://localhost:8000/process-complete', files=files, data=data)

result = response.json()
print(result)

# Convert to document
doc_data = {
    'json_file_path': 'json_out/enhanced_extraction.json',
    'output_format': 'html',  # or 'markdown', 'text'
    'patient_name': 'John Doe',
    'output_dir': 'documents'
}
doc_response = requests.post('http://localhost:8000/convert-to-document', data=doc_data)
print(doc_response.json())
```

### Testing

Run the test script to verify all endpoints:

```bash
python test_api.py
```

## Configuration

### Crop Coordinates

The application uses **fixed crop coordinates** for basic PDF processing, but supports **dynamic crop definitions** for advanced OCR processing:

#### Fixed Basic Crop Coordinates
The application uses fixed coordinates `175,0,550,60` for basic PDF cropping. These coordinates extract the top portion of each page and **cannot be changed** through the interface.

- **Fixed coordinates**: `175,0,550,60`
- **Purpose**: Extract headings from the top portion of PDF pages
- **Note**: These coordinates are optimized for the medical report format

#### Advanced Crop Definitions (Optional)
For advanced OCR processing, you can define custom crop regions:

```json
{
  "ocr3": [
    {
      "name": "Autonomic_Balance_Metrics",
      "coords": [0, 380, 611, 425],
      "parser": "process_unified_format"
    }
  ],
  "ocr2": [
    {
      "name": "Cardiovascular_Metrics", 
      "coords": [0, 482, 611, 685],
      "parser": "process_cardiovascular_tables"
    }
  ]
}
```

#### Coordinate Validation
The API automatically validates coordinates to ensure:
- Exactly 4 numeric values
- x0 < x1 and y0 < y1
- All values are non-negative

### Tesseract Path

If Tesseract is not in the default path, update the path in `src/heading.py`:

```python
TESSERACT_PATH = r'/path/to/your/tesseract'
```

## Output Structure

The enhanced formatter produces structured data in three main sections:

### AUTONOMICS
- Heart Rate (HR) data
- Blood Pressure (BP) data
- SNS/PNS metrics
- Autonomic balance indicators

### CARDIOVASCULAR
- Cardiovascular metrics
- Blood pressure indicators
- Heart rate variability

### ELECTROCARDIOGRAM
- ECG analysis
- Heart rate data
- QRS analysis
- Ventricular/Supraventricular details

### Summary of Flagged Findings
- List of all metrics that fall outside normal ranges

## Document Conversion

The application can convert the extracted JSON data into formatted documents:

### Supported Formats

#### HTML Document
- Professional medical report layout
- Color-coded flagged values
- Responsive design
- Print-friendly styling

#### Markdown Document
- Clean, readable format
- Table-based data presentation
- Easy to convert to other formats
- Version control friendly

#### Text Document
- Plain text format
- Simple structure
- Easy to read and process
- Compatible with all systems

#### Word Document (DOCX)
- Professional Microsoft Word format
- Headings: Size 12 font
- Regular text: Size 10 font
- FLAG text: Bold formatting
- Table-based data presentation
- Print-ready layout

### Usage

#### Web Interface
1. Process a PDF file
2. In the results section, enter patient name
3. Select document format (HTML, Markdown, Text)
4. Click "Generate Document"
5. Download the generated document

#### API Usage
```python
# Convert to DOCX document
response = requests.post('/convert-to-document', data={
    'json_file_path': 'json_out/enhanced_extraction.json',
    'output_format': 'docx',
    'patient_name': 'John Doe',
    'output_dir': 'documents'
})
```

## File Structure

```
ANS/
├── app.py                 # FastAPI application
├── requirements.txt       # Python dependencies
├── test_api.py           # API test script
├── static/
│   └── index.html        # Web interface
├── src/
│   ├── crop.py           # PDF cropping module
│   ├── heading.py        # Heading extraction module
│   ├── ocr.py            # OCR processing module
│   ├── enhanced_formatter.py  # Data formatting module
│   └── doc_util.py       # Document conversion utility
├── input/                # Input PDF files
├── cropped_output/       # Cropped images
├── json_output/          # JSON output files
├── json_out/             # Additional output files
└── documents/            # Generated document files
```

## Troubleshooting

### Common Issues

1. **Tesseract not found**: Ensure Tesseract is installed and the path is correct
2. **PDF processing errors**: Check that the PDF is not corrupted and is readable
3. **Crop coordinates**: Adjust crop coordinates if no data is extracted
4. **Memory issues**: For large PDFs, process specific pages instead of all pages

### Debug Mode

Enable debug logging by setting the log level in `app.py`:

```python
uvicorn.run("app:app", log_level="debug")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please create an issue in the repository or contact the development team.
