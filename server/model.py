import json
import random

# similarity1 = round(random.uniform(0.7, 1.0), 2)
# similarity2 = round(random.uniform(0.7, 1.0), 2)
# similarity3 = round(random.uniform(0.7, 1.0), 2)

# overall_similarity = round((similarity1 + similarity2 + similarity3) / 3, 2)

# this data will be saved to result.json for the web app to read
# similarity_data = {
#     "similarity1": similarity1,
#     "similarity2": similarity2,
#     "similarity3": similarity3,
#     "overall_similarity": overall_similarity
# }
# initialize similarity values to "N/A"
similarity_data = {
    "similarity1": "N/A",
    "similarity2": "N/A",
    "similarity3": "N/A",
    "overall_similarity": "N/A"
}

# Write to result.json
with open("result.json", "w") as f:
    json.dump(similarity_data, f, indent=4)

print("Saved to result.json ✅")
