#!/usr/bin/env python3
"""
Test OCR processing with test images
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.ai.vision import VisionProcessor
from bot.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

def test_ocr_images():
    """Test OCR processing with test images"""
    
    print("🔍 Testing OCR processing...")
    print("=" * 50)
    
    vision_processor = VisionProcessor()
    
    # Test images
    test_images = [
        "/home/ubuntu/radarbotV3/photo/test4.jpeg",
        "/home/ubuntu/radarbotV3/photo/test5.jpeg"
    ]
    
    for image_path in test_images:
        if not os.path.exists(image_path):
            print(f"❌ Image not found: {image_path}")
            continue
            
        print(f"\n📸 Testing image: {os.path.basename(image_path)}")
        print("-" * 40)
        
        try:
            # Read image file
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            # Process image
            result = vision_processor.extract_positions_for_ingest(image_bytes)
            
            print(f"✅ OCR processing completed")
            print(f"   Reason: {result.reason}")
            print(f"   Is portfolio: {result.is_portfolio}")
            print(f"   Accounts found: {len(result.accounts)}")
            print(f"   Cash positions: {len(result.cash_positions)}")
            print(f"   Warnings: {result.warnings}")
            
            if result.accounts:
                for i, account in enumerate(result.accounts):
                    print(f"   Account {i+1}: {account.account_name} ({account.account_id})")
                    print(f"     Portfolio value: {account.portfolio_value}")
                    print(f"     Positions: {len(account.positions)}")
                    
                    for j, position in enumerate(account.positions[:3]):  # Show first 3 positions
                        print(f"       Position {j+1}: {position.raw_name}")
                        print(f"         Ticker: {position.raw_ticker}")
                        print(f"         ISIN: {position.raw_isin}")
                        print(f"         Quantity: {position.quantity} {position.quantity_unit}")
                        print(f"         Confidence: {position.confidence}")
            
        except Exception as e:
            print(f"❌ Error processing image: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n🏁 OCR testing completed!")

def main():
    """Main function"""
    test_ocr_images()

if __name__ == "__main__":
    main()
