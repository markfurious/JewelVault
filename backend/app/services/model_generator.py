"""
3D Model Generator Service.
Uses TripoSR (self-hosted) to generate 3D models from images.
GitHub: https://github.com/VAST-AI-Research/TripoSR
"""
import os
import subprocess
import shutil
import requests
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import uuid
import pandas as pd
from openpyxl import load_workbook

from app.db.base import db_session
from app.models.jewelry import Jewelry


class TripoSRGenerator:
    """
    Self-hosted 3D model generator using TripoSR.

    Requirements:
    - TripoSR installed locally
    - NVIDIA GPU with 8GB+ VRAM (recommended)
    - Can run on CPU but slower (5-10 min per model)
    """

    def __init__(self):
        # TripoSR installation path (adjust based on your setup)
        self.tripo_sr_path = os.environ.get(
            'TRIPOR_PATH',
            '/opt/TripoSR'  # Default installation path
        )
        self.models_output_dir = os.path.join(
            os.path.dirname(__file__),
            '..', '..', '..', 'public', 'models'
        )
        os.makedirs(self.models_output_dir, exist_ok=True)

    def check_installation(self) -> bool:
        """Check if TripoSR is installed and accessible."""
        script_path = os.path.join(self.tripo_sr_path, 'infer.py')
        return os.path.exists(script_path)

    def generate_from_image(
        self,
        image_path: str,
        output_filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate 3D model from a single image.

        Args:
            image_path: Path to input image (JPG/PNG)
            output_filename: Optional output filename (without extension)

        Returns:
            Path to generated .glb file, or None if failed
        """
        if not self.check_installation():
            print("TripoSR not found. Please install: pip install triporsr")
            return None

        # Generate output filename
        if not output_filename:
            output_filename = f"gen_{uuid.uuid4().hex[:8]}"

        output_path = os.path.join(self.models_output_dir, f"{output_filename}.glb")

        # Run TripoSR inference
        cmd = [
            'python',
            os.path.join(self.tripo_sr_path, 'infer.py'),
            '--input', image_path,
            '--output', output_path,
            '--format', 'glb',
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0 and os.path.exists(output_path):
                # Return relative URL path
                return f"/models/{output_filename}.glb"
            else:
                print(f"TripoSR failed: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            print("TripoSR generation timed out")
            return None
        except Exception as e:
            print(f"Error generating 3D model: {e}")
            return None

    def generate_batch(
        self,
        image_paths: List[str],
        jewelry_ids: Optional[List[str]] = None
    ) -> List[dict]:
        """
        Generate 3D models for multiple images.

        Args:
            image_paths: List of image file paths
            jewelry_ids: Optional list of jewelry IDs to update

        Returns:
            List of dicts with {image, model_url, status, error}
        """
        results = []

        for i, image_path in enumerate(image_paths):
            jewelry_id = jewelry_ids[i] if jewelry_ids and i < len(jewelry_ids) else None

            # Generate output filename from jewelry ID or image name
            if jewelry_id:
                output_filename = f"jewelry_{jewelry_id}"
            else:
                output_filename = f"gen_{uuid.uuid4().hex[:8]}"

            model_url = self.generate_from_image(image_path, output_filename)

            result = {
                'image': image_path,
                'model_url': model_url,
                'status': 'success' if model_url else 'failed',
                'error': None if model_url else 'Generation failed'
            }

            # Update database if jewelry_id provided
            if model_url and jewelry_id:
                self._update_jewelry_model(jewelry_id, model_url)

            results.append(result)

        return results

    def _update_jewelry_model(self, jewelry_id: str, model_url: str) -> bool:
        """Update jewelry record with generated model URL."""
        try:
            db = db_session()
            jewelry = db.query(Jewelry).filter(Jewelry.id == jewelry_id).first()
            if jewelry:
                jewelry.model_url = model_url
                db.commit()
                return True
            return False
        except Exception as e:
            print(f"Failed to update jewelry: {e}")
            return False
        finally:
            db.close()


# Simple CPU-based alternative using stable-fast-3d (fallback)
class Simple3DGenerator:
    """
    Simpler 3D generator using stable-fast-3d.
    Works on CPU but lower quality.
    GitHub: https://github.com/stabilityai/stable-fast-3d
    """

    def __init__(self):
        self.models_output_dir = os.path.join(
            os.path.dirname(__file__),
            '..', '..', '..', 'public', 'models'
        )
        os.makedirs(self.models_output_dir, exist_ok=True)

    def generate_from_image(
        self,
        image_path: str,
        output_filename: Optional[str] = None
    ) -> Optional[str]:
        """Generate 3D model using stable-fast-3d."""
        try:
            from stable_fast_3d import Model
            import torch
            from PIL import Image
            import numpy as np

            # Load model (downloads on first run)
            model = Model.from_pretrained('stabilityai/stable-fast-3d')
            model = model.to('cuda' if torch.cuda.is_available() else 'cpu')

            # Load and process image
            image = Image.open(image_path).convert('RGBA')
            image = image.resize((512, 512))

            # Generate 3D
            result = model.run(image)

            # Save output
            if not output_filename:
                output_filename = f"gen_{uuid.uuid4().hex[:8]}"

            output_path = os.path.join(self.models_output_dir, f"{output_filename}.glb")
            result.save(output_path)

            return f"/models/{output_filename}.glb"

        except ImportError:
            print("stable-fast-3d not installed. Install with: pip install stable-fast-3d")
            return None
        except Exception as e:
            print(f"Error in simple 3D generator: {e}")
            return None


def get_generator():
    """Get the appropriate 3D generator."""
    # Try TripoSR first (better quality)
    generator = TripoSRGenerator()
    if generator.check_installation():
        return generator

    # Fallback to simple generator
    return Simple3DGenerator()


def generate_3d_for_all_jewelry():
    """
    Generate 3D models for all jewelry items that have thumbnail images
    but no 3D model yet.
    """
    db = db_session()
    generator = get_generator()

    # Find jewelry without 3D models
    jewelry_items = db.query(Jewelry).filter(
        Jewelry.thumbnail_url.isnot(None),
        (Jewelry.model_url.is_(None)) | (Jewelry.model_url.like('%placeholder%'))
    ).all()

    print(f"Found {len(jewelry_items)} jewelry items needing 3D models")

    results = []
    for item in jewelry_items:
        print(f"Generating 3D model for: {item.name}")

        # Convert thumbnail URL to local path
        thumbnail_path = None
        if item.thumbnail_url.startswith('/'):
            # Try to find the actual file
            possible_paths = [
                os.path.join(os.path.dirname(__file__), '..', '..', '..', item.thumbnail_url.lstrip('/')),
                os.path.join(os.path.dirname(__file__), '..', '..', 'public', item.thumbnail_url.lstrip('/')),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    thumbnail_path = path
                    break

        if thumbnail_path:
            model_url = generator.generate_from_image(
                thumbnail_path,
                f"jewelry_{item.id}"
            )

            if model_url:
                item.model_url = model_url
                db.commit()
                results.append({
                    'id': str(item.id),
                    'name': item.name,
                    'model_url': model_url,
                    'status': 'success'
                })
                print(f"  ✓ Generated: {model_url}")
            else:
                results.append({
                    'id': str(item.id),
                    'name': item.name,
                    'status': 'failed'
                })
                print(f"  ✗ Failed to generate")
        else:
            results.append({
                'id': str(item.id),
                'name': item.name,
                'status': 'no_image',
                'reason': f"Thumbnail not found: {item.thumbnail_url}"
            })
            print(f"  ✗ No image found at: {item.thumbnail_url}")

    db.close()
    return results


def download_image_from_url(image_url: str, save_dir: str, filename: str) -> Optional[str]:
    """
    Download an image from URL (S3 or any HTTP URL) and save locally.

    Args:
        image_url: URL of the image to download
        save_dir: Directory to save the image
        filename: Filename for the saved image

    Returns:
        Path to saved image, or None if failed
    """
    try:
        os.makedirs(save_dir, exist_ok=True)

        # Download image
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(image_url, headers=headers, timeout=30)
        response.raise_for_status()

        # Save image
        file_path = os.path.join(save_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(response.content)

        return file_path
    except Exception as e:
        print(f"Failed to download image from {image_url}: {e}")
        return None


def process_excel_and_generate_3d(
    excel_file_path: str,
    temp_dir: str = None
) -> List[dict]:
    """
    Process Excel file with S3 URLs and generate 3D models.

    Excel file should have columns:
    - sku: SKU number (required, must be unique)
    - name: Jewelry name
    - type: Jewelry type (earring, ring, necklace)
    - image_url: URL to product image (S3 or any HTTP URL)
    - image_link: Alternative image link column name
    - price: Price (optional, defaults to 0)
    - description: Description (required)

    Args:
        excel_file_path: Path to uploaded Excel file
        temp_dir: Temporary directory for downloaded images

    Returns:
        List of results with {name, status, model_url, error, jewelry_id}
    """
    if temp_dir is None:
        temp_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'temp', '3d-generation')

    os.makedirs(temp_dir, exist_ok=True)

    # Read Excel file
    try:
        df = pd.read_excel(excel_file_path, engine='openpyxl')
    except Exception as e:
        raise ValueError(f"Failed to read Excel file: {e}")

    # Validate required columns
    required_columns = ['sku', 'name', 'description']

    # Check for image URL column (image_url or image_link)
    image_col = None
    if 'image_url' in df.columns:
        image_col = 'image_url'
    elif 'image_link' in df.columns:
        image_col = 'image_link'

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    if not image_col:
        raise ValueError("Missing image URL column: add 'image_url' or 'image_link' column")

    db = db_session()
    generator = get_generator()
    results = []

    print(f"Processing {len(df)} rows from Excel file")

    for index, row in df.iterrows():
        print(f"Processing row {index + 1}: {row.get('name', 'Unknown')}")

        try:
            sku = str(row.get('sku', '')).strip()
            name = str(row.get('name', '')).strip()
            image_url = str(row.get(image_col, '')).strip()
            jewelry_type = str(row.get('type', 'earring')).lower()
            price = float(row.get('price', 0)) if pd.notna(row.get('price')) else 0
            description = str(row.get('description', '')).strip() if pd.notna(row.get('description')) else ''
            feature = str(row.get('feature', '')).strip() if pd.notna(row.get('feature')) and str(row.get('feature', '')) != 'nan' else None

            # Validate required fields
            if not sku or sku == 'nan':
                results.append({
                    'row': index + 1,
                    'name': name or 'Unknown',
                    'status': 'failed',
                    'error': 'Missing SKU number'
                })
                continue

            if not name or name == 'nan':
                results.append({
                    'row': index + 1,
                    'name': name or 'Unknown',
                    'status': 'failed',
                    'error': 'Missing name'
                })
                continue

            if not description or description == 'nan':
                results.append({
                    'row': index + 1,
                    'name': name,
                    'sku': sku,
                    'status': 'failed',
                    'error': 'Missing description'
                })
                continue

            if not image_url or image_url == 'nan':
                results.append({
                    'row': index + 1,
                    'name': name,
                    'sku': sku,
                    'status': 'failed',
                    'error': 'Missing image URL'
                })
                continue

            # Download image
            unique_id = uuid.uuid4().hex[:8]
            image_ext = os.path.splitext(image_url.split('?')[0])[1] or '.jpg'
            image_filename = f"img_{unique_id}{image_ext}"
            image_path = download_image_from_url(image_url, temp_dir, image_filename)

            if not image_path:
                results.append({
                    'row': index + 1,
                    'name': name,
                    'status': 'download_failed',
                    'error': f'Failed to download from {image_url}'
                })
                continue

            # Generate 3D model
            model_filename = f"jewelry_{unique_id}"
            model_url = generator.generate_from_image(image_path, model_filename)

            # Clean up downloaded image
            try:
                os.remove(image_path)
            except:
                pass

            if model_url:
                # Create jewelry record in database
                jewelry = Jewelry(
                    sku=sku,
                    name=name,
                    type=jewelry_type,
                    model_url=model_url,
                    thumbnail_url=image_url,  # Store original URL as thumbnail
                    image_link=image_url,  # Store original S3/HTTP link
                    price=price,
                    description=description,
                    feature=feature if feature else None,
                    is_active="true"
                )
                db.add(jewelry)
                db.commit()
                db.refresh(jewelry)

                results.append({
                    'row': index + 1,
                    'sku': sku,
                    'name': name,
                    'status': 'success',
                    'model_url': model_url,
                    'jewelry_id': str(jewelry.id)
                })
                print(f"  ✓ Generated: {model_url}, Jewelry ID: {jewelry.id}")
            else:
                results.append({
                    'row': index + 1,
                    'name': name,
                    'status': 'generation_failed',
                    'error': '3D generation failed'
                })
                print(f"  ✗ Failed to generate 3D model")

        except Exception as e:
            db.rollback()
            results.append({
                'row': index + 1,
                'name': str(row.get('name', 'Unknown')),
                'status': 'error',
                'error': str(e)
            })
            print(f"  ✗ Error: {e}")

    db.close()
    return results


if __name__ == '__main__':
    print("Starting 3D model generation for all jewelry...")
    results = generate_3d_for_all_jewelry()
    print(f"\nCompleted: {len(results)} items")
    success = sum(1 for r in results if r['status'] == 'success')
    print(f"Successful: {success}, Failed: {len(results) - success}")
