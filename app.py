from flask import Flask, request, render_template, send_file, session, jsonify, send_from_directory
import os
import json
from ai_engine import generate_transformation_code
from executor import apply_transformation
from dotenv import load_dotenv
from models import db, TransformationHistory
from csv_logger import CSVLogger

load_dotenv()

app = Flask(__name__)
app.secret_key = 'supersecret'

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///transformations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create folders for uploads and outputs
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Initialize CSV logger
csv_logger = CSVLogger(os.path.join(OUTPUT_FOLDER, 'transformation_logs.csv'))

# Initialize database
with app.app_context():
    db.create_all()
    # Clear transformation history on server start
    db.session.query(TransformationHistory).delete()
    db.session.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
    preview = []
    fields = []
    original_data = None
    transformed_data = None
    code = ""
    history = []

    if request.method == 'GET':
        history = TransformationHistory.query.order_by(TransformationHistory.created_at.desc()).limit(5).all()
        history = [h.to_dict() for h in history]

    if request.method == 'POST':
        file = request.files.get('json_file')
        prompt = request.form.get('prompt')
        uploaded_filename = None

        # If a new file is uploaded, save it and update session
        if file and file.filename.endswith('.json'):
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            uploaded_filename = file.filename
            with open(filepath, 'r') as f:
                original_data = json.load(f)
                session['data'] = original_data
                session['filename'] = uploaded_filename
        else:
            # If no new file, try to get filename from hidden field
            uploaded_filename = request.form.get('uploaded_filename')
            if uploaded_filename:
                filepath = os.path.join(UPLOAD_FOLDER, uploaded_filename)
                if os.path.exists(filepath):
                    with open(filepath, 'r') as f:
                        original_data = json.load(f)
                        session['data'] = original_data
                        session['filename'] = uploaded_filename

        data_to_use = session.get('data')

        if data_to_use:
            # Safe preview
            if isinstance(data_to_use, list) and data_to_use:
                preview = data_to_use[:2]
                fields = list(preview[0].keys())
            elif isinstance(data_to_use, dict):
                preview = [data_to_use]
                fields = list(data_to_use.keys())

            if prompt:
                code = generate_transformation_code(prompt, data_to_use)
                transformed_result = apply_transformation(data_to_use, code)

                history_entry = TransformationHistory(
                    original_data=data_to_use,
                    prompt=prompt,
                    transformation_code=code
                )

                success = not (isinstance(transformed_result, dict) and 'error' in transformed_result)
                
                # Log to CSV
                csv_logger.log_transformation(
                    user_query=prompt,
                    input_prompt=prompt,
                    input_json=data_to_use,
                    generated_code=code,
                    transformed_output=transformed_result,
                    success_flag=success
                )

                if not success:
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

                    if isinstance(transformed_data, list) and transformed_data:
                        preview = transformed_data[:2]
                        fields = list(preview[0].keys())
                    elif isinstance(transformed_data, dict):
                        preview = [transformed_data]
                        fields = list(transformed_data.keys())
                    session['data'] = transformed_data

                db.session.add(history_entry)
                db.session.commit()

                history = TransformationHistory.query.order_by(TransformationHistory.created_at.desc()).limit(5).all()
                history = [h.to_dict() for h in history]

    return render_template(
        'index.html',
        fields=fields,
        preview=preview,
        code=code,
        error=transformed_data.get('error') if isinstance(transformed_data, dict) and 'error' in transformed_data else None,
        history=history
    )

@app.route('/download')
def download():
    path = os.path.join(OUTPUT_FOLDER, 'transformed.json')
    if not os.path.exists(path):
        return "No transformed file available.", 404
    return send_file(path, as_attachment=True)

@app.route('/history')
def get_history():
    history = TransformationHistory.query.order_by(TransformationHistory.created_at.desc()).all()
    return jsonify([h.to_dict() for h in history])

@app.route('/history/<int:id>/reapply', methods=['POST'])
def reapply_transformation(id):
    history_entry = TransformationHistory.query.get_or_404(id)
    current_data = session.get('data')

    if not current_data:
        return jsonify({'error': 'No current uploaded data found in session.'}), 400

    transformed_result = apply_transformation(current_data, history_entry.transformation_code)

    if isinstance(transformed_result, dict) and 'error' in transformed_result:
        return jsonify({'error': transformed_result['error']}), 400

    output_path = os.path.join(OUTPUT_FOLDER, 'transformed.json')
    with open(output_path, 'w') as out_f:
        json.dump(transformed_result, out_f, indent=2)

    session['data'] = transformed_result

    return jsonify({
        'message': 'Transformation reapplied successfully on uploaded JSON',
        'data': transformed_result
    })

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

@app.route('/download-logs')
def download_logs():
    return send_from_directory(OUTPUT_FOLDER, 'transformation_logs.csv', as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
