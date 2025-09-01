#!/usr/bin/env python3
"""
Desktop State Manager - Configuration Management

Provides centralized configuration management with:
- User-customizable settings
- Default fallbacks
- Validation and schema checking
- Runtime configuration updates
- Export/import functionality
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict, field

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


@dataclass
class TimingConfig:
    """Configuration for timing and delays"""
    app_launch_delay: float = 2.0  # seconds between app launches
    window_init_delay: float = 5.0  # seconds to wait for apps to initialize
    tiling_settle_delay: float = 5.0  # seconds for TilingShell to settle
    window_operation_delay: float = 0.5  # seconds between window operations
    workspace_creation_delay: float = 3.0  # seconds for workspace creation
    manual_positioning_delay: float = 1.0  # seconds before manual positioning


@dataclass
class ApplicationConfig:
    """Configuration for application detection and handling"""
    enable_flatpak_detection: bool = True
    enable_snap_detection: bool = True
    filter_helper_processes: bool = True
    confidence_threshold: int = 20  # minimum confidence score for window matching
    retry_attempts: int = 3
    timeout_seconds: int = 30
    
    # Application-specific command mappings
    command_mappings: Dict[str, List[str]] = field(default_factory=lambda: {
        "firefox": ["firefox", "firefox-bin"],
        "chrome": ["google-chrome", "chrome", "chromium"],
        "chromium": ["chromium-browser", "chromium"],
        "code": ["code", "codium", "vscodium"],
        "gedit": ["gedit", "gnome-text-editor"],
        "nautilus": ["nautilus", "gnome-files"],
        "gnome-terminal": ["gnome-terminal", "terminal"],
        "telegram": ["telegram-desktop", "telegram"],
        "discord": ["discord"],
        "slack": ["slack"],
        "spotify": ["spotify"]
    })


@dataclass
class BackupConfig:
    """Configuration for backup and state management"""
    max_backup_count: int = 5
    enable_compression: bool = True
    backup_tilingshell: bool = True
    backup_rotation_days: int = 30
    auto_backup_before_restore: bool = True


@dataclass
class UIConfig:
    """Configuration for user interface"""
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    show_progress_bars: bool = True
    use_colored_output: bool = True
    confirm_destructive_actions: bool = True
    toast_timeout: int = 3  # seconds
    window_default_size: tuple = (600, 500)


@dataclass
class SystemConfig:
    """Configuration for system integration"""
    enable_systemd_service: bool = False
    service_delay_seconds: int = 15
    check_dependencies: bool = True
    validate_before_restore: bool = True
    create_desktop_entry: bool = True


@dataclass
class DSMConfig:
    """Main Desktop State Manager Configuration"""
    version: str = "3.5.0"
    timing: TimingConfig = field(default_factory=TimingConfig)
    applications: ApplicationConfig = field(default_factory=ApplicationConfig)
    backup: BackupConfig = field(default_factory=BackupConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    
    # Custom user settings (for extensions)
    custom: Dict[str, Any] = field(default_factory=dict)


class ConfigManager:
    """Manages configuration loading, saving, and validation"""
    
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "version": {"type": "string"},
            "timing": {
                "type": "object",
                "properties": {
                    "app_launch_delay": {"type": "number", "minimum": 0, "maximum": 10},
                    "window_init_delay": {"type": "number", "minimum": 0, "maximum": 30},
                    "tiling_settle_delay": {"type": "number", "minimum": 0, "maximum": 30},
                    "window_operation_delay": {"type": "number", "minimum": 0, "maximum": 5},
                    "workspace_creation_delay": {"type": "number", "minimum": 0, "maximum": 10},
                    "manual_positioning_delay": {"type": "number", "minimum": 0, "maximum": 5}
                }
            },
            "applications": {
                "type": "object",
                "properties": {
                    "enable_flatpak_detection": {"type": "boolean"},
                    "enable_snap_detection": {"type": "boolean"},
                    "filter_helper_processes": {"type": "boolean"},
                    "confidence_threshold": {"type": "integer", "minimum": 0, "maximum": 100},
                    "retry_attempts": {"type": "integer", "minimum": 1, "maximum": 10},
                    "timeout_seconds": {"type": "integer", "minimum": 5, "maximum": 300}
                }
            },
            "backup": {
                "type": "object", 
                "properties": {
                    "max_backup_count": {"type": "integer", "minimum": 1, "maximum": 50},
                    "enable_compression": {"type": "boolean"},
                    "backup_tilingshell": {"type": "boolean"},
                    "backup_rotation_days": {"type": "integer", "minimum": 1, "maximum": 365}
                }
            },
            "ui": {
                "type": "object",
                "properties": {
                    "log_level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]},
                    "show_progress_bars": {"type": "boolean"},
                    "use_colored_output": {"type": "boolean"},
                    "toast_timeout": {"type": "integer", "minimum": 1, "maximum": 10}
                }
            }
        }
    }
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".config" / "desktop-restore"
        self.config_file = self.config_dir / "config.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self._config: Optional[DSMConfig] = None
        
    def load_config(self) -> DSMConfig:
        """Load configuration from file or create default"""
        if self._config is not None:
            return self._config
            
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Validate against schema
                self._validate_config(data)
                
                # Convert to config object
                self._config = self._dict_to_config(data)
                
            except Exception as e:
                print(f"Warning: Invalid config file ({e}), using defaults")
                self._config = DSMConfig()
                self.save_config()  # Save corrected default config
        else:
            # Create default config
            self._config = DSMConfig()
            self.save_config()
            
        return self._config
    
    def save_config(self, config: Optional[DSMConfig] = None) -> bool:
        """Save configuration to file"""
        config_to_save = config or self._config or DSMConfig()
        
        try:
            # Convert to dict and save
            config_dict = asdict(config_to_save)
            
            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=2, default=str)
                
            self._config = config_to_save
            return True
            
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def _validate_config(self, config_dict: Dict[str, Any]) -> None:
        """Validate configuration against schema"""
        if not HAS_JSONSCHEMA:
            # Basic validation without jsonschema
            return
            
        try:
            jsonschema.validate(config_dict, self.CONFIG_SCHEMA)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Configuration validation failed: {e.message}")
    
    def _dict_to_config(self, data: Dict[str, Any]) -> DSMConfig:
        """Convert dictionary to DSMConfig object"""
        # Handle nested objects
        timing = TimingConfig(**data.get('timing', {}))
        applications = ApplicationConfig(**data.get('applications', {}))
        backup = BackupConfig(**data.get('backup', {}))
        ui = UIConfig(**data.get('ui', {}))
        system = SystemConfig(**data.get('system', {}))
        
        return DSMConfig(
            version=data.get('version', '3.5.0'),
            timing=timing,
            applications=applications,
            backup=backup,
            ui=ui,
            system=system,
            custom=data.get('custom', {})
        )
    
    def get_config(self) -> DSMConfig:
        """Get current configuration"""
        return self.load_config()
    
    def update_config(self, **kwargs) -> bool:
        """Update specific configuration values"""
        config = self.get_config()
        
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
            elif '.' in key:
                # Handle nested updates like 'timing.app_launch_delay'
                parts = key.split('.')
                obj = config
                for part in parts[:-1]:
                    if hasattr(obj, part):
                        obj = getattr(obj, part)
                    else:
                        break
                else:
                    if hasattr(obj, parts[-1]):
                        setattr(obj, parts[-1], value)
        
        return self.save_config(config)
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to default values"""
        self._config = DSMConfig()
        return self.save_config()
    
    def export_config(self, export_path: Path) -> bool:
        """Export current configuration to a file"""
        config = self.get_config()
        try:
            with open(export_path, 'w') as f:
                json.dump(asdict(config), f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error exporting config: {e}")
            return False
    
    def import_config(self, import_path: Path) -> bool:
        """Import configuration from a file"""
        try:
            with open(import_path, 'r') as f:
                data = json.load(f)
            
            self._validate_config(data)
            config = self._dict_to_config(data)
            return self.save_config(config)
            
        except Exception as e:
            print(f"Error importing config: {e}")
            return False
    
    def get_timing_config(self) -> TimingConfig:
        """Get timing configuration"""
        return self.get_config().timing
    
    def get_application_config(self) -> ApplicationConfig:
        """Get application configuration"""
        return self.get_config().applications
    
    def get_backup_config(self) -> BackupConfig:
        """Get backup configuration"""
        return self.get_config().backup
    
    def get_ui_config(self) -> UIConfig:
        """Get UI configuration"""
        return self.get_config().ui
    
    def get_system_config(self) -> SystemConfig:
        """Get system configuration"""
        return self.get_config().system


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global config manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> DSMConfig:
    """Get current configuration - convenience function"""
    return get_config_manager().get_config()


# Example usage and testing
if __name__ == "__main__":
    # Test configuration system
    config_mgr = ConfigManager()
    
    # Load/create config
    config = config_mgr.get_config()
    print(f"Loaded config version: {config.version}")
    print(f"App launch delay: {config.timing.app_launch_delay}s")
    print(f"Flatpak detection: {config.applications.enable_flatpak_detection}")
    print(f"Max backups: {config.backup.max_backup_count}")
    print(f"Log level: {config.ui.log_level}")
    
    # Test config update
    config_mgr.update_config(version="3.5.1")
    updated_config = config_mgr.get_config()
    print(f"Updated version: {updated_config.version}")
    
    # Test nested update
    config_mgr.update_config(**{"timing.app_launch_delay": 1.5})
    updated_config = config_mgr.get_config()
    print(f"Updated app launch delay: {updated_config.timing.app_launch_delay}s")
    
    print(f"Config file location: {config_mgr.config_file}")
