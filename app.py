import os
api_key = os.getenv("OPENROUTER_API_KEY")
from flask import Flask, request, render_template
from langdetect import detect
from deep_translator import GoogleTranslator
import pyttsx3
import requests

app = Flask(__name__)

# ✅ TTS Initialization
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)

def speak_text(text):
    try:
        tts_engine.stop()
        tts_engine.say(text)
        tts_engine.runAndWait()
    except RuntimeError:
        pass

# ✅ Generate free response from OpenRouter
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

# ✅ Flask chatbot route
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
                lang = "en"  # Default to English

            # ✅ Fix for short English messages
            if len(user_msg.split()) <= 3:
                if all(char in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ?!" for char in user_msg.replace(" ", "")):
                    lang = "en"

            # ✅ Only allow English and Hindi
            if lang not in ['en', 'hi']:
                bot_response = "❌ Sorry, I only support Hindi and English for now."
                return render_template("index.html", user_msg=user_msg, bot_response=bot_response)

            # ✅ Translate Hindi to English
            translated_msg = user_msg
            if lang == 'hi':
                translated_msg = GoogleTranslator(source='hi', target='en').translate(user_msg)

            # ✅ Generate response
            bot_response = generate_free_response(translated_msg)

            # ✅ Translate back to Hindi if needed
            if lang == 'hi':
                bot_response = GoogleTranslator(source='en', target='hi').translate(bot_response)

            # ✅ Speak response
            if "❌" not in bot_response:
                speak_text(bot_response)

        except Exception as e:
            print("Error:", e)
            bot_response = "❌ Sorry, something went wrong."

    return render_template("index.html", user_msg=user_msg, bot_response=bot_response)

# ✅ Run the app
if __name__ == "__main__":
    app.run(debug=True)
