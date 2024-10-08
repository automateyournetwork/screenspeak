# screenspeak
AI as a hotkey - Transform your screenshots into real-time audio analysis with chatGPT Vision and Text to Speech

## ChatGPT Version (main branch of git repository)
Step 1: Clone the Repository
Clone the ScreenSpeak repository to your local machine:

```console
git clone https://github.com/automateyournetwork/screenspeak.git
```

Step 2: Add .env File
Navigate to the cloned repository folder and create a .env file. Add your OpenAI API key to this file:

```console
OPENAI_API_KEY=<your api key here from platform.openai.com>
```

Step 3: Create a Python Virtual Environment
Set up a virtual environment to manage the project's dependencies independently of other Python projects on your system.

For Windows
Open a command prompt and run:

```console
python -m venv venv
.\venv\Scripts\activate
```

For WSL/Ubuntu
Open your terminal and run:

```console
python3 -m venv venv
source venv/bin/activate
```

Step 4: Install Dependencies
With the virtual environment activated, install the project dependencies:

```console
pip install -r requirements.txt
```

Step 5: Update Screenshots Folder Path
Before running the script, update the path to your screenshots folder in the screenspeak.py file. Modify line 17 to match your screenshots directory:

```python
screenspeak = ScreenSpeak("/mnt/c/Users/<YOUR USERNAME HERE>/OneDrive/Pictures/Screenshots")
```

Replace <YOUR USERNAME HERE> with your actual Windows username.

This path is the Ubuntu WSL path - it may differ to be a regular Windows path to your Screenshots folder; this assumes they are on OneDrive

Step 6: Run the Script
Finally, run the ScreenSpeak script:

```console
python screenspeak.py
```

Step 7: Take a screenshot 
Once the script is running - you can press Windows-Key + PrintScreen; or use the SnippingTool; to take a screenshot 
In a few seconds an MP3 will play over your speakers / headphones with an AI analysis and explaination of the screenshot that was taken. 

## Ollama (free; local) version with Google Text To Speech
Step 1: Clone the Repository
Clone the ScreenSpeak repository to your local machine:

```console
git clone https://github.com/automateyournetwork/screenspeak.git
```

Step 2: Change branches to the ollama branch 
Either in VS Code by clicking the branch icon and selecting Ollama from the drop down or via the console change the ollama branch of this repository


```console
$ git checkout ollama
```

Download ollama (ollama.com) for Windows or Linux and install it 

Download (ollama pull llava) the Llava model 

```console
$ ollama pull llava
```

Start ollama 

```console
ollama start
```

Step 3: Create a Python Virtual Environment
Set up a virtual environment to manage the project's dependencies independently of other Python projects on your system.

For Windows
Open a command prompt and run:

```console
python -m venv venv
.\venv\Scripts\activate
```

For WSL/Ubuntu
Open your terminal and run:

```console
python3 -m venv venv
source venv/bin/activate
```

Step 4: Install Dependencies
With the virtual environment activated, install the project dependencies:

```console
pip install -r requirements.txt
```

Step 5: Update Screenshots Folder Path
Before running the script, update the path to your screenshots folder in the screenspeak.py file. Modify line 17 to match your screenshots directory:

```python
screenspeak = ScreenSpeak("/mnt/c/Users/<YOUR USERNAME HERE>/OneDrive/Pictures/Screenshots")
```

Replace <YOUR USERNAME HERE> with your actual Windows username.

This path is the Ubuntu WSL path - it may differ to be a regular Windows path to your Screenshots folder; this assumes they are on OneDrive

Step 6: Run the Script
Finally, run the ScreenSpeak script:

```console
python screenspeak.py
```

Step 7: Take a screenshot 
Once the script is running - you can press Windows-Key + PrintScreen; or use the SnippingTool; to take a screenshot 
In a few seconds an MP3 will play over your speakers / headphones with an AI analysis and explaination of the screenshot that was taken. 


Enjoy using ScreenSpeak!
