import fitz  # PyMuPDF
import re

def is_heading(span):
    """
    Determines if a text span is likely a heading.
    Heuristics used:
    - Font is bold.
    - Text is not too long.
    - Text doesn't end with a period.
    """
    # Font flags: 4 is bold.
    is_bold = span['flags'] & 4 
    text = span['text'].strip()
    
    if not text:
        return False
        
    # A simple combination of boldness and length check
    if is_bold and len(text.split()) < 15 and not text.endswith('.'):
        return True
        
    return False

def extract_structured_chunks(pdf_path):
    """
    Extracts structured content from a PDF into a list of sections.
    Each section has a title, the text content, and a page number.

    Args:
        pdf_path (str): The file path to the PDF.

    Returns:
        list: A list of dictionaries, where each dict represents a structured chunk.
              e.g., [{'title': 'Introduction', 'content': '...', 'page': 1}]
    """
    chunks = []
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening or processing {pdf_path}: {e}")
        return []

    current_section = {"title": "Introduction / Abstract", "content": "", "page": 1}

    for page_num, page in enumerate(doc, start=1):
        # Extract blocks with detailed information (spans)
        blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_DICT)["blocks"]
        if not blocks:
            continue

        for block in blocks:
            # We only care about text blocks
            if block['type'] == 0:  
                for line in block['lines']:
                    # Heuristic: if the first span of a line looks like a heading, start a new section
                    if line['spans'] and is_heading(line['spans'][0]):
                        # Save the previous section if it has content
                        if current_section["content"].strip():
                            chunks.append(current_section)
                        
                        # Start a new section with the heading text
                        heading_text = " ".join([s['text'] for s in line['spans']]).strip()
                        current_section = {
                            "title": heading_text,
                            "content": "", # Reset content
                            "page": page_num
                        }
                    else:
                        # Append line text to the current section's content
                        line_text = " ".join([s['text'] for s in line['spans']])
                        current_section["content"] += line_text.strip() + " "

    # Append the last processed section to the list
    if current_section["content"].strip():
        chunks.append(current_section)

    doc.close()
    return chunks
