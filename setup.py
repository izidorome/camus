import setuptools

with open("README.md") as f:
    long_description = f.read()

setuptools.setup(
    author="Rafael Izidoro",
    author_email="izidoro.rafa@gmail.com",
    url="https://github.com/noverde/camus",
    name="camus",
    version="0.0.1",
    long_description=long_description,
    long_description_content_type="text/markdown",
    description="A Records like database API that works with Aurora Serverless Data API",
    packages=setuptools.find_packages(exclude=["docs", "tests"]),
    license="MIT",
    install_requires=["boto3"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Utilities",
    ],
)

