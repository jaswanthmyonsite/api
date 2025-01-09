from flask import Flask, request, jsonify, send_file
from pymongo import MongoClient
import gridfs
import os

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

    # Send the PDF file directly as the response
    return send_file(
        BytesIO(pdf_data),  # Convert the PDF data to a BytesIO object
        mimetype='application/pdf',  # Set the MIME type for PDF
        as_attachment=True,  # Force download
        download_name=f'fax_{serial_number}.pdf'  # Name the file based on the serial number
    )

def fetch_pdf_by_serial_number(serial_number):
    metadata = db['pdf_metadata'].find_one({"serial_number": serial_number})
    if not metadata:
        return None
    file_id = metadata['file_id']
    pdf_data = fs.get(file_id).read()
    return pdf_data

if __name__ == "__main__":
    app.run(debug=True)
