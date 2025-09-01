#!/usr/bin/env python3
"""
Desktop State Manager - Centralized Logging Module

Provides unified logging functionality across all components with:
- Multiple log levels and outputs
- Structured logging with context
- Performance monitoring
- User-friendly console output
- Debug file logging
"""

import logging
import logging.handlers
import os
import sys
import time
from datetime import datetime
from pathlib import Path
import json


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for better readability"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    SYMBOLS = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️ ',
        'WARNING': '⚠️ ',
        'ERROR': '❌',
        'CRITICAL': '🚨'
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        reset_color = self.COLORS['RESET']
        symbol = self.SYMBOLS.get(record.levelname, '')
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # Format message with color and symbol
        formatted_message = f"{log_color}{symbol} [{timestamp}] {record.getMessage()}{reset_color}"
        
        if record.exc_info:
            formatted_message += f"\n{self.formatException(record.exc_info)}"
            
        return formatted_message


class PerformanceContext:
    """Context manager for timing operations"""
    
    def __init__(self, logger, operation_name):
        self.logger = logger
        self.operation_name = operation_name
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        self.logger.debug(f"Starting: {self.operation_name}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if exc_type is None:
            self.logger.info(f"Completed: {self.operation_name} ({duration:.2f}s)")
        else:
            self.logger.error(f"Failed: {self.operation_name} after {duration:.2f}s - {exc_val}")


class DSMLogger:
    """Desktop State Manager Logger - Centralized logging for all components"""
    
    def __init__(self, component_name="dsm", log_level=logging.INFO):
        self.component_name = component_name
        self.config_dir = Path.home() / ".config" / "desktop-restore"
        self.log_dir = self.config_dir / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger(f"desktop_state_manager.{component_name}")
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
        
        # Performance tracking
        self.operation_times = {}
        
    def _setup_handlers(self):
        """Setup logging handlers for console and file output"""
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ColoredFormatter())
        self.logger.addHandler(console_handler)
        
        # File handler with rotation
        log_file = self.log_dir / f"{self.component_name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=1024*1024, backupCount=5  # 1MB per file, 5 backups
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Error file handler for errors only
        error_file = self.log_dir / f"{self.component_name}_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file, maxBytes=512*1024, backupCount=3  # 512KB per file, 3 backups
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        self.logger.addHandler(error_handler)
    
    def debug(self, message, extra_context=None):
        """Log debug message with optional context"""
        if extra_context:
            message = f"{message} | Context: {json.dumps(extra_context, default=str)}"
        self.logger.debug(message)
    
    def info(self, message, extra_context=None):
        """Log info message with optional context"""
        if extra_context:
            message = f"{message} | Context: {json.dumps(extra_context, default=str)}"
        self.logger.info(message)
    
    def warning(self, message, extra_context=None):
        """Log warning message with optional context"""
        if extra_context:
            message = f"{message} | Context: {json.dumps(extra_context, default=str)}"
        self.logger.warning(message)
    
    def error(self, message, exception=None, extra_context=None):
        """Log error message with optional exception and context"""
        if extra_context:
            message = f"{message} | Context: {json.dumps(extra_context, default=str)}"
        
        if exception:
            self.logger.error(message, exc_info=exception)
        else:
            self.logger.error(message)
    
    def critical(self, message, exception=None, extra_context=None):
        """Log critical message with optional exception and context"""
        if extra_context:
            message = f"{message} | Context: {json.dumps(extra_context, default=str)}"
        
        if exception:
            self.logger.critical(message, exc_info=exception)
        else:
            self.logger.critical(message)
    
    def time_operation(self, operation_name):
        """Create a performance timing context manager"""
        return PerformanceContext(self.logger, operation_name)
    
    def log_system_info(self):
        """Log current system information for debugging"""
        system_info = {
            'desktop_environment': os.environ.get('XDG_CURRENT_DESKTOP', 'Unknown'),
            'display': os.environ.get('DISPLAY', 'Not set'),
            'session_type': os.environ.get('XDG_SESSION_TYPE', 'Unknown'),
            'python_version': sys.version.split()[0],
            'config_dir': str(self.config_dir),
            'log_dir': str(self.log_dir)
        }
        
        self.info("System information captured", system_info)
        return system_info
    
    def log_state_summary(self, state_data):
        """Log a summary of saved state data"""
        if not state_data:
            self.warning("No state data to summarize")
            return
            
        summary = {
            'timestamp': state_data.get('timestamp', 'Unknown'),
            'workspace_count': state_data.get('workspaces', {}).get('count', 0),
            'window_count': len(state_data.get('windows', [])),
            'application_count': len(state_data.get('applications', [])),
            'has_tilingshell_config': bool(state_data.get('tilingshell', {}))
        }
        
        # Count applications by type
        app_types = {}
        for app in state_data.get('applications', []):
            pkg_type = app.get('package_type', 'unknown')
            app_types[pkg_type] = app_types.get(pkg_type, 0) + 1
        
        summary['application_types'] = app_types
        
        self.info("Desktop state summary", summary)
        return summary
    
    def set_console_level(self, level):
        """Change console logging level dynamically"""
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                if level.upper() == 'DEBUG':
                    handler.setLevel(logging.DEBUG)
                elif level.upper() == 'INFO':
                    handler.setLevel(logging.INFO)
                elif level.upper() == 'WARNING':
                    handler.setLevel(logging.WARNING)
                elif level.upper() == 'ERROR':
                    handler.setLevel(logging.ERROR)
                break
                
        self.info(f"Console log level set to {level.upper()}")
    
    def get_log_files(self):
        """Return list of current log files"""
        log_files = []
        for log_file in self.log_dir.glob("*.log*"):
            if log_file.is_file():
                stat_info = log_file.stat()
                log_files.append({
                    'path': str(log_file),
                    'size': stat_info.st_size,
                    'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                })
        return log_files


# Convenience functions for easy importing
def get_logger(component_name="main", debug=False):
    """Get a logger instance for a specific component"""
    level = logging.DEBUG if debug else logging.INFO
    return DSMLogger(component_name, level)


def log_function_call(func):
    """Decorator to automatically log function calls"""
    def wrapper(*args, **kwargs):
        logger = get_logger("decorator")
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            with logger.time_operation(func.__name__):
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} completed successfully")
                return result
        except Exception as e:
            logger.error(f"{func.__name__} failed", e)
            raise
    
    return wrapper


# Example usage and testing
if __name__ == "__main__":
    # Test the logging system
    logger = get_logger("test")
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test performance timing
    with logger.time_operation("test_operation"):
        time.sleep(1)
    
    # Test system info logging
    logger.log_system_info()
    
    # Show log files
    print("\nLog files created:")
    for log_file in logger.get_log_files():
        print(f"  {log_file['path']} ({log_file['size']} bytes)")
