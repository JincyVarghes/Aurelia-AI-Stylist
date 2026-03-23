from google import genai
import os

# 1. SETUP YOUR KEY
# Replace the text inside quotes with your actual API Key from earlier
MY_API_KEY = "AIzaSyBccWgpiI-aEzu990K8yCiGTi4nwR0Q4-A"

def analyze_image(image_path):
    try:
        print(f"🧠 AI: Connecting to brain...")
        client = genai.Client(api_key=MY_API_KEY)
        
        # Open the image file
        with open(image_path, "rb") as f:
            image_data = f.read()

        # Send to Gemini
        print(f"🧠 AI: Analyzing photo...")
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[
                "Analyze this person's hair. 1. What is the hair type? 2. Suggest 1 hairstyle. Keep it short.",
                genai.types.Part.from_bytes(data=image_data, mime_type="image/jpeg")
            ]
        )
        
        return response.text

    except Exception as e:
        return f"Error: {str(e)}"