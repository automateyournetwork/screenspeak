import io
import os
import time
import base64
import requests
import subprocess
from PIL import Image
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv

class ScreenSpeak:
    """
    ScreenSpeak continuously monitors a specified directory for new screenshots,
    processes each new screenshot by generating a voice-over script using OpenAI's GPT model,
    and then synthesizes speech from the script.
    """
    def __init__(self, screenshot_dir, voice_model="alloy", poll_interval=10):
        """
        Initializes the ScreenSpeak with the directory to monitor, voice model, and polling interval.

        :param screenshot_dir: Directory to monitor for new screenshots.
        :param voice_model: Voice model to use for speech synthesis.
        :param poll_interval: Time in seconds between directory checks for new screenshots.
        """
        self.screenshot_dir = screenshot_dir
        self.voice_model = voice_model
        self.poll_interval = poll_interval
        self.start_time = datetime.now().timestamp()
        self.last_processed = None
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def run(self):
        """
        Starts the monitoring and processing of new screenshots in the specified directory.
        """
        print(f"Monitoring for new screenshots in {self.screenshot_dir}...")
        while True:
            latest_screenshot = self._get_latest_screenshot()
            if latest_screenshot and latest_screenshot != self.last_processed:
                self._process_screenshot(latest_screenshot)
                self.last_processed = latest_screenshot
            time.sleep(self.poll_interval)

    def _get_latest_screenshot(self):
        """
        Gets the most recent screenshot file from the directory, considering only files created after the script started.

        :return: The path to the latest screenshot file, or None if no new file is found.
        """
        png_files = [f for f in os.listdir(self.screenshot_dir) if f.endswith('.png')]
        valid_files = [f for f in png_files if os.path.getctime(os.path.join(self.screenshot_dir, f)) > self.start_time]
        if not valid_files:
            return None
        latest_file = max(valid_files, key=lambda x: os.path.getctime(os.path.join(self.screenshot_dir, x)))
        return os.path.join(self.screenshot_dir, latest_file)

    def _process_screenshot(self, screenshot_path):
        """
        Processes the screenshot: generates a voice-over script using OpenAI's GPT model, synthesizes speech,
        and plays the generated audio.

        :param screenshot_path: Path to the screenshot file to be processed.
        """
        print(f"Processing screenshot: {screenshot_path}")
        try:
            description = self._generate_script(screenshot_path)
            audio_content = self._synthesize_speech(description)
            if audio_content:
                self._save_and_play_audio(audio_content)
        except Exception as e:
            print(f"Error processing screenshot: {e}")

    def _generate_script(self, screenshot_path):
        """
        Generates a voice-over script for the screenshot using OpenAI's GPT model.

        :param screenshot_path: Path to the screenshot file.
        :return: Generated script as a string.
        """
        with Image.open(screenshot_path) as img:
            img = img.convert("RGB")
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        prompt_messages = [{
            "role": "user",
            "content": [
                "This is a screenshot. Based on the image please generate the text to describe what you see. Try your best.",
                {"image": base64_image, "resize": 768}
            ],
        }]
        result = self.client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=prompt_messages,
            max_tokens=500,
        )
        return result.choices[0].message.content

    def _synthesize_speech(self, script):
        """
        Synthesizes speech from the provided script using the specified voice model.

        :param script: Script to synthesize speech from.
        :return: Binary content of the synthesized speech audio.
        """
        print("Synthesizing speech...")
        response = requests.post(
            "https://api.openai.com/v1/audio/speech",
            headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"},
            json={"model": "tts-1-hd", "input": script, "voice": self.voice_model},
        )
        if response.ok:
            return response.content
        else:
            print(f"Error with the audio generation request: {response.text}")
            return None

    def _save_and_play_audio(self, audio_content):
        """
        Saves the synthesized speech audio to a file and plays it.

        :param audio_content: Binary content of the synthesized speech audio.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_filename = f"audio_{timestamp}.mp3"
        with open(audio_filename, 'wb') as audio_file:
            audio_file.write(audio_content)
        print(f"Saved audio to {audio_filename}")
        subprocess.run(['mpg123', audio_filename], check=True)

if __name__ == "__main__":
    load_dotenv()
    screenspeak = ScreenSpeak("/mnt/c/Users/<YOUR USERNAME HERE>/OneDrive/Pictures/Screenshots")
    screenspeak.run()
