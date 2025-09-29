from setuptools import setup, find_packages
import os

def get_version():
    version_file = os.path.join(os.path.dirname(__file__), '.version')
    try:
        with open(version_file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return '1.0.0'

setup(
    name='cerebro-?',
    version=get_version(),
    packages=find_packages(exclude=('tests', '.venv', '.pytest_cache')),
    description='Template Python package for Cerebro',
    author='OPTIME.AI',
    install_requires=[],
    python_requires='>=3.9'
)
