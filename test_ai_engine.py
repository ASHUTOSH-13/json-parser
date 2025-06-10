import os
from ai_engine import generate_transformation_code
import json

# Sample data
test_data = [
    {"name": "John Doe", "age": 30},
    {"name": "Jane Smith", "age": 25}
]

# Example transformation prompt
transformation_prompt = "Capitalize all name values and add 1 to all age values"

# Set Groq API key for testing
if not os.environ.get("GROQ_API_KEY"):
    print("Please set your GROQ_API_KEY environment variable first!")
    exit(1)

# Generate transformation code
generated_code = generate_transformation_code(transformation_prompt, test_data)
print("\nGenerated code:", generated_code) 