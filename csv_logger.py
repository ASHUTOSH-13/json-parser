import csv
import os
from datetime import datetime

class CSVLogger:
    def __init__(self, csv_file='transformation_logs.csv'):
        self.csv_file = csv_file
        self._ensure_csv_exists()

    def _ensure_csv_exists(self):
        """Create CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Timestamp',
                    'User Query',
                    'Input Prompt',
                    'Input JSON',
                    'Generated Code',
                    'Transformed Output JSON',
                    'Success Flag'
                ])

    def log_transformation(self, user_query, input_prompt, input_json, generated_code, 
                         transformed_output, success_flag):
        """Log a transformation attempt to CSV"""
        try:
            with open(self.csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    user_query,
                    input_prompt,
                    str(input_json),
                    generated_code,
                    str(transformed_output),
                    'Success' if success_flag else 'Failed'
                ])
            return True
        except Exception as e:
            print(f"Error logging to CSV: {str(e)}")
            return False 