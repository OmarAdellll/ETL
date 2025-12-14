import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

def scrape_band_info_robust(url):
    MAX_RETRIES = 2  
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        for attempt in range(MAX_RETRIES):
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = context.new_page()
            
            try:
                
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                
                try:
                    page.wait_for_selector("table.eecat", state="attached", timeout=3000)
                    has_table = True
                except:
                    has_table = False

                
                if not has_table:
                    
                    
                    for tab_name in ["Bands", "Table Schema", "Schema"]:
                        
                        tab_locator = page.locator(f"//div[contains(@class, 'devsite-tabs-wrapper')]//tab[contains(., '{tab_name}')]")
                        
                        if tab_locator.count() > 0:
                            
                            try:
                                
                                click_target = tab_locator.locator("a").first if tab_locator.locator("a").count() > 0 else tab_locator
                                click_target.click(force=True)
                                
                                page.wait_for_selector("table.eecat", state="visible", timeout=2000)
                                has_table = True
                                break 
                            except:
                                pass 

                if not has_table:
                    pass
                
                attributes = page.evaluate("""
                    () => {
                        // Find the table anywhere on the page
                        const table = document.querySelector('table.eecat');
                        if (!table) return [];
                        
                        const rows = Array.from(table.querySelectorAll('tr'));
                        if (rows.length < 2) return []; // Only header found

                        const results = [];
                        
                        // Dynamic Header Parsing
                        const headerRow = rows[0];
                        const headers = Array.from(headerRow.querySelectorAll('th')).map(th => th.innerText.toLowerCase().trim());
                        
                        const nameIdx = headers.findIndex(h => h.includes('name'));
                        if (nameIdx === -1) return []; // Mandatory field
                        
                        const descIdx = headers.findIndex(h => h.includes('description'));
                        const unitIdx = headers.findIndex(h => h.includes('unit'));
                        
                        // Iterate Data Rows
                        for (let i = 1; i < rows.length; i++) {
                            const row = rows[i];
                            const cols = row.querySelectorAll('td');
                            
                            // Crash Fix: Skip colspan rows (Bitmasks/Separators)
                            if (cols.length === 0 || cols[0].hasAttribute('colspan')) continue;
                            if (cols.length <= nameIdx) continue;
                            
                            // Extract Name
                            let name = cols[nameIdx].innerText.trim().split(' ')[0]; // Remove footnotes like "B1*"
                            
                            // Extract Description
                            let description = "No description";
                            if (descIdx !== -1 && cols[descIdx]) {
                                description = cols[descIdx].innerText.trim();
                            } else {
                                // Fallback: Use last column if explicit description column missing
                                description = cols[cols.length - 1].innerText.trim();
                            }
                            
                            // Extract Unit
                            let unit = "N/A";
                            if (unitIdx !== -1 && cols[unitIdx]) {
                                unit = cols[unitIdx].innerText.trim();
                            }
                            
                            results.push({name, description, unit});
                        }
                        return results;
                    }
                """)

                context.close()
                return attributes

            except Exception as e:
                
                if attempt == MAX_RETRIES - 1:
                    print(f"                ❌ Failed to scrape {url}: {e}")
                context.close()
                time.sleep(1)
        
        return [] 