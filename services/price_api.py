import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import json


app = FastAPI(title="Commodity Price API", version="1.0.0")


def setup_driver(headless=True):
    """Setup Chrome driver with anti-detection options"""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless=new")  # Use new headless mode
    
    # Anti-detection options
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Set realistic window size
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Updated user agent
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
    
    # Additional stealth options
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--dns-prefetch-disable")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Override navigator properties
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            )
        })
        
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        print("Make sure ChromeDriver is installed and in PATH")
        raise


def fetch_avg_prices(state: str, mandi: str, crop: str):
    """Fetch commodity price data using headless Selenium.
    
    Args:
        state: State name (e.g., "maharashtra")
        mandi: Mandi name (e.g., "ahmednagar")
        crop: Crop name (e.g., "wheat")
    
    Returns:
        List of tuples: [(date, avg_price), ...]
    """
    url = f"https://www.commodityonline.com/mandiprices/{crop}/{state}/{mandi}"
    
    driver = setup_driver(headless=True)
    
    try:
        print(f"Loading page: {url}")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Wait for table to be present
        print("Waiting for table to load...")
        wait = WebDriverWait(driver, 20)
        
        # Wait for any table to be present
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        # Get page source and parse with BeautifulSoup
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        
        # Find the mandi prices table with "avg price" column
        table = None
        for tbl in soup.find_all("table"):
            headers = [th.get_text(strip=True).lower() for th in tbl.find_all("th")]
            if "avg price" in " ".join(headers):
                table = tbl
                break
        
        if table is None:
            raise RuntimeError("Average price table not found; check page structure/selectors")
        
        avg_price_list = dict()  # (date, avg_price)
        
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 9:
                continue
            
            # from the current page structure:
            # 0: Commodity, 1: Arrival Date, ..., 8: Avg price
            date_text = tds[1].get_text(strip=True)       # e.g. "27/12/2025"
            avg_text = tds[8].get_text(strip=True)        # e.g. "Rs 2650 / Quintal"
            
            if not date_text or not avg_text:
                continue
            
            # clean avg price to numeric if needed
            cleaned = "".join(ch for ch in avg_text if ch.isdigit() or ch in ".-")
            try:
                avg_val = float(cleaned)
            except ValueError:
                avg_val = avg_text
            
            avg_price_list[date_text] = avg_val

        # Parse the visible "main-table2" into headers and row dicts
        table = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "main-table2")))
        rows = table.find_elements(By.TAG_NAME, "tr")

        headers = []


       

        for row in rows:
            # Prefer header cells if present
            th_cells = row.find_elements(By.TAG_NAME, "th")
            td_cells = row.find_elements(By.TAG_NAME, "td")

            if th_cells and not headers:
                headers = [th.text.strip() for th in th_cells if th.text.strip()]
                continue

            if td_cells:
                values = [td.text.strip() for td in td_cells]

                if headers:
                    # Map headers to values, handling mismatched lengths
                    row_dict = {}
                    for idx, val in enumerate(values):
                        key = headers[idx] if idx < len(headers) else f"col_{idx}"
                        row_dict[key] = val
                else:
                    # No headers found; use generic column names
                    row_dict = {f"col_{idx}": val for idx, val in enumerate(values)}


            break

                
        
        
        
        return {"meta": row_dict, "prices": avg_price_list}
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        raise
    finally:
        driver.quit()


# FastAPI Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Commodity Price API",
        "version": "1.0.0",
        "endpoints": {
            "/price": "Get commodity prices (query params: state, mandi, crop)",
            "/docs": "Interactive API documentation"
        }
    }


@app.get("/price")
async def get_price_endpoint(
    state: str = Query(..., description="State name (e.g., 'maharashtra')"),
    mandi: str = Query(..., description="Mandi name (e.g., 'ahmednagar')"),
    crop: str = Query(..., description="Crop name (e.g., 'wheat')")
):
    """
    Fetch commodity price data from commodityonline.com
    
    Returns JSON in format: {"date": price, ...}
    """
    try:
        # Fetch data
        data = fetch_avg_prices(state=state, mandi=mandi, crop=crop)
        
        if not data:
            raise HTTPException(status_code=404, detail="No price data found")
        
        # Return structured data containing table meta and prices
        return JSONResponse(content=data)
        
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    # Test the function directly
    data = fetch_avg_prices(state="maharashtra", mandi="ahmednagar", crop="wheat")
    meta = data.get("meta", {})
    print("Meta headers:", meta.get("headers"))
    print(f"Found {len(meta.get('rows', []))} rows in table")
    print("Sample rows:")
    for row in meta.get("rows", [])[:5]:
        print(row)
    print("Prices sample:")
    for date, price in list(data.get("prices", {}).items())[:5]:
        print(f"  {date}: {price}")
