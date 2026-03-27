import os
import pickle
from sklearn.svm import SVC
from model import extract_features

X = []
y = []

labels = {
    "happy": 0,
    "angry": 1,
    "sad": 2,
    "hungry": 3
}

for label in labels:
    folder_path = os.path.join("dataset", label)
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        try:
            features = extract_features(file_path)
            X.append(features)
            y.append(labels[label])
        except Exception as e:
            print(f"Error processing {file}: {e}")

model = SVC(kernel="linear")
model.fit(X, y)

with open("pet_sound_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("Dog sound model trained successfully ✅")
