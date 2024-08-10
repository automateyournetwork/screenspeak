import io
import os
import time
import base64
import shutil
import requests
import subprocess
from PIL import Image
from openai import OpenAI
from langchain_core.messages import HumanMessage
from datetime import datetime
from dotenv import load_dotenv

class ScreenSpeak:
    def __init__(self, screenshot_dir, voice_model="alloy", poll_interval=10, output_dir="ScreenSpeakOutputs"):
        """
        Initializes the ScreenSpeak with the directory to monitor, voice model, and polling interval.

        :param screenshot_dir: Directory to monitor for new screenshots.
        :param voice_model: Voice model to use for speech synthesis.
        :param poll_interval: Time in seconds between directory checks for new screenshots.
        :param output_dir: Directory to save text analysis and audio files locally.
        """
        self.screenshot_dir = screenshot_dir
        self.voice_model = voice_model
        self.poll_interval = poll_interval
        self.start_time = datetime.now().timestamp()
        self.last_processed = None
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # Base directory for all outputs
        base_output_dir = os.path.join(os.path.dirname(__file__), "LocalScreenSpeakOutputs")
        # Specific directories for text analysis and screenshots
        self.text_analysis_output_dir = os.path.join(base_output_dir, "Text Analysis")
        self.screenshot_output_dir = os.path.join(base_output_dir, "Screenshots")
        self.audio_transcripts_dir = os.path.join(base_output_dir, "Audio Transcripts")

        # Create the directories if they don't exist
        os.makedirs(self.text_analysis_output_dir, exist_ok=True)
        os.makedirs(self.screenshot_output_dir, exist_ok=True)
        os.makedirs(self.audio_transcripts_dir, exist_ok=True)

        # Setting up local directories for text and audio output
        self.output_dir = os.path.abspath(output_dir)
        self.text_analysis_dir = os.path.join(self.output_dir, "Text Analysis")
        self.audio_transcripts_dir = os.path.join(self.output_dir, "Audio Transcripts")
        self.screenshot_output_dir = os.path.join(self.output_dir, "Screenshots")

        # Create directories if they don't exist
        os.makedirs(self.text_analysis_dir, exist_ok=True)
        os.makedirs(self.audio_transcripts_dir, exist_ok=True)
        os.makedirs(self.screenshot_output_dir, exist_ok=True)

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
        print(f"Processing screenshot: {screenshot_path}")
        try:
            # Generate scripts using both models
            chatgpt_description = self._generate_script(screenshot_path)

            # Base name for files, could be based on either description or a timestamp
            file_name_base = self._generate_file_name(chatgpt_description)

            # Save all descriptions and synthesized summary
            self._save_text_analysis(chatgpt_description, file_name_base + "_chatgpt")

            # Copy the original screenshot once
            self._copy_screenshot(screenshot_path, file_name_base)

            # Synthesize and save audio for the synthesized summary
            synthesized_audio = self._synthesize_speech(chatgpt_description)
            if synthesized_audio:
                self._save_and_play_audio(synthesized_audio, file_name_base + "_synthesized")
        except Exception as e:
            print(f"Error processing screenshot: {e}")

    def _copy_screenshot(self, screenshot_path, file_name_base):
        """
        Copies the original screenshot to the Screenshots directory with the AI-generated filename.

        :param screenshot_path: Path to the original screenshot file.
        :param file_name_base: Base name for the file, generated by AI.
        """
        new_filename = f"{file_name_base}.png"
        destination_path = os.path.join(self.screenshot_output_dir, new_filename)
        shutil.copy2(screenshot_path, destination_path)
        print(f"Copied screenshot to {destination_path}")

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
                #"You are currently analyzing a digital screenshot. Your task is to meticulously examine the visual elements and context presented in this image. Consider all visible details, including text, symbols, interface elements, and any discernible background features. Your goal is to generate a comprehensive description of the screenshot's contents, providing insights into its possible purpose, the actions it depicts or prompts, and any underlying context or information it conveys. Please employ your analytical capabilities to deduce and articulate the significance of the screenshot, offering interpretations or explanations that could assist a user in understanding its relevance, potential applications, or implications. Approach this task with attention to detail and a focus on delivering clear, informative, and useful analysis.",
                "You are currently analyzing a digital screenshot of a dashboard from Selector.AI. Your task is to meticulously examine the visual elements and context presented in this image. Pay close attention to all visible details, including text, symbols, interface elements, and any discernible background features. Focus on any text in the image to identify interface names and functionalities.Your goal is to generate a comprehensive description of the dashboard's contents, providing insights into its possible purpose, the actions it depicts or prompts, and any underlying context or information it conveys. Please use your analytical capabilities to deduce and articulate the significance of the dashboard, offering interpretations or explanations that could assist a user in understanding its relevance, potential applications, or implications.Approach this task with attention to detail and a focus on delivering clear, informative, and useful analysis, acting as a copilot or technical assistant to help decipher the meaning and functionalities of the Selector.AI dashboard.",
                {"image": base64_image, "resize": 768}
            ],
        }]
        result = self.client.chat.completions.create(
            model="gpt-4o",
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

    def _save_and_play_audio(self, audio_content, file_name_base):
        """
        Saves the synthesized speech audio to a file and plays it, using a name generated by ChatGPT.

        :param audio_content: Binary content of the synthesized speech audio.
        :param file_name_base: AI-generated base name for the file.
        """
        audio_filename = f"{file_name_base}_audio.mp3"
        audio_file_path = os.path.join(self.audio_transcripts_dir, audio_filename)

        with open(audio_file_path, 'wb') as audio_file:
            audio_file.write(audio_content)
        print(f"Saved audio to {audio_file_path}")

        # Play the audio
        try:
            subprocess.run(['mpg123', audio_file_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error playing audio: {e}")

    def _generate_file_name(self, description):
        """
        Generates a file name based on the provided description using ChatGPT.

        :param description: The script or summary of the script.
        :return: A suitable file name as a string.
        """
        messages = [{
            "role": "system",
            "content": "You are a file name generator. Using a brief description of a screenshot, you are going to create appropriate file names."
        }, {
            "role": "user",
            "content": f"Generate a concise, descriptive file name based on the following summary:\n{description}"
        }]

        result = self.client.chat.completions.create(
            model="gpt-4-0125-preview",  # Ensure you're using a valid model identifier
            messages=messages,
            max_tokens=100,
            temperature=0.7
        )

        if result.choices and len(result.choices) > 0:
            file_name = result.choices[0].message.content.strip()
        else:
            file_name = "default_filename"

        # Replace any illegal characters in file name
        file_name = "".join([c for c in file_name if c.isalnum() or c in [' ', '_', '-']]).rstrip()

        return file_name

    def _save_text_analysis(self, description, file_name_base):
        """
        Saves the AI-generated script as a text file, using a name generated by ChatGPT.

        :param description: The script to save. It can be a string or an object that needs to be converted to string.
        :param file_name_base: Base name for the file, generated by AI.
        """
        # Generate file name based on description
        text_filename = f"{file_name_base}_analysis.txt"
        text_file_path = os.path.join(self.text_analysis_dir, text_filename)

        # Ensure description is a string before writing
        if not isinstance(description, str):
            # Convert description to string if it's not already.
            # You might need to adapt this line if description is an object with specific fields to extract.
            description_str = str(description)
        else:
            description_str = description

        with open(text_file_path, 'w') as file:
            file.write(description_str)
        print(f"Saved text analysis to {text_file_path}")

if __name__ == "__main__":
    load_dotenv()
    # Customize the output directory path as needed
    screenspeak = ScreenSpeak("/mnt/c/Users/ptcap/OneDrive/Pictures/Screenshots", output_dir="LocalScreenSpeakOutputs")
    screenspeak.run()
