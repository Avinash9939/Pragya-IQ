import requests

def test_map():
    # Login to get JWT
    login_url = "http://localhost:8000/api/v1/auth/login"
    login_data = {"username": "avinash1@gmail.com", "password": "password123"}
    res = requests.post(login_url, data=login_data)
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try updating mapping with only existing columns
    mapping_url = "http://localhost:8000/api/v1/datasets/11/mapping"
    payload = {
        "mapping": {
            "date": "Order Date",
            "amount": "Sales",
            "customer_id": "Customer ID",
            "product": "Product Name",
            "quantity": "Quantity"
        }
    }
    
    res = requests.put(mapping_url, headers=headers, json=payload)
    with open("backend/db_inspection.txt", "w", encoding="utf-8") as f:
        f.write(f"Mapping PUT Status: {res.status_code}\n")
        f.write(f"Response: {res.text}\n")

if __name__ == '__main__':
    test_map()
