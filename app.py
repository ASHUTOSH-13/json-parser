from flask import Flask, request, render_template, send_file, session
import os
import json
from ai_engine import generate_transformation_code
from executor import apply_transformation
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'supersecret'  # Required for sessions
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    preview = []
    fields = []
    original_data = None
    transformed_data = None
    code = ""

    if request.method == 'POST':
        file = request.files.get('json_file')
        prompt = request.form.get('prompt')

        if file and file.filename.endswith('.json'):
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)

            with open(filepath, 'r') as f:
                original_data = json.load(f)
                session['data'] = original_data  # Store in session

        # Either uploaded now or retrieved from session
        data_to_use = session.get('data')

        if data_to_use:
            # Handle preview for both single objects and lists
            if isinstance(data_to_use, list):
                preview = data_to_use[:2]
            else:
                preview = [data_to_use]
            
            fields = list(preview[0].keys()) if preview else []

            if prompt:
                code = generate_transformation_code(prompt, data_to_use)
                transformed_result = apply_transformation(data_to_use, code)
                
                # Check if there was an error in transformation
                if isinstance(transformed_result, dict) and 'error' in transformed_result:
                    transformed_data = transformed_result
                else:
                    transformed_data = transformed_result
                    output_path = os.path.join(OUTPUT_FOLDER, 'transformed.json')
                    with open(output_path, 'w') as out_f:
                        json.dump(transformed_data, out_f, indent=2)

                    # Update preview and fields with transformed data
                    if isinstance(transformed_data, list):
                        preview = transformed_data[:2]
                    else:
                        preview = [transformed_data]
                    fields = list(preview[0].keys()) if preview else []
                    session['data'] = transformed_data  # Update session data

    return render_template('index.html', fields=fields, preview=preview, code=code, error=transformed_data.get('error') if isinstance(transformed_data, dict) and 'error' in transformed_data else None)

@app.route('/download')
def download():
    path = os.path.join(OUTPUT_FOLDER, 'transformed.json')
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)