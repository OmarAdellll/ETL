import os
import GEEQueryAssistant
import ThreadScrapper

def run_assistant(query: str = None):
    
    input_json = "gee_catalog.json"
    augmented_json = "GEE_datasets_augmented_threaded.json"

    # Optimization: Only run scraping if the augmented file doesn't exist
    if not os.path.exists(augmented_json):
        print("⚠ Augmented data not found. Starting Scraper...")
        ThreadScrapper.run_threaded_augmentation(
            input_file=input_json,
            output_file=augmented_json
        )
    else:
        print("✔ Found existing augmented data. Skipping scraper.")
    
    # Initialize Assistant
    assistant = GEEQueryAssistant.GEEQueryAssistant(
        json_path=augmented_json, # Ensure path is correct
        persist_directory="./chroma_db_v2"
    )
    return assistant.generate_sql(query)


if __name__ == "__main__":
    run_assistant()