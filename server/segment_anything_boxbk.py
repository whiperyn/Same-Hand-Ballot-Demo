import json
import numpy as np
import matplotlib.pyplot as plt
import cv2
import torch
from transformers import SamModel, SamProcessor
from PIL import Image
import requests
import cv2
import time

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


start_time = time.time()
with open('input_data.json', 'r') as f:
    data = json.load(f)

picName = data.get('picName')
boxes = data.get('boxes')
print("Segmenting for picture:", picName)
print("Boxes:", boxes)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(device)
model = SamModel.from_pretrained("facebook/sam-vit-huge").to(device)
processor = SamProcessor.from_pretrained("facebook/sam-vit-huge")

#image = cv2.imread("../ballot.jpg")
'''rotated_image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
cv2.imwrite("rotated_image.png", rotated_image)'''
raw_image = Image.open(f"uploads/{picName}").convert("RGB")

#plt.imshow(raw_image)

inputs = processor(raw_image, return_tensors="pt").to(device)
image_embeddings = model.get_image_embeddings(inputs["pixel_values"])

# Load the boxes from the saved file
'''with open('boxes.json', 'r') as f:
    boxes = json.load(f)'''

#print("Boxes:", boxes)
#print(type(boxes))
input_boxes = [boxes]
#show_boxes_on_image(raw_image, input_boxes[0])

inputs = processor(raw_image, input_boxes=input_boxes, return_tensors="pt").to(device)
inputs["input_boxes"].shape

inputs.pop("pixel_values", None)
inputs.update({"image_embeddings": image_embeddings})

with torch.no_grad():
    outputs = model(**inputs, multimask_output=False)

masks = processor.image_processor.post_process_masks(outputs.pred_masks.cpu(), inputs["original_sizes"].cpu(), inputs["reshaped_input_sizes"].cpu())
scores = outputs.iou_scores

scores.shape

#show_masks_on_image(raw_image, masks[0], scores)



raw_image_np = np.array(raw_image)  # shape (H, W, 3)

# iterate over each element in the masks list
# each mask might multiple masks
for idx, mask in enumerate(masks):
    # convert the mask tensor to a numpy array
    mask_np = mask.detach().cpu().numpy()
    print(f"Original mask {idx} shape: {mask_np.shape}")

    # check if the mask has more than one element along the first dimension
    if mask_np.shape[0] > 1:
        # there are multiple masks in this element
        for sub_idx in range(mask_np.shape[0]):
            submask = mask_np[sub_idx]
            # now submask should have shape (3, H, W)
            if submask.ndim == 3:
                # if more than one channel exists, assume channels are identical and take the first channel
                if submask.shape[0] > 1:
                    submask = submask[0]
                else:
                    submask = np.squeeze(submask, axis=0)
            # at this point, submask should be 2D: shape (H, W)
            mask_bool = submask > 0.5  # threshold the mask
            alpha_channel = (mask_bool.astype(np.uint8) * 255)  # create alpha channel

            # combine the original image with the alpha channel to form an RGBA image
            rgba_image = np.dstack([raw_image_np, alpha_channel])
            '''plt.figure()                  # Create a new figure
            plt.imshow(rgba_image)
            plt.title(f"Segmented Image {idx}")
            plt.show()'''
            # save the image
            filename = f"static/segmented_images/segmented_{idx}_{sub_idx}.png"
            success = cv2.imwrite(filename, rgba_image)
            print(f"Saved {filename}: {success}")
    else:
        # only one mask is present; remove the extra dimension
        mask_np = np.squeeze(mask_np, axis=0)
        if mask_np.ndim == 3:
            if mask_np.shape[0] > 1:
                mask_np = mask_np[0]
            else:
                mask_np = np.squeeze(mask_np, axis=0)
        mask_bool = mask_np > 0.5
        alpha_channel = (mask_bool.astype(np.uint8) * 255)
        rgba_image = np.dstack([raw_image_np, alpha_channel])
        filename = f"static/segmented_images/segmented_{idx}.png"
        success = cv2.imwrite(filename, rgba_image)
        print(f"Saved {filename}: {success}")

end_time = time.time()
print(f"Execution time: {end_time - start_time:.2f} seconds")
