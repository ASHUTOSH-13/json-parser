from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class TransformationHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_data = db.Column(db.JSON, nullable=False)
    transformed_data = db.Column(db.JSON, nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    transformation_code = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='success')  # success or error
    error_message = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'prompt': self.prompt,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'transformation_code': self.transformation_code,
            'original_data': self.original_data,
            'transformed_data': self.transformed_data
        } 