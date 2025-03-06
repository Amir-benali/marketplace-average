from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import pandas as pd

app = Flask(__name__)

# Function to scrape product data from Newegg based on a search keyword
def scrape_newegg_products(search_keyword):
    # Construct the search URL
    base_url = "https://www.newegg.com"
    search_url = f"{base_url}/p/pl?d={search_keyword.replace(' ', '+')}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    products = []

    # Scrape product items
    for item in soup.select('.item-cell'):  # Newegg's product container
        name_elem = item.select_one('.item-title')
        price_elem = item.select_one('.price-current strong')  # Main price part
        price_cents_elem = item.select_one('.price-current sup')  # Cents part

        if name_elem and price_elem:
            name = name_elem.text.strip()
            price = price_elem.text.strip().replace(',', '')  # Remove commas
            if price_cents_elem:
                price += price_cents_elem.text.strip()  # Add cents
            price = float(price)
            products.append({'name': name, 'price': price})

    return products

# Function to calculate the average market price
def calculate_average_price(products):
    df = pd.DataFrame(products)
    average_price = df['price'].mean()
    return average_price

# Flask route to handle search requests
@app.route('/search', methods=['POST'])
def search():
    # Get the search keyword from the request body
    data = request.json
    if not data or 'q' not in data:
        return jsonify({"error": "Please provide a search keyword in the request body as JSON."}), 400

    search_keyword = data['q']

    # Scrape tech products based on the search keyword
    products = scrape_newegg_products(search_keyword)

    if products:
        # Calculate the average market price
        average_price = calculate_average_price(products)
        response = {
            "search_keyword": search_keyword,
            "product_count": len(products),
            "average_price": round(average_price, 2)
        }
        return jsonify(response)
    else:
        return jsonify({"error": f"No products found for '{search_keyword}'."}), 404

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)