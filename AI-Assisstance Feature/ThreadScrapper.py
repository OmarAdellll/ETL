import json
import time
from tqdm import tqdm 
import concurrent.futures
from BandsPlaywright import scrape_band_info_robust


INPUT_FILE = "GEE_datasets_augmented.json"
OUTPUT_FILE = "GEE_datasets_augmented_threaded.json"
MAX_WORKERS = 5  # Keep this low (5-10) to avoid Google banning your IP

def process_dataset(dataset):
    band_url = dataset.get("asset_url", "")
    if not band_url:
        print(f"❌-> Skipping dataset: {dataset.get('id', 'Unknown')} (No URL)")
        return dataset 
    
    if dataset.get("bands"):
        print(f"✔-> Skipping dataset: {dataset.get('id', 'Unknown')} (bands already exist)")
        return dataset 
    
    try:
        bands = scrape_band_info_robust(band_url)
        if bands:
            dataset["bands"] = bands
            print(f"✅-> Successfully scraped bands for dataset: {dataset.get('id', 'Unknown')}")
        else:
            print(f"❌-> No bands found for dataset: {dataset.get('id', 'Unknown')}")
            dataset["bands"] = []
        
    except Exception as e:
        print(f"❌-> Error scraping dataset {dataset.get('id', 'Unknown')}: {e}")
        dataset['bands'] = [] 
        return dataset
    
    time.sleep(0.7) 
    return dataset


def run_threaded_augmentation(input_file=INPUT_FILE, output_file=OUTPUT_FILE):
    print(f"🚀 Starting Multi-Threaded Scraper (Workers: {MAX_WORKERS})...")
    
    try:
        with open(INPUT_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ Input file not found.")
        return
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    
        augmented_datasets = list(tqdm(executor.map(process_dataset, data), total=len(data), unit="dataset"))
        
    success_count = sum(1 for ds in augmented_datasets if ds.get("bands"))
    
    end_time = time.time()
    duration = end_time - start_time
    
    
    
    print("\n" + "="*40)
    print(f"✅ DONE! Processed {len(data)} datasets in {duration:.2f} seconds.")
    print(f"📊 Datasets with Bands: {success_count}")
    print("="*40)

    with open(OUTPUT_FILE, 'w') as f:
            json.dump(augmented_datasets, f, indent=4)
    print(f"💾 Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    run_threaded_augmentation()