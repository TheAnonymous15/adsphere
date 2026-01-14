#!/usr/bin/env python3
"""
Example: How to use ModelStore in your files
=============================================

This file demonstrates how other moderation files should use
the download_models.py ModelStore to ensure their required
models are available before proceeding.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from model_registry import ensure_models, get_model_path, is_model_available, ModelStore


def example_1_simple():
    """
    Simple usage: Just ensure models are available.
    The function returns True only if ALL models are available.
    """
    print("\n" + "="*60)
    print("Example 1: Simple ensure_models()")
    print("="*60)

    # Define what models this file needs
    required_models = ['yolov8n', 'detoxify', 'torch']

    # Ensure they're available (will download if missing)
    if not ensure_models(required_models):
        print("ERROR: Cannot proceed without required models!")
        return False

    print("All models ready, proceeding with processing...")
    return True


def example_2_with_model_path():
    """
    Get the path to a model file.
    """
    print("\n" + "="*60)
    print("Example 2: Get model path")
    print("="*60)

    # Ensure the model exists first
    if not ensure_models(['yolov8n'], verbose=False):
        return None

    # Get the path
    model_path = get_model_path('yolov8n')
    print(f"YOLOv8n model path: {model_path}")

    # Now you can use it
    # from ultralytics import YOLO
    # model = YOLO(str(model_path))

    return model_path


def example_3_check_availability():
    """
    Check if models are available without downloading.
    """
    print("\n" + "="*60)
    print("Example 3: Check availability")
    print("="*60)

    models_to_check = ['yolov8n', 'whisper', 'blood_cnn', 'yolov8n_violence']

    for model_id in models_to_check:
        available = is_model_available(model_id)
        status = "✓ Available" if available else "✗ Missing"
        print(f"  {model_id}: {status}")


def example_4_full_control():
    """
    Full control using ModelStore class directly.
    """
    print("\n" + "="*60)
    print("Example 4: Full control with ModelStore")
    print("="*60)

    # Create store with custom settings
    store = ModelStore(
        auto_download=True,   # Download missing models
        verbose=True          # Show progress
    )

    # Get status of all models
    status = store.get_status()
    print(f"Total models: {status['total']}")
    print(f"Available: {status['available']}")
    print(f"Required ready: {status['required_available']}/{status['required']}")
    print(f"System ready: {status['ready']}")

    # Ensure specific models with preload
    success = store.ensure_models(
        ['yolov8n', 'ultralytics'],
        preload=False  # Set True to also preload models
    )

    if success:
        # Get model path
        yolo_path = store.get_model_path('yolov8n')
        print(f"YOLO path: {yolo_path}")


def example_5_in_real_code():
    """
    How to use it in a real moderation file.
    """
    print("\n" + "="*60)
    print("Example 5: Real-world usage pattern")
    print("="*60)

    # At the top of your file, define required models
    REQUIRED_MODELS = ['yolov8n', 'detoxify', 'cv2', 'PIL']

    # Early exit if models not available
    if not ensure_models(REQUIRED_MODELS, verbose=False):
        raise RuntimeError(
            f"Cannot start moderation service. "
            f"Required models not available: {REQUIRED_MODELS}"
        )

    print("✅ All models verified, service can start")

    # Now proceed with your actual code...
    yolo_path = get_model_path('yolov8n')
    print(f"Using YOLO model: {yolo_path}")


def example_6_quiet_mode():
    """
    Silent mode for production.
    """
    print("\n" + "="*60)
    print("Example 6: Quiet mode (no output)")
    print("="*60)

    # No output, just returns True/False
    success = ensure_models(['yolov8n', 'torch'], verbose=False)
    print(f"Models ready: {success}")


if __name__ == "__main__":
    print("="*60)
    print("  MODEL STORE USAGE EXAMPLES")
    print("="*60)

    example_1_simple()
    example_2_with_model_path()
    example_3_check_availability()
    # example_4_full_control()  # Verbose, uncomment to see
    example_5_in_real_code()
    example_6_quiet_mode()

    print("\n" + "="*60)
    print("  ALL EXAMPLES COMPLETE")
    print("="*60)

