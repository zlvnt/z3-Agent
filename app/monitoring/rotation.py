"""
Log rotation untuk monitoring files.
Handles automatic rotation berdasarkan size atau time.
"""

import os
import gzip
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


class LogRotator:
    """
    Simple log rotation for monitoring files.
    Supports size-based dan time-based rotation.
    """
    
    def __init__(
        self,
        log_file: str = "logs/monitoring.jsonl",
        max_size_mb: float = 10.0,
        max_files: int = 5,
        compress: bool = True
    ):
        self.log_file = Path(log_file)
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.max_files = max_files
        self.compress = compress
        
        # Ensure logs directory exists
        self.log_file.parent.mkdir(exist_ok=True)
    
    def should_rotate(self) -> bool:
        """Check if log file should be rotated"""
        if not self.log_file.exists():
            return False
            
        return self.log_file.stat().st_size > self.max_size_bytes
    
    def rotate_now(self) -> bool:
        """
        Perform log rotation.
        Returns True if rotation was performed.
        """
        if not self.log_file.exists():
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Create rotated filename
            if self.compress:
                rotated_name = f"{self.log_file.stem}_{timestamp}.jsonl.gz"
                rotated_path = self.log_file.parent / rotated_name
                
                # Compress and move
                with open(self.log_file, 'rb') as f_in:
                    with gzip.open(rotated_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                rotated_name = f"{self.log_file.stem}_{timestamp}.jsonl"
                rotated_path = self.log_file.parent / rotated_name
                shutil.move(self.log_file, rotated_path)
            
            # Remove old log file if compression was used
            if self.compress and self.log_file.exists():
                self.log_file.unlink()
            
            # Clean up old rotated files
            self._cleanup_old_files()
            
            print(f"✓ Log rotated: {rotated_name}")
            return True
            
        except Exception as e:
            print(f"ERROR: Log rotation failed: {e}")
            return False
    
    def _cleanup_old_files(self) -> None:
        """Remove old rotated files beyond max_files limit"""
        try:
            # Find all rotated files
            pattern = f"{self.log_file.stem}_*.jsonl*"
            rotated_files = list(self.log_file.parent.glob(pattern))
            
            # Sort by modification time (oldest first)
            rotated_files.sort(key=lambda f: f.stat().st_mtime)
            
            # Remove oldest files if we exceed limit
            while len(rotated_files) > self.max_files:
                old_file = rotated_files.pop(0)
                old_file.unlink()
                print(f"✓ Removed old log: {old_file.name}")
                
        except Exception as e:
            print(f"WARNING: Cleanup failed: {e}")
    
    def auto_rotate_if_needed(self) -> bool:
        """
        Check and rotate if needed.
        Can be called before each log write.
        """
        if self.should_rotate():
            return self.rotate_now()
        return False
    
    def get_status(self) -> dict:
        """Get rotation status information"""
        if not self.log_file.exists():
            return {
                "current_size_mb": 0,
                "max_size_mb": self.max_size_bytes / (1024 * 1024),
                "needs_rotation": False,
                "rotated_files_count": 0
            }
        
        current_size = self.log_file.stat().st_size
        pattern = f"{self.log_file.stem}_*.jsonl*"
        rotated_files = list(self.log_file.parent.glob(pattern))
        
        return {
            "current_size_mb": round(current_size / (1024 * 1024), 2),
            "max_size_mb": self.max_size_bytes / (1024 * 1024),
            "needs_rotation": current_size > self.max_size_bytes,
            "rotated_files_count": len(rotated_files),
            "total_log_files": len(rotated_files) + 1
        }


# Global rotator instance
_rotator_instance: Optional[LogRotator] = None


def get_log_rotator() -> LogRotator:
    """Get or create global log rotator instance"""
    global _rotator_instance
    if _rotator_instance is None:
        _rotator_instance = LogRotator()
    return _rotator_instance


def auto_rotate_logs() -> bool:
    """Convenience function for auto rotation"""
    rotator = get_log_rotator()
    return rotator.auto_rotate_if_needed()


def force_rotate_logs() -> bool:
    """Convenience function for forced rotation"""
    rotator = get_log_rotator()
    return rotator.rotate_now()