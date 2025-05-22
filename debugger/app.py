from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
import uuid # For generating unique IDs for actions
import requests # For calling Gemini API
import json # For handling JSON data
import os  # For file path operations
from dotenv import load_dotenv # For loading environment variables

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, 
            static_url_path='/static', 
            static_folder='static',
            template_folder='templates')
CORS(app) # Enable CORS for local development

# --- Gemini API Configuration ---
# Get API key from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    print("WARNING: No Gemini API key found. Please set GEMINI_API_KEY in .env file.")
# Note: GEMINI_API_URL is constructed dynamically in call_gemini_flash_model now

# --- JSON Schema for LLM Action Generation ---
ACTION_GENERATION_SCHEMA = {
  "type": "ARRAY",
  "items": {
    "type": "OBJECT",
    "properties": {
      "action_title": {
        "type": "STRING",
        "description": "A concise title for the action to be taken. E.g., 'Follow up on driving license renewal.' or 'Research gardening sets for Mom's birthday.' Max 15 words."
      },
      "source_type": {
        "type": "STRING",
        "enum": ["Email", "Chat"],
        "description": "The type of data source (Email or Chat)."
      },
      "source_id": {
        "type": "STRING",
        "description": "The unique ID of the source email or chat object (e.g., 'email_1', 'chat_2') from the provided data."
      },
      "source_trigger_text": {
        "type": "STRING",
        "description": "The specific text snippet from the source that indicates this action. Max 30 words."
      },
      "details_for_llm2": {
        "type": "STRING",
        "description": "Key information and context for a subsequent AI to process this action. Include relevant entities, dates, and specific instructions. Max 50 words. E.g., 'License ID XZ12345 mentioned in email from DMV. Renewal needed by July 30th. Find relevant documents, outline renewal steps.'"
      }
    },
    "required": ["action_title", "source_type", "source_id", "source_trigger_text", "details_for_llm2"]
  }
}

# --- User Data Store ---
USER_DATA_FILE = 'user_data.json'

def load_user_data():
    """Loads user data from the JSON file."""
    try:
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {USER_DATA_FILE} not found. No personal data will be available.")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Could not decode {USER_DATA_FILE}. Please check its format.")
        return {}

def get_user_data_keys(keys_to_find):
    """Fetches specific keys from user data."""
    user_data = load_user_data()
    found_data = {}
    missing_keys = []
    for key in keys_to_find:
        if key in user_data:
            found_data[key] = user_data[key]
        else:
            missing_keys.append(key)
    return found_data, missing_keys

# --- Mock Data ---
mock_data = {
        "chats": [
        {
            "id": "chat_1",
            "contact_name": "Vikash",
            "platform": "WhatsApp",
            "messages": [
                {"sender": "Vikash", "text": "All fine bhai. But bone is chipped and it will remain like that for life", "timestamp": "2025-05-17T09:15:00Z"},
                {"sender": "Vikash", "text": "Should not have any issues tho as per doctor", "timestamp": "2025-05-17T09:15:30Z"},
                {"sender": "Harsh", "text": "Okay that's good", "timestamp": "2025-05-17T09:15:30Z"},
                {"sender": "Harsh", "text": "How does a chipped bone work btw? Is it broken and inside the body?", "timestamp": "2025-05-17T09:15:30Z"},
                {"sender": "Vikash", "text": "It’s separated from main ankle bone", "timestamp": "2025-05-17T09:15:30Z"},
                {"sender": "Harsh", "text": "Why did this happen?", "timestamp": "2025-05-17T09:15:30Z"},
                {"sender": "Vikash", "text": "And now in between muscle and it will be like that", "timestamp": "2025-05-17T09:15:30Z"},
                {"sender": "Harsh", "text": "And how could this have been avoided? Just for general knowledge", "timestamp": "2025-05-17T09:15:30Z"},
                {"sender": "Vikash", "text": "My bone fully chipped from bottom and it can not reattach sometimes if it’s chipped apart", "timestamp": "2025-05-17T09:15:30Z"},
                {"sender": "Vikash", "text": "No impact on functionality", "timestamp": "2025-05-17T09:15:30Z"},
                {"sender": "Vikash", "text": "It depends on fracture. Can not do anything", "timestamp": "2025-05-17T09:15:30Z"},
                {"sender": "Harsh", "text": "Haan but how do you start doing normal things? How to increase the load?", "timestamp": "2025-05-17T09:15:30Z"},
                {"sender": "Vikash", "text": "You should also check the ankle checked. I think it might be covered in the insurance", "timestamp": "2025-05-17T09:15:30Z"},
            ]
        }
    ],
    "emails": [
        {
            "id": "email_1",
            "from": "DMV Reminder <no-reply@dmv.gov>",
            "to": "user@example.com",
            "subject": "Your Driving License is Expiring Soon",
            "body": "Dear User, your driving license XZ12345 is due for renewal by July 30th, 2025. Please visit our website to start the process.",
            "received_at": "2025-05-15T10:00:00Z"
        }
    ]
}

# --- Data Transformation (Simple pass-through for this example) ---
def transform_data(raw_data):
    # In a real scenario, this would involve complex parsing, structuring, and feature extraction.
    return raw_data

# --- LLM Integration ---
def call_gemini_flash_model(prompt_text, json_schema=None):
    """
    Calls the Gemini Flash model (synchronously) with a given prompt and optional JSON schema.
    """
    global GEMINI_API_KEY 

    current_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt_text}]}]
    }
    if json_schema:
        payload["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": json_schema
        }

    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(current_api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status() 
        
        result = response.json()

        if (result.get("candidates") and
            result["candidates"][0].get("content") and
            result["candidates"][0]["content"].get("parts") and
            result["candidates"][0]["content"]["parts"][0].get("text")):
            
            if json_schema:
                return json.loads(result["candidates"][0]["content"]["parts"][0]["text"])
            else:
                return result["candidates"][0]["content"]["parts"][0]["text"]
        else:
            print(f"Unexpected Gemini API response structure: {result}")
            if result.get("promptFeedback"):
                print(f"Gemini API Prompt Feedback: {result.get('promptFeedback')}")
                block_reason = result["promptFeedback"].get("blockReason")
                if block_reason:
                    return {"error": f"Blocked by API: {block_reason}", "details": result["promptFeedback"].get("blockReasonMessage")}
            return {"error": "Failed to parse Gemini response or empty content."}

    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API: {e}")
        error_details = {"error": str(e)}
        if e.response is not None:
            try:
                error_details["response_body"] = e.response.json()
            except json.JSONDecodeError:
                error_details["response_body"] = e.response.text
        return error_details
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from Gemini API: {e}")
        return {"error": f"JSON decode error: {e}"}
    except Exception as e:
        print(f"An unexpected error occurred in call_gemini_flash_model: {e}")
        return {"error": f"Unexpected error: {e}"}


def llm_generate_actions(structured_data):
    """
    Uses Gemini LLM (synchronously) to identify actions from structured data.
    """
    actions_to_consider = []
    emails_str = json.dumps(structured_data.get("emails", []), indent=2)
    chats_str = json.dumps(structured_data.get("chats", []), indent=2)
    current_date = "May 18th, 2025" 

    prompt = f"""
    You are Dia, a super personal assistant. Your task is to analyze the user's recent data (emails and chats)
    and identify potential actions the user might need to take or things they might be interested in.
    The current date is {current_date}.

    Here is the user's data:

    Emails:
    {emails_str}

    Chats:
    {chats_str}

    Based on this data, identify actionable items. For each item, provide:
    1.  `action_title`: A concise title for the action (max 15 words).
    2.  `source_type`: "Email" or "Chat".
    3.  `source_id`: The 'id' field of the original email or chat object from the provided data.
    4.  `source_trigger_text`: The specific text snippet (max 30 words) from the source that indicates this action.
    5.  `details_for_llm2`: Key information, context, or instructions for a subsequent AI to process this action (max 50 words).
        This should include relevant entities (names, products, services), dates, and what the next step might involve (e.g., research, draft email, set reminder).

    Focus on tasks, reminders, follow-ups, potential purchases, or research topics.
    Avoid vague suggestions. Be specific.
    Ensure the `source_id` correctly matches an ID from the provided email or chat data.

    Return your findings as a JSON array according to the provided schema.
    If no actions are identified, return an empty array.
    """

    llm_response = call_gemini_flash_model(prompt, ACTION_GENERATION_SCHEMA)

    if isinstance(llm_response, dict) and "error" in llm_response:
        print(f"Error from LLM in llm_generate_actions: {llm_response['error']}")
        return []
    
    if not isinstance(llm_response, list):
        print(f"LLM response is not a list as expected: {llm_response}")
        return []

    for item in llm_response:
        source_id = item.get("source_id")
        source_type = item.get("source_type")
        source_full_object = None

        if source_type == "Email":
            source_full_object = next((e for e in structured_data.get("emails", []) if e.get("id") == source_id), None)
        elif source_type == "Chat":
            source_full_object = next((c for c in structured_data.get("chats", []) if c.get("id") == source_id), None)

        if not source_full_object:
            print(f"Warning: Could not find source object for ID '{source_id}' of type '{source_type}'. Skipping action: {item.get('action_title')}")
            continue

        actions_to_consider.append({
            "id": str(uuid.uuid4()),
            "action_title": item.get("action_title"),
            "source_type": source_type,
            "source_summary": f"{item.get('source_trigger_text', 'N/A')} (Source ID: {source_id})",
            "source_full": source_full_object,
            "details_for_llm2": item.get("details_for_llm2")
        })
    return actions_to_consider


def llm_execute_action(action_item):
    """
    Uses Gemini LLM in two phases:
    1. Generate a plan and identify needed data.
    2. (Simulated) Gather data and provide a final actionable summary.
    """
    action_title = action_item.get("action_title", "N/A")
    details_for_llm2 = action_item.get("details_for_llm2", "No specific details provided.")
    current_date = "May 18th, 2025"

    # --- Phase 1: Planning and Data Identification --- 
    planning_prompt = f"""
    You are Dia, a super personal assistant. For the action: "{action_title}" with details "{details_for_llm2}", 
    do the following:
    1.  Create a concise step-by-step execution plan.
    2.  Identify a list of specific data keys that would be helpful from the user's personal data store 
        to complete this action (e.g., ["license_number", "date_of_birth", "insurance_policy_number"]). 
        Only request keys that are highly relevant. If no specific personal data is needed, return an empty list for keys.

    Return your response as a JSON object with two keys: "plan" (a string with the plan) and "required_data_keys" (an array of strings).

    Example Response:
    {{ 
        "plan": "1. Check renewal date. 2. Gather necessary documents. 3. Fill out online form.",
        "required_data_keys": ["license_number", "vehicle_registration_id"]
    }}
    """
    
    SCHEMA_FOR_PLANNING = {
        "type": "OBJECT",
        "properties": {
            "plan": {"type": "STRING"},
            "required_data_keys": {"type": "ARRAY", "items": {"type": "STRING"}}
        },
        "required": ["plan", "required_data_keys"]
    }

    planning_response = call_gemini_flash_model(planning_prompt, SCHEMA_FOR_PLANNING)

    if isinstance(planning_response, dict) and "error" in planning_response:
        print(f"Error from LLM in llm_execute_action (Phase 1 - Planning): {planning_response['error']}")
        return {
            "error": "Failed to generate execution plan.", 
            "details": planning_response['error']
        }
    
    if not isinstance(planning_response, dict) or "plan" not in planning_response or "required_data_keys" not in planning_response:
        print(f"Unexpected planning response format: {planning_response}")
        return {"error": "Failed to parse planning response from LLM."}

    execution_plan = planning_response.get("plan", "No plan generated.")
    required_keys = planning_response.get("required_data_keys", [])

    # --- Phase 2: Data Retrieval and Final Output Generation (Simulated) ---
    found_user_data, missing_user_data_keys = get_user_data_keys(required_keys)

    # This prompt is now more about *presenting* the information based on the plan and data
    # rather than doing new complex reasoning. The heavy lifting of planning is done.
    final_summary_prompt = f"""
    You are Dia, a super personal assistant. 
    Action Title: "{action_title}"
    Context: "{details_for_llm2}"
    Execution Plan: "{execution_plan}"
    
    Available personal data for this task:
    {json.dumps(found_user_data, indent=2) if found_user_data else "No specific personal data was found or requested for this task."}
    
    Personal data keys that were identified as potentially useful but NOT found:
    {json.dumps(missing_user_data_keys, indent=2) if missing_user_data_keys else "All identified data keys were found or no specific data was requested."}

    Based on the plan and the available/missing data, provide a summary of how to proceed. 
    If data is missing, highlight what the user might need to provide.
    Use a clear, step-oriented format for the final output. 
    Prefix your response with "Dia's Action Summary for: {action_title}\n---------------------------------------\n"
    Be direct and focus on the action steps. 
    For example:
    Dia's Action Summary for: Renew Driving License
    ---------------------------------------
    Here's the plan to renew your driving license:
    1. Check renewal date: Your license XZ12345 expires on July 30th, 2025. (Using license_number from user data)
    2. Gather necessary documents: You will likely need proof of address and your current license.
    3. Fill out online form: Visit the DMV website. The form might ask for your date_of_birth (Not Found).
    
    Missing Information:
    - date_of_birth: Please provide this if needed for the renewal form.
    """

    final_llm_output = call_gemini_flash_model(final_summary_prompt)

    if isinstance(final_llm_output, dict) and "error" in final_llm_output:
        print(f"Error from LLM in llm_execute_action (Phase 2 - Summary): {final_llm_output['error']}")
        # Fallback with plan and data info if final summarization fails
        return {
            "plan": execution_plan,
            "found_data": found_user_data,
            "missing_data_keys": missing_user_data_keys,
            "summary": "Error: Could not generate final summary. Please use the plan and data information provided.",
            "error_details": final_llm_output['error']
        }

    return {
        "plan": execution_plan,
        "found_data": found_user_data,
        "missing_data_keys": missing_user_data_keys,
        "summary": final_llm_output
    }


# --- Frontend Routes ---
@app.route('/')
def index():
    """Serve the main frontend page."""
    return render_template('index.html')

# --- API Endpoints ---

@app.route('/api/raw-data', methods=['GET'])
def get_raw_data():
    return jsonify(mock_data)

@app.route('/api/dia/context-actions', methods=['GET'])
def get_dia_context_actions(): 
    current_data = mock_data
    structured_data = transform_data(current_data)
    
    potential_actions = llm_generate_actions(structured_data) 

    if not isinstance(potential_actions, list):
        print(f"Potential actions was not a list: {potential_actions}")
        potential_actions = []
        
    return jsonify(potential_actions)

@app.route('/api/dia/execute-action/<action_id>', methods=['POST'])
def execute_dia_action(action_id):
    # Get the action data from the request body
    action_data = request.get_json()
    
    if not action_data:
        return jsonify({"error": "No action data provided"}), 400
        
    # Execute the action and get detailed results
    research_result = llm_execute_action(action_data)

    return jsonify({
        "action_id": action_id,
        "research_result": research_result
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)