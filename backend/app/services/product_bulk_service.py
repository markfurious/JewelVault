"""
Product Bulk Upload Service.

Handles Excel file parsing, validation, and bulk product creation.
"""
import io
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.inventory import Inventory, InventoryStatus
from app.models.reorder import ReorderRule
from app.schemas.product import BulkUploadError
from app.utils.sku_generator import check_sku_exists, validate_sku_format


# Expected Excel column names (exact match required)
REQUIRED_COLUMNS = [
    'SKU',
    'Category',
    'Sub Category',
    'Style Number',
    'ST Carat',
    'Product wt',
    'Gold Purity',
    'Certified',
    'Wholesale Price',
    'Retail Price',
    'Online Price',
]

# Column name mapping (Excel -> Python/DB)
COLUMN_MAPPING = {
    'SKU': 'sku',
    'Category': 'category',
    'Sub Category': 'sub_category',
    'Style Number': 'style_number',
    'ST Carat': 'st_carat',
    'Product wt': 'product_weight',
    'Gold Purity': 'gold_purity',
    'Certified': 'certified',
    'Wholesale Price': 'wholesale_price',
    'Retail Price': 'retail_price',
    'Online Price': 'online_price',
}

# Required fields that cannot be empty
REQUIRED_FIELDS = ['SKU', 'Retail Price']


class ProductBulkService:
    """Service for bulk product operations via Excel upload."""

    def __init__(self, db: Session):
        self.db = db

    def parse_excel(self, file_bytes: bytes) -> Tuple[List[Dict[str, Any]], List[BulkUploadError]]:
        """
        Parse Excel file and return rows with validation errors.

        Args:
            file_bytes: Raw bytes from uploaded Excel file

        Returns:
            Tuple of (parsed_rows, errors)
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for Excel upload. Install with: pip install pandas openpyxl")

        try:
            # Read Excel file
            df = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl')
        except Exception as e:
            raise ValueError(f"Failed to parse Excel file: {str(e)}")

        # Check for required columns
        errors = []
        missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)
        if missing_columns:
            for col in missing_columns:
                errors.append(BulkUploadError(
                    row=0,
                    column=col,
                    error=f"Required column '{col}' is missing from the file"
                ))
            return [], errors

        # Convert DataFrame to list of dicts
        # Replace NaN with None for cleaner handling
        df = df.where(pd.notnull(df), None)
        rows = df.to_dict(orient='records')

        return rows, errors

    def validate_row(self, row: Dict[str, Any], row_number: int) -> List[BulkUploadError]:
        """
        Validate a single row from the Excel file.

        Args:
            row: Dictionary representing one product row
            row_number: Row number in Excel (1-indexed, header is row 1)

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        for field in REQUIRED_FIELDS:
            value = row.get(field)
            # Check for None, NaN, or empty string
            import math
            is_empty = (
                value is None or
                (isinstance(value, float) and math.isnan(value)) or
                (isinstance(value, str) and value.strip() == '')
            )
            if is_empty:
                errors.append(BulkUploadError(
                    row=row_number,
                    column=field,
                    error=f"Missing value"
                ))

        # If we have missing required fields, return early
        if errors:
            return errors

        # Validate SKU format
        sku = row.get('SKU')
        if sku and not validate_sku_format(str(sku)):
            errors.append(BulkUploadError(
                row=row_number,
                column='SKU',
                error=f"Invalid SKU format: '{sku}'. Must be SI followed by 5 digits (e.g., SI00001)"
            ))

        # Check for duplicate SKU in database
        if sku and check_sku_exists(self.db, str(sku)):
            errors.append(BulkUploadError(
                row=row_number,
                column='SKU',
                error=f"SKU '{sku}' already exists in database"
            ))

        # Validate numeric fields
        numeric_fields = ['ST Carat', 'Product wt', 'Wholesale Price', 'Retail Price', 'Online Price']
        for field in numeric_fields:
            value = row.get(field)
            if value is not None:
                try:
                    num_value = float(value)
                    if num_value < 0:
                        errors.append(BulkUploadError(
                            row=row_number,
                            column=field,
                            error=f"Value must be non-negative, got {value}"
                        ))
                except (ValueError, TypeError):
                    errors.append(BulkUploadError(
                        row=row_number,
                        column=field,
                        error=f"Invalid number: '{value}'"
                    ))

        # Validate Gold Purity values
        gold_purity = row.get('Gold Purity')
        if gold_purity:
            valid_purities = ['10K', '14K', '18K', '22K', '24K', '9K', '916', '750', '585']
            if str(gold_purity).upper() not in [p.upper() for p in valid_purities]:
                errors.append(BulkUploadError(
                    row=row_number,
                    column='Gold Purity',
                    error=f"Invalid gold purity: '{gold_purity}'. Valid values: {', '.join(valid_purities)}"
                ))

        # Validate Certified field
        certified = row.get('Certified')
        if certified is not None and not isinstance(certified, bool):
            # Try to convert string/number to boolean
            if str(certified).lower() in ['true', '1', 'yes', 'y']:
                row['Certified'] = True
            elif str(certified).lower() in ['false', '0', 'no', 'n', '']:
                row['Certified'] = False
            else:
                errors.append(BulkUploadError(
                    row=row_number,
                    column='Certified',
                    error=f"Invalid boolean value: '{certified}'"
                ))

        return errors

    def validate_all_rows(
        self,
        rows: List[Dict[str, Any]]
    ) -> Tuple[bool, List[BulkUploadError]]:
        """
        Validate all rows in the upload.

        Args:
            rows: List of row dictionaries

        Returns:
            Tuple of (all_valid, errors)
        """
        all_errors = []

        for idx, row in enumerate(rows):
            # Excel row number (1-indexed, +1 for header)
            row_number = idx + 2  # Header is row 1, data starts at row 2
            errors = self.validate_row(row, row_number)
            all_errors.extend(errors)

        return len(all_errors) == 0, all_errors

    def create_products_bulk(
        self,
        rows: List[Dict[str, Any]],
        initial_quantity: float = 0,
        initial_location: Optional[str] = None,
    ) -> int:
        """
        Create products in bulk from validated rows.

        Uses a transaction - all or nothing.

        Args:
            rows: List of validated row dictionaries
            initial_quantity: Default initial stock quantity
            initial_location: Default initial stock location

        Returns:
            Number of products created
        """
        created_count = 0

        for row in rows:
            # Map Excel columns to product fields
            product_data = {
                'sku': str(row.get('SKU')),
                'name': f"{row.get('Category', 'Unknown')} - {row.get('Style Number', 'N/A')}",
                'description': None,
                'category': row.get('Category'),
                'sub_category': row.get('Sub Category'),
                'style_number': row.get('Style Number'),
                'st_carat': float(row['ST Carat']) if row.get('ST Carat') else None,
                'product_weight': float(row['Product wt']) if row.get('Product wt') else None,
                'gold_purity': row.get('Gold Purity'),
                'certified': bool(row.get('Certified', False)),
                'cost_price': float(row['Wholesale Price']) if row.get('Wholesale Price') else None,
                'wholesale_price': float(row['Wholesale Price']) if row.get('Wholesale Price') else None,
                'retail_price': float(row['Retail Price']) if row.get('Retail Price') else None,
                'online_price': float(row['Online Price']) if row.get('Online Price') else None,
                'is_active': True,
                'attributes': {},
                'default_reorder_threshold': 10,
            }

            # Create product
            product = Product(**product_data)
            self.db.add(product)
            self.db.flush()  # Get the ID

            # Create initial inventory (item-based: always create with status)
            # In item-based model, each product has exactly one inventory item
            inventory = Inventory(
                product_id=product.id,
                status=InventoryStatus.AVAILABLE,
                location=initial_location,
            )
            self.db.add(inventory)

            # Create default reorder rule
            reorder_rule = ReorderRule(
                product_id=product.id,
                min_threshold=10,
                target_stock=50,
            )
            self.db.add(reorder_rule)

            created_count += 1

        self.db.commit()
        return created_count

    def process_upload(
        self,
        file_bytes: bytes,
        initial_quantity: float = 0,
        initial_location: Optional[str] = None,
    ) -> Tuple[bool, Any]:
        """
        Process complete Excel upload.

        Args:
            file_bytes: Raw Excel file bytes
            initial_quantity: Default initial stock quantity
            initial_location: Default initial stock location

        Returns:
            Tuple of (success, result)
            - If success: (True, records_created_count)
            - If failure: (False, list_of_errors)
        """
        # Parse Excel
        rows, parse_errors = self.parse_excel(file_bytes)

        if parse_errors:
            return False, parse_errors

        if not rows:
            return False, [BulkUploadError(
                row=0,
                column='File',
                error='No data rows found in Excel file'
            )]

        # Validate all rows
        all_valid, validation_errors = self.validate_all_rows(rows)

        if not all_valid:
            return False, validation_errors

        # All valid - create products in transaction
        try:
            created_count = self.create_products_bulk(
                rows,
                initial_quantity=initial_quantity,
                initial_location=initial_location,
            )
            return True, created_count
        except Exception as e:
            self.db.rollback()
            return False, [BulkUploadError(
                row=0,
                column='Database',
                error=f'Failed to create products: {str(e)}'
            )]
