from flask import Flask, request, render_template, send_file, session, jsonify
import os
import json
from ai_engine import generate_transformation_code
from executor import apply_transformation
from dotenv import load_dotenv
from models import db, TransformationHistory

load_dotenv()

app = Flask(__name__)
app.secret_key = 'supersecret'  # Required for sessions

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///transformations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    preview = []
    fields = []
    original_data = None
    transformed_data = None
    code = ""
    history = []

    # Get transformation history
    if request.method == 'GET':
        history = TransformationHistory.query.order_by(TransformationHistory.created_at.desc()).limit(5).all()
        history = [h.to_dict() for h in history]

    if request.method == 'POST':
        file = request.files.get('json_file')
        prompt = request.form.get('prompt')

        if file and file.filename.endswith('.json'):
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)

            with open(filepath, 'r') as f:
                original_data = json.load(f)
                session['data'] = original_data

        data_to_use = session.get('data')

        if data_to_use:
            if isinstance(data_to_use, list):
                preview = data_to_use[:2]
            else:
                preview = [data_to_use]
            
            fields = list(preview[0].keys()) if preview else []

            if prompt:
                code = generate_transformation_code(prompt, data_to_use)
                transformed_result = apply_transformation(data_to_use, code)
                
                # Create history entry
                history_entry = TransformationHistory(
                    original_data=data_to_use,
                    prompt=prompt,
                    transformation_code=code
                )

                if isinstance(transformed_result, dict) and 'error' in transformed_result:
                    transformed_data = transformed_result
                    history_entry.status = 'error'
                    history_entry.error_message = transformed_result['error']
                    history_entry.transformed_data = {}
                else:
                    transformed_data = transformed_result
                    history_entry.transformed_data = transformed_result
                    output_path = os.path.join(OUTPUT_FOLDER, 'transformed.json')
                    with open(output_path, 'w') as out_f:
                        json.dump(transformed_data, out_f, indent=2)

                    if isinstance(transformed_data, list):
                        preview = transformed_data[:2]
                    else:
                        preview = [transformed_data]
                    fields = list(preview[0].keys()) if preview else []
                    session['data'] = transformed_data

                # Save history entry
                db.session.add(history_entry)
                db.session.commit()

                # Update history list
                history = TransformationHistory.query.order_by(TransformationHistory.created_at.desc()).limit(5).all()
                history = [h.to_dict() for h in history]

    return render_template('index.html', 
                         fields=fields, 
                         preview=preview, 
                         code=code, 
                         error=transformed_data.get('error') if isinstance(transformed_data, dict) and 'error' in transformed_data else None,
                         history=history)

@app.route('/download')
def download():
    path = os.path.join(OUTPUT_FOLDER, 'transformed.json')
    return send_file(path, as_attachment=True)

@app.route('/history')
def get_history():
    history = TransformationHistory.query.order_by(TransformationHistory.created_at.desc()).all()
    return jsonify([h.to_dict() for h in history])

@app.route('/history/<int:id>/reapply', methods=['POST'])
def reapply_transformation(id):
    history_entry = TransformationHistory.query.get_or_404(id)
    
    # Apply the saved transformation
    transformed_result = apply_transformation(history_entry.original_data, history_entry.transformation_code)
    
    if isinstance(transformed_result, dict) and 'error' in transformed_result:
        return jsonify({'error': transformed_result['error']}), 400
    
    # Save the result
    output_path = os.path.join(OUTPUT_FOLDER, 'transformed.json')
    with open(output_path, 'w') as out_f:
        json.dump(transformed_result, out_f, indent=2)
    
    return jsonify({'message': 'Transformation reapplied successfully', 'data': transformed_result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)