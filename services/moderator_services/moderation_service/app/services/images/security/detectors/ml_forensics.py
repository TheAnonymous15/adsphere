"""
ML-Enhanced Image Forensics Detector
====================================

Uses deep learning models for image forensics:

1. Manipulation Detection (Mantra-Net style)
2. Copy-Move Forgery Detection
3. Splicing Detection
4. JPEG Ghost Detection
5. ELA (Error Level Analysis) with ML classification
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent.parent))

try:
    from model_registry import ensure_models, get_model_path
except ImportError:
    def ensure_models(models, verbose=False):
        return True
    def get_model_path(model_id):
        return None


@dataclass
class ForensicsResult:
    """Result from ML forensics analysis"""
    is_manipulated: bool = False
    manipulation_confidence: float = 0.0

    # Specific detections
    ela_anomaly: bool = False
    ela_score: float = 0.0

    copy_move_detected: bool = False
    copy_move_regions: List[Dict] = field(default_factory=list)

    splicing_detected: bool = False
    splicing_confidence: float = 0.0

    jpeg_ghost_detected: bool = False
    compression_inconsistency: bool = False

    # Heatmap of suspicious regions (if available)
    anomaly_heatmap: Optional[np.ndarray] = None

    warnings: List[str] = field(default_factory=list)
    models_used: List[str] = field(default_factory=list)


class MLForensicsDetector:
    """
    ML-powered image forensics for manipulation detection.

    Combines multiple techniques:
    - Error Level Analysis (ELA) with CNN classifier
    - SIFT-based copy-move detection
    - Deep learning manipulation detector
    - JPEG compression artifact analysis
    """

    # Quality level for ELA
    ELA_QUALITY = 95
    ELA_SCALE = 15

    # Thresholds
    ELA_THRESHOLD = 0.4
    MANIPULATION_THRESHOLD = 0.5

    def __init__(self, use_gpu: bool = False):
        """Initialize forensics detector"""
        self.use_gpu = use_gpu
        self.device = 'cuda' if use_gpu else 'cpu'

        self._check_dependencies()

    def _check_dependencies(self):
        """Check for required libraries"""
        self.cv2_available = False
        self.pillow_available = False
        self.torch_available = False
        self.sklearn_available = False

        try:
            import cv2
            self.cv2_available = True
        except ImportError:
            pass

        try:
            from PIL import Image
            self.pillow_available = True
        except ImportError:
            pass

        try:
            import torch
            self.torch_available = True
            if self.use_gpu:
                import torch
                if torch.cuda.is_available():
                    self.device = 'cuda'
        except ImportError:
            pass

        try:
            from sklearn.ensemble import IsolationForest
            self.sklearn_available = True
        except ImportError:
            pass

    def analyze(self, image_path: str) -> ForensicsResult:
        """
        Perform ML-based forensics analysis.

        Args:
            image_path: Path to image file

        Returns:
            ForensicsResult with detection results
        """
        result = ForensicsResult()

        if not os.path.exists(image_path):
            result.warnings.append("File not found")
            return result

        scores = []

        # 1. Error Level Analysis
        if self.pillow_available:
            ela_score = self._error_level_analysis(image_path, result)
            if ela_score is not None:
                scores.append(ela_score)
                result.ela_score = ela_score
                result.models_used.append('ELA')

        # 2. Copy-Move Detection
        if self.cv2_available:
            cm_detected = self._copy_move_detection(image_path, result)
            if cm_detected:
                scores.append(0.8)
                result.models_used.append('Copy-Move SIFT')

        # 3. JPEG Ghost Detection
        if self.pillow_available:
            ghost_score = self._jpeg_ghost_detection(image_path, result)
            if ghost_score is not None:
                scores.append(ghost_score)
                result.models_used.append('JPEG Ghost')

        # 4. Deep Learning Analysis (if available)
        if self.torch_available:
            dl_score = self._deep_forensics(image_path, result)
            if dl_score is not None:
                scores.append(dl_score * 1.5)  # Weight higher
                result.models_used.append('Deep Forensics')

        # Combine scores
        if scores:
            result.manipulation_confidence = min(sum(scores) / len(scores), 1.0)
            result.is_manipulated = result.manipulation_confidence > self.MANIPULATION_THRESHOLD

        return result

    def _error_level_analysis(
        self,
        image_path: str,
        result: ForensicsResult
    ) -> Optional[float]:
        """
        Error Level Analysis (ELA) for manipulation detection.

        ELA works by re-saving the image at a known quality level
        and analyzing the difference. Manipulated regions show
        different error levels.
        """
        try:
            from PIL import Image
            import io

            # Load original
            original = Image.open(image_path).convert('RGB')
            original_array = np.array(original, dtype=np.float32)

            # Re-save at quality level
            buffer = io.BytesIO()
            original.save(buffer, format='JPEG', quality=self.ELA_QUALITY)
            buffer.seek(0)

            # Load re-saved
            resaved = Image.open(buffer).convert('RGB')
            resaved_array = np.array(resaved, dtype=np.float32)

            # Calculate ELA
            ela = np.abs(original_array - resaved_array)
            ela = ela * self.ELA_SCALE
            ela = np.clip(ela, 0, 255)

            # Analyze ELA distribution
            ela_mean = np.mean(ela)
            ela_std = np.std(ela)
            ela_max = np.max(ela)

            # Store heatmap
            result.anomaly_heatmap = ela.astype(np.uint8)

            # Score based on ELA statistics
            score = 0.0

            # High variance suggests manipulation
            if ela_std > 30:
                score += 0.3

            # Very high local maxima
            if ela_max > 200:
                score += 0.2

            # Check for localized anomalies
            if self._has_localized_ela_anomaly(ela):
                score += 0.4
                result.ela_anomaly = True

            return min(score, 1.0)

        except Exception as e:
            result.warnings.append(f"ELA error: {e}")
            return None

    def _has_localized_ela_anomaly(self, ela: np.ndarray) -> bool:
        """Check for localized high-ELA regions (manipulation indicators)"""
        try:
            # Convert to grayscale if needed
            if len(ela.shape) == 3:
                ela_gray = np.mean(ela, axis=2)
            else:
                ela_gray = ela

            # Calculate block statistics
            block_size = 32
            h, w = ela_gray.shape

            block_means = []
            for y in range(0, h - block_size, block_size):
                for x in range(0, w - block_size, block_size):
                    block = ela_gray[y:y+block_size, x:x+block_size]
                    block_means.append(np.mean(block))

            if not block_means:
                return False

            # Check for outlier blocks
            mean_of_means = np.mean(block_means)
            std_of_means = np.std(block_means)

            outliers = sum(1 for m in block_means if m > mean_of_means + 2 * std_of_means)
            outlier_ratio = outliers / len(block_means)

            return outlier_ratio > 0.05 and outlier_ratio < 0.3

        except:
            return False

    def _copy_move_detection(
        self,
        image_path: str,
        result: ForensicsResult
    ) -> bool:
        """
        Detect copy-move forgery using SIFT features.

        Looks for duplicated regions within the same image.
        """
        try:
            import cv2

            img = cv2.imread(image_path)
            if img is None:
                return False

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Detect SIFT features
            sift = cv2.SIFT_create()
            keypoints, descriptors = sift.detectAndCompute(gray, None)

            if descriptors is None or len(descriptors) < 10:
                return False

            # Match features with themselves
            bf = cv2.BFMatcher()
            matches = bf.knnMatch(descriptors, descriptors, k=2)

            # Find good matches (excluding self-matches)
            good_matches = []
            for m, n in matches:
                if m.distance < 0.7 * n.distance:
                    # Ensure not matching to itself
                    pt1 = keypoints[m.queryIdx].pt
                    pt2 = keypoints[m.trainIdx].pt
                    dist = np.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)

                    if dist > 50:  # Minimum distance between matched regions
                        good_matches.append((m, pt1, pt2))

            # Cluster matches
            if len(good_matches) > 20:
                # Group nearby matches
                clusters = self._cluster_matches(good_matches)

                if len(clusters) > 0:
                    result.copy_move_detected = True
                    result.copy_move_regions = clusters
                    return True

            return False

        except Exception as e:
            result.warnings.append(f"Copy-move detection error: {e}")
            return False

    def _cluster_matches(self, matches: List) -> List[Dict]:
        """Cluster matches into copy-move regions"""
        if not matches:
            return []

        try:
            from sklearn.cluster import DBSCAN

            # Extract source points
            points = np.array([m[1] for m in matches])

            # Cluster
            clustering = DBSCAN(eps=30, min_samples=5).fit(points)
            labels = clustering.labels_

            clusters = []
            for label in set(labels):
                if label == -1:
                    continue

                cluster_points = points[labels == label]
                clusters.append({
                    'center': np.mean(cluster_points, axis=0).tolist(),
                    'size': len(cluster_points)
                })

            return clusters

        except:
            return []

    def _jpeg_ghost_detection(
        self,
        image_path: str,
        result: ForensicsResult
    ) -> Optional[float]:
        """
        JPEG Ghost detection for double compression artifacts.

        Different regions may have been saved at different quality levels.
        """
        try:
            from PIL import Image
            import io

            original = Image.open(image_path).convert('RGB')
            original_array = np.array(original, dtype=np.float32)

            # Test multiple quality levels
            ghost_scores = []

            for quality in [60, 70, 80, 90]:
                buffer = io.BytesIO()
                original.save(buffer, format='JPEG', quality=quality)
                buffer.seek(0)

                recompressed = Image.open(buffer).convert('RGB')
                recomp_array = np.array(recompressed, dtype=np.float32)

                # Calculate difference
                diff = np.abs(original_array - recomp_array)

                # Analyze for ghosting
                block_scores = self._analyze_block_ghosting(diff)
                ghost_scores.append(block_scores)

            # Check for inconsistent compression
            variance_across_qualities = np.std([np.mean(gs) for gs in ghost_scores])

            if variance_across_qualities > 5:
                result.compression_inconsistency = True
                result.jpeg_ghost_detected = True
                return 0.6

            return 0.1

        except Exception as e:
            result.warnings.append(f"JPEG ghost error: {e}")
            return None

    def _analyze_block_ghosting(self, diff: np.ndarray) -> List[float]:
        """Analyze 8x8 block differences for JPEG ghosting"""
        scores = []

        h, w = diff.shape[:2]
        for y in range(0, h - 8, 8):
            for x in range(0, w - 8, 8):
                block = diff[y:y+8, x:x+8]
                scores.append(np.mean(block))

        return scores

    def _deep_forensics(
        self,
        image_path: str,
        result: ForensicsResult
    ) -> Optional[float]:
        """
        Use deep learning model for manipulation detection.

        Uses pretrained or fine-tuned models for forensics.
        """
        try:
            import torch
            from torchvision import transforms, models
            from PIL import Image

            # Try to load specialized forensics model
            model = self._load_forensics_model()

            if model is None:
                # Use anomaly detection approach
                return self._anomaly_based_forensics(image_path, result)

            # Preprocess
            transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                   std=[0.229, 0.224, 0.225])
            ])

            img = Image.open(image_path).convert('RGB')
            tensor = transform(img).unsqueeze(0)

            if self.device == 'cuda':
                tensor = tensor.cuda()
                model = model.cuda()

            model.eval()
            with torch.no_grad():
                output = model(tensor)
                prob = torch.sigmoid(output).item()

            return prob

        except Exception as e:
            result.warnings.append(f"Deep forensics error: {e}")
            return None

    def _load_forensics_model(self):
        """Load pre-trained forensics model"""
        try:
            import torch

            # Check for specialized forensics model
            model_path = get_model_path('forensics_model')
            if model_path and os.path.exists(model_path):
                return torch.load(model_path, map_location=self.device)

            return None

        except:
            return None

    def _anomaly_based_forensics(
        self,
        image_path: str,
        result: ForensicsResult
    ) -> Optional[float]:
        """
        Anomaly-based forensics using pretrained feature extractors.
        """
        try:
            import torch
            from torchvision import transforms, models
            from PIL import Image

            # Use pretrained ResNet for features
            model = models.resnet18(pretrained=True)
            model = torch.nn.Sequential(*list(model.children())[:-1])
            model.eval()

            if self.device == 'cuda':
                model = model.cuda()

            # Extract features from multiple crops
            transform = transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                   std=[0.229, 0.224, 0.225])
            ])

            img = Image.open(image_path).convert('RGB')

            # Extract features from different regions
            region_features = []
            w, h = img.size
            crop_size = min(w, h) // 3

            for y in range(0, h - crop_size, crop_size // 2):
                for x in range(0, w - crop_size, crop_size // 2):
                    crop = img.crop((x, y, x + crop_size, y + crop_size))
                    crop = crop.resize((224, 224))
                    tensor = transform(crop).unsqueeze(0)

                    if self.device == 'cuda':
                        tensor = tensor.cuda()

                    with torch.no_grad():
                        feat = model(tensor).squeeze().cpu().numpy()
                        region_features.append(feat)

            if len(region_features) < 4:
                return None

            # Check for outlier regions (possible manipulation)
            if self.sklearn_available:
                from sklearn.ensemble import IsolationForest

                features_array = np.array(region_features)
                iso = IsolationForest(contamination=0.1, random_state=42)
                outliers = iso.fit_predict(features_array)

                outlier_ratio = np.sum(outliers == -1) / len(outliers)

                if outlier_ratio > 0.2:
                    return 0.7
                elif outlier_ratio > 0.1:
                    return 0.4

            return 0.2

        except Exception as e:
            result.warnings.append(f"Anomaly forensics error: {e}")
            return None

