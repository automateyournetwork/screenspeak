import io
import os
import time
import base64
import requests
import subprocess
from PIL import Image
from openai import OpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
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
        self.anthropic_client = ChatAnthropic(temperature=0, anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"), model_name="claude-3-opus-20240229")

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
            # Generate script using OpenAI
            description_openai = self._generate_script(screenshot_path)
            print("OpenAI-generated script:", description_openai)

            # Generate script using Anthropic
            description_anthropic = self._generate_script_anthropic(screenshot_path)
            print("Anthropic-generated script:", description_anthropic)

            # Combine descriptions for saving to text file
            combined_description = f"OpenAI Description:\n{description_openai}\n\nAnthropic Description:\n{description_anthropic}"
            self._save_text_analysis(combined_description, screenshot_path)

            # Synthesize speech and save as audio files separately
            audio_content_openai = self._synthesize_speech(description_openai)
            audio_content_anthropic = self._synthesize_speech(description_anthropic)

            # Save and play OpenAI audio
            if audio_content_openai:
                self._save_and_play_audio(audio_content_openai, "openai")

            # Save and play Anthropic audio
            if audio_content_anthropic:
                self._save_and_play_audio(audio_content_anthropic, "anthropic")
        except Exception as e:
            print(f"Error processing screenshot: {e}")

    def _save_text_analysis(self, combined_description, screenshot_path):
        """
        Saves the combined text analysis from OpenAI and Anthropic models to a file in the "Text Analysis" folder.
    
        :param combined_description: The combined description to save.
        :param screenshot_path: The path of the original screenshot, used to derive the name of the text file.
        """
        # Create the "Text Analysis" directory if it doesn't exist
        text_analysis_dir = os.path.join(self.screenshot_dir, "Text Analysis")
        if not os.path.exists(text_analysis_dir):
            os.makedirs(text_analysis_dir)
        
        # Extract the base name of the screenshot and replace its extension with .txt for the text file
        base_name = os.path.basename(screenshot_path)
        text_file_name = os.path.splitext(base_name)[0] + ".txt"
        
        # Define the full path for the text file within the "Text Analysis" directory
        text_file_path = os.path.join(text_analysis_dir, text_file_name)
        
        # Write the combined description to the text file
        with open(text_file_path, 'w', encoding='utf-8') as file:
            file.write(combined_description)
        
        print(f"Saved text analysis to {text_file_path}")

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
    
    def _generate_script_anthropic(self, screenshot_path):
        """
        Generates a voice-over script for the screenshot using Anthropic's Claude-3 model.

        :param screenshot_path: Path to the screenshot file.
        :return: Generated script as a string.
        """
        with Image.open(screenshot_path) as img:
            img = img.convert("RGB")
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Prepare the message for Anthropic's API using HumanMessage
        messages = [
            HumanMessage(
                content=[
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                    {"type": "text", "text": "This is a screenshot. Based on the image please generate the text to describe what you see. Try your best."},
                ]
            )
        ]

        # Assuming `self.anthropic_client` is already initialized and configured
        response = self.anthropic_client.invoke(messages)

        return response    

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

    def _save_and_play_audio(self, audio_content, identifier):
        """
        Saves the synthesized speech audio to a file and plays it.

        :param audio_content: Binary content of the synthesized speech audio.
        :param identifier: A string identifier to differentiate the source of the audio content.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_filename = f"{identifier}_audio_{timestamp}.mp3"
        with open(audio_filename, 'wb') as audio_file:
            audio_file.write(audio_content)
        print(f"Saved audio to {audio_filename}")
        subprocess.run(['mpg123', audio_filename], check=True)

if __name__ == "__main__":
    load_dotenv()
    screenspeak = ScreenSpeak("/mnt/c/Users/ptcap/OneDrive/Pictures/Screenshots")
    screenspeak.run()
