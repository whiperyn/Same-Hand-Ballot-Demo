import json
import numpy as np
import matplotlib.pyplot as plt
import cv2
import torch
from transformers import SamModel, SamProcessor
from PIL import Image, ImageOps
import os
import time
import requests

def get_and_increment_alias(alias_file_path):
    # If file doesn't exist, start from alias 1
    if not os.path.exists(alias_file_path):
        with open(alias_file_path, 'w') as f:
            f.write('1')
        return 'alias1'
    
    with open(alias_file_path, 'r+') as f:
        content = f.read().strip()
        try:
            number = int(content)
        except ValueError:
            number = 1  # fallback if file content is invalid
        
        alias = f'alias{number}'
        
        # Move pointer to beginning and update the number
        f.seek(0)
        f.write(str(number + 1))
        f.truncate()
        
        return alias



def show_mask(mask, ax, random_color=False):
    if random_color:
        color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
    else:
        color = np.array([30/255, 144/255, 255/255, 0.6])
    h, w = mask.shape[-2:]
    mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
    ax.imshow(mask_image)

def show_box(box, ax):
    x0, y0 = box[0], box[1]
    w, h = box[2] - box[0], box[3] - box[1]
    ax.add_patch(plt.Rectangle((x0, y0), w, h, edgecolor='green', facecolor=(0,0,0,0), lw=2))

def show_boxes_on_image(raw_image, boxes):
    plt.figure(figsize=(10,10))
    plt.imshow(raw_image)
    for box in boxes:
        show_box(box, plt.gca())
    plt.axis('on')
    plt.show()

def show_points_on_image(raw_image, input_points, input_labels=None):
    plt.figure(figsize=(10,10))
    plt.imshow(raw_image)
    input_points = np.array(input_points)
    if input_labels is None:
        labels = np.ones_like(input_points[:, 0])
    else:
        labels = np.array(input_labels)
    show_points(input_points, labels, plt.gca())
    plt.axis('on')
    plt.show()

def show_points_and_boxes_on_image(raw_image, boxes, input_points, input_labels=None):
    plt.figure(figsize=(10,10))
    plt.imshow(raw_image)
    input_points = np.array(input_points)
    if input_labels is None:
        labels = np.ones_like(input_points[:, 0])
    else:
        labels = np.array(input_labels)
    show_points(input_points, labels, plt.gca())
    for box in boxes:
        show_box(box, plt.gca())
    plt.axis('on')
    plt.show()

def show_points(coords, labels, ax, marker_size=375):
    pos_points = coords[labels==1]
    neg_points = coords[labels==0]
    ax.scatter(pos_points[:, 0], pos_points[:, 1], color='green', marker='*', s=marker_size, edgecolor='white', linewidth=1.25)
    ax.scatter(neg_points[:, 0], neg_points[:, 1], color='red', marker='*', s=marker_size, edgecolor='white', linewidth=1.25)

def show_masks_on_image(raw_image, masks, scores):
    if len(masks.shape) == 4:
        masks = masks.squeeze()
    if scores.shape[0] == 1:
        scores = scores.squeeze()

    nb_predictions = scores.shape[-1]
    fig, axes = plt.subplots(1, nb_predictions, figsize=(15, 15))

    for i, (mask, score) in enumerate(zip(masks, scores)):
        mask = mask.cpu().detach()
        axes[i].imshow(np.array(raw_image))
        show_mask(mask, axes[i])
        axes[i].title.set_text(f"Mask {i+1}, Score: {score.item():.3f}")
        axes[i].axis("off")
    plt.show()

def save_irregular_segmentation(original_image_np, mask, filename, threshold=0.5):
    # Ensure mask is 2D.
    if mask.ndim > 2:
        mask = mask[0]
    mask_bin = (mask > threshold).astype(np.uint8) * 255

    # Compute bounding box: np.where returns (row, col) indices.
    coords = np.column_stack(np.where(mask_bin > 0))
    if coords.size == 0:
        print(f"No segmented region found for {filename}.")
        return
    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0) + 1  # +1 to include the last pixel

    # Crop original image and mask.
    cropped_image = original_image_np[y_min:y_max, x_min:x_max]
    cropped_mask = mask_bin[y_min:y_max, x_min:x_max]

    # Apply mask to the cropped image
    # Ensure cropped_image is RGB
    if cropped_image.ndim == 2:
        cropped_image = cv2.cvtColor(cropped_image, cv2.COLOR_GRAY2RGB)

    if cropped_image.shape[-1] == 3:
        # Create a binary mask with 0/1
        binary_mask = (cropped_mask > 0).astype(np.uint8)
        # Invert to get background mask
        background_mask = 1 - binary_mask

        # Set background to white (255)
        for i in range(3):
            cropped_image[:, :, i] = (
                cropped_image[:, :, i] * binary_mask + 255 * background_mask
            )

    # Convert to BGR for OpenCV
    bgr_image = cv2.cvtColor(cropped_image, cv2.COLOR_RGB2BGR)
    # filename = filename.replace(".png", ".jpg")  # Save as JPG

    cv2.imwrite(filename, bgr_image)
    print(f"Irregular cropped segmentation saved to {filename}")
    
def save_bounding_box_cropped_segmentation(original_image_np, mask, filename, threshold=0.5):
    if mask.ndim > 2:
        mask = mask[0]
    mask_bin = (mask > threshold).astype(np.uint8) * 255
    # Get coordinates where mask is nonzero.
    coords = np.column_stack(np.where(mask_bin > 0))
    if coords.size == 0:
        print(f"No segmented region found for {filename}.")
        return
    # np.where returns (row, col) indices which correspond to (y, x)
    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0) + 1  # +1 to include the last pixel
    cropped_image = original_image_np[y_min:y_max, x_min:x_max]
    cropped_bgr = cv2.cvtColor(cropped_image, cv2.COLOR_RGB2BGR)
    # filename = filename.replace(".png", ".jpg")  # Save as JPG

    cv2.imwrite(filename, cropped_bgr)
    print(f"Bounding box cropped segmentation saved to {filename}")

def prepare_output_directories(folder):
    '''
    If static/A/ is empty → saves both versions under A/segmented_*.
    If static/A/ is not empty but B/ is → uses B/segmented_*.
    If both have files → clears both, uses A/segmented_*.
    '''
    def is_dir_empty(path):
        return not os.path.exists(path) or not os.listdir(path)

    def clear_directory(path):
        if os.path.exists(path):
            for root, dirs, files in os.walk(path, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in dirs:
                    os.rmdir(os.path.join(root, dir))

    base = f"static/{folder}"
    if base == "static/Query":
        dir_irregular = os.path.join(base, "segmented_irregular")
        dir_box = os.path.join(base, "segmented_box")
    elif base == "static/Pool":
        dir_irregular = os.path.join(base, "new_segmented_irregular")
        dir_box = os.path.join(base, "new_segmented_box")
    else:
        raise ValueError(f"Unrecognized base path: {base}")


    os.makedirs(dir_irregular, exist_ok=True)
    os.makedirs(dir_box, exist_ok=True)
    return dir_irregular, dir_box


start_time = time.time()
print("Running Box Segmentation")
# Load input parameters from JSON
with open('input_data.json', 'r') as f:
    data = json.load(f)

picName = data.get('picName')
boxes = data.get('boxes')
folder_base = data.get('input')
print("Segmenting for picture:", picName)
print("Boxes:", boxes)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Device:", device)
model = SamModel.from_pretrained("facebook/sam-vit-huge").to(device)
processor = SamProcessor.from_pretrained("facebook/sam-vit-huge")

# Load the image file (for example, from uploads directory).
raw_image = Image.open(f"uploads/{picName}").convert("RGB")
#raw_image = Image.open("ballot.jpg").convert("RGB")
# (Optional) fix orientation if needed:
raw_image = ImageOps.exif_transpose(raw_image)
print("Loaded image size:", raw_image.size)

# Compute image embeddings.
inputs = processor(raw_image, return_tensors="pt").to(device)
image_embeddings = model.get_image_embeddings(inputs["pixel_values"])

# Prepare input_boxes. (Your JSON 'boxes' should follow the expected format.)
input_boxes = [boxes]  # boxes should be in [x0, y0, x1, y1] format.
# (Optional visualization: show_boxes_on_image(raw_image, input_boxes[0]))

# Process inputs using boxes.
inputs = processor(raw_image, input_boxes=input_boxes, return_tensors="pt").to(device)
print("Input boxes shape:", inputs["input_boxes"].shape)

# Remove pixel values since we provide precomputed embeddings.
inputs.pop("pixel_values", None)
inputs.update({"image_embeddings": image_embeddings})

with torch.no_grad():
    # Setting multimask_output=False returns one mask candidate per box prompt.
    outputs = model(**inputs, multimask_output=False)

# Post-process the predicted masks so that they match the original image size.
masks = processor.image_processor.post_process_masks(
    outputs.pred_masks.cpu(),
    inputs["original_sizes"].cpu(),
    inputs["reshaped_input_sizes"].cpu()
)
scores = outputs.iou_scores  # (if you need to inspect scores)

# (Optional) Visualize the masks:
# show_masks_on_image(raw_image, masks[0], scores)

# Convert the PIL image to a NumPy array (RGB order).
raw_image_np = np.array(raw_image)

# Here, masks is a list; for boxes, masks[0] contains the candidate mask.
mask_group = masks[0]
num_candidates = mask_group.shape[0]
print(f"Found {num_candidates} candidate mask(es) for the given boxes.")

# For each candidate mask, save Version 2 (irregular) and Version 3 (bounding box cropped).
# get the correct folder to save the images
output_dir_irregular, output_dir_box = prepare_output_directories(folder_base)
alias_file = 'alias.txt'
alias = get_and_increment_alias(alias_file)
for idx in range(num_candidates):
    candidate_mask = mask_group[idx]
    candidate_mask = candidate_mask.cpu().detach().numpy()
    candidate_mask = np.squeeze(candidate_mask)
    
    # Version 2: Full-size irregular segmentation (only segmented parts opaque).
    filename_irreg = os.path.join(output_dir_irregular, f"segmented_irregular_{alias}_{idx}.png")
    raw_image_np_origin = raw_image_np.copy()  # Ensure we don't modify the original image
    save_irregular_segmentation(raw_image_np, candidate_mask, filename_irreg, threshold=0.5)
    
    # Version 3: Bounding box cropped segmentation.
    filename_bbox = os.path.join(output_dir_box, f"segmented_bounding_box_{alias}_{idx}.png")
    save_bounding_box_cropped_segmentation(raw_image_np_origin, candidate_mask, filename_bbox, threshold=0.5)

# Write a generated image json file
# Determine which folder we saved to
used_dir = "A" if "Query" in output_dir_irregular else "B"
json_output_path = f"segmented_{used_dir}.json"

# Build relative file paths for JSON
irregular_files = sorted([
    os.path.join(output_dir_irregular, f) for f in os.listdir(output_dir_irregular)
    if f.endswith(".png")
])
box_files = sorted([
    os.path.join(output_dir_box, f) for f in os.listdir(output_dir_box)
    if f.endswith(".png")
])

# Normalize paths to use forward slashes and strip leading ./ or absolute base path
def clean_path(p):
    return os.path.normpath(p).replace("\\", "/").split("static/")[-1]
json_data = {
    "irregular": [f"static/{clean_path(p)}" for p in irregular_files],
    "bounding_box": [f"static/{clean_path(p)}" for p in box_files]
}

# Save JSON
with open(json_output_path, "w") as f:
    json.dump(json_data, f, indent=4)

print(f"Saved segmentation list to {json_output_path}")


end_time = time.time()
print(f"Execution time: {end_time - start_time:.2f} seconds")
