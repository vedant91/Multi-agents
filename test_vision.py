import os
import base64
import requests
import io
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# Create a dummy image with some text
img = Image.new('RGB', (800, 600), color = (255, 255, 255))
d = ImageDraw.Draw(img)
d.text((10,10), "dummy financial data FY24 Revenue 999999", fill=(0,0,0))

buffered = io.BytesIO()
img.save(buffered, format="JPEG")
img_str = base64.b64encode(buffered.getvalue()).decode()

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
payload = {
    "model": "llama-3.2-11b-vision-preview",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract all the text and table data from this document image accurately. Return only the raw text."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_str}"
                    }
                }
            ]
        }
    ],
    "temperature": 0.1
}

print("Calling Groq Vision API...")
response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=60)
print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    print(response.json()["choices"][0]["message"]["content"])
else:
    print(response.text)
