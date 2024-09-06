import threading
from tkinter import Tk, Label
from PIL import Image, ImageTk, ImageSequence
import pyttsx3
import datetime
import speech_recognition as sr
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import os
import webbrowser
import pywhatkit as kit
import mss
import pyautogui
import cv2
import numpy as np
import psutil
import requests
import tempfile
from playsound import playsound
import subprocess
import openai

# Define the play_gif function
def play_gif():
    def run():
        root = Tk()
        root.geometry("1000x500")
        img = Image.open("ironsnap2.gif")  # Replace with your GIF file
        lbl = Label(root)
        lbl.place(x=0, y=0)
        
        frames = [ImageTk.PhotoImage(frame.resize((1000, 500))) for frame in ImageSequence.Iterator(img)]
        while True:
            for frame in frames:
                lbl.config(image=frame)
                root.update()
                root.after(50)  # Adjusted to use Tkinter's after method
                
    gif_thread = threading.Thread(target=run, daemon=True)
    gif_thread.start()

# Define the VirtualAssistant class
class VirtualAssistant:
    def __init__(self, author, api_key, media_dir,weather_api_key, openai_api_key):
        self.author = author
        self.api_key = api_key
        self.media_dir = media_dir
        self.weather_api_key = weather_api_key
        self.openai_api_key = openai_api_key
        openai.api_key = self.openai_api_key
        self.screenshot_file = f"{media_dir}/screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        self.recording_file = f"{media_dir}/recording_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
        self.screen_recording = False
        self.memory_file = "memory.txt"
        self.last_question = ""
        self.last_question = ""
        self.registration_dir = os.path.join(media_dir, "registrations")

        # Initialize text-to-speech engine
        self.engine = pyttsx3.init('sapi5')
        self.engine.setProperty('voice', self.engine.getProperty('voices')[0].id)
        if not os.path.exists(self.registration_dir):
            os.makedirs(self.registration_dir) 

        # Initialize Gemini API
        self.llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=self.api_key)
        self.vision_model = ChatGoogleGenerativeAI(model="gemini-pro-vision", google_api_key=self.api_key)

        # Ensure media directory exists
        if not os.path.exists(self.media_dir):
            os.makedirs(self.media_dir)
    def generate_code(self, prompt):
        """Generate code based on a prompt using OpenAI Codex."""
        try:
            response = openai.Completion.create(
                engine="code-davinci-002",  # Use the appropriate engine
                prompt=prompt,
                max_tokens=150,  # Adjust based on the expected length of the code
                temperature=0.2
            )
            code = response.choices[0].text.strip()
            return code
        except Exception as e:
            print(f"Error generating code: {e}")
            return "I'm having trouble generating the code."        
    def handle_registration(self):
        """Handle new registration."""
        self.speak("Opening camera for registration. Please look at the camera.")
        
        # Open camera and capture image
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.speak("Failed to open camera.")
            return
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            self.speak("Failed to capture image.")
            return
        
        # Save captured image
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        image_file = os.path.join(self.registration_dir, f"photo_{timestamp}.jpg")
        cv2.imwrite(image_file, frame)
        
        self.speak("Image captured. Now, please tell me your name.")
        name = self.listen()
        if name == "none":
            self.speak("I didn't catch your name.")
            return
        
        self.speak("And what is your place?")
        place = self.listen()
        if place == "none":
            self.speak("I didn't catch your place.")
            return
        
        # Save name and place
        registration_file = os.path.join(self.registration_dir, f"info_{timestamp}.txt")
        with open(registration_file, "w") as file:
            file.write(f"Name: {name}\nPlace: {place}\n")
        
        self.speak(f"Registration complete. Photo and details saved.")        
           

    def speak(self, audio):
        """Convert text to speech."""
        self.engine.say(audio)
        self.engine.runAndWait()

    def listen(self):
        """Listen and recognize user speech."""
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening...")
            r.pause_threshold = 1.5
            audio = r.listen(source)
        try:
            print("Recognizing...")
            query = r.recognize_google(audio, language='en-in')
            print(f"User said: {query} \n")
            return query
        except sr.UnknownValueError:
            print(f"Sorry {self.author}, I did not understand that.")
            return "None"
        except sr.RequestError as e:
            print(f"Sorry {self.author}, there was an issue with the speech recognition service: {e}")
            return "None"

    def converse(self, query):
        """Use Gemini API to process the query."""
        base_prompt = (
            "You are a virtual assistant that can identify actions based on a statement. "
            "If a suitable action is found respond with action name only. If no suitable action can be identified do not say things like I cannot perform action etc, "
            "instead respond to the statement normally as if it were a normal conversation and not a command. List of available actions are: "
            "'ACTION_AWAKEN', 'ACTION_SLEEP', 'ACTION_APPEAR', 'ACTION_EXIT', 'ACTION_OPEN_NOTEPAD', 'ACTION_OPEN_WORD', 'ACTION_OPEN_EXCEL', "
            "'ACTION_OPEN_POWERPOINT', 'ACTION_OPEN_COMMAND_PROMPT', 'ACTION_OPEN_CAMERA', 'ACTION_OPEN_CALCULATOR', 'ACTION_FIND_MY_IP', "
            "'ACTION_OPEN_YOUTUBE', 'ACTION_CHECK_WEATHER', 'ACTION_TAKE_SCREENSHOT', 'ACTION_START_SCREEN_RECORDING', 'ACTION_STOP_SCREEN_RECORDING', "
            "'ACTION_MINIMIZE_DISAPPEAR_APPLICATION', 'ACTION_OPEN_BROWSER_WEBSITE', 'ACTION_WHAT_DO_YOU_SEE_IN_CAMERA'. "
        )
        prompt = base_prompt + f"Statement prompt is: '{query}'"
        print(f"Sending prompt to API: {prompt}")  # Debugging line
        try:
            result = self.llm.invoke(prompt)
            response = result.content.strip()
            print(f"API response: {response}")  # Debugging line
            return response
        except Exception as e:
            print(f"Error during API call: {e}")
            return "I'm having trouble processing that request."

    def describe_image(self):
        """Describe the image using Gemini API."""
        if not os.path.exists(self.screenshot_file):
            return "Screenshot file not found."
        
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": "This is an image of a video feed. Describe only what you see in it, and absolutely nothing else."
                },
                {"type": "image_url", "image_url": self.screenshot_file}
            ]
        )
        try:
            result = self.vision_model.invoke([message])
            return result.content.strip()
        except Exception as e:
            print(f"Error describing image: {e}")
            return "I'm having trouble describing the image."

    def check_battery(self):
        """Check and return battery percentage."""
        try:
            battery = psutil.sensors_battery()
            if battery:
                percent = battery.percent
                plug = "plugged in" if battery.power_plugged else "not plugged in"
                return f"Your battery is at {percent}% and is currently {plug}."
            else:
                return "Battery information is not available."
        except Exception as e:
            print(f"Error checking battery: {e}")
            return "Sorry, I couldn't retrieve battery information."

    def save_memory(self, question, answer):
        """Save user question and answer to memory file."""
        with open(self.memory_file, "w") as file:  # Overwrite file with the latest question
            file.write(f"Q: {question}\nA: {answer}\n\n")
        self.last_question = question  # Update last question

    def retrieve_memory(self):
        """Retrieve the last saved question and answer."""
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r") as file:
                content = file.read()
                if content:
                    return content.strip()
                else:
                    return "No memory found."
        else:
            return "No memory found."

    def handle_action(self, intent):
        """Handle actions based on the intent."""
        actions = {
            'ACTION_WHAT_DO_YOU_SEE_IN_CAMERA': lambda: self.speak(self.describe_image()),
            'ACTION_OPEN_YOUTUBE': lambda: self.open_website('https://www.youtube.com'),
            'ACTION_TAKE_SCREENSHOT': lambda: self.take_screenshot(),
            'ACTION_START_SCREEN_RECORDING': lambda: self.start_screen_recording(),
            'ACTION_STOP_SCREEN_RECORDING': lambda: self.stop_screen_recording(),
            'ACTION_OPEN_NOTEPAD': lambda: self.open_notepad(),
            'ACTION_CHECK_BATTERY': lambda: self.speak(self.check_battery()),
            'ACTION_OPEN_CAMERA': lambda: self.open_camera_and_identify()
        }
        action = actions.get(intent)
        if action:
            try:
                action()
            except Exception as e:
                print(f"Failed to execute action '{intent}': {e}")
        else:
            self.speak("Sorry, I didn't understand that command.")
    def get_weather(self, city):
        """Fetch the weather for a particular city."""
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.weather_api_key}&units=metric"
        try:
            response = requests.get(url)
            data = response.json()
            if response.status_code == 200:
                city_name = data.get("name")
                weather_description = data.get("weather", [{}])[0].get("description", "No description")
                temperature = data.get("main", {}).get("temp", "N/A")
                return f"The current weather in {city_name} is {weather_description} with a temperature of {temperature}°C."
            else:
                return "Sorry, I couldn't retrieve the weather information."
        except Exception as e:
            print(f"Error retrieving weather: {e}")
            return "Sorry, there was an error retrieving the weather information."        

    def handle_direct_commands(self, query):
        """Handle specific commands directly."""
        if 'battery percentage' in query:
            self.speak(self.check_battery())
        if 'write code for' in query:
            self.speak("What kind of code would you like me to write?")
            code_prompt = self.listen()
            if code_prompt != "none":
                code = self.generate_code(code_prompt)
                self.speak("Here is the code I generated:")
                print(code)  # Display the code in the console or UI
                # Optionally, save to a file
                code_file = os.path.join(self.media_dir, "generated_code.py")
                with open(code_file, "w") as file:
                    file.write(code)
                self.speak(f"The code has been saved as {code_file}.")    
        elif 'remember' in query:
            self.speak("What should I remember?")
            memory_content = self.listen()
            if memory_content != "none":
                self.save_memory(memory_content, "Stored")
                self.speak(f"Remembered: {memory_content}")
            else:
                self.speak("I didn't catch what you wanted to remember.")
        elif 'what did I say before' in query:
            self.speak(self.retrieve_memory())
        elif 'weather' in query and 'in' in query:
            city = query.split('in', 1)[1].strip()
            weather_info = self.get_weather(city)
            self.speak(weather_info)    
        elif 'guess the person' in query:
            self.open_camera_and_identify()
        elif 'open' in query and 'website' in query:
            self.speak("Which website would you like to open?")
            website = self.listen().lower()
            if website != "none":
                self.open_website(website)
            else:
                self.speak("I didn't catch the website name.")
        elif 'open google' in query:
            self.open_website('https://www.google.com')
        elif 'open youtube' in query:
            self.open_website('https://www.youtube.com')
        elif 'open Zomato' in query:
            self.open_website('https://www.zomato.com')
        elif 'open ola' in query:
            self.open_website('https://www.ola.com')
        elif 'open discord' in query:
            self.open_website('https://www.discord.com')
        elif 'open github' in query:
            self.open_website('https://www.gihub.com')
        elif 'open twitter' in query:
            self.open_website('https://www.twitter.com')
        elif 'open instagram' in query:
            self.open_website('https://www.instagram.com')
        elif 'open whatapp' in query:
            self.open_website('https://www.whatsappweb.com')
        elif 'open gmail' in query:
            self.open_website('https://www.gmail.com')
        elif 'open netflix' in query:
            self.open_website('https://www.netflix.com')
        elif 'open hotstar' in query:
            self.open_website('https://www.hotstar.com')
        elif 'open zee5' in query:
            self.open_website('https://www.zee5.com')
        elif 'open chatgpt' in query:
            self.open_website('https://www.chatgpt.com')
        elif 'open Linkedin' in query:
            self.open_website('https://www.linkedin.com')
        elif 'open swiggy' in query:
            self.open_website('https://www.swiggy.com')
        elif 'open movies' in query:
            self.open_website('https://www.actvid.com')
        elif 'open spotify' in query:
            self.open_website('https://www.spotify.com')                                                                
            

        elif 'open command prompt' in query:
              os.system("start cmd")
        elif 'open microsoft word' in query:
              os.system("start winword")
        elif 'open microsoft excel' in query:
              os.system("start excel")
        elif 'open microsoft powerpoint' in query:
              os.system("start powerpnt")
        elif 'open microsoft paint' in query:
              os.system("start mspaint")
        elif 'open calculator' in query:
              os.system("start calc")
        elif 'open control panel' in query:
              os.system("control")
        elif 'open settings' in query:
              os.system("start ms-settings:")
        elif 'open task manager' in query:
              os.system("start taskmgr")
        elif 'open powershell' in query:
              os.system("start powershell")
        elif 'open explorer' in query:
              os.system("start explorer")                                                                   
        elif 'open' in query and 'flipkart' in query:
            self.open_website('https://www.amazon.com')
            self.last_opened_website = 'Amazon'
            self.speak("Opened Amazon instead of Flipkart.")
        elif 'why you opened amazon' in query and self.last_opened_website == 'Amazon':
            self.play_audio("change.mp3")
        elif 'play youtube' in query:
            self.speak("What should I search for on YouTube?")
            song_query = self.listen().lower()
            if song_query != "none":
                kit.playonyt(song_query)
                self.speak(f"Playing '{song_query}' on YouTube.")
            else:
                self.speak("I didn't catch the song name.")
        elif 'take screenshot' in query:
            self.take_screenshot()
        elif 'start screen recording' in query:
            self.start_screen_recording()
          
        elif 'stop screen recording' in query:
            self.stop_screen_recording()
        elif 'search for' in query:
            search_terms = query.split('search for', 1)[1].strip()
            self.search_google(search_terms)
           
        else:
            return False
        return True

    def search_google(self, query):
        """Search for a query on Google."""
        search_url = f"https://www.google.com/search?q={query}"
        try:
            webbrowser.open(search_url)
            self.speak(f"Searching for {query} on Google.")
        except Exception as e:
            self.speak(f"Failed to perform Google search. Error: {e}")

    def open_website(self, url):
        """Open a specific website."""
        try:
            webbrowser.open(url)
            self.speak(f"Opening {url}")
        except Exception as e:
            self.speak(f"Failed to open {url}. Error: {e}")

    def take_screenshot(self):
        """Take a screenshot and save it to the specified folder."""
        with mss.mss() as sct:
            screenshot = sct.grab(sct.monitors[1])
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=self.screenshot_file)
            self.speak(f"Screenshot taken and saved as {self.screenshot_file}")

    def start_screen_recording(self):
        """Start screen recording."""
        self.screen_recording = True
        self.speak("Screen recording started.")
        
        def record_screen():
            fourcc = cv2.VideoWriter_fourcc(*"XVID")
            out = cv2.VideoWriter(self.recording_file, fourcc, 8.0, (1920, 1080))
            while self.screen_recording:
                img = pyautogui.screenshot()
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                out.write(frame)
            out.release()

        recording_thread = threading.Thread(target=record_screen)
        recording_thread.start()

    def stop_screen_recording(self):
        """Stop screen recording."""
        if self.screen_recording:
            self.screen_recording = False
            self.speak(f"Screen recording stopped. The file is saved as {self.recording_file}.")
        else:
            self.speak("No active screen recording to stop.")

    def open_notepad(self):
        """Open Notepad and type the text."""
        try:
            # Open Notepad
            subprocess.Popen(['notepad.exe'])
            self.speak("Notepad opened. What would you like to type?")
            
            # Listen to what the user wants to type
            text_to_type = self.listen()
            if text_to_type != "none":
                # Wait for Notepad to be ready and type text
                pyautogui.write(text_to_type, interval=0.1)
                self.speak(f"Typed '{text_to_type}' in Notepad.")
            else:
                self.speak("I didn't catch what you wanted to type.")
        except Exception as e:
            self.speak(f"Failed to open Notepad. Error: {e}")
            print(f"Error: {e}")

    def open_camera_and_identify(self):
        """Open camera, capture an image, and identify the person."""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.speak("Failed to open camera.")
            return

        self.speak("Please show me the person you want to identify.")
        ret, frame = cap.read()
        if not ret:
            self.speak("Failed to capture image from camera.")
            cap.release()
            return
        
        temp_image_path = tempfile.mktemp(suffix=".jpg")
        cv2.imwrite(temp_image_path, frame)
        cap.release()

        try:
            api_url = "https://api.example.com/identify_person"  # Replace with your API endpoint
            files = {'image': open(temp_image_path, 'rb')}
            response = requests.post(api_url, files=files)
            if response.status_code == 200:
                person_name = response.json().get('name', 'Unknown')
                self.speak(f"I think the person is {person_name}.")
            else:
                self.speak("Failed to identify the person.")
        except Exception as e:
            print(f"Error identifying person: {e}")
            self.speak("Error occurred while identifying the person.")

    def play_audio(self, file_name):
        audio_path = os.path.join(self.media_dir, file_name)
        if os.path.exists(audio_path):
            playsound(audio_path)
        else:
            self.speak(f"Audio file {file_name} not found.")
        
    def run(self):
        """Run the assistant and listen for commands."""
        self.speak(f"Namaskara {self.author}, I am your PA. How can I help you?")
        while True:
            query = self.listen().lower()
            if query:
                if self.handle_direct_commands(query):
                    continue
                elif 'new registration' in query:
                    self.handle_registration()

                intent = self.converse(query)
                print(f"Model response: {intent}")
                if intent.startswith('ACTION_'):
                    self.handle_action(intent)
                else:
                    self.speak(intent)

# Run both audio, GIF, and assistant
def main():
    # Play the introductory audio file
    audio_file = "intro.mp3"  # Replace with your audio file
    playsound(audio_file)

    play_gif()  # Start the GIF playback in a separate thread

    # Initialize and run the virtual assistant
    author = "Boss"
    api_key = "AIzaSyAyDweyTVxV-sf5eUBAo96vlag2W5dPDwc"
    weather_api_key = "f749375b5cf6ade84c1f001ff17cd80c"
    openai_api_key = "sk-bIbSdPLDNzg7BWMjvgUbuWiuJ4JZWDUsoWOqbJmFn2T3BlbkFJcgU08O6Qu3Jk5_qiJTe4xSUVu3keiuiGzvKDOHghYA"  # Replace with your actual API key
    media_dir = "media"
    
    assistant = VirtualAssistant(author, api_key, media_dir, weather_api_key, openai_api_key)
    assistant.run()

if __name__ == "__main__":
    main()
