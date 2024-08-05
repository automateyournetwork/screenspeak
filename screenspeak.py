import io
import os
import time
import base64
import shutil
from PIL import Image
from datetime import datetime
import ollama

class ScreenSpeak:
    def __init__(self, screenshot_dir, poll_interval=10, output_dir="ScreenSpeakOutputs"):
        """
        Initializes the ScreenSpeak with the directory to monitor and polling interval.

        :param screenshot_dir: Directory to monitor for new screenshots.
        :param poll_interval: Time in seconds between directory checks for new screenshots.
        :param output_dir: Directory to save text analysis and audio files locally.
        """
        self.screenshot_dir = screenshot_dir
        self.poll_interval = poll_interval
        self.start_time = datetime.now().timestamp()
        self.last_processed = None

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
            # Generate script using the Llava model from Ollama
            description = self._generate_script(screenshot_path)

            # Generate a file name based on the description
            file_name_base = self._generate_file_name(description)

            # Save the description
            self._save_text_analysis(description, file_name_base + "_llava")

            # Copy the original screenshot
            self._copy_screenshot(screenshot_path, file_name_base)
        except Exception as e:
            print(f"Error processing screenshot: {e}")

    def _generate_script(self, screenshot_path):
        """
        Generates a voice-over script for the screenshot using the Llava model from Ollama.

        :param screenshot_path: Path to the screenshot file.
        :return: Generated script as a string.
        """
        with Image.open(screenshot_path) as img:
            img = img.convert("RGB")
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # Call the Ollama API to generate the description
        res = ollama.chat(
            model="llava",
            messages=[
                {
                    'role': 'user',
                    'content': 'Describe this from the Selector.ai dashboard. Please pay attention to the text in the image and help provide a network analysis of the screenshot to help a user understand what they are looking at:',
                    'images': [base64_image]
                }
            ]
        )
        
        return res['message']['content']

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

    def _generate_file_name(self, description):
        """
        Generates a file name based on the provided description.

        :param description: The script or summary of the script.
        :return: A suitable file name as a string.
        """
        # Generate a concise, descriptive file name
        file_name = "".join([c for c in description[:50] if c.isalnum() or c in [' ', '_', '-']]).rstrip()
        return file_name

    def _save_text_analysis(self, description, file_name_base):
        """
        Saves the AI-generated script as a text file, using a name generated by the Llava model.

        :param description: The script to save.
        :param file_name_base: Base name for the file.
        """
        text_filename = f"{file_name_base}_analysis.txt"
        text_file_path = os.path.join(self.text_analysis_dir, text_filename)

        with open(text_file_path, 'w') as file:
            file.write(description)
        print(f"Saved text analysis to {text_file_path}")

if __name__ == "__main__":
    # Customize the output directory path as needed
    screenspeak = ScreenSpeak("/mnt/c/Users/ptcap/OneDrive/Pictures/Screenshots", output_dir="LocalScreenSpeakOutputs")
    screenspeak.run()
