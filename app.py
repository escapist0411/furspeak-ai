from flask import Flask, render_template, request
import os
import pickle
from model import extract_features
from flask import Flask, render_template, request, redirect, session
from database import cursor, db

app = Flask(__name__)
app.secret_key = "furspeak_secret_key"
app.config["UPLOAD_FOLDER"] = "uploads"

# Load trained model
model = pickle.load(open("pet_sound_model.pkl", "rb"))

labels = {
    0: "Happy",
    1: "Angry",
    2: "Sad",
    3: "Hungry"
}

emoji_map = {
    "dog": {
        "Happy": "😊🐶",
        "Angry": "😡🐶",
        "Sad": "😢🐶",
        "Hungry": "🍖🐶"
    },
    "cat": {
        "Happy": "😺",
        "Angry": "😾",
        "Sad": "😿",
        "Hungry": "🐟"
    }
}

@app.route("/", methods=["GET", "POST"])
def index():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        audio_file = request.files["audio"]

        if audio_file.filename == "":
            return render_template("index.html", error="No file selected")

        # ✅ define animal HERE (inside POST)
        animal = request.form.get("animal", "dog")

        file_path = os.path.join(app.config["UPLOAD_FOLDER"], audio_file.filename)
        audio_file.save(file_path)

        # ✅ load correct model
        if animal == "dog":
            model = pickle.load(open("pet_sound_model.pkl", "rb"))
        else:
            model = pickle.load(open("cat_sound_model.pkl", "rb"))

        features = extract_features(file_path)
        prediction = int(model.predict([features])[0])

        mood = labels[prediction]
        confidence = float(70 + prediction * 5)

        emoji = emoji_map[animal][mood]

        # ✅ save in DB
        cursor.execute(
            "INSERT INTO history (user_id, filename, mood, confidence, animal) VALUES (%s,%s,%s,%s,%s)",
            (session["user_id"], audio_file.filename, mood, confidence, animal)
        )
        db.commit()

        return render_template(
            "result.html",
            mood=mood,
            confidence=confidence,
            emoji=emoji,
            filename=audio_file.filename
        )

    # ✅ GET request (no animal needed here)
    return render_template("index.html")

@app.route("/signup", methods=["GET","POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        cursor.execute(
            "INSERT INTO users (name,email,password) VALUES (%s,%s,%s)",
            (name,email,password)
        )
        db.commit()

        return redirect("/login")

    return render_template("signup.html")

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email,password)
        )

        user = cursor.fetchone()

        if user:
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            return redirect("/dashboard")

        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/login")

    cursor.execute(
        "SELECT * FROM users WHERE id=%s",
        (session["user_id"],)
    )
    user = cursor.fetchone()

    # total analyses
    cursor.execute(
        "SELECT COUNT(*) as total FROM history WHERE user_id=%s",
        (session["user_id"],)
    )
    total = cursor.fetchone()["total"]

    # favorite emotion
    cursor.execute(
        """
        SELECT mood, COUNT(*) as count
        FROM history
        WHERE user_id=%s
        GROUP BY mood
        ORDER BY count DESC
        LIMIT 1
        """,
        (session["user_id"],)
    )

    fav = cursor.fetchone()

    favorite = fav["mood"] if fav else "N/A"

    join_date = user.get("created_at", "Unknown")

    return render_template(
        "profile.html",
        user=user,
        total=total,
        favorite=favorite,
        join_date=join_date
    )

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    cursor.execute("SELECT COUNT(*) as total FROM history WHERE user_id=%s",(session["user_id"],))
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM history WHERE mood='Happy' AND user_id=%s",(session["user_id"],))
    happy = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM history WHERE mood='Sad' AND user_id=%s",(session["user_id"],))
    sad = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM history WHERE mood='Angry' AND user_id=%s",(session["user_id"],))
    angry = cursor.fetchone()["total"]

    return render_template(
    "dashboard.html",
    name=session["name"],
    total=total,
    happy=happy,
    sad=sad,
    angry=angry
    )

@app.route("/analytics")
def analytics():

    if "user_id" not in session:
        return redirect("/login")

    # default animal = dog
    animal = request.args.get("animal", "dog")

    cursor.execute(
        "SELECT mood, COUNT(*) as total FROM history WHERE animal=%s GROUP BY mood",
        (animal,)
    )

    data = cursor.fetchall()

    stats = {"Happy":0,"Angry":0,"Sad":0,"Hungry":0}

    for row in data:
        stats[row["mood"]] = row["total"]

    return render_template(
        "analytics.html",
        happy=stats["Happy"],
        angry=stats["Angry"],
        sad=stats["Sad"],
        hungry=stats["Hungry"],
        selected_animal=animal
    )

@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect("/login")

    cursor.execute(
        "SELECT * FROM history WHERE user_id=%s ORDER BY date DESC",
        (session["user_id"],)
    )

    data = cursor.fetchall()

    return render_template("history.html", data=data)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/logout")
def logout():

    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
