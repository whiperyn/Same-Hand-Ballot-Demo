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

@app.route('/api/save-boxesA', methods=['POST'])
def save_boxesA():
    data = request.get_json()
    boxes = data.get('boxes')
    picName = data.get('picName')
    input_data = {
        'picName': picName,
        'boxes': boxes,
        'input': 'Query'
    }
    with open('input_data.json', 'w') as f:
        json.dump(input_data, f)
    
    # Full paths
    path_a = os.path.join(app.root_path, 'segmented_A.json')
    path_b = os.path.join(app.root_path, 'segmented_B.json')

    a_exists = os.path.exists(path_a)
    b_exists = os.path.exists(path_b)

    # Delete based on the rule
    if a_exists:
        os.remove(path_a)

    try:
        subprocess.Popen(["python", "segment_anything_box.py"])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'success': True}), 200

@app.route('/api/save-boxes', methods=['POST'])
def save_boxes():
    data = request.get_json()
    boxes = data.get('boxes')
    picName = data.get('picName')
    input_data = {
        'picName': picName,
        'boxes': boxes,
        'input': 'A'
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


@app.route('/api/save-boxesB', methods=['POST'])
def save_boxesB():
    data = request.get_json()
    boxes = data.get('boxes')
    picName = data.get('picName')
    input_data = {
        'picName': picName,
        'boxes': boxes,
        'input': 'Pool'
    }
    with open('input_data.json', 'w') as f:
        json.dump(input_data, f)
    
    # Full paths
   
    path_b = os.path.join(app.root_path, 'segmented_B.json')


    b_exists = os.path.exists(path_b)

    # Delete based on the rule
    if b_exists:
        os.remove(path_b)

    try:
        subprocess.Popen(["python", "segment_anything_box.py"])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'success': True}), 200

@app.route('/api/save-pointsA', methods=['POST'])
def save_pointsA():
    data = request.get_json()
    points = data.get('points')
    picName = data.get('picName')

    input_data = {
        'picName': picName,
        'boxes': [],
        'points': points, 
        'input': 'Query'
    }

    with open('input_data.json', 'w') as f:
        json.dump(input_data, f)
    
     # Full paths
    path_a = os.path.join(app.root_path, 'segmented_A.json')
    path_b = os.path.join(app.root_path, 'segmented_B.json')

    a_exists = os.path.exists(path_a)
    b_exists = os.path.exists(path_b)

    # Delete based on the rule
    if a_exists:
        os.remove(path_a)

    try:
        subprocess.Popen(["python", "segment_anything_dot.py"])
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
        'points': points, 
        'input': 'A'
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

@app.route('/api/save-pointsB', methods=['POST'])
def save_pointsB():
    data = request.get_json()
    points = data.get('points')
    picName = data.get('picName')

    input_data = {
        'picName': picName,
        'boxes': [],
        'points': points, 
        'input': 'Pool'
    }

    with open('input_data.json', 'w') as f:
        json.dump(input_data, f)
    
     # Full paths
    path_a = os.path.join(app.root_path, 'segmented_A.json')
    path_b = os.path.join(app.root_path, 'segmented_B.json')

    a_exists = os.path.exists(path_a)
    b_exists = os.path.exists(path_b)

    # Delete based on the rule
    if b_exists:
        os.remove(path_b)


    try:
        subprocess.Popen(["python", "segment_anything_dot.py"])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'success': True}), 200

@app.route('/api/generated-imageA', methods=['GET'])
def get_generated_imageA():
    folder_path = os.path.join(app.root_path, 'static', 'Query', 'segmented_irregular')
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
    folder_path = os.path.join(app.root_path, 'static', 'Pool', 'new_segmented_irregular')
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
        #process = subprocess.run(["python", "model.py"], capture_output=True, text=True, check=True)
        #print("Model stdout:", process.stdout)
        #print("Model stderr:", process.stderr)
        print("hello world")
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'success': True}), 200

@app.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    folders_to_clear = [
        #os.path.join(app.root_path, 'static', 'segmented_images'),
        os.path.join(app.root_path, 'uploads'),
        os.path.join(app.root_path, 'static', 'Query'),
        os.path.join(app.root_path, 'static', 'Pool', 'new_segmented_box'),
        os.path.join(app.root_path, 'static', 'Pool', 'new_segmented_irregular'),
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

    '''with open("result.json", "w") as f:
        json.dump(similarity_data, f, indent=4)'''

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


@app.route('/api/heatmap-data', methods=['GET'])
def get_heatmap_data():
    # Load the result.json file.
    with open('result.json', 'r') as f:
        data = json.load(f)
    
    # The data is expected to have a structure like:
    # {
    #    "K_0": [
    #        { "Pool": "K_1", "Score": 0.9108, "Logit": 13.5651, ... },
    #        { "Pool": "I_1", "Score": 0.0484, "Logit": 10.6296, ... },
    #         ...
    #    ],
    #    "K_1": [ ... ],
    #    ...
    # }
    
    # 1. Extract query keys from the top-level dictionary.
    query_keys = list(data.keys())
    
    # 2. Build the set of all pool keys by combining:
    #    - the query keys themselves (since a query key may also appear as a pool key), and
    #    - all the "Pool" fields from the data.
    pool_keys_set = set(query_keys)
    for query in data:
        for item in data[query]:
            pool_keys_set.add(item["Pool"])
    
    # 3. Order the pool keys such that the ones that are query keys appear first.
    #    First, sort the query keys (you can choose to keep the original order if you like),
    #    then append the remainder of the pool keys sorted.
    sorted_query_keys = sorted(query_keys)
    remaining_pools = sorted(list(pool_keys_set - set(query_keys)))
    pool_keys = sorted_query_keys + remaining_pools

    # 4. (Optional) Also sort the query keys for consistency
    query_keys = sorted_query_keys

    # 5. Initialize the matrix: for each pool (row) and query (column)
    #    If pool equals query (diagonal cells) we set it to None,
    #    otherwise we initialize as None (to be updated later)
    matrix = {}
    for pool in pool_keys:
        matrix[pool] = {}
        for query in query_keys:
            if pool == query:
                matrix[pool][query] = None   # Diagonal cells (will be grey on frontend)
            else:
                matrix[pool][query] = None

    # 6. Fill in the matrix with data from the JSON.
    for query in query_keys:
        for item in data[query]:
            pool = item["Pool"]
            # Only update non-diagonal cells.
            if pool != query:
                matrix[pool][query] = {
                    "score": item.get("Score"),
                    "logit": item.get("Logit")
                }
    
    # 7. Build the data structure expected by the frontend.
    #    Each row represents a pool key and includes an array of column objects,
    #    each containing the corresponding query key and its cell data.
    heatmap_data = []
    for pool in pool_keys:
        row = {"poolKey": pool, "columns": []}
        for query in query_keys:
            row["columns"].append({
                "queryKey": query,
                "score": matrix[pool][query]  # This is either an object or None (for diagonal)
            })
        heatmap_data.append(row)
    
    return jsonify({
        "queryKeys": query_keys,
        "poolKeys": pool_keys,
        "data": heatmap_data
    })


@app.route('/api/ranking-data', methods=['GET'])
def get_ranking_data():
    # Load the result JSON file.
    with open('result.json', 'r') as f:
        data = json.load(f)
    
    # Assume each top-level key is a query key.
    # Optionally sort the query keys.
    query_keys = list(data.keys())
    query_keys.sort()
    
    # Build the ranking data structure.
    # For each query key, we return only the top 5 pool results.
    ranking_data = {}
    for query in query_keys:
        # The original file already has the pool items sorted.
        ranking_data[query] = data[query][:5]
    
    return jsonify({
        "queryKeys": query_keys,
        "rankingData": ranking_data
    })


@app.route('/api/copy-irregular', methods=['POST'])
@cross_origin()
def copy_irregular_files():
    source_dirs = ['static/Query/segmented_irregular/', 'static/Pool/new_segmented_irregular/']
    dest_dir = 'static/Pool/segmented_irregular/'

    # Ensure destination directory exists
    os.makedirs(dest_dir, exist_ok=True)

    # Copy all files
    for source_dir in source_dirs:
        for filename in os.listdir(source_dir):
            src_path = os.path.join(source_dir, filename)
            dst_path = os.path.join(dest_dir, filename)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dst_path)

    return jsonify({"status": "success", "message": "Files copied."})

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=8000)
