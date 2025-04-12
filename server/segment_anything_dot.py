import numpy as np
import matplotlib.pyplot as plt
import cv2
import torch
from transformers import SamModel, SamProcessor
from PIL import Image, ImageOps
import requests
import os
import time
import json

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


def save_segmented_in_original(raw_image_np, mask, filename, threshold=0.5):
    """
    Given a raw RGB image (NumPy array) and a predicted mask (values in [0,1]),
    produce and save an RGBA image where the alpha channel is determined by thresholding the mask.
    
    Parameters:
      raw_image_np: Original image as a NumPy array (shape: H x W x 3, in RGB).
      mask: 2D NumPy array (shape: H x W) of mask predictions.
      filename: Path to save the RGBA PNG image.
      threshold: Threshold (default 0.5) to convert mask to binary.
    """
    # Create a boolean mask from the predicted mask.
    mask_bool = mask > threshold
    # Generate an alpha channel: segmented areas become opaque, background transparent.
    alpha_channel = (mask_bool.astype(np.uint8)) * 255
    # Combine the original image (RGB) with the alpha channel to get an RGBA image.
    rgba_image = np.dstack([raw_image_np, alpha_channel])
    # OpenCV expects BGRA order for 4-channel images when saving.
    rgba_bgra = cv2.cvtColor(rgba_image, cv2.COLOR_RGBA2BGRA)
    success = cv2.imwrite(filename, rgba_bgra)
    print(f"Segmented image saved to {filename}: {success}")

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
    # Create alpha channel for the cropped mask.
    alpha_channel = (cropped_mask > 0).astype(np.uint8) * 255
    rgba_cropped = np.dstack([cropped_image, alpha_channel])
    rgba_bgra = cv2.cvtColor(rgba_cropped, cv2.COLOR_RGBA2BGRA)
    cv2.imwrite(filename, rgba_bgra)
    print(f"Irregular Cropped segmentation saved to {filename}")

def save_bounding_box_cropped_segmentation(original_image_np, mask, filename, threshold=0.5):
    if mask.ndim > 2:
        mask = mask[0]
    mask_bin = (mask > threshold).astype(np.uint8) * 255
    coords = np.column_stack(np.where(mask_bin > 0))
    if coords.size == 0:
        print(f"No segmented region found for {filename}.")
        return
    # Note: np.where returns (row, col) which corresponds to (y, x)
    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0) + 1  # +1 so last pixel is included
    # Crop the original image (which is in RGB)
    cropped_image = original_image_np[y_min:y_max, x_min:x_max]
    # Convert cropped image from RGB to BGR for saving with OpenCV.
    cropped_bgr = cv2.cvtColor(cropped_image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(filename, cropped_bgr)
    print(f"Bounding box cropped segmentation saved to {filename}")

def prepare_output_directories():
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

    base_a = "static/A"
    base_b = "static/B"

    if is_dir_empty(base_a):
        dir_irregular = os.path.join(base_a, "segmented_irregular")
        dir_box = os.path.join(base_a, "segmented_box")
    elif is_dir_empty(base_b):
        dir_irregular = os.path.join(base_b, "segmented_irregular")
        dir_box = os.path.join(base_b, "segmented_box")
    else:
        clear_directory(base_a)
        clear_directory(base_b)
        dir_irregular = os.path.join(base_a, "segmented_irregular")
        dir_box = os.path.join(base_a, "segmented_box")

    os.makedirs(dir_irregular, exist_ok=True)
    os.makedirs(dir_box, exist_ok=True)
    return dir_irregular, dir_box

start_time = time.time()
print("Running Dots Segmentation")
with open('input_data.json', 'r') as f:
    data = json.load(f)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = SamModel.from_pretrained("facebook/sam-vit-huge").to(device)
processor = SamProcessor.from_pretrained("facebook/sam-vit-huge")

picName = data.get('picName')
points = data.get('points')
print("Segmenting for picture:", picName)

# Load your image ("ballot.jpg") and fix orientation via EXIF if needed.
pil_image = Image.open("uploads/ballot.jpg")
pil_image = ImageOps.exif_transpose(pil_image).convert("RGB")
print("PIL image size (width, height):", pil_image.size)

# Convert PIL image to a NumPy array in RGB.
original_image_np = np.array(pil_image)

# Compute image embeddings (only need to do this once per image).
inputs = processor(pil_image, return_tensors="pt").to(device)
image_embeddings = model.get_image_embeddings(inputs["pixel_values"])

# Define segmentation input points (SAM expects points in (x, y) order).
input_points = [points]

# Prepare inputs for SAM using the point prompts.
inputs = processor(pil_image, input_points=input_points, return_tensors="pt").to(device)
inputs.pop("pixel_values", None)  # remove raw image pixels since we supply embeddings
inputs.update({"image_embeddings": image_embeddings})

with torch.no_grad():
    outputs = model(**inputs)

# Post-process the predicted masks to match the original image size.
masks = processor.image_processor.post_process_masks(
    outputs.pred_masks.cpu(),
    inputs["original_sizes"].cpu(),
    inputs["reshaped_input_sizes"].cpu()
)
# Here, masks[0] contains the candidate masks (shape e.g. (N, H, W) or (N, 3, H, W)).
mask_group = masks[0]
num_candidates = mask_group.shape[0]
print(f"Found {num_candidates} candidate mask(es) for the given input points.")

# Loop over each candidate mask and save three versions.
# get the correct folder to save the images
output_dir_irregular, output_dir_box = prepare_output_directories()
for idx in range(num_candidates):
    candidate_mask = mask_group[idx]
    candidate_mask = candidate_mask.cpu().detach().numpy()
    candidate_mask = np.squeeze(candidate_mask)
    
    # the first one is to extract the segmentation in the original image (exported size = original image size)
    # it has some error but because it's not used, so nvm
    filename1 = f"segmentation_full_size/segmented_overlay_{idx}.png"
    #save_segmented_in_original(original_image_np, candidate_mask, filename1, threshold=0.5)
    
    # Version 2: segmented part only, irregular shape
    filename2 = os.path.join(output_dir_irregular, f"segmented_irregular_{idx}.png")
    save_irregular_segmentation(original_image_np, candidate_mask, filename2, threshold=0.5)
    
    # Version 3: segmented part with minimum bounding box
    filename3 = os.path.join(output_dir_box, f"segmented_bounding_box_{idx}.png")
    save_bounding_box_cropped_segmentation(original_image_np, candidate_mask, filename3, threshold=0.5)


end_time = time.time()
print(f"Execution time: {end_time - start_time:.2f} seconds")