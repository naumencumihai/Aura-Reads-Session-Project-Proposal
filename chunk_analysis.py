import os
import sys
import json
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from typing import List

# --- Environment and API Configuration ---

# Load environment variables from a .env file for security
load_dotenv()

# It's recommended to place your Gemini API key in a .env file
# like this: GEMINI_API_KEY="your_api_key_here"
# The script will then load it automatically.
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file or environment variables.")

# --- Pydantic Model Definitions ---
# These models define the expected structure of our data.

class ParagraphChunk(BaseModel):
    """
    Represents a single chunk read from the input JSON file.
    Pydantic will automatically ignore extra fields like 'word_count'.
    """
    id: int
    content: str

class ParagraphChunk_Response(BaseModel):
    """
    Defines the structure for a single item in the JSON response
    we expect from the Gemini API.
    """
    paragraph_id: int
    mood: str
    sentiment: str
    type: str
    type_details: str

class AnalysisResponse(BaseModel):
    """
    A container model for the list of analysis results from the API.
    This is the correct way to define a schema for a JSON array response.
    """
    analysis_results: List[ParagraphChunk_Response]

# --- Core Functions ---

def load_chunks_from_file(file_path: str) -> List[ParagraphChunk]:
    """
    Reads a JSON file containing chunked paragraphs and validates its structure.

    Args:
        file_path: The full path to the input JSON file (e.g., 'results/book_name/0.json').

    Returns:
        A list of ParagraphChunk objects. Returns an empty list if the file is not found
        or if the data is invalid.
    """
    if not os.path.exists(file_path):
        print(f"Error: Input file not found at '{file_path}'")
        return []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        try:
            # Pydantic validates that the data matches the list of ParagraphChunk models
            return [ParagraphChunk(**item) for item in data]
        except ValidationError as e:
            print(f"Error: Data in '{file_path}' does not match expected format.")
            print(e)
            return []

def paragraphs_to_string(paragraphs: List[ParagraphChunk]) -> str:
    """
    Formats a list of paragraph chunks into a single string for the prompt.
    """
    return "\n\t".join([f'[Paragraph with id={p.id}]: "{p.content}"' for p in paragraphs])

def analyze_paragraphs(paragraphs: List[ParagraphChunk]) -> List[dict]:
    """
    Sends the formatted paragraphs to the Gemini API for analysis.

    Args:
        paragraphs: A list of ParagraphChunk objects to be analyzed.

    Returns:
        A list of dictionaries with the analysis results from the API.
    """
    # This lazy import allows the script to run other functions even if the library isn't installed.
    try:
        import google.generativeai as genai
    except ImportError:
        print("Error: The 'google-generativeai' library is required. Please install it using 'pip install google-generativeai'")
        sys.exit(1)

    genai.configure(api_key=API_KEY)
    
    # The prompt clearly defines the task and the expected output format for the model.
    prompt = f"""
    Analyze the mood, sentiment, type, and type_details of the following paragraphs:

    The output should be a JSON object with a single key "analysis_results" that contains a JSON array of objects with the following format:
    paragraph_id: [id of the paragraph]
    mood: [mood of the paragraph; possible values: happy, sad, angry, excited, anxious, confused, surprised, disappointed, grateful, lonely, hopeful, content, frustrated]
    sentiment: [sentiment of the paragraph; possible values: positive, negative, neutral]
    type: [type of the paragraph; possible values: dialogue, description, action, contemplation, reflection]
    type_details: [details of the type; ex: if the paragraph is a description of nature, the type_details will be "nature"]

    {paragraphs_to_string(paragraphs)}
    """

    model = genai.GenerativeModel('gemini-2.5-pro')

    print("Sending request to Gemini API for analysis...")
    try:
        response = model.generate_content(
            contents=prompt,
            generation_config={
                "response_mime_type": "application/json",
                # By providing the response schema, we ask the model to return valid JSON.
                "response_schema": AnalysisResponse,
            },
        )
        print("Analysis received successfully.")
        # Parse the JSON response and extract the list from the container object
        result_data = json.loads(response.text)
        return result_data.get("analysis_results", [])
    except Exception as e:
        print(f"An error occurred while contacting the Gemini API: {e}")
        return []

def save_analysis_result(result_list: List[dict], output_path: str):
    """
    Saves the analysis result from the API to a new JSON file.

    Args:
        result_list: A list of dictionaries containing the analysis.
        output_path: The full path for the output file.
    """
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    try:
        # We can now directly dump the list of dictionaries into the file.
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result_list, f, indent=4, ensure_ascii=False)
        print(f"Successfully saved analysis to '{output_path}'")
    except Exception as e:
        print(f"An error occurred while saving the JSON file: {e}")

# --- Main Execution ---

def main():
    """
    Main function to orchestrate the analysis process.
    """
    # --- Command-Line Argument Parsing ---
    if len(sys.argv) != 3:
        print("Usage: python chunk_analysis.py <book_name> <file_number>")
        print("Example: python chunk_analysis.py divine_comedy 0")
        sys.exit(1)

    book_name = sys.argv[1]
    file_number = sys.argv[2]
    
    # --- File Path Setup ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file_path = os.path.join(script_dir, 'results', book_name, f"{file_number}.json")
    output_file_path = os.path.join(script_dir, 'analysis_results', book_name, f"{file_number}.json")

    # --- Script Logic ---
    print(f"--- Starting analysis for '{book_name}', file '{file_number}.json' ---")
    
    # 1. Load the chunked paragraphs from the specified file.
    paragraphs = load_chunks_from_file(input_file_path)
    if not paragraphs:
        print("Processing stopped because no paragraphs were loaded.")
        return

    # 2. Send the paragraphs to the Gemini API for analysis.
    analysis_result_list = analyze_paragraphs(paragraphs)
    if not analysis_result_list:
        print("Processing stopped because no analysis was returned from the API.")
        return

    # 3. Save the returned analysis to a new file.
    save_analysis_result(analysis_result_list, output_file_path)
    
    print(f"--- Finished analysis ---")


if __name__ == "__main__":
    main()
