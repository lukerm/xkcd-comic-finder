#  Copyright (C) 2025 lukerm of www.zl-labs.tech
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

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