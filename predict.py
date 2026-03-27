import pickle
from model import extract_features

model = pickle.load(open("cat_sound_model.pkl", "rb"))

file = "C:\\Users\\ASUS\\OneDrive\\Documents\\Desktop\\furspeak\\dataset\\cat\\happy\\happycat_1.mp3"

features = extract_features(file)

prediction = model.predict([features])[0]

print("Prediction:", prediction)