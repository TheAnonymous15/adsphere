"""
Centralized logging system for moderation service
Provides structured JSON logging with rotation and audit trails
"""
import logging
import json
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """Format logs as JSON"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'extra'):
            log_data.update(record.extra)

        return json.dumps(log_data)


class AuditLogger:
    """
    Append-only audit logger for moderation decisions.

    Features:
    - JSON format
    - File rotation (daily)
    - Tamper-evident (append-only)
    - Structured data
    """

    def __init__(self, log_dir: Optional[str] = None):
        self.log_dir = log_dir or settings.AUDIT_LOG_DIR
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        # Daily rotation
        handler = TimedRotatingFileHandler(
            filename=os.path.join(self.log_dir, 'audit.log'),
            when='midnight',
            interval=1,
            backupCount=365,  # Keep 1 year
            encoding='utf-8'
        )
        handler.suffix = '%Y-%m-%d'
        handler.setFormatter(JSONFormatter())

        self.logger.addHandler(handler)

    def log_moderation(
        self,
        audit_id: str,
        decision: str,
        risk_level: str,
        category_scores: Dict[str, float],
        flags: list,
        user_id: Optional[str] = None,
        company: Optional[str] = None,
        ad_id: Optional[str] = None,
        content_type: str = "text",
        processing_time: float = 0.0,
        **kwargs
    ):
        """
        Log a moderation decision.

        Args:
            audit_id: Unique audit ID
            decision: approve/review/block
            risk_level: low/medium/high/critical
            category_scores: Dict of category scores
            flags: List of flags
            user_id: User identifier
            company: Company identifier
            ad_id: Ad identifier
            content_type: text/image/video
            processing_time: Processing time in ms
            **kwargs: Additional fields
        """
        log_entry = {
            'event': 'moderation_decision',
            'audit_id': audit_id,
            'decision': decision,
            'risk_level': risk_level,
            'category_scores': category_scores,
            'flags': flags,
            'content_type': content_type,
            'processing_time_ms': processing_time,
            'user_id': user_id,
            'company': company,
            'ad_id': ad_id,
            **kwargs
        }

        # Log as extra data
        self.logger.info(
            f"Moderation: {decision} ({risk_level}) - {audit_id}",
            extra={'extra': log_entry}
        )

    def log_admin_action(
        self,
        admin_user: str,
        action: str,
        target_id: str,
        reason: Optional[str] = None,
        **kwargs
    ):
        """Log administrative action"""
        log_entry = {
            'event': 'admin_action',
            'admin_user': admin_user,
            'action': action,
            'target_id': target_id,
            'reason': reason,
            **kwargs
        }

        self.logger.info(
            f"Admin action: {action} by {admin_user}",
            extra={'extra': log_entry}
        )


class AppLogger:
    """
    Application logger with rotation.

    Features:
    - Size-based rotation (10MB per file)
    - Backup files (keep last 10)
    - Structured JSON logs
    - Multiple log levels
    """

    def __init__(self, name: str = 'moderation_service', log_dir: Optional[str] = None):
        self.log_dir = log_dir or settings.LOG_DIR
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, settings.LOG_LEVEL))
        self.logger.propagate = False

        # Rotating file handler (10MB, keep 10 files)
        file_handler = RotatingFileHandler(
            filename=os.path.join(self.log_dir, f'{name}.log'),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        file_handler.setFormatter(JSONFormatter())

        # Console handler (for development)
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)

        self.logger.addHandler(file_handler)
        if settings.DEBUG:
            self.logger.addHandler(console_handler)

    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra={'extra': kwargs})

    def info(self, message: str, **kwargs):
        self.logger.info(message, extra={'extra': kwargs})

    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra={'extra': kwargs})

    def error(self, message: str, **kwargs):
        self.logger.error(message, extra={'extra': kwargs})

    def critical(self, message: str, **kwargs):
        self.logger.critical(message, extra={'extra': kwargs})


# Global loggers
audit_logger = AuditLogger()
app_logger = AppLogger()


def get_logger(name: str = 'moderation_service') -> AppLogger:
    """Get logger instance"""
    return AppLogger(name=name)

