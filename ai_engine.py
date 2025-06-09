import os
from groq import Groq
import json

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def generate_transformation_code(prompt, json_data):
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