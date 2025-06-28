from flask import Flask, request, render_template
from langdetect import detect
from deep_translator import GoogleTranslator
import requests
import os

app = Flask(__name__)

# ✅ Load API key safely
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("❌ OPENROUTER_API_KEY not set in environment variables.")

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

# ✅ Generate response from OpenRouter
def generate_free_response(prompt):
    try:
        payload = {
            "model": "mistralai/mistral-7b-instruct",
            "messages": [
                {"role": "system", "content": "You are an empathetic assistant named Pragya Assist."},
                {"role": "user", "content": prompt}
            ]
        }
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"❌ AI error: {str(e)}"

# ✅ Flask route
@app.route("/", methods=["GET", "POST"])
def chatbot():
    user_msg = ""
    bot_response = ""

    if request.method == "POST":
        try:
            user_msg = request.form["message"]

            # ✅ Language detection
            try:
                lang = detect(user_msg)
            except:
                lang = "en"

            if len(user_msg.split()) <= 3:
                if all(char.isalpha() or char in "?! " for char in user_msg):
                    lang = "en"

            if lang not in ['en', 'hi']:
                bot_response = "❌ Sorry, I only support Hindi and English for now."
                return render_template("index.html", user_msg=user_msg, bot_response=bot_response)

            if lang == 'hi':
                translated_msg = GoogleTranslator(source='hi', target='en').translate(user_msg)
            else:
                translated_msg = user_msg

            bot_response = generate_free_response(translated_msg)

            if lang == 'hi':
                bot_response = GoogleTranslator(source='en', target='hi').translate(bot_response)

            if os.getenv("RENDER") != "True":
                try:
                    import pyttsx3
                    tts_engine = pyttsx3.init()
                    tts_engine.setProperty('rate', 150)
                    tts_engine.say(bot_response)
                    tts_engine.runAndWait()
                except:
                    pass

        except Exception as e:
            print("Error:", e)
            bot_response = "❌ Sorry, something went wrong."

    return render_template("index.html", user_msg=user_msg, bot_response=bot_response)

# ✅ Run locally
if __name__ == "__main__":
    app.run(debug=True)
