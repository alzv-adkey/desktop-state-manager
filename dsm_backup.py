#!/usr/bin/env python3
"""
Desktop State Manager - Backup and State Management

Provides advanced backup functionality with:
- Multiple state saves with automatic rotation
- Compression and space optimization
- Metadata tracking and search
- Backup restoration and validation
- Clean-up and maintenance operations
"""

import json
import gzip
import shutil
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess
import tempfile

try:
    from dsm_logger import get_logger
    from dsm_config import get_config
    HAS_DSM_MODULES = True
except ImportError:
    HAS_DSM_MODULES = False


class BackupManager:
    """Manages multiple desktop state backups with rotation and metadata"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".config" / "desktop-restore"
        self.backup_dir = self.config_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = self.backup_dir / "metadata.json"
        self.current_state_file = self.config_dir / "desktop-state.json"
        
        if HAS_DSM_MODULES:
            self.logger = get_logger("backup")
            self.config = get_config().backup
        else:
            self.logger = None
            # Default config if modules not available
            from types import SimpleNamespace
            self.config = SimpleNamespace(
                max_backup_count=5,
                enable_compression=True,
                backup_rotation_days=30,
                auto_backup_before_restore=True
            )
        
        self.metadata = self._load_metadata()
    
    def _log(self, level: str, message: str, **kwargs):
        """Helper method for logging"""
        if self.logger:
            getattr(self.logger, level.lower())(message, **kwargs)
        else:
            print(f"[{level.upper()}] {message}")
    
    def _load_metadata(self) -> Dict:
        """Load backup metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self._log("warning", f"Failed to load metadata: {e}")
        
        return {
            "version": "1.0",
            "backups": {},
            "last_cleanup": None,
            "statistics": {
                "total_backups_created": 0,
                "total_restores": 0,
                "last_backup": None,
                "last_restore": None
            }
        }
    
    def _save_metadata(self):
        """Save backup metadata"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except Exception as e:
            self._log("error", f"Failed to save metadata: {e}")
    
    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""
    
    def _compress_file(self, source: Path, destination: Path) -> bool:
        """Compress a file using gzip"""
        try:
            with open(source, 'rb') as f_in:
                with gzip.open(destination, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return True
        except Exception as e:
            self._log("error", f"Compression failed: {e}")
            return False
    
    def _decompress_file(self, source: Path, destination: Path) -> bool:
        """Decompress a gzip file"""
        try:
            with gzip.open(source, 'rb') as f_in:
                with open(destination, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return True
        except Exception as e:
            self._log("error", f"Decompression failed: {e}")
            return False
    
    def create_backup(self, name: Optional[str] = None, description: str = "") -> Optional[str]:
        """Create a new backup of the current state"""
        if not self.current_state_file.exists():
            self._log("error", "No current state file to backup")
            return None
        
        # Generate backup ID and name
        timestamp = datetime.now()
        backup_id = timestamp.strftime("%Y%m%d_%H%M%S")
        if name:
            backup_name = f"{backup_id}_{name}"
        else:
            backup_name = backup_id
        
        # Determine file extension based on compression setting
        if self.config.enable_compression:
            backup_filename = f"{backup_name}.json.gz"
            backup_path = self.backup_dir / backup_filename
        else:
            backup_filename = f"{backup_name}.json"
            backup_path = self.backup_dir / backup_filename
        
        try:
            # Load and validate current state
            with open(self.current_state_file, 'r') as f:
                state_data = json.load(f)
            
            # Create backup
            if self.config.enable_compression:
                success = self._compress_file(self.current_state_file, backup_path)
            else:
                shutil.copy2(self.current_state_file, backup_path)
                success = True
            
            if not success:
                return None
            
            # Calculate metadata
            file_size = backup_path.stat().st_size
            original_size = self.current_state_file.stat().st_size
            file_hash = self._calculate_hash(backup_path)
            
            # Count applications and windows
            app_count = len(state_data.get('applications', []))
            window_count = len(state_data.get('windows', []))
            workspace_count = state_data.get('workspaces', {}).get('count', 0)
            
            # Store metadata
            backup_metadata = {
                "id": backup_id,
                "name": backup_name,
                "filename": backup_filename,
                "created": timestamp.isoformat(),
                "description": description,
                "compressed": self.config.enable_compression,
                "file_size": file_size,
                "original_size": original_size,
                "compression_ratio": round((1 - file_size / original_size) * 100, 1) if self.config.enable_compression else 0,
                "hash": file_hash,
                "application_count": app_count,
                "window_count": window_count,
                "workspace_count": workspace_count,
                "state_timestamp": state_data.get('timestamp', ''),
                "tags": []
            }
            
            self.metadata["backups"][backup_id] = backup_metadata
            self.metadata["statistics"]["total_backups_created"] += 1
            self.metadata["statistics"]["last_backup"] = timestamp.isoformat()
            
            self._save_metadata()
            
            # Perform cleanup if needed
            self._cleanup_old_backups()
            
            self._log("info", f"Backup created: {backup_name} (ID: {backup_id}, Size: {file_size} bytes)")
            
            return backup_id
            
        except Exception as e:
            self._log("error", f"Failed to create backup: {e}")
            # Clean up partial backup
            if backup_path.exists():
                backup_path.unlink()
            return None
    
    def list_backups(self, limit: Optional[int] = None) -> List[Dict]:
        """List available backups with metadata"""
        backups = []
        for backup_id, metadata in self.metadata["backups"].items():
            # Check if backup file still exists
            backup_path = self.backup_dir / metadata["filename"]
            if backup_path.exists():
                backup_info = metadata.copy()
                backup_info["exists"] = True
                backup_info["age_days"] = (datetime.now() - datetime.fromisoformat(metadata["created"])).days
                backups.append(backup_info)
            else:
                self._log("warning", f"Backup file missing: {metadata['filename']}")
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x["created"], reverse=True)
        
        if limit:
            backups = backups[:limit]
        
        return backups
    
    def get_backup_info(self, backup_id: str) -> Optional[Dict]:
        """Get detailed information about a specific backup"""
        if backup_id not in self.metadata["backups"]:
            return None
        
        metadata = self.metadata["backups"][backup_id].copy()
        backup_path = self.backup_dir / metadata["filename"]
        
        metadata["exists"] = backup_path.exists()
        metadata["age_days"] = (datetime.now() - datetime.fromisoformat(metadata["created"])).days
        
        if backup_path.exists():
            metadata["current_file_size"] = backup_path.stat().st_size
        
        return metadata
    
    def restore_backup(self, backup_id: str, validate: bool = True) -> bool:
        """Restore a specific backup"""
        if backup_id not in self.metadata["backups"]:
            self._log("error", f"Backup not found: {backup_id}")
            return False
        
        backup_metadata = self.metadata["backups"][backup_id]
        backup_path = self.backup_dir / backup_metadata["filename"]
        
        if not backup_path.exists():
            self._log("error", f"Backup file not found: {backup_metadata['filename']}")
            return False
        
        try:
            # Create automatic backup before restore if enabled
            if self.config.auto_backup_before_restore and self.current_state_file.exists():
                auto_backup_id = self.create_backup(
                    name="auto_before_restore",
                    description=f"Automatic backup before restoring {backup_id}"
                )
                if auto_backup_id:
                    self._log("info", f"Created automatic backup: {auto_backup_id}")
            
            # Create temporary file for decompression/validation
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
                temp_path = Path(temp_file.name)
            
            try:
                # Decompress or copy the backup
                if backup_metadata["compressed"]:
                    success = self._decompress_file(backup_path, temp_path)
                else:
                    shutil.copy2(backup_path, temp_path)
                    success = True
                
                if not success:
                    return False
                
                # Validate the restored file if requested
                if validate:
                    try:
                        with open(temp_path, 'r') as f:
                            restored_data = json.load(f)
                        
                        # Basic validation
                        required_keys = ['timestamp', 'workspaces', 'windows', 'applications']
                        for key in required_keys:
                            if key not in restored_data:
                                raise ValueError(f"Missing required key: {key}")
                        
                        self._log("info", "Backup validation passed")
                    
                    except Exception as e:
                        self._log("error", f"Backup validation failed: {e}")
                        return False
                
                # Replace current state file
                shutil.move(str(temp_path), str(self.current_state_file))
                
                # Update statistics
                self.metadata["statistics"]["total_restores"] += 1
                self.metadata["statistics"]["last_restore"] = datetime.now().isoformat()
                self._save_metadata()
                
                self._log("info", f"Successfully restored backup: {backup_id}")
                return True
                
            finally:
                # Clean up temporary file
                if temp_path.exists():
                    temp_path.unlink()
        
        except Exception as e:
            self._log("error", f"Failed to restore backup: {e}")
            return False
    
    def delete_backup(self, backup_id: str) -> bool:
        """Delete a specific backup"""
        if backup_id not in self.metadata["backups"]:
            self._log("error", f"Backup not found: {backup_id}")
            return False
        
        backup_metadata = self.metadata["backups"][backup_id]
        backup_path = self.backup_dir / backup_metadata["filename"]
        
        try:
            if backup_path.exists():
                backup_path.unlink()
            
            del self.metadata["backups"][backup_id]
            self._save_metadata()
            
            self._log("info", f"Deleted backup: {backup_id}")
            return True
        
        except Exception as e:
            self._log("error", f"Failed to delete backup: {e}")
            return False
    
    def _cleanup_old_backups(self):
        """Clean up old backups based on configuration"""
        backups = self.list_backups()
        
        # Remove excess backups (keep only max_backup_count)
        if len(backups) > self.config.max_backup_count:
            excess_backups = backups[self.config.max_backup_count:]
            for backup in excess_backups:
                self.delete_backup(backup["id"])
        
        # Remove backups older than rotation_days
        cutoff_date = datetime.now() - timedelta(days=self.config.backup_rotation_days)
        for backup in backups:
            backup_date = datetime.fromisoformat(backup["created"])
            if backup_date < cutoff_date:
                self.delete_backup(backup["id"])
        
        self.metadata["last_cleanup"] = datetime.now().isoformat()
        self._save_metadata()
    
    def get_statistics(self) -> Dict:
        """Get backup system statistics"""
        backups = self.list_backups()
        
        total_size = sum(backup["file_size"] for backup in backups)
        total_original_size = sum(backup["original_size"] for backup in backups)
        
        stats = self.metadata["statistics"].copy()
        stats.update({
            "active_backups": len(backups),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_original_size_mb": round(total_original_size / (1024 * 1024), 2),
            "average_compression": round((1 - total_size / total_original_size) * 100, 1) if total_original_size > 0 else 0,
            "oldest_backup": min((b["created"] for b in backups), default=None),
            "newest_backup": max((b["created"] for b in backups), default=None)
        })
        
        return stats
    
    def search_backups(self, query: str = "", tag: str = "", 
                      min_apps: int = 0, max_age_days: Optional[int] = None) -> List[Dict]:
        """Search backups based on criteria"""
        backups = self.list_backups()
        results = []
        
        for backup in backups:
            # Text search in name and description
            if query and query.lower() not in f"{backup['name']} {backup['description']}".lower():
                continue
            
            # Tag search
            if tag and tag not in backup.get('tags', []):
                continue
            
            # Minimum applications filter
            if backup["application_count"] < min_apps:
                continue
            
            # Age filter
            if max_age_days is not None and backup["age_days"] > max_age_days:
                continue
            
            results.append(backup)
        
        return results
    
    def add_backup_tag(self, backup_id: str, tag: str) -> bool:
        """Add a tag to a backup"""
        if backup_id not in self.metadata["backups"]:
            return False
        
        tags = self.metadata["backups"][backup_id].get("tags", [])
        if tag not in tags:
            tags.append(tag)
            self.metadata["backups"][backup_id]["tags"] = tags
            self._save_metadata()
        
        return True
    
    def remove_backup_tag(self, backup_id: str, tag: str) -> bool:
        """Remove a tag from a backup"""
        if backup_id not in self.metadata["backups"]:
            return False
        
        tags = self.metadata["backups"][backup_id].get("tags", [])
        if tag in tags:
            tags.remove(tag)
            self.metadata["backups"][backup_id]["tags"] = tags
            self._save_metadata()
        
        return True


# Example usage and testing
if __name__ == "__main__":
    # Test backup functionality
    backup_mgr = BackupManager()
    
    print("=== Desktop State Manager - Backup System Test ===")
    
    # Show statistics
    stats = backup_mgr.get_statistics()
    print(f"Current statistics:")
    print(f"  Active backups: {stats['active_backups']}")
    print(f"  Total backups created: {stats['total_backups_created']}")
    print(f"  Total size: {stats['total_size_mb']:.2f} MB")
    
    # List existing backups
    backups = backup_mgr.list_backups(limit=5)
    print(f"\nRecent backups ({len(backups)}):")
    for backup in backups:
        print(f"  {backup['id']}: {backup['name']} ({backup['age_days']} days old)")
    
    # Test creating a backup (if current state exists)
    if backup_mgr.current_state_file.exists():
        print(f"\nCreating test backup...")
        backup_id = backup_mgr.create_backup(
            name="test_backup",
            description="Test backup created by backup system"
        )
        if backup_id:
            print(f"✅ Created backup: {backup_id}")
        else:
            print("❌ Failed to create backup")
    else:
        print("\n⚠️  No current state file found, skipping backup creation test")
    
    print(f"\n✅ Backup system test completed")
