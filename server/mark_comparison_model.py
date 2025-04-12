


import os
import random
from PIL import Image
import copy
import json
import pickle
print("loading tensorflow...")
import tensorflow as tf
from tensorflow import keras
from keras.layers import *
from keras.layers import Concatenate
from tensorflow.keras import Model, Input
from tensorflow.keras.applications import DenseNet121
from tensorflow.keras.layers import Dense
import keras.backend as K
import numpy as np
import time

start_time = time.time()
with open('input_data.json', 'r') as f:
    data = json.load(f)
print("Checking GPU...")

tf.test.is_gpu_available(
    cuda_only=False, min_cuda_compute_capability=None
)
print("Num GPUs Available: ", len(tf.config.list_physical_devices('GPU')))


def get_similarity_scores(model, X1, X2, temperature=0.07):
    """
    Compute similarity probabilities for a set of image pairs.
    """
    emb_a, emb_b = model((X1, X2), training=False)
    norm_a = tf.math.l2_normalize(emb_a, axis=1)
    norm_b = tf.math.l2_normalize(emb_b, axis=1)
    cosine_sim = tf.reduce_sum(norm_a * norm_b, axis=1, keepdims=True)
    logits = cosine_sim / temperature
    probs = tf.sigmoid(logits)
    return probs.numpy().ravel()  # flatten to 1D array


import numpy as np
import tensorflow as tf
from PIL import Image





# -------------------------------
# Custom CLIP Model with DenseNet121 Encoder
# -------------------------------
class CLIPModel(Model):
    def __init__(self, input_shape, embedding_dim=64, temperature=0.07, trainable_encoder=False):
        """
        Initialize the CLIP model.
        
        Parameters:
          - input_shape: Shape of the input image (e.g., (224, 224, 3))
          - embedding_dim: Dimension of the output embeddings.
          - temperature: Temperature scaling factor for the logits.
          - trainable_encoder: Whether to fine-tune the DenseNet121 weights.
        """
        super(CLIPModel, self).__init__()
        self.temperature = temperature
        self.encoder = self.create_encoder(input_shape, embedding_dim, trainable_encoder)
        
    def create_encoder(self, input_shape, embedding_dim, trainable):
        """
        Create a DenseNet121-based encoder that outputs embeddings.
        """
        base_model = DenseNet121(include_top=False, 
                                 weights='imagenet', 
                                 input_shape=input_shape, 
                                 pooling='avg')
        base_model.trainable = trainable  # Freeze or fine-tune as needed
        inputs = Input(shape=input_shape)
        x = base_model(inputs)
        embedding = Dense(embedding_dim, activation=None)(x)
        return Model(inputs, embedding, name="DenseNet121_encoder")
    
    def call(self, inputs, training=False):
        """
        Forward pass: compute embeddings for both branches.
        
        inputs: a tuple/list of two tensors (image_a, image_b)
        """
        image_a, image_b = inputs
        emb_a = self.encoder(image_a)
        emb_b = self.encoder(image_b)
        return emb_a, emb_b
    
    def compute_loss(self, emb_a, emb_b):
        """
        Compute the CLIP loss using batch contrastive learning.
        
        1. Normalize the embeddings.
        2. Compute the cosine similarity matrix (scaled by temperature).
        3. Create labels such that the i-th image in branch A should match the i-th image in branch B.
        4. Compute cross-entropy loss in both directions.
        """
        # Normalize embeddings to unit length.
        norm_a = tf.math.l2_normalize(emb_a, axis=1)
        norm_b = tf.math.l2_normalize(emb_b, axis=1)
        
        # Compute similarity logits: shape (batch_size, batch_size)
        logits = tf.matmul(norm_a, norm_b, transpose_b=True) / self.temperature
        
        # Ground truth: matching pair should be at the diagonal.
        batch_size = tf.shape(emb_a)[0]
        labels = tf.range(batch_size)
        
        # Cross-entropy loss in both directions.
        loss_a2b = tf.keras.losses.sparse_categorical_crossentropy(labels, logits, from_logits=True)
        loss_b2a = tf.keras.losses.sparse_categorical_crossentropy(labels, tf.transpose(logits), from_logits=True)
        loss = tf.reduce_mean(loss_a2b + loss_b2a) / 2.0
        return loss

class CLIPModel(Model):
    def __init__(self, input_shape, embedding_dim=64, temperature=0.07, trainable_encoder=False):
        super(CLIPModel, self).__init__()
        self.temperature = temperature
        self.encoder = self.create_encoder(input_shape, embedding_dim, trainable_encoder)
    
    def create_encoder(self, input_shape, embedding_dim, trainable):
        base_model = DenseNet121(include_top=False, 
                                 weights='imagenet', 
                                 input_shape=input_shape, 
                                 pooling='avg')
        base_model.trainable = trainable
        inputs = Input(shape=input_shape)
        x = base_model(inputs)
        embedding = Dense(embedding_dim, activation=None)(x)
        return Model(inputs, embedding, name="DenseNet121_encoder")
    
    def call(self, inputs, training=False):
        image_a, image_b = inputs
        emb_a = self.encoder(image_a)
        emb_b = self.encoder(image_b)
        return emb_a, emb_b
    
    def compute_loss_and_accuracy(self, emb_a, emb_b):
        # Normalize embeddings.
        norm_a = tf.math.l2_normalize(emb_a, axis=1)
        norm_b = tf.math.l2_normalize(emb_b, axis=1)
        
        # Compute similarity logits (cosine similarity scaled by temperature).
        logits = tf.matmul(norm_a, norm_b, transpose_b=True) / self.temperature
        
        # Ground truth: the matching pair for sample i is at index i.
        batch_size = tf.shape(emb_a)[0]
        labels = tf.range(batch_size)
        
        # CLIP-style loss: compute cross entropy loss in both directions.
        loss_a2b = tf.keras.losses.sparse_categorical_crossentropy(labels, logits, from_logits=True)
        loss_b2a = tf.keras.losses.sparse_categorical_crossentropy(labels, tf.transpose(logits), from_logits=True)
        clip_loss = tf.reduce_mean(loss_a2b + loss_b2a) / 2.0
        
        # --- Additional Contrastive Loss ---
        # Compute the probability for the matching pair from the diagonal of logits.
        diag_logits = tf.linalg.diag_part(logits)  # shape (batch_size,)
        diag_prob = tf.sigmoid(diag_logits)
        # For positive pairs, we want the probability to be close to 1.

        # Compute binary cross entropy loss for positive pairs.
        bce_loss = tf.keras.losses.binary_crossentropy(tf.ones_like(diag_prob), diag_prob)
        contrastive_loss = tf.reduce_mean(bce_loss)

        # Combine the losses with a balancing weight alpha.
        alpha = 1.0  # Adjust this weight as needed.
        total_loss = clip_loss + alpha * contrastive_loss
        
        # --- Accuracy Computation ---
        preds_a2b = tf.argmax(logits, axis=1, output_type=tf.int32)
        preds_b2a = tf.argmax(tf.transpose(logits), axis=1, output_type=tf.int32)
        acc_a2b = tf.reduce_mean(tf.cast(tf.equal(preds_a2b, labels), tf.float32))
        acc_b2a = tf.reduce_mean(tf.cast(tf.equal(preds_b2a, labels), tf.float32))
        accuracy = (acc_a2b + acc_b2a) / 2.0
        
        return total_loss, accuracy

    def train_step(self, data):
        (image_a, image_b), _ = data
        with tf.GradientTape() as tape:
            emb_a, emb_b = self((image_a, image_b), training=True)
            loss, accuracy = self.compute_loss_and_accuracy(emb_a, emb_b)
        gradients = tape.gradient(loss, self.trainable_variables)
        self.optimizer.apply_gradients(zip(gradients, self.trainable_variables))
        return {"loss": loss, "accuracy": accuracy}

    def test_step(self, data):
        (image_a, image_b), _ = data
        emb_a, emb_b = self((image_a, image_b), training=False)
        loss, accuracy = self.compute_loss_and_accuracy(emb_a, emb_b)
        return {"loss": loss, "accuracy": accuracy}
    

# -------------------------------
# Model Building, Compilation, and Training
# -------------------------------
# Use an input size of 224x224 as required by DenseNet121.
input_shape = (51, 51, 3)
temperature = 0.07
embedding_dim = 64
batch_size = 1
optimal_threshold = 0.9961812496185303

print("Building model...")
# Create the model. Set trainable_encoder=True if you wish to fine-tune DenseNet121.
clip_model = CLIPModel(input_shape, embedding_dim, temperature, trainable_encoder=True)

clip_model.load_weights('model_weight.h5')

print("loading data...")

def preprocess_single_image(image_path):
    """
    Applies the same preprocessing as used in form_data.
    """
    # Load image and convert to RGB
    image = Image.open(image_path).convert('RGB')
    
    # Convert to NumPy array and float32
    image = np.asarray(image).astype(np.float32)
    
    # Invert the image (255 - pixel values)
    image = 255.0 - image
    
    # Resize with cropping/padding to 51x51
    image = tf.image.resize_with_crop_or_pad(image, 51, 51)
    
    # Normalize to [0, 1]
    image = image / 255.0
    
    return image


# -------------------------------

# # test on 3 marks, 2 same hand, 1 different hand (if you would like to see the performance of the model, uncomment this part)

# # Your image paths
# img_path1 = "./static/segmented_images/examples/0_MER01 BATCH 1-13.jpg"  # same hand, mark 0 from MER01 BATCH 1-13
# img_path2 = "./static/segmented_images/examples/1_MER01 BATCH 1-13.jpg"  # same hand, mark 1 from MER01 BATCH 1-13
# img_path3 = "./static/segmented_images/examples/2_MER02 BATCH 1-13.jpg"  # different hand, mark 0 from MER02 BATCH 1-13

# # Preprocess each image
# image1 = preprocess_single_image(img_path1)
# image2 = preprocess_single_image(img_path2)
# image3 = preprocess_single_image(img_path3)

# # Form a batch of 2 pairs:
# # Pair 1: (image1, image2)
# # Pair 2: (image1, image3)
# X1 = tf.stack([image1, image1], axis=0)  # shape: (2, 51, 51, 3)
# X2 = tf.stack([image2, image3], axis=0)  # shape: (2, 51, 51, 3)

# # Compute similarity scores
# scores = get_similarity_scores(clip_model, X1, X2, temperature=temperature)

# # Print results
# print("\n--- Similarity Scores ---")
# print(f"Pair 1 (same hand):      {scores[0]:.4f} → {'Same' if scores[0] >= optimal_threshold else 'Different'}")
# print(f"Pair 2 (different hand): {scores[1]:.4f} → {'Same' if scores[1] >= optimal_threshold else 'Different'}")


# -------------------------------

# Your image paths
img_path1 = "./static/segmented_images/examples/0_20111129114909694_0004.jpg"  # mark 0 
img_path2 = "./static/segmented_images/examples/0_20111129114909694_0014.jpg"  # mark 1 

# Preprocess each image
image1 = preprocess_single_image(img_path1)
image2 = preprocess_single_image(img_path2)

# Form a batch of 2 pairs:
# Pair: (image1, image2)
X1 = tf.stack([image1], axis=0)  # shape: (2, 51, 51, 3)
X2 = tf.stack([image2], axis=0)  # shape: (2, 51, 51, 3)

# Compute similarity scores
scores = get_similarity_scores(clip_model, X1, X2, temperature=temperature)

# Print results
print("\n--- Similarity Scores ---")
print(f"Detected Pair (same hand):      {scores[0]:.4f} → {'Same' if scores[0] >= optimal_threshold else 'Different'}")



# Load or initialize result.json
result_file = "result.json"

if os.path.exists(result_file):
    with open(result_file, "r") as f:
        similarity_data = json.load(f)
else:
    similarity_data = {
        "similarity1": "N/A",
        "similarity2": "N/A",
        "similarity3": "N/A",
        "overall_similarity": "N/A"
    }



current_score = round(float(scores[0]), 4)

# Update the first available "N/A" similarity field
updated = False
for key in ["similarity1", "similarity2", "similarity3"]:
    if similarity_data[key] == "N/A":
        similarity_data[key] = current_score
        print(f"✅ Updated {key} with score: {current_score}")
        updated = True
        break

if not updated:
    print("⚠️ All similarity scores are already filled. No update made.")

# Recalculate overall_similarity based on how many valid scores we have
valid_scores = [
    float(similarity_data[key]) for key in ["similarity1", "similarity2", "similarity3"]
    if similarity_data[key] != "N/A"
]

if valid_scores:
    overall_similarity = round(sum(valid_scores) / len(valid_scores), 4)
    similarity_data["overall_similarity"] = overall_similarity
else:
    similarity_data["overall_similarity"] = "N/A"

# Save back to result.json
with open(result_file, "w") as f:
    json.dump(similarity_data, f, indent=4)

print("📁 Saved updated similarity results to result.json")

end_time = time.time()
print(f"Execution time: {end_time - start_time:.2f} seconds")
# -------------------------------