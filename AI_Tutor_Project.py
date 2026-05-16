import streamlit as st
from streamlit_mic_recorder import mic_recorder
import google.generativeai as genai
from gtts import gTTS
import io
import re
import extra_streamlit_components as stx
import speech_recognition as sr
from pydub import AudioSegment
import datetime
# --- 1. SETUP ---
st.set_page_config(page_title="AI English Tutor", page_icon="🎙️")

custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');

    /* Global Font and Overall Dark App Background */
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }

    /* Set overall theme to dark via CSS */
    .stApp {
        background: linear-gradient(135deg, #121212 0%, #1e1e1e 100%); /* Elegant dark gradient background */
        color: #f8f9fa; /* Clear, bright white global text */
    }

    /* Ensure default text is always bright white (very important!) */
    [data-testid="stMarkdownContainer"] p, [data-testid="stExpander"] {
        color: #f8f9fa;
    }

    /* Stylish Titles using HTML - Now designed with light colors */
    .main-title {
        color: #e3f2fd; /* Bright, light blue/white */
        font-size: 2.8rem;
        font-weight: 600;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(255,255,255,0.1); /* light shadow for dark background */
        margin-bottom: 0px;
        padding-top: 20px;
    }

    .sub-title {
        color: #bbdefb; /* Slightly darker light blue/white */
        font-size: 1.2rem;
        font-weight: 400;
        text-align: center;
        margin-bottom: 30px;
    }

    /* User Text Box Styling - Now: Dark Box, Perfect White Text */
    .user-box {
        background-color: #212121; /* Dark grey box background */
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2); /* darker shadow for dark background */
        border-left: 5px solid #10B981;
        margin-top: 15px;
        margin-bottom: 15px;
        color: #f8f9fa; /* Perfect white text inside the dark box */
        font-size: 1.05rem;
    }

    /* Sidebar Styling - Darker and clearer */
    [data-testid="stSidebar"] {
        background-color: #1a1a1a;
        border-right: 1px solid #333333;
    }
    
    [data-testid="stSidebar"] h2 {
        color: #e3f2fd !important; /* ensures title is light */
    }
    
    [data-testid="stSidebar"] .stMarkdown p {
        color: #bbdefb !important; /* light grey/blue text */
    }

    /* Footer Styling */
    .footer {
        text-align: center;
        color: #f8f9fa; /* Perfect white text for the footer tip */
        font-size: 0.9rem;
        margin-top: 50px;
        padding: 10px;
        border-top: 1px solid #333333; /* darker separator */
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)
st.markdown('<div class="main-title">🎙️ AI English Tutor</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Boliye, Sikhiye aur Improve Kijiye!</div>', unsafe_allow_html=True)

# cookie_manager = stx.CookieManager(key="my_cookie_manager")

# # Check if API key is already saved in cookies
# saved_key = cookie_manager.get(cookie="gemini_api_key")
# default_key = saved_key if saved_key else ""

# Sidebar UI for API Key
st.sidebar.markdown("## 🔑 API Key Setup")
st.sidebar.caption("Gemini AI se connect karne ke liye apni API key daalein.")
api_key = st.sidebar.text_input("Insert Gemini API key", type="password")

# if st.sidebar.button("Save API Key"):
#     if api_key:
#         # Save the API key in the browser for 30 days
#         expire_date = datetime.datetime.now() + datetime.timedelta(days=30)
#         cookie_manager.set("gemini_api_key", api_key, expires_at=expire_date)
#         st.sidebar.success("API Key saved! Ab aapko baar-baar key nahi dalni padegi.")
#     else:
#         st.sidebar.error("Pehle API key enter karein.")

# --- 2. FUNCTIONS ---

def convert_audio_to_text(audio_bytes):
    """Convert recorded audio to text"""
    recognizer = sr.Recognizer()

    try:
        audio_file = io.BytesIO(audio_bytes)

        # Convert WebM/recorded audio to WAV
        audio = AudioSegment.from_file(audio_file, format="webm")
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_io.seek(0)

        with sr.AudioFile(wav_io) as source:
            audio_data = recognizer.record(source)

        return recognizer.recognize_google(audio_data)

    except sr.UnknownValueError:
        return "Sorry, I couldn't understand your speech. Please try again."

    except Exception as e:
        return f"Audio processing error: {str(e)}"

def get_ai_response(user_text):
    """Get grammar correction and feedback from Gemini"""
    try:
        genai.configure(api_key=api_key)
        # Using the standard gemini-1.5-flash or your preferred model
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""
        You are a friendly and encouraging English teacher.

        The student said: "{user_text}"

        Please analyze the sentence and provide feedback based on these two conditions:

        CONDITION 1 - IF THE SENTENCE HAS GRAMMAR MISTAKES:
        1. Corrected sentence: (Provide the grammatically correct version)
        2. Explanation: (Explain the grammar mistake simply. Strictly ignore basic punctuation rules like capital letters, commas, or full stops, because this is voice-to-text input.)
        3. Reply: (A short friendly reply or question to continue the conversation)

        CONDITION 2 - IF THE SENTENCE IS ALREADY CORRECT:
        1. Praise: (Tell the student their grammar is perfectly correct!)
        2. Better ways to say it: (Suggest 1 or 2 advanced, native-sounding, or more vocabulary-rich ways to say the exact same thing to help them improve.)
        3. Reply: (A short friendly reply or question to continue the conversation)

        Keep the response concise, well-formatted, and very easy to understand.
        """

        response = model.generate_content(prompt)
        return response.text
    
    except Exception as e:
        return "⚠️ Error or API limit exceeded! Please try again after a few minutes."


def text_to_speech(text):
    """Convert text to speech"""
    if api_key and text:
        # Gemini ke markdown characters (* aur #) ko hatayein, 
        # par comma (,) aur full stop (.) ko rehne dein taki AI naturally pause le sake.
        clean_text = re.sub(r"[\d*#]", "", text)
        
        # Extra spaces remove karein
        clean_text = clean_text.strip()
        
        # Agar text completely empty ho gaya hai, toh wahi ruk jayein
        if not clean_text:
            return None
            
        try:
            tts = gTTS(text=clean_text, lang="en")
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)
            return audio_fp
        except Exception as e:
            st.error(f"Audio generate karne mein error aayi: {e}")
            return None


# --- 3. UI LOGIC ---

st.subheader("🗣️ Boliye aur Sikhiye")

audio_info = mic_recorder(
    start_prompt="Bolna Shuru Karein 🎙️",
    stop_prompt="Stop 🛑",
    key="recorder"
)

if audio_info and audio_info.get("bytes"):
    # Speech to Text
    with st.spinner("⏳ Aapki awaaz samajh raha hoon..."):
        user_text = convert_audio_to_text(audio_info["bytes"])

    st.markdown(f'<div class="user-box">🗣️ <b>Aapne kaha:</b> {user_text}</div>', unsafe_allow_html=True)

    if "error" not in user_text.lower() and "sorry" not in user_text.lower():
        # AI Response
        if api_key:
            with st.spinner("🤖 AI aapke sentence ko analyze kar raha hai..."):
                correction = get_ai_response(user_text)
        
                st.success(correction,icon="💡")
                
        else:
            st.error("⚠️ First, insert your API key in the Sidebar...", icon="🚨")

        # Text to Speech
        if api_key:
            with st.spinner("🔊 AI bol raha hai..."):
                audio_reply = text_to_speech(correction)
                st.audio(audio_reply, format="audio/mp3", autoplay=True)

# Footer
st.markdown('<div class="footer">💡 <b>Tip:</b> Clear aur dheere boliye taki AI aapki baat sahi samajh sake.</div>', unsafe_allow_html=True)
