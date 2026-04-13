# Commodity Price API Documentation

A FastAPI-based web service that scrapes commodity price data from commodityonline.com using Selenium.

## 📋 Prerequisites

- Python 3.8 or higher
- Google Chrome browser
- ChromeDriver (matching your Chrome version)

## 🔧 Installation

### Step 1: Install Python Dependencies

```bash
pip install fastapi uvicorn selenium beautifulsoup4
```

### Step 2: Install ChromeDriver

**Option A: Automatic Installation (Recommended)**
```bash
pip install webdriver-manager
```

**Option B: Manual Installation**
1. Check your Chrome version: `chrome://version/`
2. Download matching ChromeDriver from [chromedriver.chromium.org](https://chromedriver.chromium.org/)
3. Add ChromeDriver to your system PATH

### Step 3: Verify Installation

```bash
# Test if ChromeDriver is accessible
chromedriver --version
```

## 🚀 Running the API

### Start the Server

```bash
# From the project root directory
uvicorn services.price_api:app --reload --host 0.0.0.0 --port 8000
```

**Command Options:**
- `--reload`: Auto-reload on code changes (development mode)
- `--host 0.0.0.0`: Accept connections from any IP
- `--port 8000`: Run on port 8000

### Production Mode

```bash
uvicorn services.price_api:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📡 API Endpoints

### 1. Root Endpoint
**GET** `/`

Returns API information and available endpoints.

**Example:**
```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "message": "Commodity Price API",
  "version": "1.0.0",
  "endpoints": {
    "/price": "Get commodity prices (query params: state, mandi, crop)",
    "/docs": "Interactive API documentation"
  }
}
```

---

### 2. Get Commodity Prices
**GET** `/price`

Fetches commodity price data from commodityonline.com.

**Query Parameters:**
- `state` (required): State name (e.g., "maharashtra")
- `mandi` (required): Mandi/market name (e.g., "ahmednagar")
- `crop` (required): Crop/commodity name (e.g., "wheat")

**Example Request:**
```bash
curl "http://localhost:8000/price?state=maharashtra&mandi=ahmednagar&crop=wheat"
```

**Example Response:**
```json
{
  "27/12/2025": 2650.0,
  "26/12/2025": 2625.0,
  "25/12/2025": 2600.0,
  "24/12/2025": 2575.0,
  "23/12/2025": 2550.0
}
```

**Response Format:**
- Keys: Date strings in DD/MM/YYYY format
- Values: Average price as float (in Rupees per Quintal)

---

### 3. Interactive Documentation
**GET** `/docs`

Access Swagger UI for interactive API testing.

**URL:** `http://localhost:8000/docs`

---

## 🧪 Testing

### Test Direct Function Call

```bash
# Run the script directly
python services/price_api.py
```

This will fetch sample data and print the first 5 records.

### Test API Endpoints

**Using curl:**
```bash
# Test root endpoint
curl http://localhost:8000/

# Test price endpoint
curl "http://localhost:8000/price?state=maharashtra&mandi=ahmednagar&crop=wheat"
```

**Using Python requests:**
```python
import requests

# Fetch prices
response = requests.get(
    "http://localhost:8000/price",
    params={
        "state": "maharashtra",
        "mandi": "ahmednagar",
        "crop": "wheat"
    }
)

prices = response.json()
print(prices)
```

**Using browser:**
- Navigate to: `http://localhost:8000/docs`
- Click on `/price` endpoint
- Click "Try it out"
- Fill in parameters and click "Execute"

---

## 🔍 How It Works

1. **Request Received**: API receives query parameters (state, mandi, crop)
2. **Browser Launch**: Selenium launches headless Chrome with anti-detection settings
3. **Page Load**: Navigates to commodityonline.com URL
4. **Wait for Content**: Waits for price table to load (up to 20 seconds)
5. **Parse HTML**: Extracts HTML and parses with BeautifulSoup
6. **Extract Data**: Finds table with "avg price" column and extracts date/price pairs
7. **Return JSON**: Converts to `{date: price}` format and returns as JSON

---

## ⚙️ Configuration

### Headless Mode
The browser runs in headless mode by default. To see the browser window (for debugging):

Edit `price_api.py`:
```python
driver = setup_driver(headless=False)  # Change True to False
```

### Timeout Settings
Adjust wait times in `fetch_avg_prices()`:
```python
time.sleep(3)  # Initial page load wait
wait = WebDriverWait(driver, 20)  # Max wait for table (seconds)
```

---

## 🐛 Troubleshooting

### ChromeDriver Not Found
**Error:** `selenium.common.exceptions.WebDriverException: 'chromedriver' executable needs to be in PATH`

**Solution:**
1. Install ChromeDriver manually or use webdriver-manager
2. Ensure ChromeDriver version matches Chrome browser version

### Table Not Found
**Error:** `RuntimeError: Average price table not found`

**Possible Causes:**
- Website structure changed
- Page didn't load completely
- Network issues

**Solution:**
- Increase timeout values
- Check if website is accessible
- Verify URL format is correct

### 403 Forbidden / Bot Detection
**Error:** Browser gets blocked by website

**Solution:**
- The code already includes anti-detection measures
- Try increasing delays between requests
- Check if your IP is blocked

---

## 📝 Example Use Cases

### 1. Get Wheat Prices in Maharashtra
```bash
curl "http://localhost:8000/price?state=maharashtra&mandi=ahmednagar&crop=wheat"
```

### 2. Get Rice Prices in Punjab
```bash
curl "http://localhost:8000/price?state=punjab&mandi=amritsar&crop=rice"
```

### 3. Integration with Python Application
```python
import requests

def get_commodity_prices(state, mandi, crop):
    response = requests.get(
        "http://localhost:8000/price",
        params={"state": state, "mandi": mandi, "crop": crop}
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

# Usage
prices = get_commodity_prices("maharashtra", "ahmednagar", "wheat")
for date, price in prices.items():
    print(f"{date}: ₹{price}")
```

---

## 📊 Response Codes

- `200 OK`: Success
- `404 Not Found`: No price data found or table not found
- `422 Unprocessable Entity`: Missing or invalid query parameters
- `500 Internal Server Error`: Scraping error or server issue

---

## 🔒 Security Notes

- This API scrapes public data from commodityonline.com
- No authentication required
- Rate limiting recommended for production use
- Respect website's robots.txt and terms of service

---

## 📄 License

This is a utility tool for educational and research purposes.

---

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs in terminal
3. Verify all dependencies are installed correctly
