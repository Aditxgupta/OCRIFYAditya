import os
import base64
import uuid
import io
from pathlib import Path
from flask import (
    Flask, request, render_template, redirect, url_for,
    send_file, flash, session
)
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from mistralai import Mistral, OCRResponse
from PIL import Image, UnidentifiedImageError
import markdown # <-- ADD THIS LINE HERE

# --- Configuration ---
load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
UPLOAD_FOLDER = 'uploads' # Optional: if you need to temporarily save files
ALLOWED_EXTENSIONS_IMG = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
ALLOWED_EXTENSIONS_DOC = {'pdf'}
ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS_IMG.union(ALLOWED_EXTENSIONS_DOC)
MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16 MB limit

# In-memory storage for markdown results (simple demo; consider alternatives for production)
markdown_storage = {}

# --- Flask App Setup ---
app = Flask(__name__,
            template_folder=Path(__file__).parent / 'templates',
            static_folder=Path(__file__).parent / 'static')
app.config['SECRET_KEY'] = os.urandom(24) # Needed for flash messages and session
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER # Uncomment if saving files locally
# Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True) # Uncomment if saving

# --- Mistral Client ---
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY environment variable not set.")
# --- Use Mistral() as per documentation ---
client = Mistral(api_key=MISTRAL_API_KEY)

# --- Helper Functions ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext in ALLOWED_EXTENSIONS_IMG:
        return 'image'
    elif ext in ALLOWED_EXTENSIONS_DOC:
        return 'pdf'
    return None

# Function adapted from Mistral AI cookbook (Modified slightly for robustness)
# --- Modified get_combined_markdown ---
def get_combined_markdown(ocr_response: OCRResponse) -> str:
    markdowns: list[str] = []
    print("DEBUG (get_combined_markdown): Starting...") # ADDED
    if not ocr_response or not ocr_response.pages:
        print("DEBUG (get_combined_markdown): OCR response or pages empty.") # ADDED
        return ""

    for i, page in enumerate(ocr_response.pages):
        print(f"\n--- DEBUG (get_combined_markdown) Processing Page {i} ---") # ADDED
        image_data = {}
        if page.images:
            print(f"DEBUG (get_combined_markdown): Found {len(page.images)} images on page {i}.") # ADDED
            for img_idx, img in enumerate(page.images): # ADDED index
                print(f"DEBUG (get_combined_markdown): Checking image {img_idx}: ID='{img.id}', HasBase64={bool(img.image_base64)}") # ADDED
                if img.id and img.image_base64:
                    image_data[img.id] = img.image_base64
                    print(f"DEBUG (get_combined_markdown): Added to image_data: ID='{img.id}', Base64Len={len(img.image_base64)}") # ADDED
                #else:
                    #print(f"DEBUG (get_combined_markdown): Skipping image {img_idx} on page {i}.") # Keep if needed
        else:
            print(f"DEBUG (get_combined_markdown): No images found on page {i}.") # ADDED

        page_markdown = page.markdown or ""
        print(f"DEBUG (get_combined_markdown): Raw Page Markdown (Page {i}, len {len(page_markdown)}):\n'''\n{page_markdown[:500]}...\n'''") # ADDED, more context

        # Call the replacement function
        processed_page_markdown = replace_images_in_markdown(page_markdown, image_data)
        print(f"DEBUG (get_combined_markdown): Processed Page Markdown (Page {i}, len {len(processed_page_markdown)}):\n'''\n{processed_page_markdown[:500]}...\n'''") # ADDED
        markdowns.append(processed_page_markdown)
        print(f"--- End DEBUG Page {i} ---") # ADDED

    final_markdown = "\n\n".join(markdowns)
    print(f"\nDEBUG (get_combined_markdown): Final Combined Markdown Length: {len(final_markdown)}") # ADDED
    return final_markdown


# --- Modified replace_images_in_markdown ---
def replace_images_in_markdown(markdown_str: str, images_dict: dict) -> str:
    print(f"DEBUG (replace_images): Called with markdown len {len(markdown_str)}, images_dict keys: {list(images_dict.keys())}") # ADDED
    if not markdown_str or not images_dict:
        return markdown_str # Return original if no markdown or no images to replace

    processed_markdown = markdown_str # Start with the original string
    replacements_done = 0 # ADDED: Counter

    for img_id, base64_str in images_dict.items():
        print(f"DEBUG (replace_images): Processing img_id='{img_id}'...") # ADDED
        if not img_id or not base64_str:
            print(f"DEBUG (replace_images): Skipping img_id='{img_id}' due to missing id or base64.") # ADDED
            continue

        full_base64_uri = None # Initialize
        try:
            # Quick check if already a data URI (unlikely for OCR output, but safe)
            if base64_str.startswith('data:image'):
                 full_base64_uri = base64_str
                 print("DEBUG (replace_images): Base64 already a data URI.") # ADDED
            else:
                 # Attempt to decode and create data URI
                 img_bytes = base64.b64decode(base64_str)
                 img = Image.open(io.BytesIO(img_bytes))
                 img_format = img.format.lower() if img.format else 'jpeg'
                 mime_type = f"image/{img_format}"
                 full_base64_uri = f"data:{mime_type};base64,{base64_str}"
                 print(f"DEBUG (replace_images): Generated data URI: data:{mime_type};base64,... (len {len(full_base64_uri)})") # ADDED
        except (base64.binascii.Error, UnidentifiedImageError, ValueError, Exception) as e:
            print(f"DEBUG (replace_images): ERROR processing base64 for '{img_id}': {e}. Skipping replacement.") # ADDED
            continue # Skip replacement for this image if processing fails

        if full_base64_uri:
             # Construct the placeholder string EXACTLY as it appears in the markdown
             placeholder = f"![{img_id}]({img_id})"
             print(f"DEBUG (replace_images): Attempting to replace '{placeholder}'") # ADDED

             # Check if placeholder exists before replacing
             if placeholder in processed_markdown:
                 processed_markdown = processed_markdown.replace(placeholder, f"![{img_id}]({full_base64_uri})")
                 replacements_done += 1 # Increment counter
                 print(f"DEBUG (replace_images): Replacement successful for '{img_id}'.") # ADDED
             else:
                 print(f"DEBUG (replace_images): Placeholder '{placeholder}' NOT FOUND in current markdown.") # ADDED

    print(f"DEBUG (replace_images): Finished. Total replacements made: {replacements_done}") # ADDED
    return processed_markdown


# --- Routes ---
@app.route('/')
def index():
    # Clear previous results if any when returning home
    session.pop('file_id', None)
    session.pop('filename', None)
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_type = get_file_type(filename)
        file_bytes = file.read() # Read file content into memory

        try:
            ocr_response = None
            if file_type == 'pdf':
                # 1. Upload PDF using client.files.upload as per docs
                uploaded_file = client.files.upload(
                    file=(filename, file_bytes), # Pass as tuple (filename, file_bytes)
                    purpose="ocr",
                )
                # 2. Get a temporary signed URL
                # Added expiry=60 for slightly longer validity if needed
                signed_url_response = client.files.get_signed_url(file_id=uploaded_file.id, expiry=60)

                # 3. Process with OCR using the dictionary format for 'document'
                ocr_response = client.ocr.process(
                    model="mistral-ocr-latest",
                    document={
                        "type": "document_url",
                        "document_url": signed_url_response.url, # Use the URL from response
                    },
                    include_image_base64=True # Include images found in PDF
                )
                # Optionally delete the file from Mistral service after processing
                try:
                     client.files.delete(file_id=uploaded_file.id)
                except Exception as delete_err:
                     app.logger.warning(f"Could not delete temporary file {uploaded_file.id}: {delete_err}")


            elif file_type == 'image':
                # Encode image as base64 data URL
                try:
                    # Verify it's a valid image and get format
                    img = Image.open(io.BytesIO(file_bytes))
                    img_format = img.format.lower() if img.format else 'jpeg'
                    if img_format not in ['jpeg', 'png', 'webp', 'gif']:
                        img_format = 'jpeg' # Default
                    encoded = base64.b64encode(file_bytes).decode('utf-8') # Ensure utf-8 decoding
                    # Construct data URI as per documentation example
                    base64_data_url = f"data:image/{img_format};base64,{encoded}"

                    # Process image with OCR using the dictionary format for 'document'
                    ocr_response = client.ocr.process(
                        model="mistral-ocr-latest",
                        document={
                            "type": "image_url",
                            "image_url": base64_data_url
                        },
                        include_image_base64=True # include_image_base64 is not typically needed here
                    )
                except UnidentifiedImageError:
                    flash(f'Cannot identify image file: {filename}. It might be corrupted or an unsupported format.', 'error')
                    return redirect(url_for('index'))
                except Exception as img_err:
                    app.logger.error(f"Image processing error: {img_err}")
                    flash(f'Error processing image file: {img_err}', 'error')
                    return redirect(url_for('index'))

            else:
                flash('Invalid file type determined internally.', 'error')
                return redirect(url_for('index'))

            # Extract markdown
            if ocr_response:
                markdown_content = get_combined_markdown(ocr_response)

                # Store result temporarily for download/copy
                file_id = str(uuid.uuid4())
                markdown_storage[file_id] = markdown_content
                session['file_id'] = file_id # Store ID in session for results page
                session['filename'] = filename # Store original filename

                return redirect(url_for('show_results'))
            else:
                 flash('OCR processing failed or returned an empty result.', 'error')
                 return redirect(url_for('index'))

        # Catch specific Mistral API errors if possible, otherwise general Exception
        except Exception as e:
            # Consider adding more specific error catching from mistralai.exceptions if needed
            app.logger.error(f"API Error or processing error: {e}", exc_info=True) # Log traceback
            flash(f'An error occurred during processing: {e}', 'error')
            return redirect(url_for('index'))

    else:
        flash(f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}', 'error')
        return redirect(url_for('index'))


@app.route('/results')
def show_results():
    file_id = session.get('file_id')
    filename = session.get('filename', 'result')
    if not file_id or file_id not in markdown_storage:
        flash('No result found or session expired. Please upload again.', 'info')
        return redirect(url_for('index'))

    # 1. Print the raw markdown retrieved from storage
    raw_markdown_content = markdown_storage.get(file_id, "")
    print("-" * 20)
    print("DEBUG: Raw Markdown from Storage:")
    print(f"Length: {len(raw_markdown_content)}")
    # Print first 500 chars for preview, handle potential None/empty
    print(raw_markdown_content[:500] if raw_markdown_content else "[EMPTY]")
    print("-" * 20)

    # Convert raw markdown to HTML
    html_content_for_display = markdown.markdown(raw_markdown_content, extensions=['extra'])

    # 2. Print the HTML generated by the markdown library
    print("-" * 20)
    print("DEBUG: HTML Content for Display:")
    print(f"Length: {len(html_content_for_display)}")
    # Print first 500 chars for preview
    print(html_content_for_display[:500] if html_content_for_display else "[EMPTY]")
    print("-" * 20)


    download_filename = Path(filename).stem + ".md"

    # Pass BOTH raw markdown and HTML to the template
    return render_template('results.html',
                           html_content_for_display=html_content_for_display,
                           raw_markdown_for_copy=raw_markdown_content,
                           file_id=file_id,
                           download_filename=download_filename)

@app.route('/download/<file_id>')
def download_markdown(file_id):
    if file_id in markdown_storage:
        markdown_content = markdown_storage[file_id]
        original_filename = session.get('filename', 'ocr_result')
        download_filename = Path(original_filename).stem + ".md"

        mem_file = io.BytesIO()
        mem_file.write(markdown_content.encode('utf-8'))
        mem_file.seek(0)

        return send_file(
            mem_file,
            as_attachment=True,
            download_name=download_filename,
            mimetype='text/markdown'
        )
    else:
        flash('File not found or result expired. Please upload again.', 'error')
        return redirect(url_for('index'))

# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True) # Turn off debug in production
