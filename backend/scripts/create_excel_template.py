#!/usr/bin/env python3
"""
Create Excel template for 3D model generation.
Run this script to generate a sample Excel file with the required format.
"""
import pandas as pd

# Sample data with S3 URLs (replace with your actual S3 URLs)
sample_data = {
    'sku': [
        'SI-001',
        'SI-002',
        'SI-003',
        'SI-004',
        'SI-005'
    ],
    'name': [
        'Diamond Stud Earrings',
        'Gold Hoop Earrings',
        'Pearl Drop Earrings',
        'Ruby Ring',
        'Silver Necklace'
    ],
    'type': [
        'earring',
        'earring',
        'earring',
        'ring',
        'necklace'
    ],
    'image_url': [
        'https://your-s3-bucket.s3.amazonaws.com/products/earring1.jpg',
        'https://your-s3-bucket.s3.amazonaws.com/products/earring2.jpg',
        'https://your-s3-bucket.s3.amazonaws.com/products/earring3.jpg',
        'https://your-s3-bucket.s3.amazonaws.com/products/ring1.jpg',
        'https://your-s3-bucket.s3.amazonaws.com/products/necklace1.jpg'
    ],
    'price': [299.99, 199.99, 149.99, 599.99, 399.99],
    'description': [
        'Classic diamond stud earrings with brilliant cut stones',
        'Elegant gold hoop earrings perfect for daily wear',
        'Beautiful pearl drop earrings for special occasions',
        'Stunning ruby ring set in 18k gold',
        'Elegant silver necklace with delicate chain design'
    ],
    'feature': [
        'bestseller',
        'new_arrival',
        '',
        'handcrafted',
        ''
    ]
}

# Create DataFrame and save to Excel
df = pd.DataFrame(sample_data)
output_file = 'excel_3d_generation_template.xlsx'
df.to_excel(output_file, index=False, engine='openpyxl')

print(f"Template created: {output_file}")
print("\nRequired Columns:")
print("  - sku: Unique SKU number (must start with SI, e.g., SI-001)")
print("  - name: Jewelry name")
print("  - image_url: URL to product image - S3 or any HTTP URL (or use 'image_link')")
print("  - description: Product description")
print("\nOptional Columns:")
print("  - type: Jewelry type - earring, ring, necklace (default: earring)")
print("  - price: Price in currency units")
print("  - feature: Special feature tag (e.g., bestseller, new_arrival, handcrafted)")
print("\nReplace the S3 URLs with your actual product image URLs.")
