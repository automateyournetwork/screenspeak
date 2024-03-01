from PIL import Image
import io
import os
import time
import base64
import requests
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SCREENSHOT_DIR = "/mnt/c/Users/<YOUR USERNAME>/OneDrive/Pictures/Screenshots"  # Adjust to your path
VOICE_MODEL = "alloy"
POLL_INTERVAL = 10  # Time in seconds between checks

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def get_latest_screenshot(directory):
    """Get the most recent screenshot file from the directory."""
    png_files = [f for f in os.listdir(directory) if f.endswith('.png')]
    if not png_files:
        return None
    latest_file = max(png_files, key=lambda x: os.path.getctime(os.path.join(directory, x)))
    return os.path.join(directory, latest_file)

def process_screenshot(screenshot_path):
    print(f"Processing screenshot: {screenshot_path}")
    try:
        # Open the screenshot and convert to JPEG
        with Image.open(screenshot_path) as img:
            img = img.convert("RGB")

            # Convert the JPEG image to base64
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=85)  # Save as JPEG with good quality
            base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Generate script from the screenshot
        description = generate_script(base64_image)

        # Synthesize speech from the description
        audio_content = synthesize_speech(description)

        # Save the audio content to a file
        if audio_content:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = os.path.join("", f"audio_{timestamp}.mp3")  # Corrected to save in SCREENSHOT_DIR
            with open(audio_filename, 'wb') as audio_file:
                audio_file.write(audio_content)
            print(f"Saved audio to {audio_filename}")

            # Play the MP3 file
            play_audio(audio_filename)
    except Exception as e:
        print(f"Error processing screenshot: {e}")

def play_audio(audio_filename):
    try:
        subprocess.run(['mpg123', audio_filename], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error playing audio: {e}")

# Function to generate voice-over script using OpenAI's GPT model
def generate_script(base64_frame):
    prompt_messages = [
        {
            "role": "user",
            "content": [
                f"This is a screenshot. Based on the image please generate the text to describe what you see. Try your best.",
                {"image": base64_frame, "resize": 768}
            ],
        },
    ]

    # Create the completion request
    result = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=prompt_messages,
        max_tokens=500,
    )

    return result.choices[0].message.content

def synthesize_speech(script, voice=VOICE_MODEL):
    print("Synthesizing speech...")
    response = requests.post(
        "https://api.openai.com/v1/audio/speech",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        json={"model": "tts-1-hd", "input": script, "voice": voice},
    )
    if response.ok:
        return response.content
    else:
        print(f"Error with the audio generation request: {response.text}")
        return None

def main():
    last_processed = None
    print(f"Monitoring for new screenshots in {SCREENSHOT_DIR}...")
    while True:
        latest_screenshot = get_latest_screenshot(SCREENSHOT_DIR)
        if latest_screenshot and latest_screenshot != last_processed:
            process_screenshot(latest_screenshot)
            last_processed = latest_screenshot
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
