from setuptools import setup, find_packages  # Always prefer setuptools over distutils
from codecs import open  # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='gwasrv',
    version="0.0.1",
    description='A RESTful backend for accessing GWAS HDF5 files GWA-Portal',
    long_description=long_description,
    url='https://github.com/timeu/gwaportal-gwas-server',
    author='Uemit Seren',
    author_email='uemit.seren@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
	'Topic :: Scientific/Engineering :: Bio-Informatics',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    keywords='GWAS hdf5 GWA-Portal',
    py_modules=['gwasrv'],
    install_requires=[
        "PyGWAS >= 1.1.1",
        "gunicorn >=19.0.0",
        "falcon >= 0.3.0",
    ],
    entry_points={
        'console_scripts': [
            'gwasrv=gwasrv:main'
        ],
    },
)

