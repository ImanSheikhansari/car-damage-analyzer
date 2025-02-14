# Car Damage Analysis

This is a minimal viable product (MVP) for a car damage analysis web application. It uses AI to analyze images of car damage and provide a report.

## Technologies Used

*   Python
*   Flask
*   OpenAI API
*   Google Gemini API
*   Tailwind CSS

## Setup

1.  Clone the repository: `git clone https://github.com/your-username/car-damage-analysis.git`
2.  Create a virtual environment: `python3 -m venv venv` (or `python -m venv venv`)
3.  Activate the virtual environment: `source venv/bin/activate` (Linux/macOS) or `venv\Scripts\activate` (Windows)
4.  Install dependencies: `pip install -r requirements.txt`
5.  Create a `.env` file and add your OpenAI and Gemini API keys.
6.  Run the app: `python app.py`

## Usage

1.  Visit `http://127.0.0.1:8080` in your browser.
2.  Upload an image of car damage.
3.  Select the AI engine and report language.
4.  Click "آپلود و تحلیل".
5.  View the report.

## Deployment

This application is designed to be deployed on Render.  See the deployment instructions below.

## Deployment on Render

1.  Create a Render account.
2.  Connect your GitHub repository to Render.
3.  Render will automatically detect that this is a Python Flask app.
4.  Set the environment variables (API keys) in the Render dashboard.

## Contributing

Contributions are welcome!

## License

MIT
