from flask import Flask, request, redirect, url_for, render_template, send_from_directory
import os
import subprocess

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

# Ensure the upload and processed directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an empty file without a filename
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            try:
                # Use the full path to the Python script
                script_path = os.path.abspath('lpd.py')
                subprocess.run(["python", script_path, filepath], check=True)

                # Define expected output filenames
                output_filename = filename.rsplit('.', 1)[0] + '_out.csv'
                peak_filename = filename.rsplit('.', 1)[0] + '_peak.csv'
                factors_filename = filename.rsplit('.', 1)[0] + '_factors.csv'

                # Check if the files exist before moving
                for file in [output_filename, peak_filename, factors_filename]:
                    source_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
                    if not os.path.exists(source_path):
                        raise FileNotFoundError(f"Expected output file not found: {source_path}")

                # Move the processed files to the processed folder
                os.rename(os.path.join(app.config['UPLOAD_FOLDER'], output_filename),
                          os.path.join(app.config['PROCESSED_FOLDER'], output_filename))
                os.rename(os.path.join(app.config['UPLOAD_FOLDER'], peak_filename),
                          os.path.join(app.config['PROCESSED_FOLDER'], peak_filename))
                os.rename(os.path.join(app.config['UPLOAD_FOLDER'], factors_filename),
                          os.path.join(app.config['PROCESSED_FOLDER'], factors_filename))

                return render_template('download.html', 
                                       output_filename=output_filename, 
                                       peak_filename=peak_filename,
                                       factors_filename=factors_filename)
            except subprocess.CalledProcessError as e:
                return f"An error occurred: {e}"
            except FileNotFoundError as e:
                return f"An error occurred while moving files: {e}"

    return render_template('upload.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
