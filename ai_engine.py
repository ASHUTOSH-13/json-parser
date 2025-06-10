import os
from groq import Groq
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def validate_transformation_prompt(prompt, json_data):
    """
    Validates if the prompt is related to JSON transformation.
    Returns (is_valid, message) tuple.
    """
    # First, check if prompt is too short or just a question
    if len(prompt.strip()) < 10:
        return False, "Prompt is too short. Please provide a detailed transformation instruction."
    
    if prompt.strip().endswith('?'):
        return False, "This appears to be a question rather than a transformation instruction. Please provide a transformation instruction for the JSON data."

    # Ask LLM to validate if the prompt is about JSON transformation
    validation_prompt = f"""
You are a JSON transformation validator. Determine if the following prompt is requesting a valid JSON data transformation.
The JSON data structure is: {json.dumps(json_data if not isinstance(json_data, list) else json_data[0], indent=2)}

Prompt: "{prompt}"

Only respond with either:
VALID: If the prompt is asking for JSON data transformation/modification
INVALID: If the prompt is a general question or unrelated to JSON transformation

Provide your one-word response (VALID or INVALID) followed by a brief explanation.
"""

    validation_response = client.chat.completions.create(
        messages=[{"role": "user", "content": validation_prompt}],
        model="llama-3.3-70b-versatile",
        max_tokens=50  # Limiting response size for efficiency
    )

    response_text = validation_response.choices[0].message.content.strip()
    is_valid = response_text.upper().startswith('VALID')
    
    # Extract explanation (everything after the first colon)
    explanation = response_text.split(':', 1)[1].strip() if ':' in response_text else "Invalid transformation prompt."
    
    return is_valid, explanation


def generate_transformation_code(prompt, json_data):
    # First validate the prompt
    is_valid, message = validate_transformation_prompt(prompt, json_data)
    if not is_valid:
        return f"# {message}"  # Return comment with explanation

    # Convert single object to list for preview
    if not isinstance(json_data, list):
        preview_data = json.dumps(json_data, indent=2)
        is_single_object = True
    else:
        preview_data = json.dumps(json_data[:2], indent=2)
        is_single_object = False

    user_prompt = f"""
You are a senior Python developer.

Write a function called `transform(data)` that:
- Takes {'a dictionary' if is_single_object else 'a list of dictionaries'} (loaded from JSON)
- Applies the following transformation: {prompt}
- Uses safe methods like `.get()` to handle missing keys
- Does NOT print anything
- Returns the modified data in the same format it was received
- DO NOT use .copy() method directly on strings
- Use copy.deepcopy() for any copying needs (it's already imported)
- Assume the data looks like this:\n{preview_data}

Only return the Python code, do not include explanations or markdown.
"""

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "user", "content": user_prompt}
        ],
        model="llama-3.3-70b-versatile",
    )

    response_text = chat_completion.choices[0].message.content
    code = extract_code_block(response_text)
    print(f"Generated transformation code:\n{code}")  # Debug print
    return code


def extract_code_block(text):
    """
    Removes ```python blocks or markdown formatting if present
    """
    if "```python" in text:
        return text.split("```python")[1].split("```")[0].strip()
    elif "```" in text:
        return text.split("```")[1].split("```")[0].strip()
    else:
        return text.strip()