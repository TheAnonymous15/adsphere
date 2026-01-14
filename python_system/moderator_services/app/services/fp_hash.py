"""
Video Fingerprint Hashing System
Avoid reprocessing identical videos using perceptual hashing
"""

import os
import hashlib
import imagehash
from PIL import Image
import numpy as np
from typing import Dict, Optional, List, Tuple
import json
import time


class VideoFingerprint:
    """
    Multi-level video fingerprinting system
    - Exact matching (SHA256 of file)
    - Perceptual matching (hash of keyframes)
    - Scene detection hashing
    """

    def __init__(self, cache_file: str = "cache/video_fingerprints.json"):
        self.cache_file = cache_file
        self.fingerprints = self._load_cache()

        # Ensure cache directory exists
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)

    def _load_cache(self) -> Dict:
        """Load fingerprint cache"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠ Error loading fingerprint cache: {e}")
                return {}
        return {}

    def _save_cache(self):
        """Save fingerprint cache"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.fingerprints, f, indent=2)
        except Exception as e:
            print(f"⚠ Error saving fingerprint cache: {e}")

    def compute_file_hash(self, video_path: str) -> str:
        """Compute exact file hash (SHA256)"""
        sha256 = hashlib.sha256()

        try:
            with open(video_path, 'rb') as f:
                # Read in chunks for memory efficiency
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)

            return sha256.hexdigest()
        except Exception as e:
            print(f"⚠ Error hashing file: {e}")
            return None

    def compute_frame_hash(self, frame_path: str) -> Dict[str, str]:
        """
        Compute perceptual hashes for a frame
        Returns multiple hash types for robustness
        """
        try:
            img = Image.open(frame_path)

            return {
                'phash': str(imagehash.phash(img)),      # Perceptual hash
                'ahash': str(imagehash.average_hash(img)),  # Average hash
                'dhash': str(imagehash.dhash(img)),      # Difference hash
                'whash': str(imagehash.whash(img))       # Wavelet hash
            }
        except Exception as e:
            print(f"⚠ Error computing frame hash: {e}")
            return None

    def compute_keyframe_fingerprint(self, frame_paths: List[str], sample_rate: int = 10) -> Dict:
        """
        Compute fingerprint from keyframes

        Args:
            frame_paths: List of extracted frame paths
            sample_rate: Sample every Nth frame

        Returns:
            Fingerprint dictionary with composite hashes
        """
        if not frame_paths:
            return None

        # Sample keyframes
        keyframes = frame_paths[::sample_rate][:10]  # Max 10 keyframes

        frame_hashes = []
        for frame_path in keyframes:
            frame_hash = self.compute_frame_hash(frame_path)
            if frame_hash:
                frame_hashes.append(frame_hash)

        if not frame_hashes:
            return None

        # Compute composite hash from all keyframes
        composite = {
            'phash_composite': self._composite_hash([h['phash'] for h in frame_hashes]),
            'ahash_composite': self._composite_hash([h['ahash'] for h in frame_hashes]),
            'frame_count': len(frame_hashes),
            'sample_rate': sample_rate
        }

        return composite

    def _composite_hash(self, hash_list: List[str]) -> str:
        """Create composite hash from multiple hashes"""
        combined = ''.join(sorted(hash_list))
        return hashlib.sha256(combined.encode()).hexdigest()[:32]

    def compute_video_fingerprint(self, video_path: str, frame_paths: List[str]) -> Dict:
        """
        Compute complete video fingerprint

        Args:
            video_path: Path to video file
            frame_paths: Paths to extracted frames

        Returns:
            Complete fingerprint with multiple hash levels
        """
        fingerprint = {
            'timestamp': time.time(),
            'video_path': os.path.basename(video_path),
            'file_size': os.path.getsize(video_path) if os.path.exists(video_path) else 0
        }

        # Level 1: Exact file hash
        file_hash = self.compute_file_hash(video_path)
        if file_hash:
            fingerprint['file_hash'] = file_hash

        # Level 2: Keyframe perceptual hashes
        keyframe_fp = self.compute_keyframe_fingerprint(frame_paths)
        if keyframe_fp:
            fingerprint['keyframe_fingerprint'] = keyframe_fp

        # Level 3: Scene-level hashes (sample beginning, middle, end)
        if len(frame_paths) >= 3:
            scene_hashes = []
            scenes = [
                frame_paths[0],                          # Beginning
                frame_paths[len(frame_paths) // 2],      # Middle
                frame_paths[-1]                           # End
            ]

            for scene_frame in scenes:
                scene_hash = self.compute_frame_hash(scene_frame)
                if scene_hash:
                    scene_hashes.append(scene_hash['phash'])

            if scene_hashes:
                fingerprint['scene_signature'] = '-'.join(scene_hashes)

        return fingerprint

    def find_match(self, fingerprint: Dict, similarity_threshold: float = 0.90) -> Optional[Dict]:
        """
        Find matching video in cache

        Args:
            fingerprint: Video fingerprint to match
            similarity_threshold: Similarity threshold (0-1)

        Returns:
            Matching fingerprint and result if found
        """
        if not fingerprint:
            return None

        file_hash = fingerprint.get('file_hash')

        # Level 1: Exact match
        if file_hash and file_hash in self.fingerprints:
            match = self.fingerprints[file_hash]
            return {
                'match_type': 'exact',
                'similarity': 1.0,
                'fingerprint': match,
                'cached_result': match.get('moderation_result')
            }

        # Level 2: Perceptual match
        keyframe_fp = fingerprint.get('keyframe_fingerprint', {})
        phash_composite = keyframe_fp.get('phash_composite')

        if phash_composite:
            for cached_hash, cached_fp in self.fingerprints.items():
                cached_keyframe = cached_fp.get('keyframe_fingerprint', {})
                cached_phash = cached_keyframe.get('phash_composite')

                if cached_phash:
                    # Simple string similarity (in production, use Hamming distance)
                    similarity = self._hash_similarity(phash_composite, cached_phash)

                    if similarity >= similarity_threshold:
                        return {
                            'match_type': 'perceptual',
                            'similarity': similarity,
                            'fingerprint': cached_fp,
                            'cached_result': cached_fp.get('moderation_result')
                        }

        # Level 3: Scene signature match
        scene_sig = fingerprint.get('scene_signature')

        if scene_sig:
            for cached_hash, cached_fp in self.fingerprints.items():
                cached_scene = cached_fp.get('scene_signature')

                if cached_scene and cached_scene == scene_sig:
                    return {
                        'match_type': 'scene',
                        'similarity': 1.0,
                        'fingerprint': cached_fp,
                        'cached_result': cached_fp.get('moderation_result')
                    }

        return None

    def _hash_similarity(self, hash1: str, hash2: str) -> float:
        """Calculate similarity between two hashes"""
        if len(hash1) != len(hash2):
            return 0.0

        matches = sum(c1 == c2 for c1, c2 in zip(hash1, hash2))
        return matches / len(hash1)

    def store_fingerprint(self, fingerprint: Dict, moderation_result: Dict):
        """
        Store fingerprint with moderation result

        Args:
            fingerprint: Video fingerprint
            moderation_result: Moderation decision and scores
        """
        if not fingerprint:
            return

        file_hash = fingerprint.get('file_hash')
        if not file_hash:
            # Use composite hash as key if no file hash
            keyframe_fp = fingerprint.get('keyframe_fingerprint', {})
            file_hash = keyframe_fp.get('phash_composite')

        if not file_hash:
            print("⚠ Cannot store fingerprint: no valid hash")
            return

        # Store with result
        fingerprint['moderation_result'] = moderation_result
        fingerprint['cached_at'] = time.time()

        self.fingerprints[file_hash] = fingerprint
        self._save_cache()

        print(f"✓ Fingerprint cached: {file_hash[:16]}...")

    def cleanup_old_entries(self, max_age_days: int = 30):
        """Remove fingerprints older than max_age_days"""
        current_time = time.time()
        max_age_seconds = max_age_days * 86400

        to_remove = []

        for hash_key, fp in self.fingerprints.items():
            cached_at = fp.get('cached_at', fp.get('timestamp', 0))
            age = current_time - cached_at

            if age > max_age_seconds:
                to_remove.append(hash_key)

        for key in to_remove:
            del self.fingerprints[key]

        if to_remove:
            self._save_cache()
            print(f"🧹 Cleaned {len(to_remove)} old fingerprints")

    def get_stats(self) -> Dict:
        """Get fingerprint cache statistics"""
        total = len(self.fingerprints)

        with_results = sum(1 for fp in self.fingerprints.values() if 'moderation_result' in fp)

        # Age distribution
        current_time = time.time()
        age_24h = sum(1 for fp in self.fingerprints.values()
                      if current_time - fp.get('cached_at', 0) < 86400)
        age_7d = sum(1 for fp in self.fingerprints.values()
                     if current_time - fp.get('cached_at', 0) < 7*86400)

        return {
            'total_fingerprints': total,
            'with_results': with_results,
            'last_24h': age_24h,
            'last_7d': age_7d
        }


# Singleton instance
_fingerprint_instance = None

def get_fingerprint_service() -> VideoFingerprint:
    """Get or create fingerprint service singleton"""
    global _fingerprint_instance
    if _fingerprint_instance is None:
        _fingerprint_instance = VideoFingerprint()
    return _fingerprint_instance

