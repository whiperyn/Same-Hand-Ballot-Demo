import os
import json
import base64
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS, cross_origin
from datetime import datetime
import subprocess
import shutil

app = Flask(__name__, static_url_path='/static')
# You can keep this global CORS, but we will also add an after_request handler.
CORS(app, resources={r"/*": {"origins": "*"}})

# Add CORS headers to every response.
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# Folder to save uploaded images.
UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return "Hello, Flask is running!"

@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part in request'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    filename = file.filename  # In production, use secure_filename()
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    return jsonify({'filename': filename}), 200

@app.route('/uploads/<filename>')
@cross_origin()
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/save-boxes', methods=['POST'])
def save_boxes():
    data = request.get_json()
    boxes = data.get('boxes')
    picName = data.get('picName')
    input_data = {
        'picName': picName,
        'boxes': boxes
    }
    with open('input_data.json', 'w') as f:
        json.dump(input_data, f)
    
    # Full paths
    path_a = os.path.join(app.root_path, 'segmented_A.json')
    path_b = os.path.join(app.root_path, 'segmented_B.json')

    a_exists = os.path.exists(path_a)
    b_exists = os.path.exists(path_b)

    # Delete based on the rule
    if a_exists and b_exists:
        os.remove(path_a)
        os.remove(path_b)
        print("Removed both segmented_A.json and segmented_B.json")
    elif not a_exists and b_exists:
        os.remove(path_b)
        print("Removed segmented_B.json because A was not present")

    try:
        subprocess.Popen(["python", "segment_anything_box.py"])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'success': True}), 200

@app.route('/api/save-points', methods=['POST'])
def save_points():
    data = request.get_json()
    points = data.get('points')
    picName = data.get('picName')

    input_data = {
        'picName': picName,
        'boxes': [],
        'points': points
    }

    with open('input_data.json', 'w') as f:
        json.dump(input_data, f)
    
     # Full paths
    path_a = os.path.join(app.root_path, 'segmented_A.json')
    path_b = os.path.join(app.root_path, 'segmented_B.json')

    a_exists = os.path.exists(path_a)
    b_exists = os.path.exists(path_b)

    # Delete based on the rule
    if a_exists and b_exists:
        os.remove(path_a)
        os.remove(path_b)
        print("Removed both segmented_A.json and segmented_B.json")
    elif not a_exists and b_exists:
        os.remove(path_b)
        print("Removed segmented_B.json because A was not present")

    try:
        subprocess.Popen(["python", "segment_anything_dot.py"])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'success': True}), 200

@app.route('/api/generated-imageA', methods=['GET'])
def get_generated_imageA():
    folder_path = os.path.join(app.root_path, 'static', 'A', 'segmented_box')
    json_file_path = os.path.join(app.root_path, 'segmented_A.json')

    if not os.path.exists(json_file_path):
        return jsonify({'images': []})  # JSON not yet created by segmentation

    try:
        files = [f for f in os.listdir(folder_path)
                 if f.startswith('segmented_') and f.endswith('.png')]
    except Exception as e:
        print(f"Error listing segmented images: {e}")
        files = []

    return jsonify({'images': files})

@app.route('/api/generated-imageB', methods=['GET'])
def get_generated_imageB():
    folder_path = os.path.join(app.root_path, 'static', 'B', 'segmented_box')
    json_file_path = os.path.join(app.root_path, 'segmented_B.json')
    
    if not os.path.exists(json_file_path):
        return jsonify({'images': []})  # JSON not yet created by segmentation

    try:
        files = [f for f in os.listdir(folder_path)
                 if f.startswith('segmented_') and f.endswith('.png')]
    except Exception as e:
        print(f"Error listing segmented images: {e}")
        files = []

    return jsonify({'images': files})

@app.route('/api/check-segmentation-status', methods=['GET'])
def check_segmentation_status():
    json_a_path = os.path.join(app.root_path, 'segmented_A.json')
    json_b_path = os.path.join(app.root_path, 'segmented_B.json')
    return jsonify({
        'segmentedA': os.path.exists(json_a_path),
        'segmentedB': os.path.exists(json_b_path)
    }), 200


@app.route('/api/result', methods=['GET'])
def get_result():
    try:
        with open('result.json', 'r') as f:
            data = json.load(f)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calculate-similarity', methods=['POST'])
def calculate_similarity():
    try:
        process = subprocess.run(["python", "model.py"], capture_output=True, text=True, check=True)
        print("Model stdout:", process.stdout)
        print("Model stderr:", process.stderr)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'success': True}), 200

@app.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    folders_to_clear = [
        #os.path.join(app.root_path, 'static', 'segmented_images'),
        os.path.join(app.root_path, 'uploads'),
        os.path.join(app.root_path, 'static', 'A'),
        os.path.join(app.root_path, 'static', 'B')
    ]

    for folder in folders_to_clear:
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")
    
    for json_file in ['segmented_A.json', 'segmented_B.json']:
        json_path = os.path.join(app.root_path, json_file)
        if os.path.exists(json_path):
            try:
                os.remove(json_path)
                print(f"Removed {json_file}")
            except Exception as e:
                print(f"Error removing {json_file}: {e}")

    similarity_data = {
        "similarity1": -1,
        "similarity2": -1,
        "similarity3": -1,
        "overall_similarity": -1
    }

    with open("result.json", "w") as f:
        json.dump(similarity_data, f, indent=4)

    with open("input_data.json", "w") as f:
        f.write("{}")

    return jsonify({'success': True}), 200

@app.route('/api/export-combined', methods=['POST', 'OPTIONS'])
def export_combined():
    if request.method == "OPTIONS":
        response = jsonify({"success": True})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response, 200

    data = request.get_json()
    combined_data_url = data.get('combinedImage')
    if not combined_data_url:
        return jsonify({"error": "No combined image provided"}), 400
    try:
        header, encoded = combined_data_url.split(',', 1)
        image_data = base64.b64decode(encoded)
    except Exception as e:
        return jsonify({"error": "Invalid image data", "details": str(e)}), 400
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"combined_{timestamp}.png"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    with open(file_path, 'wb') as f:
        f.write(image_data)
    input_file = os.path.join(app.root_path, "input_data.json")
    try:
        with open(input_file, "r") as f:
            input_data = json.load(f)
    except Exception:
        input_data = {}
    input_data["combinedImageName"] = filename
    with open(input_file, "w") as f:
        json.dump(input_data, f)
    response = jsonify({"success": True, "filename": filename})
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response, 200

@app.route('/api/get-combined-image', methods=['GET'])
def get_combined_image():
    input_file = os.path.join(app.root_path, "input_data.json")
    combined_name = None
    if os.path.exists(input_file):
        try:
            with open(input_file, "r") as f:
                data = json.load(f)
            combined_name = data.get("combinedImageName")
        except Exception as e:
            print("Error reading input_data.json:", e)
    if combined_name:
        file_path = os.path.join(app.root_path, "uploads", combined_name)
        if not os.path.exists(file_path):
            combined_name = None
    return jsonify({"combinedImageName": combined_name}), 200

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=8000)
