import requests
import json

# API configuration
BASE_URL = "http://localhost:8000/api/v1"
PRODUCT_ID = 2  # Áo Thun 3 Sọc

# Colors: 1=Đen, 2=Trắng, 3=Xám, etc.
# Sizes: 1=S, 2=M, 3=L, 4=XL, 5=2XL

# Variants to create
variants = [
    # Màu Đen
    {"color_id": 1, "size_id": 1, "sku": "AO-THUN-3-SOC-BLACK-S", "stock_quantity": 20},
    {"color_id": 1, "size_id": 2, "sku": "AO-THUN-3-SOC-BLACK-M", "stock_quantity": 25},
    {"color_id": 1, "size_id": 3, "sku": "AO-THUN-3-SOC-BLACK-L", "stock_quantity": 30},
    {"color_id": 1, "size_id": 4, "sku": "AO-THUN-3-SOC-BLACK-XL", "stock_quantity": 15},
    
    # Màu Trắng
    {"color_id": 2, "size_id": 1, "sku": "AO-THUN-3-SOC-WHITE-S", "stock_quantity": 18},
    {"color_id": 2, "size_id": 2, "sku": "AO-THUN-3-SOC-WHITE-M", "stock_quantity": 22},
    {"color_id": 2, "size_id": 3, "sku": "AO-THUN-3-SOC-WHITE-L", "stock_quantity": 28},
    {"color_id": 2, "size_id": 4, "sku": "AO-THUN-3-SOC-WHITE-XL", "stock_quantity": 12},
    
    # Màu Xám (nếu color_id = 3)
    {"color_id": 3, "size_id": 1, "sku": "AO-THUN-3-SOC-GREY-S", "stock_quantity": 15},
    {"color_id": 3, "size_id": 2, "sku": "AO-THUN-3-SOC-GREY-M", "stock_quantity": 20},
    {"color_id": 3, "size_id": 3, "sku": "AO-THUN-3-SOC-GREY-L", "stock_quantity": 25},
    {"color_id": 3, "size_id": 4, "sku": "AO-THUN-3-SOC-GREY-XL", "stock_quantity": 10},
]

def create_variant(product_id, variant_data):
    """Create a single product variant via API"""
    url = f"{BASE_URL}/products/{product_id}/variants"
    
    # API payload
    payload = {
        "product_id": product_id,
        "color_id": variant_data["color_id"],
        "size_id": variant_data["size_id"],
        "sku": variant_data["sku"],
        "price_adjustment": 0,  # No price difference
        "stock_quantity": variant_data["stock_quantity"],
        "is_active": True
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code in [200, 201]:
            print(f"✓ Created variant: {variant_data['sku']}")
            return True
        else:
            print(f"✗ Failed to create {variant_data['sku']}: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error creating {variant_data['sku']}: {str(e)}")
        return False

def main():
    print(f"Creating variants for product ID: {PRODUCT_ID}")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    for variant in variants:
        if create_variant(PRODUCT_ID, variant):
            success_count += 1
        else:
            fail_count += 1
    
    print("=" * 60)
    print(f"Summary: {success_count} created, {fail_count} failed")
    
    # Verify by fetching variants
    print("\nVerifying variants...")
    try:
        response = requests.get(f"{BASE_URL}/products/{PRODUCT_ID}/variants")
        if response.status_code == 200:
            variants = response.json()
            print(f"Total variants now: {len(variants)}")
            for v in variants:
                print(f"  - Color ID {v.get('color_id')}, Size ID {v.get('size_id')}: Stock {v.get('stock_quantity')}")
        else:
            print(f"Failed to fetch variants: {response.status_code}")
    except Exception as e:
        print(f"Error verifying: {str(e)}")

if __name__ == "__main__":
    main()
