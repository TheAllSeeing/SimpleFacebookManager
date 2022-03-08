from setuptools import setup

with open('requirements.txt') as req_file:
    deps = req_file.readlines()

setup(
    name='feedscraper',
    packages=['feedscraper'],
    version='1.0.0',
    install_requires=deps,
    description='A library for scraping facebook and automating basic user actions.',
    author='Atai Ambus',
    license='MIT'
)
