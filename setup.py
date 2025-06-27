from setuptools import setup, find_packages

setup(
    name="xkcd-comic-finder",
    version="0.1.0",
    description="A tool for finding XKCD comics",
    author="",
    author_email="",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "beautifulsoup4~=4.11.1",
        "boto3~=1.38.44",
        "python-dotenv~=0.21.0",
        "requests~=2.28.1",
        "weaviate-client~=3.15.4",
    ],
    extras_require={
        "test": [
            "coverage",
            "pytest",
            "pytest-cov",
        ],
        "tsne": [
            "numpy",
            "openai",
            "pandas",
            "scikit-learn",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)