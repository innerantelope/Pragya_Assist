from flask import Flask, request, render_template
from langdetect import detect
from deep_translator import GoogleTranslator
import os
import requests

# ✅ Optional TTS (works locally, not on Render)
try:
    import pyttsx3
    tts_engine = pyttsx3.init()
    tts_engine.setProperty('rate', 150)
except:
    tts_engine = None

app = Flask(__name__)

# ✅ Secure API key loading
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ✅ TTS Function (local only)
def speak_text(text):
    if tts_engine:
        try:
            tts_engine.stop()
            tts_engine.say(text)
            tts_engine.runAndWait()
        except RuntimeError:
            pass

# ✅ Generate response from OpenRouter
def generate_free_response(prompt):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

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

# ✅ Main route
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

            # ✅ Fix short English message misclassification
            if len(user_msg.split()) <= 3:
                if all(char in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ?!" for char in user_msg.replace(" ", "")):
                    lang = "en"

            # ✅ Limit to Hindi and English
            if lang not in ['en', 'hi']:
                bot_response = "❌ Sorry, I only support Hindi and English for now."
                return render_template("index.html", user_msg=user_msg, bot_response=bot_response)

            # ✅ Translate Hindi → English
            translated_msg = user_msg
            if lang == 'hi':
                translated_msg = GoogleTranslator(source='hi', target='en').translate(user_msg)

            # ✅ Generate AI response
            bot_response = generate_free_response(translated_msg)

            # ✅ Translate English → Hindi (if needed)
            if lang == 'hi':
                bot_response = GoogleTranslator(source='en', target='hi').translate(bot_response)

            # ✅ Speak locally only
            if "❌" not in bot_response and os.getenv("RENDER") != "True":
                speak_text(bot_response)

        except Exception as e:
            print("Error:", e)
            bot_response = "❌ Sorry, something went wrong."

    return render_template("index.html", user_msg=user_msg, bot_response=bot_response)

# ✅ Local dev
if __name__ == "__main__":
    app.run(debug=True)
