# app.py
from flask import Flask, render_template, request, send_file
from flashcard_utils import generate_flashcards, export_flashcards_to_csv_buffer
import io
import os
from dotenv import load_dotenv # <--- ADD THIS LINE

load_dotenv() # <--- ADD THIS LINE: This loads variables from .env

app = Flask(__name__)

# ... rest of your app.py code ...

# Rest of your app.py code...

@app.route('/', methods=['GET', 'POST'])
def index():
    flashcards = []
    text = ''
    language = ''
    difficulty = ''
    error = None
    loading = False # To indicate if generation is in progress

    if request.method == 'POST':
        text = request.form.get('text', '').strip()
        language = request.form.get('language', '')
        difficulty = request.form.get('difficulty', '')
        action = request.form.get('action')

        if action == 'generate':
            if not text:
                error = "⚠️ Please enter some text to generate flashcards."
            else:
                loading = True
                try:
                    flashcards = generate_flashcards(text, language, difficulty)
                    if not flashcards:
                        # --- CORRECTED FALLBACK MESSAGE ---
                        flashcards = [{
                            "question": "No flashcards could be generated.",
                            "answer": "Try providing more detailed input. The AI model might have struggled to extract Q&A from the text, or there might be an issue with the API service.",
                            "language": language,
                            "difficulty": difficulty
                        }]
                except Exception as e:
                    error = f"An error occurred during generation: {e}"
                finally:
                    loading = False

    return render_template('index.html',
                           flashcards=flashcards,
                           text=text,
                           language=language,
                           difficulty=difficulty,
                           error=error,
                           loading=loading)


@app.route('/export_csv', methods=['POST'])
def export_csv():
    text = request.form.get('text', '').strip()
    language = request.form.get('language', 'English')
    difficulty = request.form.get('difficulty', 'medium')

    if not text:
        return "⚠️ No text provided for export.", 400

    try:
        flashcards = generate_flashcards(text, language, difficulty)
        if not flashcards:
            return "⚠️ No flashcards could be generated for export. Try with more input.", 400

        csv_buffer = io.BytesIO()
        export_flashcards_to_csv_buffer(flashcards, csv_buffer)
        csv_buffer.seek(0)

        return send_file(
            csv_buffer,
            mimetype='text/csv',
            as_attachment=True,
            download_name='flashcards.csv'
        )
    except Exception as e:
        return f"An error occurred during CSV export: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)