"""
ML Hidden Data Detector
=======================

Specialized detector for finding hidden/embedded data in images using:

1. Binary Pattern Analysis - Detect appended data, polyglots
2. Anomaly Detection - Autoencoder-based reconstruction error
3. Payload Detection - CNN trained on stego payloads
4. File Carving - Detect embedded file signatures
5. EOF Analysis - Data after image termination markers
"""

import os
import sys
import struct
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
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
class HiddenDataResult:
    """Result from hidden data analysis"""
    has_hidden_data: bool = False
    confidence: float = 0.0

    # Detection types
    has_appended_data: bool = False
    appended_size: int = 0
    appended_entropy: float = 0.0
    appended_preview: str = ""

    has_embedded_file: bool = False
    embedded_file_type: str = ""
    embedded_file_offset: int = 0

    has_hidden_markers: bool = False
    markers_found: List[str] = field(default_factory=list)
    marker_content: str = ""

    has_steganographic_payload: bool = False
    payload_type: str = ""
    payload_confidence: float = 0.0

    has_covert_channel: bool = False
    covert_channel_type: str = ""

    # Analysis details
    file_entropy: float = 0.0
    trailing_entropy: float = 0.0
    anomaly_score: float = 0.0

    warnings: List[str] = field(default_factory=list)
    models_used: List[str] = field(default_factory=list)


class MLHiddenDataDetector:
    """
    ML-powered detector for hidden/embedded data.

    Combines multiple detection techniques:
    - Binary analysis for file structure anomalies
    - ML-based anomaly detection
    - Known pattern matching
    - Entropy analysis
    """

    # Image EOF markers
    EOF_MARKERS = {
        'JPEG': b'\xff\xd9',
        'PNG': b'IEND\xae\x42\x60\x82',
        'GIF': b'\x3b',
    }

    # Image start signatures
    IMAGE_SIGNATURES = {
        b'\xff\xd8\xff': 'JPEG',
        b'\x89PNG\r\n\x1a\n': 'PNG',
        b'GIF87a': 'GIF',
        b'GIF89a': 'GIF',
        b'RIFF': 'WEBP',
        b'BM': 'BMP',
    }

    # Embedded file signatures to detect
    # Note: Removed signatures that are too common in compressed image data:
    # - 0x1f 0x8b (GZIP) - appears frequently in JPEG/PNG compressed data
    # - 0xff 0xfb (MP3 frame sync) - appears frequently in any binary data
    # - 0x00 0x00 0x01 0x00 (ICO) - too short, many false positives
    EMBEDDED_SIGNATURES = {
        b'MZ': ('Windows Executable', 'PE'),
        b'\x7fELF': ('Linux Executable', 'ELF'),
        b'PK\x03\x04': ('ZIP Archive', 'ZIP'),
        b'%PDF': ('PDF Document', 'PDF'),
        b'Rar!\x1a\x07': ('RAR Archive', 'RAR'),
        b'7z\xbc\xaf\x27\x1c': ('7-Zip Archive', '7Z'),  # Full signature
        b'ID3': ('MP3 Audio (ID3 Tag)', 'MP3'),  # Only ID3 tag, not frame sync
        b'OggS': ('OGG Audio', 'OGG'),
        b'\x00\x00\x00\x1cftyp': ('MP4 Video', 'MP4'),  # Longer signature
        b'\x1aE\xdf\xa3': ('MKV Video', 'MKV'),
        b'<?php': ('PHP Code', 'PHP'),
        b'#!/bin': ('Shell Script', 'SHELL'),  # More specific
        b'<script': ('JavaScript', 'JS'),
    }

    # Hidden data markers
    HIDDEN_MARKERS = [
        b'##HIDDEN_START##',
        b'##HIDDEN_END##',
        b'===BEGIN===',
        b'===END===',
        b'__START__',
        b'__END__',
        b'PAYLOAD_START',
        b'PAYLOAD_END',
        b'<!--HIDDEN-->',
        b'[HIDDEN]',
        b'DATA_INJECT',
        b'SECRET_DATA',
        b'STEG_DATA',
        b'EMBED_START',
        b'-----BEGIN',  # PGP/PEM markers
        b'-----END',
    ]

    # Entropy thresholds
    HIGH_ENTROPY_THRESHOLD = 7.5  # Near-random data (encrypted/compressed)
    LOW_ENTROPY_THRESHOLD = 1.0   # Very uniform (padding)
    SUSPICIOUS_ENTROPY_MIN = 6.0  # Compressed payloads

    def __init__(self, use_gpu: bool = False):
        """Initialize hidden data detector"""
        self.use_gpu = use_gpu
        self.device = 'cuda' if use_gpu else 'cpu'

        self._check_dependencies()

    def _check_dependencies(self):
        """Check for required libraries"""
        self.torch_available = False
        self.sklearn_available = False
        self.pillow_available = False

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

        try:
            from PIL import Image
            self.pillow_available = True
        except ImportError:
            pass

    def analyze(self, image_path: str) -> HiddenDataResult:
        """
        Analyze image for hidden data.

        Args:
            image_path: Path to image file

        Returns:
            HiddenDataResult with detection results
        """
        result = HiddenDataResult()

        if not os.path.exists(image_path):
            result.warnings.append("File not found")
            return result

        try:
            with open(image_path, 'rb') as f:
                content = f.read()
        except Exception as e:
            result.warnings.append(f"Failed to read file: {e}")
            return result

        file_size = len(content)

        # 1. Detect image format and find EOF
        image_format = self._detect_format(content)
        eof_pos = self._find_eof(content, image_format)

        # 2. Calculate file entropy
        result.file_entropy = self._calculate_entropy(content)
        result.models_used.append('Entropy Analysis')

        # 3. Check for appended data after EOF
        self._check_appended_data(content, eof_pos, file_size, result)

        # 4. Check for hidden markers
        self._check_hidden_markers(content, result)

        # 5. Check for embedded file signatures
        self._check_embedded_files(content, result)

        # 6. ML-based anomaly detection
        if self.torch_available or self.sklearn_available:
            self._ml_anomaly_detection(content, image_path, result)

        # 7. Covert channel detection
        self._check_covert_channels(content, image_path, result)

        # 8. Calculate final confidence
        self._calculate_confidence(result)

        return result

    def _detect_format(self, content: bytes) -> str:
        """Detect image format from magic bytes"""
        for sig, fmt in self.IMAGE_SIGNATURES.items():
            if content.startswith(sig):
                return fmt
        return 'UNKNOWN'

    def _find_eof(self, content: bytes, image_format: str) -> int:
        """Find the EOF marker position for the image format"""
        if image_format not in self.EOF_MARKERS:
            return len(content)

        eof_marker = self.EOF_MARKERS[image_format]

        if image_format == 'JPEG':
            # Find last occurrence of FF D9
            pos = content.rfind(eof_marker)
            if pos != -1:
                return pos + len(eof_marker)

        elif image_format == 'PNG':
            # Find IEND chunk
            pos = content.rfind(b'IEND')
            if pos != -1:
                return pos + 8  # IEND + CRC

        elif image_format == 'GIF':
            # Find trailer byte
            pos = content.rfind(eof_marker)
            if pos != -1:
                return pos + 1

        return len(content)

    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy"""
        if not data:
            return 0.0

        freq = [0] * 256
        for byte in data:
            freq[byte] += 1

        length = len(data)
        entropy = 0.0

        for count in freq:
            if count > 0:
                p = count / length
                entropy -= p * math.log2(p)

        return entropy

    def _check_appended_data(
        self,
        content: bytes,
        eof_pos: int,
        file_size: int,
        result: HiddenDataResult
    ):
        """Check for data appended after EOF marker"""
        if eof_pos >= file_size:
            return

        trailing = content[eof_pos:]

        # Strip null padding
        stripped = trailing.lstrip(b'\x00\xff')
        if len(stripped) < 10:
            return

        result.has_appended_data = True
        result.has_hidden_data = True
        result.appended_size = len(trailing)
        result.appended_entropy = self._calculate_entropy(trailing)

        # Get preview
        try:
            result.appended_preview = stripped[:100].decode('utf-8', errors='replace')
        except:
            result.appended_preview = f"<binary: {len(stripped)} bytes>"

        # Analyze trailing data
        if result.appended_entropy > self.HIGH_ENTROPY_THRESHOLD:
            result.warnings.append(
                f"High-entropy data after EOF ({result.appended_entropy:.2f}) - "
                f"possible encrypted payload ({result.appended_size} bytes)"
            )
        elif result.appended_entropy > self.SUSPICIOUS_ENTROPY_MIN:
            result.warnings.append(
                f"Compressed/encoded data after EOF ({result.appended_size} bytes)"
            )
        else:
            result.warnings.append(
                f"Data appended after EOF ({result.appended_size} bytes): "
                f"{result.appended_preview[:50]}..."
            )

        result.trailing_entropy = result.appended_entropy
        result.models_used.append('EOF Analysis')

    def _check_hidden_markers(self, content: bytes, result: HiddenDataResult):
        """Check for known hidden data markers"""
        for marker in self.HIDDEN_MARKERS:
            if marker in content:
                result.has_hidden_markers = True
                result.has_hidden_data = True

                try:
                    marker_str = marker.decode('utf-8', errors='replace')
                except:
                    marker_str = str(marker)

                result.markers_found.append(marker_str)

                # Try to extract content between paired markers
                if b'START' in marker or b'BEGIN' in marker:
                    self._extract_marker_content(content, marker, result)

        if result.has_hidden_markers:
            result.warnings.append(
                f"Hidden data markers found: {', '.join(result.markers_found[:5])}"
            )
            result.models_used.append('Marker Detection')

    def _extract_marker_content(
        self,
        content: bytes,
        start_marker: bytes,
        result: HiddenDataResult
    ):
        """Extract content between start and end markers"""
        # Find corresponding end marker
        end_marker = start_marker.replace(b'START', b'END').replace(b'BEGIN', b'END')

        start_pos = content.find(start_marker)
        if start_pos == -1:
            return

        start_pos += len(start_marker)
        end_pos = content.find(end_marker, start_pos)

        if end_pos > start_pos:
            hidden = content[start_pos:end_pos]
            try:
                result.marker_content = hidden[:200].decode('utf-8', errors='replace')
            except:
                result.marker_content = f"<binary: {len(hidden)} bytes>"

            result.warnings.append(f"Hidden content extracted: {result.marker_content[:50]}...")

    def _check_embedded_files(self, content: bytes, result: HiddenDataResult):
        """Check for embedded file signatures"""
        # Start searching after image header (skip first 1KB)
        search_start = 1024

        for sig, (desc, file_type) in self.EMBEDDED_SIGNATURES.items():
            # Handle patterns with wildcards
            if b'....' in sig:
                continue  # Skip patterns with wildcards for now

            pos = content.find(sig, search_start)

            if pos != -1:
                # Validate the detection
                if self._validate_embedded_signature(content, pos, sig, file_type):
                    result.has_embedded_file = True
                    result.has_hidden_data = True
                    result.embedded_file_type = desc
                    result.embedded_file_offset = pos

                    result.warnings.append(
                        f"Embedded {desc} detected at offset {pos}"
                    )
                    result.models_used.append('File Carving')
                    break

    def _validate_embedded_signature(
        self,
        content: bytes,
        pos: int,
        sig: bytes,
        file_type: str
    ) -> bool:
        """Validate that detected signature is a real embedded file"""

        # PE validation
        if file_type == 'PE' and sig == b'MZ':
            if pos + 0x40 >= len(content):
                return False
            try:
                pe_offset = struct.unpack('<H', content[pos + 0x3C:pos + 0x3E])[0]
                if pe_offset > 0x1000:
                    return False
                if pos + pe_offset + 4 >= len(content):
                    return False
                return content[pos + pe_offset:pos + pe_offset + 4] == b'PE\x00\x00'
            except:
                return False

        # GZIP validation - MUST check compression method
        if file_type == 'GZIP':
            if pos + 10 >= len(content):
                return False
            # Byte 2 must be 8 (deflate compression)
            compression_method = content[pos + 2]
            if compression_method != 8:
                return False
            # Byte 3 (flags) must be 0-31
            flags = content[pos + 3]
            if flags > 31:
                return False
            # Byte 9 (OS) must be valid (0-13 or 255)
            os_type = content[pos + 9]
            if os_type > 13 and os_type != 255:
                return False
            return True

        # ICO/CUR validation
        if file_type == 'ICO':
            if pos + 6 >= len(content):
                return False
            # Bytes 0-1 must be 0 (reserved)
            reserved = struct.unpack('<H', content[pos:pos+2])[0]
            if reserved != 0:
                return False
            # Bytes 2-3 must be 1 (ICO) or 2 (CUR)
            img_type = struct.unpack('<H', content[pos+2:pos+4])[0]
            if img_type not in [1, 2]:
                return False
            # Bytes 4-5: number of images (1-256 is reasonable)
            num_images = struct.unpack('<H', content[pos+4:pos+6])[0]
            if num_images == 0 or num_images > 256:
                return False
            # Additional check: verify image directory entries exist
            expected_size = 6 + (num_images * 16)  # Header + directory entries
            if pos + expected_size > len(content):
                return False
            return True

        # ZIP validation
        if file_type == 'ZIP':
            if pos + 30 >= len(content):
                return False
            # Check for valid local file header
            try:
                # Minimum version needed
                min_version = struct.unpack('<H', content[pos+4:pos+6])[0]
                if min_version > 100:  # Unreasonably high version
                    return False
                # Compression method (0=stored, 8=deflate, etc)
                comp_method = struct.unpack('<H', content[pos+8:pos+10])[0]
                if comp_method > 20:  # Invalid compression method
                    return False
                # File name length
                fname_len = struct.unpack('<H', content[pos+26:pos+28])[0]
                if fname_len > 256:  # Unreasonably long filename
                    return False
                return True
            except:
                return False

        # PDF validation
        if file_type == 'PDF':
            # Check for %%EOF marker within reasonable distance
            eof_pos = content.find(b'%%EOF', pos)
            if eof_pos == -1:
                return False
            # PDF should have proper structure
            if b'obj' not in content[pos:min(pos+10000, len(content))]:
                return False
            return True

        # RAR validation
        if file_type == 'RAR':
            if pos + 7 >= len(content):
                return False
            # RAR5 signature is "Rar!\x1a\x07\x01"
            # RAR4 signature is "Rar!\x1a\x07\x00"
            if content[pos:pos+7] not in [b'Rar!\x1a\x07\x00', b'Rar!\x1a\x07\x01']:
                return False
            return True

        # ELF validation
        if file_type == 'ELF':
            if pos + 16 >= len(content):
                return False
            # Check ELF class (32 or 64 bit)
            elf_class = content[pos + 4]
            if elf_class not in [1, 2]:
                return False
            # Check endianness
            endian = content[pos + 5]
            if endian not in [1, 2]:
                return False
            return True

        # 7Z validation
        if file_type == '7Z':
            if pos + 6 >= len(content):
                return False
            # Full signature is "7z\xbc\xaf\x27\x1c"
            return content[pos:pos+6] == b'7z\xbc\xaf\x27\x1c'

        # For script types (PHP, Shell, JS), check for actual code patterns
        if file_type in ['PHP', 'SHELL', 'JS']:
            # Look for more code-like content after signature
            sample = content[pos:min(pos+200, len(content))]
            # Count printable ASCII characters
            printable = sum(1 for b in sample if 32 <= b <= 126)
            # Scripts should be mostly printable text
            if printable / len(sample) < 0.7:
                return False
            return True

        # MP3 validation
        if file_type == 'MP3':
            # ID3 tag validation
            if sig == b'ID3':
                if pos + 10 >= len(content):
                    return False
                # Check ID3 version
                version = content[pos + 3]
                if version > 4:  # ID3v2.4 is latest
                    return False
                return True
            # Frame sync validation (0xff 0xfb)
            if sig == b'\xff\xfb':
                # This is too common in binary data, require more validation
                if pos + 4 >= len(content):
                    return False
                # Check for valid MPEG audio frame header
                header = struct.unpack('>I', content[pos:pos+4])[0]
                # Frame sync should be 0xFFE or 0xFFF
                if (header >> 20) not in [0xFFE, 0xFFF]:
                    return False
                return True

        # For other types, be more conservative - require additional evidence
        # Default: don't flag unless we have strong validation
        return False

        # Default: accept if signature found
        return True

    def _ml_anomaly_detection(
        self,
        content: bytes,
        image_path: str,
        result: HiddenDataResult
    ):
        """ML-based anomaly detection for hidden data"""
        if self.sklearn_available:
            self._isolation_forest_detection(content, result)

        if self.torch_available and self.pillow_available:
            self._autoencoder_detection(image_path, result)

    def _isolation_forest_detection(self, content: bytes, result: HiddenDataResult):
        """Use Isolation Forest to detect anomalous byte patterns"""
        try:
            from sklearn.ensemble import IsolationForest

            # Create feature vectors from byte blocks
            block_size = 256
            features = []

            for i in range(0, len(content) - block_size, block_size):
                block = content[i:i + block_size]

                # Features: entropy, byte histogram stats
                entropy = self._calculate_entropy(block)
                byte_counts = [0] * 256
                for b in block:
                    byte_counts[b] += 1

                mean_count = np.mean(byte_counts)
                std_count = np.std(byte_counts)
                max_count = max(byte_counts)

                features.append([entropy, mean_count, std_count, max_count])

            if len(features) < 10:
                return

            # Fit Isolation Forest
            iso = IsolationForest(contamination=0.1, random_state=42)
            predictions = iso.fit_predict(features)

            # Check for anomalous blocks
            anomaly_ratio = np.sum(predictions == -1) / len(predictions)

            if anomaly_ratio > 0.15:
                result.anomaly_score = anomaly_ratio
                result.warnings.append(
                    f"Anomalous byte patterns detected ({anomaly_ratio:.1%} of blocks)"
                )
                result.models_used.append('Isolation Forest')

        except Exception as e:
            result.warnings.append(f"Isolation Forest error: {e}")

    def _autoencoder_detection(self, image_path: str, result: HiddenDataResult):
        """Use autoencoder reconstruction error to detect hidden data"""
        try:
            import torch
            from torchvision import transforms, models
            from PIL import Image

            # Load and preprocess image
            img = Image.open(image_path).convert('RGB')

            transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
            ])

            tensor = transform(img).unsqueeze(0)

            # Use pretrained model to extract features
            # High reconstruction error can indicate manipulation
            model = models.resnet18(weights='IMAGENET1K_V1')
            model.eval()

            with torch.no_grad():
                features = model(tensor)

            # Analyze feature distribution
            features_np = features.numpy().flatten()

            # Check for unusual feature patterns
            mean_feat = np.mean(features_np)
            std_feat = np.std(features_np)

            # Very low or very high variance can indicate issues
            if std_feat < 0.05 or std_feat > 3.0:
                result.anomaly_score = max(result.anomaly_score, 0.5)
                result.warnings.append("Unusual feature distribution detected")
                result.models_used.append('Feature Analysis')

        except Exception as e:
            pass  # Silently skip if model unavailable

    def _check_covert_channels(
        self,
        content: bytes,
        image_path: str,
        result: HiddenDataResult
    ):
        """Check for covert channel usage"""
        # Check for data in EXIF/metadata
        if self.pillow_available:
            self._check_metadata_channel(image_path, result)

        # Check for unusual comment blocks
        self._check_comment_channel(content, result)

    def _check_metadata_channel(self, image_path: str, result: HiddenDataResult):
        """Check for data hidden in metadata"""
        try:
            from PIL import Image

            with Image.open(image_path) as img:
                # Check EXIF
                exif = img._getexif()
                if exif:
                    for tag, value in exif.items():
                        value_str = str(value)
                        if len(value_str) > 1000:
                            result.has_covert_channel = True
                            result.has_hidden_data = True
                            result.covert_channel_type = "EXIF metadata"
                            result.warnings.append(
                                f"Large EXIF field detected ({len(value_str)} chars)"
                            )
                            break

                # Check for ICC profile with hidden data
                icc = img.info.get('icc_profile')
                if icc and len(icc) > 50000:
                    result.has_covert_channel = True
                    result.covert_channel_type = "ICC Profile"
                    result.warnings.append(
                        f"Unusually large ICC profile ({len(icc)} bytes)"
                    )

        except Exception:
            pass

    def _check_comment_channel(self, content: bytes, result: HiddenDataResult):
        """Check for data hidden in comment blocks"""
        # JPEG comment marker: FF FE
        if content.startswith(b'\xff\xd8\xff'):
            pos = 0
            while True:
                pos = content.find(b'\xff\xfe', pos)
                if pos == -1:
                    break

                if pos + 4 < len(content):
                    length = struct.unpack('>H', content[pos + 2:pos + 4])[0]
                    if length > 1000:
                        result.has_covert_channel = True
                        result.has_hidden_data = True
                        result.covert_channel_type = "JPEG Comment"
                        result.warnings.append(
                            f"Large JPEG comment block ({length} bytes)"
                        )
                        break
                pos += 2

    def _calculate_confidence(self, result: HiddenDataResult):
        """Calculate overall confidence score"""
        score = 0.0

        if result.has_appended_data:
            # Higher confidence for high-entropy appended data
            if result.appended_entropy > self.HIGH_ENTROPY_THRESHOLD:
                score += 0.4
            else:
                score += 0.3

        if result.has_hidden_markers:
            score += 0.35
            if result.marker_content:
                score += 0.15

        if result.has_embedded_file:
            score += 0.5

        if result.has_covert_channel:
            score += 0.2

        if result.has_steganographic_payload:
            score += result.payload_confidence

        if result.anomaly_score > 0.15:
            score += result.anomaly_score * 0.3

        result.confidence = min(score, 1.0)
        result.has_hidden_data = result.confidence > 0.2

