import os
import sys
import json
import re
from pydantic import BaseModel
from typing import List

class ParagraphChunk(BaseModel):
    """Represents a single chunk of content, containing one or more paragraphs."""
    id: int
    content: str
    word_count: int

# --- Core Functions ---

def get_target_chunk_size(age: int) -> int:
    """
    Determines the target chunk size in words based on the user's age.
    The values are derived from average reading speeds to create chunks
    that are manageable for different age groups.

    Args:
        age: The age of the user.

    Returns:
        An integer representing the target word count for chunks.
    """
    if age <= 12:
        return 150  # Younger readers
    elif age <= 20:
        return 220  # Teens / Young Adults
    elif age <= 35:
        return 250  # Peak adult reading speed
    elif age <= 50:
        return 240  # Slight decline
    elif age <= 65:
        return 200  # Moderate decline
    else: # 65+
        return 180  # Slower reading speed

def read_book_text(file_path: str) -> str:
    """
    Reads the entire content of a text file.

    Args:
        file_path: The full path to the .txt file.

    Returns:
        The content of the file as a single string.
        Returns an empty string if the file cannot be read.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return ""
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return ""

def split_into_paragraphs(text: str) -> List[str]:
    """
    Splits a large block of text into a list of paragraphs.
    Paragraphs are assumed to be separated by one or more blank lines.

    Args:
        text: The string content of the book.

    Returns:
        A list of strings, where each string is a paragraph.
    """
    # Split by one or more newline characters (\n\s*\n)
    paragraphs = re.split(r'\n\s*\n', text)
    # Filter out any empty strings that may result from the split
    return [p.strip() for p in paragraphs if p.strip()]

def chunk_paragraphs(paragraphs: List[str], target_chunk_size: int) -> List[ParagraphChunk]:
    """
    Groups a list of paragraphs into chunks of a target word count.

    This function iterates through paragraphs, adding them to a running
    chunk until the target word count is met or exceeded. It never splits
    an individual paragraph.

    Args:
        paragraphs: A list of paragraph strings.
        target_chunk_size: The desired average number of words per chunk.

    Returns:
        A list of ParagraphChunk objects.
    """
    chunks = []
    current_chunk_content = []
    current_chunk_word_count = 0
    chunk_id = 0

    for p in paragraphs:
        paragraph_word_count = len(p.split())
        
        if not current_chunk_content:
            current_chunk_content.append(p)
            current_chunk_word_count += paragraph_word_count
        elif current_chunk_word_count < target_chunk_size:
            current_chunk_content.append(p)
            current_chunk_word_count += paragraph_word_count
        else:
            final_content = "\n\n".join(current_chunk_content)
            chunks.append(ParagraphChunk(id=chunk_id, content=final_content, word_count=current_chunk_word_count))
            
            chunk_id += 1
            current_chunk_content = [p]
            current_chunk_word_count = paragraph_word_count
            
    if current_chunk_content:
        final_content = "\n\n".join(current_chunk_content)
        chunks.append(ParagraphChunk(id=chunk_id, content=final_content, word_count=current_chunk_word_count))
        
    return chunks

def get_next_output_path(base_results_dir: str, book_name: str) -> str:
    """
    Determines the next sequential filename (e.g., 3.json) for a given book.

    Args:
        base_results_dir: The root 'chunked_results' directory.
        book_name: The name of the book (used as a subfolder).

    Returns:
        The full path for the new JSON file.
    """
    book_output_dir = os.path.join(base_results_dir, book_name)
    os.makedirs(book_output_dir, exist_ok=True)

    existing_ids = []
    for filename in os.listdir(book_output_dir):
        if filename.endswith('.json'):
            file_id_str = os.path.splitext(filename)[0]
            try:
                existing_ids.append(int(file_id_str))
            except ValueError:
                continue
    
    next_id = max(existing_ids) + 1 if existing_ids else 0
    return os.path.join(book_output_dir, f"{next_id}.json")

def save_chunks_to_json(chunks: List[ParagraphChunk], output_path: str):
    """
    Saves the list of chunk objects to a JSON file.

    Args:
        chunks: The list of ParagraphChunk objects to save.
        output_path: The full path for the output JSON file.
    """
    chunks_as_dict = [chunk.model_dump() for chunk in chunks]
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks_as_dict, f, indent=4, ensure_ascii=False)
        print(f"Successfully saved {len(chunks)} chunks to '{output_path}'")
    except Exception as e:
        print(f"An error occurred while saving the JSON file: {e}")

# --- Main Execution ---

def process_book(book_filename: str, target_chunk_size: int):
    """
    Main function to orchestrate the entire process for a single book.
    
    Args:
        book_filename: The name of the .txt file in the 'books' folder.
        target_chunk_size: The desired average number of words per chunk.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    books_dir = os.path.join(script_dir, 'books')
    results_dir = os.path.join(script_dir, 'chunked_results')
    input_file_path = os.path.join(books_dir, book_filename)
    book_name = os.path.splitext(book_filename)[0]
    output_file_path = get_next_output_path(results_dir, book_name)
    
    print(f"--- Starting processing for '{book_filename}' ---")
    print(f"Target chunk size set to {target_chunk_size} words based on user age.")
    
    book_text = read_book_text(input_file_path)
    if not book_text:
        print("Processing stopped due to reading error.")
        return
        
    paragraphs = split_into_paragraphs(book_text)
    print(f"Found {len(paragraphs)} paragraphs.")
    
    chunks = chunk_paragraphs(paragraphs, target_chunk_size)
    
    save_chunks_to_json(chunks, output_file_path)
    
    print(f"--- Finished processing '{book_filename}' ---")


if __name__ == "__main__":
    # --- TO RUN THE SCRIPT ---
    # 1. Provide two arguments: the filename and the user's age.
    #    Example: python chunk_script.py your_book.txt 30
    
    if len(sys.argv) != 3:
        print("Usage: python chunk_script.py <filename.txt> <user_age>")
        sys.exit(1)
    
    file_to_process = sys.argv[1]
    
    try:
        user_age = int(sys.argv[2])
    except ValueError:
        print("Error: Please provide a valid integer for user_age.")
        sys.exit(1)

    # Determine the target chunk size based on age
    TARGET_CHUNK_SIZE_WORDS = get_target_chunk_size(user_age)
    
    # Process the book with the dynamic chunk size
    process_book(file_to_process, TARGET_CHUNK_SIZE_WORDS)
