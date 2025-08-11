import csv
import io
import requests
import json
import re
import os
from dotenv import load_dotenv

# --- Configuration for OpenRouter API ---
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-r1:free"  # Or another OpenRouter-supported model

# Your OpenRouter API key
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

        # Extract generated text from OpenRouter's chat completion response
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
        text_wrapper.flush()  # Ensure all data is written to the buffer
    finally:
        text_wrapper.detach()  # Detach the TextIOWrapper to prevent closing the buffer

# import csv
# import io
# import requests
# import json
# import re
# import os
# import time

# # --- Configuration for OpenRouter API ---
# API_URL = "https://openrouter.ai/api/v1/chat/completions"
# MODEL_NAME = "meta-llama/llama-3-8b-instruct:free"  # Switched to a different free model to avoid rate limits on deepseek/deepseek-r1:free

# # Your OpenRouter API key
# API_KEY = "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"

# if not API_KEY:
#     raise ValueError("OpenRouter API key is not set.")

# HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


# def query_openrouter_api(messages, retries=5, backoff_factor=4):
#     """Sends a request to the OpenRouter API using chat format with retry logic."""
#     for attempt in range(retries):
#         payload = {
#             "model": MODEL_NAME,
#             "messages": messages,
#             "temperature": 0,
#             "max_tokens": 2000
#         }

#         print(f"\n--- DEBUGGING API CALL (Attempt {attempt + 1}/{retries}) ---")
#         print(f"Request Headers: {{'Authorization': 'Bearer ...{API_KEY[-5:]}'}}")
#         print(f"Request Payload: {json.dumps(payload)[:100]}...")
        
#         try:
#             response = requests.post(API_URL, headers=HEADERS, json=payload)

#             print(f"API Response Status Code: {response.status_code}")
#             print(f"API Response Content: {response.text}")
#             print(f"--- END DEBUGGING API CALL ---\n")

#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.HTTPError as http_err:
#             if response.status_code == 429:
#                 if attempt < retries - 1:
#                     wait_time = backoff_factor ** attempt
#                     print(f"Rate limit hit (429). Retrying in {wait_time} seconds...")
#                     time.sleep(wait_time)
#                     continue
#                 else:
#                     print(f"Max retries reached for 429 error: {http_err}")
#                     raise
#             else:
#                 raise
#         except requests.exceptions.RequestException as req_err:
#             print(f"Network or API request error: {req_err}")
#             if req_err.response is not None:
#                 print(f"API Error Response: {req_err.response.text}")
#             raise

#     raise Exception("Failed to get a valid response after retries")


# def generate_flashcards(text: str, language: str = 'English', difficulty: str = 'medium') -> list[dict]:
#     if not text:
#         return []

#     difficulty_instruction = {
#         'easy': "Generate simple, direct questions and answers of 1 - 2 sentences.",
#         'medium': "Generate factual questions and detailed concise answers of 2-3 sentences covering key details.",
#         'hard': "Generate more complex questions and detailed answers of about 4-5 sentences requiring broader understanding."
#     }.get(difficulty, "")

#     user_prompt = f"""
#     Create exactly 7 flashcards in "{language}" based on the following text.
#     {difficulty_instruction}
#     Output only a JSON array of objects, each with "question" and "answer" keys. Do not add any other text.
#     Example: [{{"question": "Example Q", "answer": "Example A"}}, ...]

#     Text:
#     {text}
#     """

#     max_attempts = 3
#     for attempt in range(max_attempts):
#         try:
#             messages = [
#                 {"role": "system", "content": "You are a helpful assistant that generates educational flashcards."},
#                 {"role": "user", "content": user_prompt}
#             ]

#             api_response = query_openrouter_api(messages)

#             # Extract generated text from OpenRouter's chat completion response
#             generated_text = api_response["choices"][0]["message"]["content"]

#             print(f"\n--- API Generated Raw Text (for debugging) ---\n{generated_text}\n----------------------------\n")

#             # --- Parsing logic ---
#             flashcards = []
#             try:
#                 raw_flashcards = json.loads(generated_text)
#             except json.JSONDecodeError as json_err:
#                 print(f"JSON parsing error: {json_err}. Attempting to fix...")
#                 # Attempt to fix truncated JSON
#                 fixed_text = generated_text
#                 if not fixed_text.endswith(']'):
#                     fixed_text = fixed_text.rsplit('}', 1)[0] + '}]'
#                 raw_flashcards = json.loads(fixed_text)

#             for card in raw_flashcards:
#                 question = card.get('question', '').strip()
#                 answer = card.get('answer', '').strip()

#                 # Clean up extra whitespace
#                 question = re.sub(r'\s+', ' ', question)
#                 answer   = re.sub(r'\s+', ' ', answer)

#                 if question and answer and len(question) > 5 and len(answer) > 5:
#                     flashcards.append({
#                         "question": question,
#                         "answer": answer,
#                         "language": language,
#                         "difficulty": difficulty
#                     })

#             # Remove duplicates
#             unique_flashcards = []
#             seen_pairs = set()
#             for card in flashcards:
#                 pair_check = (card['question'].lower(), card['answer'].lower())
#                 if pair_check not in seen_pairs:
#                     unique_flashcards.append(card)
#                     seen_pairs.add(pair_check)

#             # Check if we got exactly 7 flashcards
#             if len(unique_flashcards) == 7:
#                 return unique_flashcards
#             else:
#                 print(f"Got {len(unique_flashcards)} flashcards instead of 7. Retrying (attempt {attempt + 1}/{max_attempts})...")
#                 continue

#         except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
#             print(f"Error on attempt {attempt + 1}: {e}")
#             if attempt < max_attempts - 1:
#                 print(f"Retrying (attempt {attempt + 2}/{max_attempts})...")
#                 time.sleep(2 ** attempt)  # Exponential backoff
#                 continue
#             else:
#                 print(f"Max retries reached. Returning available flashcards: {len(unique_flashcards)}")
#                 return unique_flashcards

#     return unique_flashcards if 'unique_flashcards' in locals() else []


# def export_flashcards_to_csv_buffer(flashcards: list[dict], buffer: io.BytesIO):
#     text_wrapper = io.TextIOWrapper(buffer, encoding='utf-8', newline='')
#     try:
#         writer = csv.writer(text_wrapper)
#         writer.writerow(['Question', 'Answer', 'Language', 'Difficulty'])
#         for card in flashcards:
#             writer.writerow([
#                 card.get('question', ''),
#                 card.get('answer', ''),
#                 card.get('language', ''),
#                 card.get('difficulty', '')
#             ])
#         text_wrapper.flush()  # Ensure all data is written to the buffer
#     finally:
#         text_wrapper.detach()  # Detach the TextIOWrapper to prevent closing the buffer