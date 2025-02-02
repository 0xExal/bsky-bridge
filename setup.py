from setuptools import setup, find_packages

setup(
    name="bsky-bridge",
    version="1.0.11",
    description="A Python interface for interacting with the BlueSky social network's API.",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    keywords='bluesky, api, bluesky api, python, bridge, social network, social network api, bluesky python, post content, bluesky post, open-source Python, open-source API',
    author="Exal",
    author_email="hello@exal.sh",
    url="https://github.com/0xExal/bsky-bridge",
    packages=find_packages(),
    install_requires=[
        "requests",
        "Pillow",
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires=">=3.6",
)
