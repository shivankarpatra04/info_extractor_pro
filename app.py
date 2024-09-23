from flask import Flask, render_template, request, redirect, url_for, send_file
import os
import io
from werkzeug.utils import secure_filename
from utils.extraction import process_document, read_file_content

# Initialize Flask app
app = Flask(__name__)

# Set upload folder
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        text_input = request.form.get('text_input')

        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            content = read_file_content(file_path)
        elif text_input:
            content = text_input
        else:
            return redirect(request.url)

        if not content:
            return "The file is empty or could not be read.", 400
        
        df = process_document(content)
        
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return send_file(io.BytesIO(output.getvalue().encode('utf-8')),
                         mimetype="text/csv",
                         download_name="extracted_information.csv",
                         as_attachment=True)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
