"""
Content fingerprinting and perceptual hashing
"""
import hashlib
import imagehash
from PIL import Image
from typing import Optional


class ContentHasher:
    """
    Generate content fingerprints for caching and duplicate detection.
    """

    @staticmethod
    def hash_bytes(data: bytes) -> str:
        """SHA256 hash of raw bytes"""
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def hash_file(filepath: str) -> str:
        """SHA256 hash of file contents"""
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def hash_text(text: str) -> str:
        """SHA256 hash of text"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    @staticmethod
    def perceptual_hash_image(image_path: str) -> Optional[str]:
        """
        Generate perceptual hash (pHash) of image.
        Useful for detecting near-duplicates.
        """
        try:
            img = Image.open(image_path)
            phash = imagehash.phash(img)
            return str(phash)
        except Exception as e:
            print(f"Error hashing image {image_path}: {e}")
            return None

    @staticmethod
    def average_hash_image(image_path: str) -> Optional[str]:
        """
        Generate average hash (aHash) of image.
        Faster but less robust than pHash.
        """
        try:
            img = Image.open(image_path)
            ahash = imagehash.average_hash(img)
            return str(ahash)
        except Exception as e:
            print(f"Error hashing image {image_path}: {e}")
            return None

    @staticmethod
    def difference_hash_image(image_path: str) -> Optional[str]:
        """
        Generate difference hash (dHash) of image.
        Good for detecting transformations.
        """
        try:
            img = Image.open(image_path)
            dhash = imagehash.dhash(img)
            return str(dhash)
        except Exception as e:
            print(f"Error hashing image {image_path}: {e}")
            return None

    @staticmethod
    def combined_image_fingerprint(image_path: str) -> dict:
        """
        Generate multiple hashes for robust fingerprinting.
        """
        return {
            "sha256": ContentHasher.hash_file(image_path),
            "phash": ContentHasher.perceptual_hash_image(image_path),
            "ahash": ContentHasher.average_hash_image(image_path),
            "dhash": ContentHasher.difference_hash_image(image_path),
        }

