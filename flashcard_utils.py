import csv
import io
import requests
import json
import re
import os
from dotenv import load_dotenv
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-r1:free" 

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    raise ValueError("OpenRouter API key is not set.")

HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def query_openrouter_api(messages):
    """Sends a request to the OpenRouter API using chat format."""
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 1000
    }

    print(f"\n--- DEBUGGING API CALL ---")
    print(f"Request Headers: {{'Authorization': 'Bearer ...{API_KEY[-5:]}'}}")
    print(f"Request Payload: {json.dumps(payload)[:100]}...")
    
    response = requests.post(API_URL, headers=HEADERS, json=payload)

    print(f"API Response Status Code: {response.status_code}")
    print(f"API Response Content: {response.text}")
    print(f"--- END DEBUGGING API CALL ---\n")

    response.raise_for_status()
    return response.json()


def generate_flashcards(text: str, language: str = 'English', difficulty: str = 'medium') -> list[dict]:
    if not text:
        return []

    difficulty_instruction = {
        'easy': "Generate simple, direct questions and answers of 1 - 2 sentences .",
        'medium': "Generate factual questions and detailed concise answers of 2-3 sentences covering key details.",
        'hard': "Generate more complex questions and detailed answers of about 4-5 sentences requiring broader understanding."
    }.get(difficulty, "")

    user_prompt = f"""
    Create more than 5 flashcards in "{language}" based on the following text.
    {difficulty_instruction}
    Format:
    Q: [question]
    A: [answer]
    ---
    Q: [question]
    A: [answer]
    ---
    (continue for 5-10 flashcards)

    Text:
    {text}

    Flashcards:
    """

    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant that generates educational flashcards."},
            {"role": "user", "content": user_prompt}
        ]

        api_response = query_openrouter_api(messages)
        generated_text = api_response["choices"][0]["message"]["content"]

        print(f"\n--- API Generated Raw Text (for debugging) ---\n{generated_text}\n----------------------------\n")

        # --- Parsing logic ---
        flashcards = []
        card_blocks = generated_text.split("---")

        for block in card_blocks:
            block = block.strip()
            if not block:
                continue

            question_match = re.search(r'Q:\s*(.*?)(?=\nA:|$)', block, re.IGNORECASE | re.DOTALL)
            answer_match   = re.search(r'A:\s*(.*?)(?=\nQ:|---|$)', block, re.IGNORECASE | re.DOTALL)
            

            question = question_match.group(1).strip() if question_match else ""
            answer   = answer_match.group(1).strip() if answer_match else ""

            # Clean up extra whitespace
            question = re.sub(r'\s+', ' ', question)
            answer   = re.sub(r'\s+', ' ', answer)

            if question and answer and len(question) > 5 and len(answer) > 5:
                flashcards.append({
                    "question": question,
                    "answer": answer,
                    "language": language,
                    "difficulty": difficulty
                })




        # Remove duplicates
        unique_flashcards = []
        seen_pairs = set()
        for card in flashcards:
            pair_check = (card['question'].lower(), card['answer'].lower())
            if pair_check not in seen_pairs:
                unique_flashcards.append(card)
                seen_pairs.add(pair_check)

        return unique_flashcards

    except requests.exceptions.RequestException as req_err:
        print(f"Network or API request error: {req_err}")
        if req_err.response is not None:
            print(f"API Error Response: {req_err.response.text}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred during API generation: {e}")
        return []


def export_flashcards_to_csv_buffer(flashcards: list[dict], buffer: io.BytesIO):
    text_wrapper = io.TextIOWrapper(buffer, encoding='utf-8', newline='')
    try:
        writer = csv.writer(text_wrapper)
        writer.writerow(['Question', 'Answer', 'Language', 'Difficulty'])
        for card in flashcards:
            writer.writerow([
                card.get('question', ''),
                card.get('answer', ''),
                card.get('language', ''), 
                card.get('difficulty', '')
            ])
        text_wrapper.flush() 
    finally:
        text_wrapper.detach()  # Detach the TextIOWrapper to prevent closing the buffer

