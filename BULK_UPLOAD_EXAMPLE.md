# Bulk Upload Feature Guide

## Overview

The bulk upload feature allows you to import multiple products at once via Excel file.

## Excel File Format

### Required Columns (exact names):

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| SKU | String | Yes | Must match pattern `SI#####` (e.g., SI00001) |
| Category | String | Yes | Product category (e.g., Rings, Necklaces) |
| Sub Category | String | No | Sub-category (e.g., Gold, Diamond) |
| Style Number | String | No | Product style/SKU reference |
| ST Carat | Number | No | Stone carat weight |
| Product wt | Number | No | Product weight in grams |
| Gold Purity | String | No | e.g., 10K, 14K, 18K, 22K, 24K |
| Certified | Boolean | No | true/false or 1/0 |
| Wholesale Price | Number | No | Wholesale price |
| Retail Price | Number | **Yes** | Retail price (REQUIRED) |
| Online Price | Number | No | Online store price |

## API Endpoint

```
POST /api/v1/products/bulk-upload
```

### Parameters:
- `file`: Excel file (.xlsx) - **Required**
- `initial_quantity`: Default stock quantity - Optional (default: 0)
- `initial_location`: Default stock location - Optional

### Example (curl):

```bash
curl -X POST http://localhost:8000/api/v1/products/bulk-upload \
  -F "file=@products.xlsx" \
  -F "initial_quantity=10"
```

## Success Response

```json
{
  "message": "Bulk upload successful",
  "records_created": 5
}
```

## Error Response

```json
{
  "detail": [
    {
      "row": 4,
      "column": "Retail Price",
      "error": "Missing value"
    },
    {
      "row": 7,
      "column": "SKU",
      "error": "Invalid SKU format: 'INVALID123'. Must be SI followed by 5 digits (e.g., SI00001)"
    }
  ]
}
```

## Validation Rules

1. **All rows are validated BEFORE any insertion**
   - If ANY row fails, the ENTIRE file is rejected
   - No partial uploads

2. **SKU Format**
   - Must match pattern: `^SI\d{5}$`
   - Examples: SI00001, SI00123, SI99999
   - Must be unique in database

3. **Required Fields**
   - SKU: Always required
   - Retail Price: Always required

4. **Gold Purity Values**
   - Valid: 9K, 10K, 14K, 18K, 22K, 24K, 585, 750, 916

## Example Excel Data

| SKU | Category | Sub Category | Style Number | ST Carat | Product wt | Gold Purity | Certified | Wholesale Price | Retail Price | Online Price |
|-----|----------|--------------|--------------|----------|------------|-------------|-----------|-----------------|--------------|--------------|
| SI00001 | Rings | Gold | RG-001 | | 5.5 | 18K | FALSE | 800 | 1500 | 1400 |
| SI00002 | Necklaces | Diamond | NK-001 | 0.75 | 8.2 | 14K | TRUE | 2000 | 3500 | 3300 |
| SI00003 | Earrings | Gold | ER-001 | | 3.1 | 22K | FALSE | 500 | 950 | 900 |

## SKU Auto-Generation

If you don't provide a SKU, the system will auto-generate one:
- Format: SI + 5 digit sequential number
- Example: SI00001, SI00002, SI00003...
- Guaranteed unique with database-level locking

## Testing Scenarios

### 1. Duplicate SKU Test
```bash
# First upload succeeds
curl -X POST http://localhost:8000/api/v1/products/bulk-upload \
  -F "file=@products.xlsx"

# Second upload with same SKUs fails
# Response: {"detail": [{"row": 2, "column": "SKU", "error": "SKU 'SI00001' already exists"}]}
```

### 2. Invalid SKU Format Test
```bash
# File with SKU "INVALID123"
# Response: {"detail": [{"row": 3, "column": "SKU", "error": "Invalid SKU format..."}]}
```

### 3. Missing Required Field Test
```bash
# File with missing Retail Price
# Response: {"detail": [{"row": 4, "column": "Retail Price", "error": "Missing value"}]}
```

### 4. Atomic Upload Test
```bash
# File with 10 rows, row 7 has error
# Result: 0 records created (all rejected)
```

## Python Example

```python
import requests

# Upload file
with open('products.xlsx', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/products/bulk-upload',
        files={'file': f},
        data={'initial_quantity': 10}
    )

if response.status_code == 200:
    print(response.json())
else:
    print(f"Error: {response.json()}")
```
