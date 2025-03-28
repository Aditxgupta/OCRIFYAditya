# OCRIFY

OCRIFY is a web application that converts images and PDFs into markdown format using Mistral AI's OCR capabilities. It provides a user-friendly interface for uploading documents and receiving markdown output that can be easily downloaded or copied.

## Features

- Support for multiple image formats (PNG, JPG, JPEG, WEBP, GIF) and PDFs
- Real-time OCR processing using Mistral AI's latest OCR model
- Automatic conversion of detected images to base64-encoded data URIs
- Clean and responsive web interface
- Download markdown results or copy to clipboard
- Preview of converted content in HTML format

## Prerequisites

- Python 3.x
- Mistral AI API key
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/OCRIFY.git
cd OCRIFY
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your Mistral AI API key:
```
MISTRAL_API_KEY=your_api_key_here
```

## Usage

1. Start the Flask application:
```bash
python app.py
```

2. Open your web browser and navigate to `http://localhost:5000`

3. Upload an image or PDF file through the web interface

4. View the converted markdown content and either:
   - Download the markdown file
   - Copy the content to your clipboard
   - Preview the rendered HTML version

## File Size Limits

- Maximum file size: 16 MB
- Supported image formats: PNG, JPG, JPEG, WEBP, GIF
- Supported document formats: PDF

## Technical Details

- Built with Flask web framework
- Uses Mistral AI's OCR API for text extraction
- Implements secure file handling and validation
- Stores results temporarily in memory (resets on server restart)
- Includes comprehensive error handling and user feedback

## Security Considerations

- File upload validation and sanitization
- Secure filename handling
- Temporary file storage in memory
- Environment variable for API key management

## Development

The application is structured as follows:
- `app.py`: Main Flask application file
- `templates/`: HTML templates for the web interface
- `static/`: Static assets (CSS, JavaScript, images)
- `.env`: Environment variables (not included in repository)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Mistral AI for providing the OCR capabilities
- Flask web framework
- All contributors and users of the project 