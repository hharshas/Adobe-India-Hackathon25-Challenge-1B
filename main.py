import os
# This environment variable MUST be set BEFORE importing transformers or sentence_transformers
# to ensure the library runs in full offline mode.
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import json
import glob
from datetime import datetime
import time

from pdf_parser import extract_structured_chunks
from semantic_analyzer import SemanticAnalyzer

# Define input/output directories as per challenge specification
INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"

def process_documents(input_json_path, analyzer):
    """
    Main function to process a single challenge input JSON.
    """
    start_time = time.time()
    print(f"--- Starting processing for {os.path.basename(input_json_path)} ---")

    # 1. Load and parse the input JSON
    with open(input_json_path, 'r') as f:
        input_data = json.load(f)

    # --- ROBUST INPUT PARSING ---
    # Handles variations in key names like 'persona' vs 'personnel'
    persona_data = input_data.get('persona', input_data.get('personnel', {}))
    job_data = input_data.get('job_to_be_done', input_data.get('job_to_bc_done', {}))

    persona = persona_data.get('role', 'No persona specified')
    job = job_data.get('task', 'No task specified')
    documents_info = input_data.get('documents', [])
    
    query_text = f"As a {persona}, I need to {job}."
    print(f"Constructed Query: {query_text}")

    # 2. Extract content from all specified PDFs
    all_document_chunks = []
    for doc_info in documents_info:
        pdf_filename = doc_info.get('filename')
        if not pdf_filename:
            continue
        
        pdf_path = os.path.join(INPUT_DIR, pdf_filename)
        if not os.path.exists(pdf_path):
            print(f"WARNING: PDF file not found at {pdf_path}. Skipping.")
            continue
        
        print(f"Parsing '{pdf_filename}'...")
        chunks = extract_structured_chunks(pdf_path)
        for chunk in chunks:
            chunk['document'] = pdf_filename  # Tag each chunk with its source document
        all_document_chunks.extend(chunks)

    # 3. Rank all sections using the semantic analyzer
    ranked_sections = analyzer.rank_sections(query_text, all_document_chunks)

    # 4. Prepare the final output structure according to the new format
    output_data = {
        "metadata": {
            "input_documents": [d.get('filename') for d in documents_info if d.get('filename')],
            "persona": persona,
            "job_to_be_done": job,
            "processing_timestamp": datetime.utcnow().isoformat() + "Z"
        },
        "extracted_sections": [],
        "subsection_analysis": []
    }

    # 5. Populate the output with ranked sections and sub-section analysis
    top_n_for_analysis = 15 # Perform detailed analysis on the top N sections

    for i, section in enumerate(ranked_sections):
        rank = i + 1
        
        # Populate 'extracted_sections'
        output_data["extracted_sections"].append({
            "document": section.get('document'),
            "page_number": section.get('page'),
            "section_title": section.get('title'),
            "importance_rank": rank
        })

        # Populate 'subsection_analysis' for the top N sections
        if rank <= top_n_for_analysis:
            print(f"Performing subsection analysis for rank {rank}...")
            refined_text = analyzer.find_most_relevant_sentence(query_text, section.get('content'))
            
            output_data["subsection_analysis"].append({
                "document": section.get('document'),
                "refined_text": refined_text,
                "page_number": section.get('page'),
                "importance_rank": rank
            })

    # 6. Write the final JSON output
    base_name = os.path.splitext(os.path.basename(input_json_path))[0]
    output_filename = f"{base_name}_output.json"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    print(f"Writing final output to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=4)
    
    end_time = time.time()
    print(f"--- Finished processing in {end_time - start_time:.2f} seconds ---")

if __name__ == "__main__":
    # This check is important for running in a container
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Input directory {INPUT_DIR} not found. Exiting.")
    else:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        analyzer = SemanticAnalyzer()
        
        json_files = glob.glob(os.path.join(INPUT_DIR, '*.json'))
        if not json_files:
            print(f"Error: No input JSON files found in {INPUT_DIR}. Please place your input files there.")
        else:
            for json_file in json_files:
                process_documents(json_file, analyzer)
