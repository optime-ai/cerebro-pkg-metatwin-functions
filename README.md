# cerebro-tpl-python-package

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Build](https://img.shields.io/badge/Build-setuptools-green.svg)
![Testing](https://img.shields.io/badge/Testing-pytest-yellow.svg)

Python package template for the Cerebro AI Platform.

## 🚀 Features

- Python 3.9+ support
- Setuptools-based packaging
- Automated CI/CD with Cloud Build
- Version management with Git tags
- Artifact Registry integration
- Comprehensive testing with pytest

## 📋 Prerequisites

- **Python 3.9** or later
- **pip** package manager
- **Git** for version control

## 🛠️ Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd cerebro-tpl-python-package

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

### Running Tests

```bash
# Run all tests
./run_tests.sh

# Or directly with pytest
PYTHONPATH=$(pwd) pytest tests
```

## 🏗️ Project Structure

```
cerebro_[package name]/
├── __init__.py       # Package initialization
├── ...              # Your package modules
tests/
├── __init__.py      # Test initialization
├── ...              # Test modules
├── setup.py         # Package configuration
├── pyproject.toml   # Build system requirements
└── requirements.txt # Development dependencies
```

## ⚙️ Configuration

### Package Setup

Update `setup.py` with your package details:
- Replace `cerebro-?` with your package name
- Add runtime dependencies to `install_requires`
- Update package description and metadata

## 🔄 Version Management

Versions are managed through Git tags and Cloud Build:

| Branch | Version Type | Example |
|--------|-------------|---------|
| `staging` | Release Candidate | `1.0.0-rc1` |
| `main` | Release | `1.0.0` |

### Manual Version Override

Include version in commit message: `[1.2.0]` or `[v1.2.0]`

## 📦 Building and Distribution

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Upload to repository (configured in Cloud Build)
python -m twine upload dist/*
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cerebro_[package name]

# Run specific test
pytest tests/test_specific.py
```

## 🚢 Deployment

The package is automatically deployed via Cloud Build:
- **Staging branch**: Creates RC versions
- **Main branch**: Creates release versions
- Artifacts are pushed to Artifact Registry
- Git tags are created automatically

## 📚 Documentation

- [Python Packaging Guide](https://packaging.python.org/)
- [pytest Documentation](https://docs.pytest.org/)
- [setuptools Documentation](https://setuptools.pypa.io/)