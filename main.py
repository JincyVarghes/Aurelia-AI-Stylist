import cv2
import threading
import sqlite3
import pyttsx3
import os
from dotenv import load_dotenv
from google import genai

from kivy.lang import Builder
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics.texture import Texture

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

# ===============================
# LOAD ENV VARIABLES
# ===============================
load_dotenv()
MY_API_KEY = os.getenv("MY_API_KEY")

Window.size = (360, 640)
CAPTURED_FILE = "aurelia_scan.jpg"
DB_FILE = "aurelia_users.db"

# ===============================
# DATABASE
# ===============================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("CREATE TABLE IF NOT EXISTS users (username TEXT UNIQUE, password TEXT)")
    conn.commit()
    conn.close()

def register(u, p):
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("INSERT INTO users VALUES (?,?)", (u, p))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def verify(u, p):
    conn = sqlite3.connect(DB_FILE)
    res = conn.execute(
        "SELECT * FROM users WHERE username=? AND password=?", (u, p)
    ).fetchone()
    conn.close()
    return res is not None

# ===============================
# VOICE
# ===============================
def speak(text):
    def run():
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.say(text)
            engine.runAndWait()
        except:
            pass
    threading.Thread(target=run).start()

# ===============================
# AI ANALYSIS
# ===============================
def analyze(app):
    try:
        if not MY_API_KEY:
            raise Exception("API KEY missing")

        client = genai.Client(api_key=MY_API_KEY)

        with open(CAPTURED_FILE, "rb") as f:
            img = f.read()

        prompt = """
You are a 2026 fashion stylist.
Return 3 short lines:
FACE: shape
STYLE: haircut name
WHY: short explanation
"""

        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=[
                prompt,
                genai.types.Part.from_bytes(data=img, mime_type="image/jpeg"),
            ],
        )

        Clock.schedule_once(lambda dt: app.show_result(response.text))
        speak(response.text)

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        Clock.schedule_once(lambda dt: app.show_result(error_msg))

# ===============================
# UI
# ===============================
KV = '''
MDScreenManager:
    LoginScreen:
    CameraScreen:
    ResultScreen:

<LoginScreen>:
    name: "login"
    md_bg_color: 0.07,0.07,0.1,1

    MDBoxLayout:
        orientation: "vertical"
        padding: 40
        spacing: 25

        MDLabel:
            text: "AURÉLIA"
            halign: "center"
            font_style: "H3"
            theme_text_color: "Custom"
            text_color: 0.3,0.9,1,1

        MDTextField:
            id: user
            hint_text: "Username"

        MDTextField:
            id: pwd
            hint_text: "Password"
            password: True

        MDRaisedButton:
            text: "LOGIN"
            on_release: root.login()

        MDRaisedButton:
            text: "REGISTER"
            on_release: root.register()

<CameraScreen>:
    name: "camera"
    md_bg_color: 0,0,0,1

    FloatLayout:
        Image:
            id: cam
            allow_stretch: True

        MDRaisedButton:
            text: "CAPTURE"
            pos_hint: {"center_x":0.5,"center_y":0.1}
            on_release: root.capture()

<ResultScreen>:
    name: "result"
    md_bg_color: 0.07,0.07,0.1,1

    MDBoxLayout:
        orientation: "vertical"
        padding: 20
        spacing: 20

        Image:
            id: photo
            size_hint_y: 0.5

        MDLabel:
            id: result_text
            text: "Analyzing..."
            theme_text_color: "Custom"
            text_color: 1,1,1,1

        MDRaisedButton:
            text: "NEW SCAN"
            on_release: app.root.current="camera"
'''

# ===============================
# SCREENS
# ===============================
class LoginScreen(MDScreen):
    def login(self):
        if verify(self.ids.user.text, self.ids.pwd.text):
            self.manager.current = "camera"
        else:
            self.ids.user.error = True

    def register(self):
        register(self.ids.user.text, self.ids.pwd.text)

class CameraScreen(MDScreen):
    def on_enter(self):
        self.cap = cv2.VideoCapture(0)
        self.current_frame = None
        Clock.schedule_interval(self.update, 1 / 30)

    def update(self, dt):
        ret, frame = self.cap.read()
        if ret:
            # ✅ Correct preview
            frame = cv2.flip(frame, 0)
            frame = cv2.flip(frame, 1)

            self.current_frame = frame.copy()

            buf = frame.tobytes()
            tex = Texture.create(
                size=(frame.shape[1], frame.shape[0]),
                colorfmt='bgr'
            )
            tex.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.ids.cam.texture = tex

    def capture(self):
        if self.current_frame is not None:
            cv2.imwrite(CAPTURED_FILE, self.current_frame)

            Clock.unschedule(self.update)
            self.cap.release()

            self.manager.current = "result"

            threading.Thread(
                target=analyze,
                args=(MDApp.get_running_app(),)
            ).start()

class ResultScreen(MDScreen):
    pass

# ===============================
# APP
# ===============================
class AureliaApp(MDApp):
    def build(self):
        init_db()
        return Builder.load_string(KV)

    def show_result(self, text):
        scr = self.root.get_screen("result")

        img = cv2.imread(CAPTURED_FILE)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        buf = img.tobytes()
        tex = Texture.create(
            size=(img.shape[1], img.shape[0]),
            colorfmt='rgb'
        )
        tex.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')

        scr.ids.photo.texture = tex
        scr.ids.result_text.text = text

if __name__ == "__main__":
    AureliaApp().run()