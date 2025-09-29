from setuptools import setup, find_packages
import os

setup(
    name='cerebro-pkg-metatwin-functions',
    version='{{VERSION}}',
    packages=find_packages(exclude=['tests*', 'examples*']),
    description='Function-as-a-Service SDK for Cerebro MetaTwin Functions',
    long_description=open('README.md').read() if os.path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    author='OPTIME.AI',
    url='https://github.com/optime-ai/cerebro-pkg-metatwin-functions',
    python_requires='>=3.9',
    install_requires=[
        'fastapi>=0.100.0',
        'uvicorn>=0.23.0',
        'pydantic>=2.0.0',
        'pydantic-settings>=2.0.0',
        'python-json-logger>=2.0.0',
        'aio-pika>=9.0.0'
    ],
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-mock>=3.10.0',
            'pytest-asyncio>=0.21.0',
            'httpx>=0.24.0',
            'build>=1.1.1',
            'twine>=5.0.0'
        ]
    }
)