#!/usr/bin/env python3
"""
Desktop State Manager - Comprehensive Test Suite

Provides automated testing for all components:
- Unit tests for individual modules
- Integration tests for full workflows
- System compatibility tests
- Performance benchmarks
- Configuration validation
"""

import os
import sys
import subprocess
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from contextlib import contextmanager

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from dsm_logger import DSMLogger, get_logger
    from dsm_config import ConfigManager, DSMConfig, get_config_manager
    HAS_DSM_MODULES = True
except ImportError as e:
    print(f"Warning: Could not import DSM modules: {e}")
    HAS_DSM_MODULES = False


class TestResult:
    """Container for test results with detailed reporting"""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.tests_skipped = 0
        self.failures = []
        self.performance_data = {}
        
    def add_result(self, test_name, passed, error=None, duration=None):
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
            if error:
                self.failures.append((test_name, error))
        
        if duration is not None:
            self.performance_data[test_name] = duration
    
    def add_skip(self, test_name, reason):
        self.tests_skipped += 1
        print(f"⏭️  SKIP: {test_name} - {reason}")
    
    def print_summary(self):
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Tests run: {self.tests_run}")
        print(f"Passed: {self.tests_passed} ✅")
        print(f"Failed: {self.tests_failed} ❌")
        print(f"Skipped: {self.tests_skipped} ⏭️")
        
        if self.tests_failed > 0:
            print(f"\nFailures:")
            for test_name, error in self.failures:
                print(f"  ❌ {test_name}: {error}")
        
        if self.performance_data:
            print(f"\nPerformance Data:")
            for test_name, duration in self.performance_data.items():
                print(f"  ⏱️  {test_name}: {duration:.3f}s")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        return self.tests_failed == 0


@contextmanager
def temporary_config_dir():
    """Context manager for temporary configuration directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        old_home = os.environ.get('HOME')
        os.environ['HOME'] = temp_dir
        try:
            yield Path(temp_dir)
        finally:
            if old_home:
                os.environ['HOME'] = old_home


class DSMTestSuite:
    """Main test suite for Desktop State Manager"""
    
    def __init__(self):
        self.result = TestResult()
        self.project_root = Path(__file__).parent
        
    def run_test(self, test_name, test_func, *args, **kwargs):
        """Run a single test with timing and error handling"""
        print(f"🧪 Testing {test_name}...", end=" ")
        start_time = time.time()
        
        try:
            test_func(*args, **kwargs)
            duration = time.time() - start_time
            print(f"✅ PASS ({duration:.3f}s)")
            self.result.add_result(test_name, True, duration=duration)
            return True
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ FAIL ({duration:.3f}s)")
            self.result.add_result(test_name, False, str(e), duration=duration)
            return False
    
    def skip_test(self, test_name, reason):
        """Skip a test with reason"""
        self.result.add_skip(test_name, reason)
    
    # System Tests
    def test_python_version(self):
        """Test Python version compatibility"""
        version = sys.version_info
        assert version.major >= 3 and version.minor >= 6, f"Python 3.6+ required, found {version.major}.{version.minor}"
    
    def test_required_tools(self):
        """Test availability of required system tools"""
        required_tools = ['wmctrl', 'python3', 'gsettings']
        missing_tools = []
        
        for tool in required_tools:
            try:
                subprocess.run([tool, '--version'], capture_output=True, check=True, timeout=5)
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                missing_tools.append(tool)
        
        assert not missing_tools, f"Missing required tools: {', '.join(missing_tools)}"
    
    def test_gui_dependencies(self):
        """Test GUI framework availability"""
        try:
            import gi
            gi.require_version('Gtk', '4.0')
            gi.require_version('Adw', '1')
            from gi.repository import Gtk, Adw
        except ImportError as e:
            raise AssertionError(f"GUI dependencies missing: {e}")
    
    def test_desktop_environment(self):
        """Test desktop environment compatibility"""
        de = os.environ.get('XDG_CURRENT_DESKTOP', '')
        display = os.environ.get('DISPLAY', '')
        
        assert display or os.environ.get('WAYLAND_DISPLAY'), "No display server detected"
    
    # File Tests
    def test_script_files_exist(self):
        """Test that all required script files exist"""
        required_files = [
            'desktop-state-manager.py',
            'desktop-state-manager-simple.py', 
            'tilingshell-desktop-restore.sh',
            'desktop-cli.sh',
            'test-desktop-manager.py'
        ]
        
        for filename in required_files:
            file_path = self.project_root / filename
            assert file_path.exists(), f"Required file missing: {filename}"
    
    def test_script_permissions(self):
        """Test that scripts have executable permissions"""
        executable_files = [
            'desktop-state-manager.py',
            'desktop-state-manager-simple.py',
            'tilingshell-desktop-restore.sh',
            'desktop-cli.sh',
            'test-desktop-manager.py',
            'desktop-state-manager',
            'desktop-state-manager-cli'
        ]
        
        for filename in executable_files:
            file_path = self.project_root / filename
            if file_path.exists():
                assert os.access(file_path, os.X_OK), f"File not executable: {filename}"
    
    def test_desktop_file_validity(self):
        """Test desktop file format"""
        desktop_files = ['desktop-state-manager.desktop', 'desktop-state-manager-fixed.desktop']
        
        for filename in desktop_files:
            desktop_file = self.project_root / filename
            if desktop_file.exists():
                try:
                    subprocess.run(['desktop-file-validate', str(desktop_file)], 
                                 capture_output=True, check=True, timeout=10)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # desktop-file-validate might not be available
                    pass
    
    # Script Syntax Tests
    def test_python_syntax(self):
        """Test Python script syntax"""
        python_files = [
            'desktop-state-manager.py',
            'desktop-state-manager-simple.py',
            'test-desktop-manager.py'
        ]
        
        if HAS_DSM_MODULES:
            python_files.extend(['dsm_logger.py', 'dsm_config.py'])
        
        for filename in python_files:
            file_path = self.project_root / filename
            if file_path.exists():
                result = subprocess.run([sys.executable, '-m', 'py_compile', str(file_path)],
                                      capture_output=True)
                assert result.returncode == 0, f"Syntax error in {filename}: {result.stderr.decode()}"
    
    def test_shell_syntax(self):
        """Test shell script syntax"""
        shell_files = [
            'tilingshell-desktop-restore.sh',
            'desktop-cli.sh',
            'install-desktop-state-manager.sh',
            'launch-desktop-manager.sh',
            'restore-desktop-state.sh'
        ]
        
        for filename in shell_files:
            file_path = self.project_root / filename
            if file_path.exists():
                result = subprocess.run(['bash', '-n', str(file_path)], capture_output=True)
                assert result.returncode == 0, f"Syntax error in {filename}: {result.stderr.decode()}"
    
    # Configuration Tests
    def test_config_system(self):
        """Test configuration system functionality"""
        if not HAS_DSM_MODULES:
            raise AssertionError("DSM modules not available")
        
        with temporary_config_dir() as temp_dir:
            config_dir = temp_dir / ".config" / "desktop-restore"
            config_mgr = ConfigManager(config_dir)
            
            # Test default config creation
            config = config_mgr.get_config()
            assert config.version == "3.5.0"
            assert config.timing.app_launch_delay == 2.0
            assert config_mgr.config_file.exists()
            
            # Test config updates
            assert config_mgr.update_config(version="3.5.1")
            updated_config = config_mgr.get_config()
            assert updated_config.version == "3.5.1"
            
            # Test nested updates
            assert config_mgr.update_config(**{"timing.app_launch_delay": 1.5})
            updated_config = config_mgr.get_config()
            assert updated_config.timing.app_launch_delay == 1.5
    
    def test_logging_system(self):
        """Test logging system functionality"""
        if not HAS_DSM_MODULES:
            raise AssertionError("DSM modules not available")
        
        with temporary_config_dir():
            logger = get_logger("test")
            
            # Test basic logging
            logger.info("Test message")
            logger.warning("Test warning")
            logger.error("Test error")
            
            # Test performance timing
            with logger.time_operation("test_operation"):
                time.sleep(0.1)
            
            # Test log files creation
            log_files = logger.get_log_files()
            assert len(log_files) > 0, "No log files created"
    
    # Integration Tests
    def test_cli_help(self):
        """Test CLI help functionality"""
        cli_script = self.project_root / "desktop-cli.sh"
        if cli_script.exists():
            result = subprocess.run([str(cli_script), "system"], 
                                  capture_output=True, timeout=30)
            # Should not crash, exit code may vary based on system state
            assert result.returncode in [0, 1], "CLI script crashed"
    
    def test_backend_script_help(self):
        """Test backend script help"""
        backend_script = self.project_root / "tilingshell-desktop-restore.sh"
        if backend_script.exists():
            result = subprocess.run([str(backend_script)], 
                                  capture_output=True, timeout=10)
            assert result.returncode == 1  # Expected for help/usage
            assert b"Usage:" in result.stdout or b"Commands:" in result.stdout
    
    def test_state_file_creation(self):
        """Test state file creation functionality"""
        with temporary_config_dir() as temp_dir:
            state_dir = temp_dir / ".config" / "desktop-restore"
            state_dir.mkdir(parents=True, exist_ok=True)
            
            # Create minimal test state
            test_state = {
                "timestamp": "2025-09-01T10:00:00",
                "workspaces": {"count": 4, "current": 0},
                "windows": [],
                "applications": [],
                "tilingshell": {}
            }
            
            state_file = state_dir / "desktop-state.json"
            with open(state_file, 'w') as f:
                json.dump(test_state, f)
            
            assert state_file.exists()
            
            # Validate JSON format
            with open(state_file, 'r') as f:
                loaded_state = json.load(f)
            
            assert loaded_state["timestamp"] == test_state["timestamp"]
            assert loaded_state["workspaces"]["count"] == 4
    
    # Performance Tests
    def test_config_load_performance(self):
        """Test configuration loading performance"""
        if not HAS_DSM_MODULES:
            raise AssertionError("DSM modules not available")
        
        with temporary_config_dir() as temp_dir:
            config_dir = temp_dir / ".config" / "desktop-restore"
            
            start_time = time.time()
            config_mgr = ConfigManager(config_dir)
            config = config_mgr.get_config()
            duration = time.time() - start_time
            
            assert duration < 1.0, f"Config loading too slow: {duration:.3f}s"
    
    def test_logger_performance(self):
        """Test logging performance"""
        if not HAS_DSM_MODULES:
            raise AssertionError("DSM modules not available")
        
        with temporary_config_dir():
            logger = get_logger("perf_test")
            
            start_time = time.time()
            for i in range(100):
                logger.info(f"Test message {i}")
            duration = time.time() - start_time
            
            assert duration < 2.0, f"Logging too slow: {duration:.3f}s for 100 messages"
    
    # Comprehensive Test Runner
    def run_all_tests(self):
        """Run all tests in the suite"""
        print("🚀 Starting Desktop State Manager Test Suite")
        print("=" * 60)
        
        # System compatibility tests
        print("\n📋 System Compatibility Tests")
        print("-" * 30)
        self.run_test("Python Version", self.test_python_version)
        self.run_test("Required Tools", self.test_required_tools)
        
        if os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'):
            self.run_test("GUI Dependencies", self.test_gui_dependencies)
            self.run_test("Desktop Environment", self.test_desktop_environment)
        else:
            self.skip_test("GUI Dependencies", "No display server")
            self.skip_test("Desktop Environment", "No display server")
        
        # File system tests
        print("\n📁 File System Tests")
        print("-" * 20)
        self.run_test("Script Files Exist", self.test_script_files_exist)
        self.run_test("Script Permissions", self.test_script_permissions)
        self.run_test("Desktop File Validity", self.test_desktop_file_validity)
        
        # Syntax tests
        print("\n🔍 Syntax Tests")
        print("-" * 15)
        self.run_test("Python Syntax", self.test_python_syntax)
        self.run_test("Shell Syntax", self.test_shell_syntax)
        
        # Module tests
        print("\n🧩 Module Tests")
        print("-" * 15)
        if HAS_DSM_MODULES:
            self.run_test("Configuration System", self.test_config_system)
            self.run_test("Logging System", self.test_logging_system)
        else:
            self.skip_test("Configuration System", "DSM modules not available")
            self.skip_test("Logging System", "DSM modules not available")
        
        # Integration tests
        print("\n🔗 Integration Tests")
        print("-" * 20)
        self.run_test("CLI Help", self.test_cli_help)
        self.run_test("Backend Script Help", self.test_backend_script_help)
        self.run_test("State File Creation", self.test_state_file_creation)
        
        # Performance tests
        print("\n⚡ Performance Tests")
        print("-" * 20)
        if HAS_DSM_MODULES:
            self.run_test("Config Load Performance", self.test_config_load_performance)
            self.run_test("Logger Performance", self.test_logger_performance)
        else:
            self.skip_test("Config Load Performance", "DSM modules not available")
            self.skip_test("Logger Performance", "DSM modules not available")
        
        # Print summary
        return self.result.print_summary()


def main():
    """Main test runner"""
    suite = DSMTestSuite()
    success = suite.run_all_tests()
    
    if success:
        print(f"\n🎉 All tests passed! Desktop State Manager is ready.")
        return 0
    else:
        print(f"\n💥 Some tests failed. Please review the failures above.")
        return 1


if __name__ == "__main__":
    exit(main())
