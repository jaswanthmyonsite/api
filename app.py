

from flask import Flask, request, jsonify, send_file
from pymongo import MongoClient
import gridfs
from pdf2image import convert_from_bytes
from io import BytesIO
import os

app = Flask(__name__)
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client['fax']
fs = gridfs.GridFS(db)

@app.route('/', methods=['GET'])
def convert_fax():
    serial_number = request.args.get('serial_number', type=int)
    if not serial_number:
        return jsonify({"error": "Serial number is required"}), 400

    pdf_data = fetch_pdf_by_serial_number(serial_number)
    if not pdf_data:
        return jsonify({"error": "Fax not found"}), 404

    image_files = pdf_to_images(pdf_data)
    if not image_files:
        return jsonify({"error": "Error converting PDF to images"}), 500

    return send_file(image_files[0], mimetype='image/png')

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

