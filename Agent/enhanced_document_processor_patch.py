# Patch for enhanced_document_processor.py
# Add this inside process_document function after processed_data is ready

import json
from pathlib import Path

def ensure_processed_output(document_path, processed_data, output_dir='data/processed'):
    """
    Ensure the processed document is saved to the output directory.
    
    Args:
        document_path (str): Path to the original document
        processed_data (dict): Processed document data
        output_dir (str): Directory to save processed files
    """
    # Create output directory if it doesn't exist
    processed_out = Path(output_dir)
    processed_out.mkdir(parents=True, exist_ok=True)
    
    # Create output filename using the original document's stem
    out_file = processed_out / (Path(document_path).stem + '.json')
    
    # Write the processed data to the output file
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(processed_data, indent=2, ensure_ascii=False, f)
    
    print(f"Saved processed document to {out_file}")
    return out_file 