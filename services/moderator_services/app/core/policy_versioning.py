"""
Policy Versioning System
Store moderation decisions with policy version numbers
Track policy changes over time and enable A/B testing
"""

import json
import os
import time
import hashlib
from typing import Dict, Optional, List, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from threading import Lock
import yaml


@dataclass
class PolicyVersion:
    """Represents a specific policy version"""
    version: str
    created_at: float
    created_by: str
    description: str
    config: Dict[str, Any]
    is_active: bool
    hash: str

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class PolicyVersionManager:
    """
    Manages policy versions and tracks which version was used for each decision
    """

    def __init__(self, policy_dir: str = "config/policies"):
        self.policy_dir = policy_dir
        self.versions: Dict[str, PolicyVersion] = {}
        self.active_version: Optional[str] = None
        self.version_history_file = os.path.join(policy_dir, "version_history.json")
        self.lock = Lock()

        # Ensure directory exists
        os.makedirs(policy_dir, exist_ok=True)

        # Load existing versions
        self._load_versions()

    def _load_versions(self):
        """Load policy versions from disk"""
        if os.path.exists(self.version_history_file):
            try:
                with open(self.version_history_file, 'r') as f:
                    data = json.load(f)

                for version_data in data.get('versions', []):
                    version = PolicyVersion(**version_data)
                    self.versions[version.version] = version

                self.active_version = data.get('active_version')

                print(f"✓ Loaded {len(self.versions)} policy versions")

            except Exception as e:
                print(f"⚠ Error loading policy versions: {e}")

    def _save_versions(self):
        """Save policy versions to disk"""
        try:
            data = {
                'active_version': self.active_version,
                'versions': [v.to_dict() for v in self.versions.values()],
                'last_updated': time.time()
            }

            with open(self.version_history_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"⚠ Error saving policy versions: {e}")

    def _compute_hash(self, config: Dict) -> str:
        """Compute hash of policy configuration"""
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]

    def create_version(self,
                      description: str,
                      config: Dict[str, Any],
                      created_by: str = "system",
                      activate: bool = True) -> str:
        """
        Create a new policy version

        Args:
            description: Description of changes
            config: Policy configuration
            created_by: Who created this version
            activate: Whether to activate immediately

        Returns:
            Version string (e.g., "v1.0.0")
        """
        with self.lock:
            # Generate version number
            version_num = len(self.versions) + 1
            major = version_num // 100
            minor = (version_num % 100) // 10
            patch = version_num % 10
            version = f"v{major}.{minor}.{patch}"

            # Compute hash
            config_hash = self._compute_hash(config)

            # Check if identical config already exists
            for existing_version, existing_policy in self.versions.items():
                if existing_policy.hash == config_hash:
                    print(f"⚠ Policy configuration identical to {existing_version}")
                    if activate:
                        self.activate_version(existing_version)
                    return existing_version

            # Create new version
            policy_version = PolicyVersion(
                version=version,
                created_at=time.time(),
                created_by=created_by,
                description=description,
                config=config,
                is_active=activate,
                hash=config_hash
            )

            # Save policy config to file
            policy_file = os.path.join(self.policy_dir, f"policy_{version}.yaml")
            with open(policy_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)

            # Store version
            self.versions[version] = policy_version

            # Activate if requested
            if activate:
                # Deactivate all others
                for v in self.versions.values():
                    v.is_active = False

                policy_version.is_active = True
                self.active_version = version

            # Save to disk
            self._save_versions()

            print(f"✓ Created policy version {version}")
            if activate:
                print(f"✓ Activated version {version}")

            return version

    def activate_version(self, version: str):
        """Activate a specific policy version"""
        with self.lock:
            if version not in self.versions:
                raise ValueError(f"Version {version} not found")

            # Deactivate all
            for v in self.versions.values():
                v.is_active = False

            # Activate requested version
            self.versions[version].is_active = True
            self.active_version = version

            self._save_versions()

            print(f"✓ Activated policy version {version}")

    def get_active_version(self) -> Optional[PolicyVersion]:
        """Get currently active policy version"""
        if self.active_version:
            return self.versions.get(self.active_version)
        return None

    def get_version(self, version: str) -> Optional[PolicyVersion]:
        """Get specific policy version"""
        return self.versions.get(version)

    def get_all_versions(self) -> List[PolicyVersion]:
        """Get all policy versions"""
        return sorted(self.versions.values(), key=lambda v: v.created_at, reverse=True)

    def get_version_config(self, version: Optional[str] = None) -> Dict:
        """
        Get policy configuration for a version

        Args:
            version: Version string, or None for active version

        Returns:
            Policy configuration dict
        """
        if version is None:
            policy = self.get_active_version()
        else:
            policy = self.get_version(version)

        if not policy:
            raise ValueError(f"Policy version not found: {version}")

        return policy.config

    def compare_versions(self, version1: str, version2: str) -> Dict:
        """
        Compare two policy versions

        Returns:
            Dictionary showing differences
        """
        v1 = self.get_version(version1)
        v2 = self.get_version(version2)

        if not v1 or not v2:
            raise ValueError("One or both versions not found")

        # Simple diff - in production, use a proper diff library
        changes = {
            'version1': version1,
            'version2': version2,
            'same_config': v1.hash == v2.hash,
            'time_difference': v2.created_at - v1.created_at,
            'changes': []
        }

        # Find config differences
        def find_diff(path, obj1, obj2):
            if isinstance(obj1, dict) and isinstance(obj2, dict):
                # Check all keys
                all_keys = set(obj1.keys()) | set(obj2.keys())
                for key in all_keys:
                    new_path = f"{path}.{key}" if path else key

                    if key not in obj1:
                        changes['changes'].append({
                            'type': 'added',
                            'path': new_path,
                            'value': obj2[key]
                        })
                    elif key not in obj2:
                        changes['changes'].append({
                            'type': 'removed',
                            'path': new_path,
                            'value': obj1[key]
                        })
                    elif obj1[key] != obj2[key]:
                        if isinstance(obj1[key], (dict, list)):
                            find_diff(new_path, obj1[key], obj2[key])
                        else:
                            changes['changes'].append({
                                'type': 'modified',
                                'path': new_path,
                                'old_value': obj1[key],
                                'new_value': obj2[key]
                            })

            elif isinstance(obj1, list) and isinstance(obj2, list):
                if obj1 != obj2:
                    changes['changes'].append({
                        'type': 'modified',
                        'path': path,
                        'old_value': obj1,
                        'new_value': obj2
                    })

        find_diff('', v1.config, v2.config)

        return changes

    def rollback(self, target_version: Optional[str] = None) -> str:
        """
        Rollback to previous version or specific version

        Args:
            target_version: Version to rollback to, or None for previous

        Returns:
            Version that was activated
        """
        with self.lock:
            if target_version is None:
                # Find previous version
                sorted_versions = sorted(
                    self.versions.values(),
                    key=lambda v: v.created_at,
                    reverse=True
                )

                if len(sorted_versions) < 2:
                    raise ValueError("No previous version to rollback to")

                target_version = sorted_versions[1].version

            self.activate_version(target_version)
            print(f"✓ Rolled back to version {target_version}")

            return target_version

    def get_version_stats(self) -> Dict:
        """Get statistics about policy versions"""
        with self.lock:
            sorted_versions = sorted(
                self.versions.values(),
                key=lambda v: v.created_at
            )

            return {
                'total_versions': len(self.versions),
                'active_version': self.active_version,
                'oldest_version': sorted_versions[0].version if sorted_versions else None,
                'newest_version': sorted_versions[-1].version if sorted_versions else None,
                'created_by': list(set(v.created_by for v in self.versions.values())),
                'version_list': [v.version for v in sorted_versions]
            }

    def export_version_history(self, output_file: str):
        """Export version history to file"""
        history = {
            'versions': [v.to_dict() for v in self.get_all_versions()],
            'active_version': self.active_version,
            'exported_at': time.time()
        }

        with open(output_file, 'w') as f:
            json.dump(history, f, indent=2)

        print(f"✓ Exported version history to {output_file}")


class DecisionLogger:
    """
    Logs moderation decisions with policy version information
    """

    def __init__(self,
                 log_file: str = "logs/decisions_with_versions.jsonl",
                 policy_manager: Optional[PolicyVersionManager] = None):
        self.log_file = log_file
        self.policy_manager = policy_manager or PolicyVersionManager()
        self.lock = Lock()

        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

    def log_decision(self,
                    job_id: str,
                    decision: str,
                    risk_level: str,
                    scores: Dict,
                    content_type: str,
                    policy_version: Optional[str] = None) -> Dict:
        """
        Log a moderation decision with policy version

        Args:
            job_id: Job identifier
            decision: Moderation decision (approve/review/block)
            risk_level: Risk level
            scores: Category scores
            content_type: Type of content (text/image/video)
            policy_version: Policy version used (None = active)

        Returns:
            Decision record
        """
        with self.lock:
            # Get policy version
            if policy_version is None:
                policy = self.policy_manager.get_active_version()
                policy_version = policy.version if policy else "unknown"

            # Create decision record
            record = {
                'job_id': job_id,
                'timestamp': time.time(),
                'decision': decision,
                'risk_level': risk_level,
                'scores': scores,
                'content_type': content_type,
                'policy_version': policy_version,
                'policy_hash': self.policy_manager.get_version(policy_version).hash if policy_version != "unknown" else None
            }

            # Append to log file (JSONL format - one JSON per line)
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(record) + '\n')

            return record

    def get_decisions_by_version(self, version: str, limit: int = 100) -> List[Dict]:
        """Get decisions made with specific policy version"""
        decisions = []

        if not os.path.exists(self.log_file):
            return decisions

        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    if record.get('policy_version') == version:
                        decisions.append(record)

                        if len(decisions) >= limit:
                            break
                except:
                    continue

        return decisions

    def analyze_version_performance(self, version: str) -> Dict:
        """Analyze performance of specific policy version"""
        decisions = self.get_decisions_by_version(version, limit=10000)

        if not decisions:
            return {'error': 'No decisions found for this version'}

        # Calculate statistics
        total = len(decisions)
        by_decision = {}
        by_risk = {}

        for d in decisions:
            dec = d.get('decision', 'unknown')
            risk = d.get('risk_level', 'unknown')

            by_decision[dec] = by_decision.get(dec, 0) + 1
            by_risk[risk] = by_risk.get(risk, 0) + 1

        return {
            'version': version,
            'total_decisions': total,
            'decisions': {k: v / total for k, v in by_decision.items()},
            'risk_levels': {k: v / total for k, v in by_risk.items()},
            'block_rate': by_decision.get('block', 0) / total,
            'approve_rate': by_decision.get('approve', 0) / total,
            'review_rate': by_decision.get('review', 0) / total
        }


# Singleton instances
_policy_manager = None
_decision_logger = None

def get_policy_manager() -> PolicyVersionManager:
    """Get global policy version manager"""
    global _policy_manager
    if _policy_manager is None:
        _policy_manager = PolicyVersionManager()
    return _policy_manager

def get_decision_logger() -> DecisionLogger:
    """Get global decision logger"""
    global _decision_logger
    if _decision_logger is None:
        _decision_logger = DecisionLogger()
    return _decision_logger


if __name__ == '__main__':
    # Test policy versioning
    manager = PolicyVersionManager()

    # Create initial policy
    config_v1 = {
        'thresholds': {
            'nudity': 0.7,
            'violence': 0.6,
            'hate_speech': 0.5
        },
        'enforcement': {
            'auto_block': ['nudity', 'violence'],
            'review': ['hate_speech']
        }
    }

    v1 = manager.create_version(
        description="Initial policy with strict nudity/violence thresholds",
        config=config_v1,
        created_by="admin@example.com"
    )

    # Create updated policy
    config_v2 = config_v1.copy()
    config_v2['thresholds']['hate_speech'] = 0.4  # Lower threshold
    config_v2['enforcement']['auto_block'].append('hate_speech')

    v2 = manager.create_version(
        description="Stricter hate speech detection",
        config=config_v2,
        created_by="admin@example.com"
    )

    # Compare versions
    diff = manager.compare_versions(v1, v2)
    print("\n" + "="*60)
    print("Version Comparison:")
    print(json.dumps(diff, indent=2))

    # Log some decisions
    logger = get_decision_logger()

    logger.log_decision(
        job_id='job-001',
        decision='block',
        risk_level='high',
        scores={'nudity': 0.85},
        content_type='image'
    )

    # Analyze version performance
    print("\n" + "="*60)
    print("Version Performance:")
    print(json.dumps(manager.get_version_stats(), indent=2))

