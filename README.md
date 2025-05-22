# Dia - Personal Assistant

A smart personal assistant application that analyzes email and chat data to suggest actions and provide detailed execution plans. Built with Flask and Gemini AI.

## Features

- Analyzes emails and chat messages to identify actionable items
- Generates step-by-step execution plans for each action
- Uses personal data when needed (with privacy in mind)
- Modern dark mode UI with responsive design

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Gemini API key (get one from [Google AI Studio](https://makersuite.google.com/app/apikey))

### Installation

1. Clone the repository:
```bash
git clone https://github.com/harshshahgit/dia.git
cd dia
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Copy the example environment file
cp .env.example .env
# Edit .env and add your Gemini API key
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to `http://localhost:5001`

## Project Structure

- `app.py` - Main Flask application
- `user_data.json` - Example user personal data
- `static/` - CSS and JavaScript files
- `templates/` - HTML templates

## License

MIT 