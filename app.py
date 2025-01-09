from flask import Flask, request, jsonify, send_file
from pymongo import MongoClient
import gridfs
from pdf2image import convert_from_bytes
from io import BytesIO
import os
import zipfile

def create_zip_file(image_paths, zip_file_name):
    """Create a zip file containing all images."""
    with zipfile.ZipFile(zip_file_name, 'w') as zipf:
        for image_path in image_paths:
            zipf.write(image_path, os.path.basename(image_path))

app = Flask(__name__)
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client['jaswanth']
fs = gridfs.GridFS(db)

@app.route('/', methods=['GET'])
def convert_fax():
    serial_number = request.args.get('serial_number', type=int)
    if not serial_number:
        return jsonify({"error": "Serial number is required"}), 400

    print(f"Received serial_number: {serial_number}")  # Log the serial_number for debugging

    pdf_data = fetch_pdf_by_serial_number(serial_number)

    if not pdf_data:
        print(f"Fax not found for serial_number: {serial_number}")  # Log the error if fax is not found
        return jsonify({"error": "Fax not found"}), 404

    image_files = pdf_to_images(pdf_data)
    if not image_files:
        return jsonify({"error": "Error converting PDF to images"}), 500

    zip_file_name = 'images.zip'
    create_zip_file(image_files, zip_file_name)

    return send_file(zip_file_name, mimetype='application/zip', as_attachment=True)

def fetch_pdf_by_serial_number(serial_number):
    metadata = db['pdf_metadata'].find_one({"serial_number": serial_number})
    if not metadata:
        return None
    file_id = metadata['file_id']
    pdf_data = fs.get(file_id).read()
    return pdf_data

def pdf_to_images(pdf_data, output_folder='output_images'):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    images = convert_from_bytes(pdf_data, 300)
    image_paths = []
    for i, image in enumerate(images):
        image_filename = os.path.join(output_folder, f"page_{i + 1}.png")
        image.save(image_filename, 'PNG')
        image_paths.append(image_filename)
    return image_paths

if __name__ == "__main__":
    app.run(debug=True)
