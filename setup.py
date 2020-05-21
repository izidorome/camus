import setuptools

with open("README.md") as f:
    long_description = f.read()

setuptools.setup(
    author="Rafael Izidoro",
    author_email="izidoro.rafa@gmail.com",
    url="https://github.com/rizidoro/camus",
    name="camus",
    version="0.4.0",
    py_modules = ['camus'],
    package_data={'': ['LICENSE']},
    include_package_data=True,
    long_description=long_description,
    long_description_content_type="text/markdown",
    description="A Records like database API that works with Aurora Serverless Data API",
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
