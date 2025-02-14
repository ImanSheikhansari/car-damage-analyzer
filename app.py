import os
import re
import base64
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from openai import OpenAI
import google.generativeai as genai
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Configuration
load_dotenv()

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize AI clients (using try-except for better error handling)
try:
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    print(f"Error initializing AI clients: {e}")
    exit(1)  # Exit if API keys are not configured correctly


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_analysis(content):
    try:
        vehicle = {}
        damages = []

        # Improved regex for vehicle info extraction (more flexible)
        vehicle_match = re.search(r"###\s*1\.\s*Vehicle\s*Identification\n([\s\S]*?)(?=\n###|\Z)", content, re.IGNORECASE)
        if vehicle_match:
            vehicle_info = vehicle_match.group(1)
            vehicle["make"] = extract_value(vehicle_info, "make|manufacturer")
            vehicle["model"] = extract_value(vehicle_info, "model")
            vehicle["year"] = extract_value(vehicle_info, "year")
            vehicle["plate"] = extract_value(vehicle_info, "license plate|plate")

        # Improved and more robust regex for damage assessment
        damages_match = re.search(r"###\s*2\.\s*Damage\s*Assessment\n([\s\S]*?)(?=\n###|\Z)", content, re.IGNORECASE)
        if damages_match:
            damage_items = re.findall(r"- (.*?) \((.*?)\) - (minor|moderate|severe|جزئی|متوسط|شدید)", damages_match.group(1))
            for part, damage_type, severity in damage_items:
                damages.append({
                    "part": part.strip(),
                    "type": damage_type.strip(),
                    "severity": translate_severity(severity),
                    "action": "تعویض" if severity.lower() in ["severe", "شدید"] else "تعمیر",
                    "cost": estimate_cost(severity)
                })

        total_cost = extract_value(content, "total estimated repair cost|total cost")
        repair_time = extract_value(content, "estimated repair timeline|repair time")
        safety_status = "ایمن" if re.search(r"safe to drive: yes|safe: yes", content, re.IGNORECASE) else "غیر ایمن"

        return {
            "vehicle": vehicle,
            "damages": damages,
            "total_cost": total_cost,
            "repair_time": repair_time,
            "safety_status": safety_status,
            "content": content
        }

    except Exception as e:
        print(f"Parsing error: {str(e)}")
        return {"content": content}


def translate_severity(severity):
    severity_map = {
        "minor": "جزئی",
        "moderate": "متوسط",
        "severe": "شدید",
        "جزئی": "جزئی",
        "متوسط": "متوسط",
        "شدید": "شدید"
    }
    return severity_map.get(severity.lower(), severity)

def extract_value(text, keys):  # keys can be a pipe-separated string
    for key in keys.split("|"):
        pattern = rf"{key.strip()}:\s*(.*?)(?=\n|$)"  # Improved regex to handle variations in spacing
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return "---"

def estimate_cost(severity):
    costs = {
        "minor": "1-2 میلیون تومان",
        "moderate": "3-5 میلیون تومان",
        "severe": "6-10 میلیون تومان"
    }
    return costs.get(severity.lower(), "---")


def analyze_with_openai(image_data, language):
    try:
        prompt = ("As a certified automotive damage assessor, provide a detailed report including: "
                  "1. Vehicle identification 2. Damage assessment 3. Repair recommendations "
                  "4. Cost estimation 5. Safety analysis. Use professional terminology.")

        response = openai_client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }},
                ],
            }],
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI Error: {str(e)}")
        return "Analysis failed. Please try again."

def analyze_with_gemini(image_data, language):
    try:
        model = genai.GenerativeModel('gemini-pro-vision')
        response = model.generate_content([
            "Analyze this car damage image professionally. Include: vehicle details, damage assessment, "
            "repair recommendations, cost estimates, and safety analysis.",
            genai.types.Blob(mime_type='image/jpeg', data=base64.b64decode(image_data))
        ])
        return response.text
    except Exception as e:
        print(f"Gemini Error: {str(e)}")
        return "Analysis failed. Please try again."


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files['image']
    if not file or file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file format"}), 400

    try:
        image_data = base64.b64encode(file.read()).decode('utf-8')
        engine = request.form.get("api", "openai")
        language = "persian" if request.form.get("language") == "persian" else "english"

        if engine == "openai":
            analysis = analyze_with_openai(image_data, language)
        else:
            analysis = analyze_with_gemini(image_data, language)

        report = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "engine": "OpenAI" if engine == "openai" else "Google Gemini",
            **parse_analysis(analysis)
        }

        return jsonify(report)  # Return JSON report

    except Exception as e:
        print(f"Analysis error: {str(e)}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@app.route("/report")
def report():
    return render_template("report.html")  # Ensure report.html exists in templates

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)  # debug=True for development (remove in production)