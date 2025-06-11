from setuptools import setup, find_packages
from pathlib import Path 

# Read README.md
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')  

setup(
    name='ElecMap',
    version='0.1.0',
    author='Mohammad Saber',
    author_email='mohammadsaber@gmail.com',
    description='A package for electrode detection and visualization in CT/MR scans',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/saberm2837/ElecMap',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'SimpleITK',
        'matplotlib',
        'nipype',
        'termcolor',
    ],
    python_requires='>=3.7',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    entry_points={
        'console_scripts': [
            'elecmap-detect=ElecMap.electrode_detection:detect_electrodes',
            'elecmap-visualize=ElecMap.electrode_visualization:display_electrode_locations',
        ],
    },
    project_urls={
        'Source': 'https://github.com/saberm2837/ElecMap',
        'Bug Reports': 'https://github.com/saberm2837/ElecMap/issues',
    },
)