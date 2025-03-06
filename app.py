from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import pandas as pd
import random

app = Flask(__name__)

# Function to get a random user agent
def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    ]
    return random.choice(user_agents)

# Function to scrape product data from Newegg using a proxy
def scrape_newegg_products(search_keyword):
    try:
        base_url = "https://www.newegg.com"
        search_url = f"{base_url}/p/pl?d={search_keyword.replace(' ', '+')}"
        
        # Use ScraperAPI
        proxy_url = "http://api.scraperapi.com"
        params = {
            "api_key": "b41aa80c88b8d99d0720d4f40256185b",  
            "url": search_url
        }
        headers = {
            "User-Agent": get_random_user_agent()
        }
        response = requests.get(proxy_url, params=params, headers=headers)
        
        if response.status_code != 200:
            return None, f"Failed to fetch data. Status code: {response.status_code}"

        soup = BeautifulSoup(response.content, 'html.parser')
        products = []

        # Scrape product items
        for item in soup.select('.item-cell'):
            name_elem = item.select_one('.item-title')
            price_elem = item.select_one('.price-current strong')
            price_cents_elem = item.select_one('.price-current sup')

            if name_elem and price_elem:
                name = name_elem.text.strip()
                price = price_elem.text.strip().replace(',', '')
                if price_cents_elem:
                    price += price_cents_elem.text.strip()
                price = float(price)
                products.append({'name': name, 'price': price})

        return products, None

    except Exception as e:
        return None, f"An error occurred while scraping: {str(e)}"

# Function to calculate the average market price
def calculate_average_price(products):
    df = pd.DataFrame(products)
    average_price = df['price'].mean()
    return average_price

# Flask route to handle search requests
@app.route('/search', methods=['POST'])
def search():
    data = request.json
    if not data or 'q' not in data:
        return jsonify({
            "error": "Please provide a search keyword in the request body as JSON.",
            "example_request_body": {"q": "laptop"}
        }), 400

    search_keyword = data['q']
    products, error_message = scrape_newegg_products(search_keyword)

    if error_message:
        return jsonify({
            "error": "Failed to scrape products.",
            "details": error_message,
            "search_keyword": search_keyword
        }), 500

    if products:
        average_price = calculate_average_price(products)
        response = {
            "search_keyword": search_keyword,
            "product_count": len(products),
            "average_price": round(average_price, 2)
        }
        return jsonify(response)
    else:
        return jsonify({
            "error": f"No products found for '{search_keyword}'.",
            "search_keyword": search_keyword
        }), 404

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)