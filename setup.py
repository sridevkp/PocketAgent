from setuptools import setup, find_packages

setup(
    name='pocket_agent',
    version='0.2.0',
    packages=find_packages(),
    install_requires=[
        'mcp>=0.1.0',
    ],
    entry_points={
        'console_scripts': [
            'pocket-agent=pocket_agent:help',
        ],
    },
)