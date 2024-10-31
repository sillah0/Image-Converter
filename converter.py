from flask import Flask, request, send_file, render_template_string
from PIL import Image
import io
import zipfile
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# HTML template with enhanced CSS and dropdown for format selection
html_template = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Format Converter</title>
    <style>
        body {
            background-color: #f8f1f6;
            font-family: Arial, sans-serif;
            color: #333;
            text-align: center;
        }
        h2 {
            color: #e91e63;
            font-size: 2em;
        }
        .upload-container {
            max-width: 500px;
            margin: 20px auto;
            padding: 20px;
            background-color: #ffffff;
            border-radius: 10px;
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
        }
        .upload-container input[type="file"],
        .upload-container select,
        .upload-container button {
            margin-top: 20px;
            padding: 10px;
            width: 100%;
            background-color: #ffffff;
            border: 2px solid #e91e63;
            border-radius: 5px;
            font-size: 1em;
            cursor: pointer;
        }
        .upload-container button {
            background-color: #e91e63;
            color: #fff;
            border: none;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        .upload-container button:hover {
            background-color: #c2185b;
        }
    </style>
</head>
<body>
    <h2>Convert Images to Selected Format</h2>
    <div class="upload-container">
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="files" accept=".jpg,.jpeg,.png,.bmp,.tif,.tiff,.gif,.raw" multiple required>
            <select name="output_format" required>
                <option value="webp">WebP</option>
                <option value="jpeg">JPEG</option>
                <option value="png">PNG</option>
                <option value="bmp">BMP</option>
                <option value="tiff">TIFF</option>
                <option value="gif">GIF</option>
            </select>
            <button type="submit">Convert</button>
        </form>
    </div>
</body>
</html>
"""

def convert_to_format(file, output_format):
    """Convert an image file to the specified format in memory."""
    img = Image.open(file.stream).convert("RGB")
    img_io = io.BytesIO()
    img.save(img_io, format=output_format.upper())
    img_io.seek(0)
    return img_io.getvalue(), file.filename

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('files')
        output_format = request.form.get('output_format').lower()
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.gif', '.raw'}

        if not files or not any(file.filename.lower().endswith(tuple(valid_extensions)) for file in files):
            return "Please upload at least one valid image file."

        # Create an in-memory ZIP file
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            # Process files in parallel
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(convert_to_format, file, output_format) for file in files if file.filename.lower().endswith(tuple(valid_extensions))]
                for future in futures:
                    img_data, original_filename = future.result()
                    # Add each converted image to the ZIP file with selected extension
                    zip_file.writestr(f"{original_filename.rsplit('.', 1)[0]}.{output_format}", img_data)

        zip_io.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        zip_filename = f"converted_images_{timestamp}.zip"

        # Send the ZIP file as a download
        return send_file(zip_io, mimetype="application/zip", download_name=zip_filename)

    return render_template_string(html_template)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
