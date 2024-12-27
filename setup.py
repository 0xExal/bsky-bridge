from setuptools import setup, find_packages

setup(
    name="bsky-bridge",
    version="1.0.8",
    description="A Python interface for interacting with the BlueSky social network's API.",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    keywords='bluesky, api, python, bridge, social network, bluesky api, social network api, bluesky python',
    author="Exal",
    author_email="hello@exal.sh",
    url="https://github.com/4xe1/bsky-bridge",
    packages=find_packages(),
    install_requires=[
        "requests",
        "Pillow",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
