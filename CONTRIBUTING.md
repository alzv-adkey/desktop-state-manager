# Contributing to Desktop State Manager

Thank you for your interest in contributing to Desktop State Manager! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites
- Linux distribution (Fedora/Nobara recommended)
- GNOME desktop environment
- Python 3.6+
- GTK4 and libadwaita development packages
- wmctrl, jq, and standard development tools

### Setup Development Environment
```bash
# Clone the repository
git clone <repository-url>
cd desktop-state-manager

# Install dependencies (Fedora/Nobara)
sudo dnf install python3 python3-gobject gtk4-devel libadwaita-devel wmctrl jq

# Make scripts executable
chmod +x *.sh *.py desktop-state-manager desktop-state-manager-cli

# Test the setup
./test-desktop-manager.py
```

## Branch Structure

- `main` - Stable releases only
- `develop` - Main development branch
- `feature/*` - New feature development
- `hotfix/*` - Critical bug fixes
- `release/*` - Release preparation

## Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout develop
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Follow existing code style and conventions
   - Add tests for new functionality
   - Update documentation as needed

3. **Test thoroughly**:
   ```bash
   ./test-desktop-manager.py
   ./desktop-cli.sh test
   ```

4. **Commit with descriptive messages**:
   ```bash
   git add .
   git commit -m "feature: Add new functionality
   
   - Detailed description of changes
   - Any breaking changes noted
   - References to issues if applicable"
   ```

5. **Merge back to develop**:
   ```bash
   git checkout develop
   git merge feature/your-feature-name
   git branch -d feature/your-feature-name
   ```

## Code Standards

### Python Code
- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Handle exceptions gracefully
- Use the logging system instead of print statements

### Shell Scripts
- Use proper error handling with `set -e` where appropriate
- Quote variables properly
- Use meaningful function names
- Add comments for complex logic
- Follow consistent indentation (4 spaces)

### GUI Development
- Use GTK4 and Adwaita design patterns
- Ensure accessibility compliance
- Test on different screen sizes
- Follow GNOME Human Interface Guidelines

## Testing

### Manual Testing
- Test on clean system with no existing state
- Test with various application types (native, Flatpak, Snap)
- Test TilingShell integration if available
- Test auto-restore functionality
- Verify RPM installation/uninstallation

### Automated Testing
- Run the existing test suite: `./test-desktop-manager.py`
- Add tests for new functionality
- Ensure tests pass on different GNOME versions

## Documentation

- Update README.md for new features
- Add inline code documentation
- Update man pages if creating new CLI options
- Update the spec file for packaging changes

## Submitting Changes

### Commit Message Format
```
type: Short description (50 chars max)

Detailed explanation of the change, including:
- What was changed and why
- Any breaking changes
- References to issues or related work
```

Types: `feature`, `fix`, `docs`, `style`, `refactor`, `test`, `build`

### Code Review Process
1. Ensure all tests pass
2. Update documentation
3. Create descriptive commit messages
4. Test on the develop branch before merging

## Release Process

1. **Prepare release branch**:
   ```bash
   git checkout develop
   git checkout -b release/v3.5.0
   ```

2. **Update version information**:
   - Update version in spec file
   - Update changelog
   - Update README if needed

3. **Test release candidate**:
   - Build RPM package
   - Test installation/uninstallation
   - Verify all functionality

4. **Merge to main and tag**:
   ```bash
   git checkout main
   git merge release/v3.5.0
   git tag -a v3.5.0 -m "Release v3.5.0: Description"
   git checkout develop
   git merge main
   ```

## Bug Reports

When reporting bugs, please include:
- Operating system and version
- GNOME version
- Steps to reproduce the issue
- Expected vs. actual behavior
- Log files from `~/.config/desktop-restore/`
- Output of `./desktop-cli.sh system`

## Feature Requests

- Check existing issues first
- Describe the use case clearly
- Explain why it would be valuable
- Consider implementation complexity
- Be open to alternative solutions

## Questions and Support

- Check the README.md and existing documentation first
- Search existing issues
- Create a new issue with the "question" label
- Provide context and specific details

## License

By contributing to Desktop State Manager, you agree that your contributions will be licensed under the GPL-3.0 license.
