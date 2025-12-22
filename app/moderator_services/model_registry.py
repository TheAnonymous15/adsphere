#!/usr/bin/env python3
"""
Model Store for AdSphere Moderation Service
============================================

This module acts as a central model registry and downloader.
Other modules call this to ensure their required models are available.

Usage as import:
    from download_models import ModelStore

    # Ensure models are available before proceeding
    store = ModelStore()
    if not store.ensure_models(['yolov8n', 'whisper', 'detoxify']):
        raise RuntimeError("Required models not available")

    # Get model path
    yolo_path = store.get_model_path('yolov8n')

Usage as CLI:
    python download_models.py --check           # Check all models
    python download_models.py --download all    # Download all models
    python download_models.py --ensure yolov8n whisper  # Ensure specific models
"""

import sys
import argparse
import subprocess
import urllib.request
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base directories
BASE_DIR = Path(__file__).parent
MODERATION_SERVICE_DIR = BASE_DIR / "moderation_service"
MODELS_DIR = MODERATION_SERVICE_DIR / "models_weights"
CACHE_DIR = Path.home() / ".cache" / "adsphere_moderation"

# Ensure directories exist
MODELS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class ModelType(Enum):
    """Type of model."""
    FILE = "file"           # Downloadable file (e.g., .pt, .pth)
    PACKAGE = "package"     # Python package that auto-downloads models
    PRELOAD = "preload"     # Package that needs explicit preloading


@dataclass
class ModelInfo:
    """Information about a model."""
    name: str
    model_type: ModelType
    filename: Optional[str] = None
    url: Optional[str] = None
    size_mb: float = 0
    package: Optional[str] = None
    import_name: Optional[str] = None
    preload_func: Optional[str] = None
    description: str = ""
    required: bool = True


# =============================================================================
# MODEL REGISTRY - All available models
# =============================================================================
MODEL_REGISTRY: Dict[str, ModelInfo] = {
    # -------------------------------------------------------------------------
    # YOLO Models (File downloads)
    # -------------------------------------------------------------------------
    "yolov8n": ModelInfo(
        name="YOLOv8n (Object Detection)",
        model_type=ModelType.FILE,
        filename="yolov8n.pt",
        url="https://github.com/ultralytics/assets/releases/download/v8.1.0/yolov8n.pt",
        size_mb=6.2,
        description="Lightweight object detection for weapons, people, vehicles"
    ),
    "yolov8s": ModelInfo(
        name="YOLOv8s (Object Detection - Medium)",
        model_type=ModelType.FILE,
        filename="yolov8s.pt",
        url="https://github.com/ultralytics/assets/releases/download/v8.1.0/yolov8s.pt",
        size_mb=21.5,
        required=False,
        description="Medium-sized object detection (more accurate)"
    ),
    "yolov5s": ModelInfo(
        name="YOLOv5s (Legacy Detection)",
        model_type=ModelType.FILE,
        filename="yolov5s.pt",
        url="https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5s.pt",
        size_mb=14.1,
        required=False,
        description="Legacy object detection (fallback)"
    ),
    "yolov8n_violence": ModelInfo(
        name="YOLOv8n Violence Detection",
        model_type=ModelType.FILE,
        filename="yolov8n-violence.pt",
        # Using base YOLOv8n as fallback - can detect people in fighting poses
        # For production, train on violence dataset or use specialized model
        url="https://github.com/ultralytics/assets/releases/download/v8.1.0/yolov8n.pt",
        size_mb=6.2,
        required=False,
        description="Violence detection model (using YOLOv8n base, fine-tune for production)"
    ),
    "blood_cnn": ModelInfo(
        name="Blood Detection CNN",
        model_type=ModelType.FILE,
        filename="blood_cnn.pth",
        # No public blood detection model available - will create placeholder
        url=None,
        size_mb=10,
        required=False,
        description="Blood/gore detection model (requires custom training)"
    ),

    # -------------------------------------------------------------------------
    # Text Moderation Models (NEW)
    # -------------------------------------------------------------------------
    "xlm_roberta_lang": ModelInfo(
        name="XLM-RoBERTa Language Detection",
        model_type=ModelType.PACKAGE,
        package="transformers",
        import_name="transformers",
        description="XLM-RoBERTa fine-tuned for language detection (papluca/xlm-roberta-base-language-detection)"
    ),
    "fasttext_lid": ModelInfo(
        name="fastText Language Identification (Compressed)",
        model_type=ModelType.FILE,
        filename="lid.176.ftz",
        url="https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz",
        size_mb=0.9,  # Compressed model ~900KB
        required=False,
        description="Language detection for 176 languages (compressed, faster) - DEPRECATED: Use xlm_roberta_lang"
    ),
    "fasttext_lid_full": ModelInfo(
        name="fastText Language Identification (Full)",
        model_type=ModelType.FILE,
        filename="lid.176.bin",
        url="https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin",
        size_mb=131,  # Full model ~131MB
        required=False,
        description="Language detection for 176 languages (full accuracy) - DEPRECATED: Use xlm_roberta_lang"
    ),
    "sentence_transformers": ModelInfo(
        name="Sentence Transformers",
        model_type=ModelType.PACKAGE,
        package="sentence-transformers",
        import_name="sentence_transformers",
        description="Semantic text embeddings (all-MiniLM-L6-v2)"
    ),
    "faiss": ModelInfo(
        name="FAISS (Vector Search)",
        model_type=ModelType.PACKAGE,
        package="faiss-cpu",
        import_name="faiss",
        required=False,
        description="Facebook AI Similarity Search for vector DB"
    ),
    "spacy": ModelInfo(
        name="spaCy (NLP)",
        model_type=ModelType.PACKAGE,
        package="spacy",
        import_name="spacy",
        required=False,
        description="Industrial-strength NLP library"
    ),
    "fasttext": ModelInfo(
        name="fastText",
        model_type=ModelType.PACKAGE,
        package="fasttext",
        import_name="fasttext",
        required=False,
        description="Text classification and language detection"
    ),

    # -------------------------------------------------------------------------
    # Python Package Models
    # -------------------------------------------------------------------------
    "whisper": ModelInfo(
        name="OpenAI Whisper (Speech Recognition)",
        model_type=ModelType.PRELOAD,
        package="openai-whisper",
        import_name="whisper",
        preload_func="_preload_whisper",
        description="Automatic speech recognition for audio moderation"
    ),
    "paddleocr": ModelInfo(
        name="PaddleOCR (Text Recognition)",
        model_type=ModelType.PRELOAD,
        package="paddleocr",
        import_name="paddleocr",
        preload_func="_preload_paddleocr",
        description="OCR for detecting text in images/video frames"
    ),
    "detoxify": ModelInfo(
        name="Detoxify (Text Toxicity)",
        model_type=ModelType.PRELOAD,
        package="detoxify",
        import_name="detoxify",
        preload_func="_preload_detoxify",
        description="Toxic language detection"
    ),
    "nudenet": ModelInfo(
        name="NudeNet (NSFW Detection)",
        model_type=ModelType.PRELOAD,
        package="nudenet",
        import_name="nudenet",
        preload_func="_preload_nudenet",
        required=False,
        description="NSFW image classification"
    ),
    "transformers": ModelInfo(
        name="Transformers (HuggingFace)",
        model_type=ModelType.PACKAGE,
        package="transformers",
        import_name="transformers",
        description="HuggingFace transformers for various models"
    ),
    "ultralytics": ModelInfo(
        name="Ultralytics (YOLO Framework)",
        model_type=ModelType.PACKAGE,
        package="ultralytics",
        import_name="ultralytics",
        description="YOLO model framework"
    ),
    "torch": ModelInfo(
        name="PyTorch",
        model_type=ModelType.PACKAGE,
        package="torch",
        import_name="torch",
        description="PyTorch deep learning framework"
    ),
    "cv2": ModelInfo(
        name="OpenCV",
        model_type=ModelType.PACKAGE,
        package="opencv-python",
        import_name="cv2",
        description="Computer vision library"
    ),
    "PIL": ModelInfo(
        name="Pillow (Image Processing)",
        model_type=ModelType.PACKAGE,
        package="pillow",
        import_name="PIL",
        description="Image processing library"
    ),
    "ffmpeg": ModelInfo(
        name="FFmpeg (via ffmpeg-python)",
        model_type=ModelType.PACKAGE,
        package="ffmpeg-python",
        import_name="ffmpeg",
        required=False,
        description="Video/audio processing"
    ),
}


class ModelStore:
    """
    Central model store that manages all AI/ML models for the moderation service.

    Usage:
        store = ModelStore()

        # Check if models are available
        if store.ensure_models(['yolov8n', 'whisper', 'detoxify']):
            # All models ready, proceed
            model_path = store.get_model_path('yolov8n')
        else:
            # Some models missing, cannot proceed
            raise RuntimeError("Models not available")
    """

    def __init__(self, auto_download: bool = True, verbose: bool = True):
        """
        Initialize the model store.

        Args:
            auto_download: If True, automatically download missing models
            verbose: If True, print status messages
        """
        self.auto_download = auto_download
        self.verbose = verbose
        self.registry = MODEL_REGISTRY
        self._loaded_models: Dict[str, Any] = {}

    def _log(self, message: str, level: str = "info"):
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            icon = {"info": "ℹ️", "ok": "✅", "error": "❌", "warning": "⚠️", "download": "⬇️"}.get(level, "•")
            print(f"{icon} {message}")

        if level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)
        else:
            logger.info(message)

    def _get_file_size_mb(self, filepath: Path) -> float:
        """Get file size in MB."""
        if filepath.exists():
            return filepath.stat().st_size / (1024 * 1024)
        return 0

    def _find_model_file(self, filename: str) -> Optional[Path]:
        """Find a model file in known locations."""
        locations = [
            MODELS_DIR / filename,
            BASE_DIR / filename,
            MODERATION_SERVICE_DIR / filename,
            Path.home() / ".cache" / "torch" / "hub" / "checkpoints" / filename,
        ]

        for loc in locations:
            if loc.exists():
                return loc
        return None

    def _check_package_installed(self, model_id: str) -> bool:
        """Check if a Python package is installed."""
        info = self.registry.get(model_id)
        if not info:
            return False

        import_name = info.import_name or info.package.replace("-", "_")

        try:
            __import__(import_name)
            return True
        except ImportError:
            return False

    def _install_package(self, package_name: str) -> bool:
        """Install a Python package via pip."""
        try:
            self._log(f"Installing package: {package_name}", "download")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package_name, "-q"],
                stdout=subprocess.DEVNULL if not self.verbose else None,
                stderr=subprocess.DEVNULL if not self.verbose else None
            )
            self._log(f"Installed: {package_name}", "ok")
            return True
        except subprocess.CalledProcessError as e:
            self._log(f"Failed to install {package_name}: {e}", "error")
            return False

    def _download_file(self, url: str, dest: Path, expected_size_mb: float = 0) -> bool:
        """Download a file with progress indication."""
        try:
            self._log(f"Downloading: {dest.name}", "download")

            def progress_hook(count, block_size, total_size):
                if self.verbose and total_size > 0:
                    percent = min(100, count * block_size * 100 / total_size)
                    downloaded_mb = count * block_size / (1024 * 1024)
                    total_mb = total_size / (1024 * 1024)
                    sys.stdout.write(f"\r   Progress: {percent:.1f}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)")
                    sys.stdout.flush()

            urllib.request.urlretrieve(url, dest, reporthook=progress_hook if self.verbose else None)

            if self.verbose:
                print()  # New line after progress

            # Verify size
            if expected_size_mb > 0:
                actual_size = self._get_file_size_mb(dest)
                if actual_size < expected_size_mb * 0.5:
                    self._log(f"File size mismatch: expected ~{expected_size_mb}MB, got {actual_size:.1f}MB", "warning")
                    return False

            self._log(f"Downloaded: {dest.name}", "ok")
            return True

        except Exception as e:
            self._log(f"Download failed: {e}", "error")
            if dest.exists():
                dest.unlink()
            return False

    # =========================================================================
    # Preload functions for specific models
    # =========================================================================

    def _preload_whisper(self) -> bool:
        """Preload Whisper model."""
        try:
            import whisper
            whisper.load_model("small")
            return True
        except Exception as e:
            self._log(f"Whisper preload failed: {e}", "error")
            return False

    def _preload_paddleocr(self) -> bool:
        """Preload PaddleOCR model."""
        try:
            import logging
            logging.getLogger("ppocr").setLevel(logging.ERROR)
            from paddleocr import PaddleOCR
            PaddleOCR(lang='en', show_log=False)
            return True
        except Exception as e:
            self._log(f"PaddleOCR preload failed: {e}", "error")
            return False

    def _preload_detoxify(self) -> bool:
        """Preload Detoxify model."""
        try:
            from detoxify import Detoxify
            Detoxify('original')
            return True
        except Exception as e:
            self._log(f"Detoxify preload failed: {e}", "error")
            return False

    def _preload_nudenet(self) -> bool:
        """Preload NudeNet model."""
        try:
            from nudenet import NudeClassifier
            NudeClassifier()
            return True
        except Exception as e:
            self._log(f"NudeNet preload failed: {e}", "warning")
            return False

    # =========================================================================
    # Public API
    # =========================================================================

    def is_available(self, model_id: str) -> bool:
        """
        Check if a model is available (installed/downloaded).

        Args:
            model_id: The model identifier (e.g., 'yolov8n', 'whisper')

        Returns:
            True if the model is available, False otherwise
        """
        info = self.registry.get(model_id)
        if not info:
            self._log(f"Unknown model: {model_id}", "warning")
            return False

        if info.model_type == ModelType.FILE:
            # Check if file exists
            if info.filename:
                return self._find_model_file(info.filename) is not None
            return False

        elif info.model_type in (ModelType.PACKAGE, ModelType.PRELOAD):
            # Check if package is installed
            return self._check_package_installed(model_id)

        return False

    def get_model_path(self, model_id: str) -> Optional[Path]:
        """
        Get the path to a model file.

        Args:
            model_id: The model identifier (e.g., 'yolov8n')

        Returns:
            Path to the model file, or None if not found
        """
        info = self.registry.get(model_id)
        if not info or info.model_type != ModelType.FILE:
            return None

        if info.filename:
            return self._find_model_file(info.filename)
        return None

    def download_model(self, model_id: str, force: bool = False) -> bool:
        """
        Download/install a specific model.

        Args:
            model_id: The model identifier
            force: If True, re-download even if exists

        Returns:
            True if successful, False otherwise
        """
        info = self.registry.get(model_id)
        if not info:
            self._log(f"Unknown model: {model_id}", "error")
            return False

        self._log(f"Ensuring model: {info.name}")

        if info.model_type == ModelType.FILE:
            # Download file
            if not force and self.is_available(model_id):
                self._log(f"{info.name}: Already available", "ok")
                return True

            if not info.url:
                self._log(f"{info.name}: No download URL (custom model)", "warning")
                return False

            dest = MODELS_DIR / info.filename
            return self._download_file(info.url, dest, info.size_mb)

        elif info.model_type == ModelType.PACKAGE:
            # Install package
            if self.is_available(model_id):
                self._log(f"{info.name}: Already installed", "ok")
                return True

            return self._install_package(info.package)

        elif info.model_type == ModelType.PRELOAD:
            # Install package and preload
            if not self._check_package_installed(model_id):
                if not self._install_package(info.package):
                    return False

            # Run preload function
            if info.preload_func:
                preload_method = getattr(self, info.preload_func, None)
                if preload_method:
                    self._log(f"Preloading {info.name}...", "download")
                    return preload_method()

            self._log(f"{info.name}: Ready", "ok")
            return True

        return False

    def ensure_models(self, model_ids: List[str], preload: bool = False) -> bool:
        """
        Ensure all specified models are available.
        Downloads missing models if auto_download is enabled.

        THIS IS THE MAIN METHOD OTHER FILES SHOULD CALL.

        Args:
            model_ids: List of model identifiers to ensure
            preload: If True, preload models that require it

        Returns:
            True if ALL models are available, False if ANY is missing

        Example:
            store = ModelStore()
            if not store.ensure_models(['yolov8n', 'whisper', 'detoxify']):
                raise RuntimeError("Cannot proceed without required models")
        """
        self._log(f"Ensuring {len(model_ids)} model(s): {', '.join(model_ids)}")

        missing = []
        failed = []

        for model_id in model_ids:
            if self.is_available(model_id):
                self._log(f"  {model_id}: ✓ Available", "ok")
                continue

            missing.append(model_id)

            if self.auto_download:
                self._log(f"  {model_id}: ✗ Missing, downloading...", "download")
                if not self.download_model(model_id):
                    failed.append(model_id)
            else:
                self._log(f"  {model_id}: ✗ Missing (auto-download disabled)", "error")
                failed.append(model_id)

        # Preload if requested
        if preload and not failed:
            for model_id in model_ids:
                info = self.registry.get(model_id)
                if info and info.model_type == ModelType.PRELOAD and info.preload_func:
                    preload_method = getattr(self, info.preload_func, None)
                    if preload_method:
                        self._log(f"  Preloading {model_id}...")
                        if not preload_method():
                            failed.append(f"{model_id}_preload")

        # Summary
        if failed:
            self._log(f"FAILED: {len(failed)} model(s) not available: {', '.join(failed)}", "error")
            return False

        if missing:
            self._log(f"SUCCESS: Downloaded {len(missing)} missing model(s)", "ok")
        else:
            self._log(f"SUCCESS: All {len(model_ids)} model(s) available", "ok")

        return True

    def list_models(self) -> Dict[str, Dict]:
        """
        List all available models in the registry.

        Returns:
            Dictionary of model_id -> model info
        """
        result = {}
        for model_id, info in self.registry.items():
            result[model_id] = {
                "name": info.name,
                "type": info.model_type.value,
                "available": self.is_available(model_id),
                "required": info.required,
                "description": info.description
            }
        return result

    def get_status(self) -> Dict[str, Any]:
        """
        Get full status of all models.

        Returns:
            Status dictionary with counts and details
        """
        models = self.list_models()
        available = sum(1 for m in models.values() if m["available"])
        required = sum(1 for m in models.values() if m["required"])
        required_available = sum(1 for m in models.values() if m["required"] and m["available"])

        return {
            "total": len(models),
            "available": available,
            "missing": len(models) - available,
            "required": required,
            "required_available": required_available,
            "ready": required_available == required,
            "models": models
        }


# =============================================================================
# Convenience functions for quick access
# =============================================================================

_default_store: Optional[ModelStore] = None

def get_store(auto_download: bool = True, verbose: bool = True) -> ModelStore:
    """Get the default model store instance."""
    global _default_store
    if _default_store is None:
        _default_store = ModelStore(auto_download=auto_download, verbose=verbose)
    return _default_store


def ensure_models(model_ids: List[str], auto_download: bool = True, verbose: bool = True) -> bool:
    """
    Quick function to ensure models are available.

    Usage:
        from download_models import ensure_models

        if not ensure_models(['yolov8n', 'whisper']):
            raise RuntimeError("Models not available")
    """
    store = get_store(auto_download=auto_download, verbose=verbose)
    return store.ensure_models(model_ids)


def get_model_path(model_id: str) -> Optional[Path]:
    """
    Quick function to get a model path.

    Usage:
        from download_models import get_model_path

        yolo_path = get_model_path('yolov8n')
    """
    store = get_store(verbose=False)
    return store.get_model_path(model_id)


def is_model_available(model_id: str) -> bool:
    """
    Quick function to check if a model is available.

    Usage:
        from download_models import is_model_available

        if is_model_available('yolov8n'):
            # Use the model
            pass
    """
    store = get_store(verbose=False)
    return store.is_available(model_id)


# =============================================================================
# CLI Interface
# =============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_status_table(store: ModelStore):
    """Print a formatted status table."""
    status = store.get_status()

    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}  ADSPHERE MODERATION - MODEL STORE STATUS{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

    print(f"  Models Directory: {MODELS_DIR}\n")

    # Summary
    ready_icon = f"{Colors.GREEN}✓ READY{Colors.END}" if status["ready"] else f"{Colors.RED}✗ NOT READY{Colors.END}"
    print(f"  Status: {ready_icon}")
    print(f"  Total: {status['total']}, Available: {status['available']}, Missing: {status['missing']}")
    print(f"  Required: {status['required_available']}/{status['required']}\n")

    # Model table
    print(f"  {'Model':<25} {'Type':<10} {'Status':<12} {'Required':<10}")
    print(f"  {'-'*25} {'-'*10} {'-'*12} {'-'*10}")

    for model_id, info in status["models"].items():
        status_icon = f"{Colors.GREEN}✓{Colors.END}" if info["available"] else f"{Colors.RED}✗{Colors.END}"
        required_str = "Yes" if info["required"] else "No"
        print(f"  {model_id:<25} {info['type']:<10} {status_icon} {'Available' if info['available'] else 'Missing':<10} {required_str:<10}")

    print()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AdSphere Moderation Model Store",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python download_models.py --check                    # Check all models
  python download_models.py --ensure yolov8n whisper   # Ensure specific models
  python download_models.py --download all             # Download all models
  python download_models.py --download yolov8n         # Download specific model
  python download_models.py --list                     # List all models
        """
    )

    parser.add_argument("--check", action="store_true",
                        help="Check status of all models")
    parser.add_argument("--ensure", nargs="+", metavar="MODEL",
                        help="Ensure specified models are available")
    parser.add_argument("--download", nargs="+", metavar="MODEL",
                        help="Download specified models (use 'all' for all)")
    parser.add_argument("--list", action="store_true",
                        help="List all available models")
    parser.add_argument("--preload", action="store_true",
                        help="Preload models after ensuring")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Minimal output")
    parser.add_argument("--no-auto-download", action="store_true",
                        help="Don't auto-download missing models")

    args = parser.parse_args()

    store = ModelStore(
        auto_download=not args.no_auto_download,
        verbose=not args.quiet
    )

    if args.list:
        print_status_table(store)
        return

    if args.check:
        print_status_table(store)
        status = store.get_status()
        sys.exit(0 if status["ready"] else 1)

    if args.ensure:
        success = store.ensure_models(args.ensure, preload=args.preload)
        sys.exit(0 if success else 1)

    if args.download:
        if "all" in args.download:
            model_ids = list(MODEL_REGISTRY.keys())
        else:
            model_ids = args.download

        success = True
        for model_id in model_ids:
            if not store.download_model(model_id, force=True):
                success = False

        sys.exit(0 if success else 1)

    # Default: show status
    print_status_table(store)


if __name__ == "__main__":
    main()

