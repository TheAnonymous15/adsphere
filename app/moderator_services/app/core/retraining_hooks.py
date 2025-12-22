"""
Automatic Retraining Hooks
Log false positives and negatives to training data store
Enable continuous model improvement
"""

import json
import os
import time
import shutil
import hashlib
from typing import Dict, Optional, List, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from threading import Lock
from enum import Enum
import sqlite3


class FeedbackType(Enum):
    """Type of feedback"""
    FALSE_POSITIVE = "false_positive"  # Blocked but should be approved
    FALSE_NEGATIVE = "false_negative"  # Approved but should be blocked
    CORRECT = "correct"                 # Decision was correct
    UNCERTAIN = "uncertain"             # Human unsure


@dataclass
class TrainingExample:
    """Represents a training example from feedback"""
    example_id: str
    job_id: str
    content_type: str
    content_hash: str
    asset_path: Optional[str]

    # Original decision
    original_decision: str
    original_risk_level: str
    original_scores: Dict[str, float]

    # Feedback
    feedback_type: str
    correct_label: str
    correct_categories: List[str]
    feedback_source: str  # 'admin', 'user_appeal', 'automated'

    # Metadata
    created_at: float
    reviewed_by: Optional[str]
    notes: Optional[str]

    # Training metadata
    used_in_training: bool
    training_runs: List[str]
    quality_score: Optional[float]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class RetrainingDataStore:
    """
    Stores feedback and training examples for model retraining
    """

    def __init__(self,
                 db_path: str = "app/database/retraining.db",
                 asset_storage: str = "app/retraining_data/assets"):
        self.db_path = db_path
        self.asset_storage = asset_storage
        self.lock = Lock()

        # Ensure directories exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        os.makedirs(asset_storage, exist_ok=True)

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for training examples"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_examples (
                example_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                content_type TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                asset_path TEXT,
                
                original_decision TEXT NOT NULL,
                original_risk_level TEXT NOT NULL,
                original_scores TEXT,  -- JSON
                
                feedback_type TEXT NOT NULL,
                correct_label TEXT NOT NULL,
                correct_categories TEXT,  -- JSON array
                feedback_source TEXT NOT NULL,
                
                created_at REAL NOT NULL,
                reviewed_by TEXT,
                notes TEXT,
                
                used_in_training INTEGER DEFAULT 0,
                training_runs TEXT,  -- JSON array
                quality_score REAL,
                
                INDEX idx_feedback_type ON training_examples(feedback_type),
                INDEX idx_content_type ON training_examples(content_type),
                INDEX idx_created_at ON training_examples(created_at)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_runs (
                run_id TEXT PRIMARY KEY,
                started_at REAL NOT NULL,
                completed_at REAL,
                model_type TEXT NOT NULL,
                examples_count INTEGER,
                performance_metrics TEXT,  -- JSON
                model_path TEXT,
                status TEXT,
                notes TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback_stats (
                stat_date TEXT PRIMARY KEY,
                total_feedback INTEGER DEFAULT 0,
                false_positives INTEGER DEFAULT 0,
                false_negatives INTEGER DEFAULT 0,
                correct_decisions INTEGER DEFAULT 0,
                by_content_type TEXT,  -- JSON
                by_category TEXT  -- JSON
            )
        """)

        conn.commit()
        conn.close()

        print(f"✓ Initialized retraining database at {self.db_path}")

    def add_feedback(self,
                    job_id: str,
                    content_type: str,
                    content_hash: str,
                    asset_path: Optional[str],
                    original_decision: str,
                    original_risk_level: str,
                    original_scores: Dict[str, float],
                    feedback_type: FeedbackType,
                    correct_label: str,
                    correct_categories: List[str],
                    feedback_source: str = "admin",
                    reviewed_by: Optional[str] = None,
                    notes: Optional[str] = None) -> str:
        """
        Add feedback example to training data store

        Returns:
            example_id
        """
        with self.lock:
            # Generate example ID
            example_id = hashlib.sha256(
                f"{job_id}_{time.time()}".encode()
            ).hexdigest()[:16]

            # Copy asset to storage if provided
            stored_asset_path = None
            if asset_path and os.path.exists(asset_path):
                ext = os.path.splitext(asset_path)[1]
                stored_asset_path = os.path.join(
                    self.asset_storage,
                    f"{example_id}{ext}"
                )
                shutil.copy2(asset_path, stored_asset_path)

            # Create example
            example = TrainingExample(
                example_id=example_id,
                job_id=job_id,
                content_type=content_type,
                content_hash=content_hash,
                asset_path=stored_asset_path,
                original_decision=original_decision,
                original_risk_level=original_risk_level,
                original_scores=original_scores,
                feedback_type=feedback_type.value,
                correct_label=correct_label,
                correct_categories=correct_categories,
                feedback_source=feedback_source,
                created_at=time.time(),
                reviewed_by=reviewed_by,
                notes=notes,
                used_in_training=False,
                training_runs=[],
                quality_score=None
            )

            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO training_examples VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                example.example_id,
                example.job_id,
                example.content_type,
                example.content_hash,
                example.asset_path,
                example.original_decision,
                example.original_risk_level,
                json.dumps(example.original_scores),
                example.feedback_type,
                example.correct_label,
                json.dumps(example.correct_categories),
                example.feedback_source,
                example.created_at,
                example.reviewed_by,
                example.notes,
                0,  # used_in_training
                json.dumps([]),  # training_runs
                example.quality_score
            ))

            conn.commit()
            conn.close()

            # Update stats
            self._update_stats(feedback_type, content_type)

            print(f"✓ Added training example {example_id} ({feedback_type.value})")

            return example_id

    def _update_stats(self, feedback_type: FeedbackType, content_type: str):
        """Update daily feedback statistics"""
        stat_date = datetime.now().strftime('%Y-%m-%d')

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get or create stats for today
        cursor.execute("""
            INSERT OR IGNORE INTO feedback_stats (stat_date, by_content_type, by_category)
            VALUES (?, '{}', '{}')
        """, (stat_date,))

        # Increment counters
        cursor.execute("""
            UPDATE feedback_stats
            SET total_feedback = total_feedback + 1
            WHERE stat_date = ?
        """, (stat_date,))

        if feedback_type == FeedbackType.FALSE_POSITIVE:
            cursor.execute("""
                UPDATE feedback_stats
                SET false_positives = false_positives + 1
                WHERE stat_date = ?
            """, (stat_date,))
        elif feedback_type == FeedbackType.FALSE_NEGATIVE:
            cursor.execute("""
                UPDATE feedback_stats
                SET false_negatives = false_negatives + 1
                WHERE stat_date = ?
            """, (stat_date,))
        elif feedback_type == FeedbackType.CORRECT:
            cursor.execute("""
                UPDATE feedback_stats
                SET correct_decisions = correct_decisions + 1
                WHERE stat_date = ?
            """, (stat_date,))

        conn.commit()
        conn.close()

    def get_training_dataset(self,
                            content_type: Optional[str] = None,
                            feedback_type: Optional[FeedbackType] = None,
                            min_quality_score: Optional[float] = None,
                            exclude_used: bool = False,
                            limit: int = 1000) -> List[TrainingExample]:
        """
        Get training examples for model retraining

        Args:
            content_type: Filter by content type
            feedback_type: Filter by feedback type
            min_quality_score: Minimum quality score
            exclude_used: Exclude already used examples
            limit: Maximum number of examples

        Returns:
            List of training examples
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM training_examples WHERE 1=1"
        params = []

        if content_type:
            query += " AND content_type = ?"
            params.append(content_type)

        if feedback_type:
            query += " AND feedback_type = ?"
            params.append(feedback_type.value)

        if min_quality_score is not None:
            query += " AND quality_score >= ?"
            params.append(min_quality_score)

        if exclude_used:
            query += " AND used_in_training = 0"

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        conn.close()

        # Convert to TrainingExample objects
        examples = []
        columns = [
            'example_id', 'job_id', 'content_type', 'content_hash', 'asset_path',
            'original_decision', 'original_risk_level', 'original_scores',
            'feedback_type', 'correct_label', 'correct_categories', 'feedback_source',
            'created_at', 'reviewed_by', 'notes',
            'used_in_training', 'training_runs', 'quality_score'
        ]

        for row in rows:
            data = dict(zip(columns, row))

            # Parse JSON fields
            data['original_scores'] = json.loads(data['original_scores'])
            data['correct_categories'] = json.loads(data['correct_categories'])
            data['training_runs'] = json.loads(data['training_runs'])
            data['used_in_training'] = bool(data['used_in_training'])

            examples.append(TrainingExample(**data))

        return examples

    def mark_as_used(self, example_ids: List[str], run_id: str):
        """Mark examples as used in training run"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for example_id in example_ids:
            # Get current training_runs
            cursor.execute("""
                SELECT training_runs FROM training_examples WHERE example_id = ?
            """, (example_id,))

            row = cursor.fetchone()
            if row:
                runs = json.loads(row[0])
                runs.append(run_id)

                cursor.execute("""
                    UPDATE training_examples
                    SET used_in_training = 1,
                        training_runs = ?
                    WHERE example_id = ?
                """, (json.dumps(runs), example_id))

        conn.commit()
        conn.close()

        print(f"✓ Marked {len(example_ids)} examples as used in run {run_id}")

    def record_training_run(self,
                           model_type: str,
                           examples_count: int,
                           model_path: Optional[str] = None,
                           notes: Optional[str] = None) -> str:
        """Record a new training run"""
        run_id = f"run_{int(time.time())}"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO training_runs (
                run_id, started_at, model_type, examples_count,
                model_path, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            time.time(),
            model_type,
            examples_count,
            model_path,
            'in_progress',
            notes
        ))

        conn.commit()
        conn.close()

        print(f"✓ Started training run {run_id} with {examples_count} examples")

        return run_id

    def complete_training_run(self,
                             run_id: str,
                             performance_metrics: Dict[str, float],
                             model_path: str):
        """Mark training run as complete"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE training_runs
            SET completed_at = ?,
                performance_metrics = ?,
                model_path = ?,
                status = 'completed'
            WHERE run_id = ?
        """, (
            time.time(),
            json.dumps(performance_metrics),
            model_path,
            run_id
        ))

        conn.commit()
        conn.close()

        print(f"✓ Completed training run {run_id}")

    def get_stats(self) -> Dict:
        """Get retraining data statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total examples
        cursor.execute("SELECT COUNT(*) FROM training_examples")
        total_examples = cursor.fetchone()[0]

        # By feedback type
        cursor.execute("""
            SELECT feedback_type, COUNT(*) 
            FROM training_examples 
            GROUP BY feedback_type
        """)
        by_feedback = dict(cursor.fetchall())

        # By content type
        cursor.execute("""
            SELECT content_type, COUNT(*) 
            FROM training_examples 
            GROUP BY content_type
        """)
        by_content = dict(cursor.fetchall())

        # Unused examples
        cursor.execute("""
            SELECT COUNT(*) FROM training_examples WHERE used_in_training = 0
        """)
        unused = cursor.fetchone()[0]

        # Training runs
        cursor.execute("SELECT COUNT(*) FROM training_runs")
        total_runs = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM training_runs WHERE status = 'completed'
        """)
        completed_runs = cursor.fetchone()[0]

        conn.close()

        return {
            'total_examples': total_examples,
            'unused_examples': unused,
            'by_feedback_type': by_feedback,
            'by_content_type': by_content,
            'training_runs': {
                'total': total_runs,
                'completed': completed_runs
            },
            'storage_path': self.asset_storage
        }

    def export_training_data(self,
                            output_dir: str,
                            content_type: Optional[str] = None,
                            format: str = 'coco') -> str:
        """
        Export training data in standard format

        Args:
            output_dir: Output directory
            content_type: Filter by content type
            format: Export format ('coco', 'yolo', 'tfrecord')

        Returns:
            Path to exported data
        """
        os.makedirs(output_dir, exist_ok=True)

        # Get examples
        examples = self.get_training_dataset(
            content_type=content_type,
            limit=100000
        )

        if format == 'coco':
            # Export in COCO format
            coco_data = {
                'images': [],
                'annotations': [],
                'categories': []
            }

            # Create categories
            categories = set()
            for ex in examples:
                categories.update(ex.correct_categories)

            for i, cat in enumerate(sorted(categories)):
                coco_data['categories'].append({
                    'id': i,
                    'name': cat
                })

            # Create images and annotations
            for i, ex in enumerate(examples):
                if ex.asset_path and os.path.exists(ex.asset_path):
                    coco_data['images'].append({
                        'id': i,
                        'file_name': os.path.basename(ex.asset_path),
                        'example_id': ex.example_id
                    })

                    # Copy asset
                    shutil.copy2(
                        ex.asset_path,
                        os.path.join(output_dir, os.path.basename(ex.asset_path))
                    )

            # Save annotations
            annotations_path = os.path.join(output_dir, 'annotations.json')
            with open(annotations_path, 'w') as f:
                json.dump(coco_data, f, indent=2)

            print(f"✓ Exported {len(examples)} examples to {output_dir}")

            return annotations_path

        else:
            raise ValueError(f"Unsupported format: {format}")


# Singleton instance
_retraining_store = None

def get_retraining_store() -> RetrainingDataStore:
    """Get global retraining data store"""
    global _retraining_store
    if _retraining_store is None:
        _retraining_store = RetrainingDataStore()
    return _retraining_store


if __name__ == '__main__':
    # Test retraining hooks
    store = RetrainingDataStore()

    # Add some feedback examples
    store.add_feedback(
        job_id='job-001',
        content_type='image',
        content_hash='abc123',
        asset_path=None,
        original_decision='block',
        original_risk_level='high',
        original_scores={'nudity': 0.85},
        feedback_type=FeedbackType.FALSE_POSITIVE,
        correct_label='safe',
        correct_categories=[],
        feedback_source='admin',
        reviewed_by='admin@example.com',
        notes='False positive - swimsuit photo, not nudity'
    )

    store.add_feedback(
        job_id='job-002',
        content_type='text',
        content_hash='def456',
        asset_path=None,
        original_decision='approve',
        original_risk_level='safe',
        original_scores={'hate_speech': 0.2},
        feedback_type=FeedbackType.FALSE_NEGATIVE,
        correct_label='block',
        correct_categories=['hate_speech'],
        feedback_source='user_report',
        notes='Subtle hate speech missed by detector'
    )

    # Get training dataset
    dataset = store.get_training_dataset(
        feedback_type=FeedbackType.FALSE_POSITIVE,
        limit=10
    )

    print(f"\n✓ Retrieved {len(dataset)} training examples")

    # Start training run
    run_id = store.record_training_run(
        model_type='nudity_detector',
        examples_count=len(dataset),
        notes='Retraining with false positive examples'
    )

    # Mark as used
    store.mark_as_used([ex.example_id for ex in dataset], run_id)

    # Complete training
    store.complete_training_run(
        run_id=run_id,
        performance_metrics={'accuracy': 0.95, 'precision': 0.92},
        model_path='models/nudity_detector_v2.pt'
    )

    # Show stats
    print("\n" + "="*60)
    print("Retraining Data Stats:")
    print(json.dumps(store.get_stats(), indent=2))

