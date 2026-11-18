from setuptools import setup, find_packages

setup(
    name="faultline-sdk",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.25.0",
    ],
    author="Dhathri Vaddiraju",
    author_email="dhathrivaddiraju@gmail.com",
    description="Custom lightweight Python SDK for Faultline Error Monitoring",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
