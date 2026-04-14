import os
import base64
import requests
import io
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

img = Image.new('RGB', (800, 600), color = (255, 255, 255))
d = ImageDraw.Draw(img)
d.text((10,10), "dummy financial data FY24 Revenue 999999", fill=(0,0,0))
buffered = io.BytesIO()
img.save(buffered, format="JPEG")
img_str = base64.b64encode(buffered.getvalue()).decode()

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

payload = {
  "contents": [
    {
      "parts": [
        {"text": "Extract all the text and table data from this document image accurately. Return only the raw text."},
        {
          "inline_data": {
            "mime_type": "image/jpeg",
            "data": img_str
          }
        }
      ]
    }
  ],
  "generationConfig": {
    "temperature": 0.1
  }
}

print("Calling Gemini API...")
response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)
print(response.status_code)
if response.status_code == 200:
    print(response.json()["candidates"][0]["content"]["parts"][0]["text"])
else:
    print(response.text)
