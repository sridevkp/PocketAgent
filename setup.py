from setuptools import setup, find_packages

setup(
    name='pocket_agent',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'mcp>=0.1.0',
    ],
)