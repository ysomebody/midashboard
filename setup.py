import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="midashboard-ysomebody",
    version="1.0.0dev3",
    author="ysomebody",
    author_email="ysomebody@163.com",
    description="MI dashboard",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ysomebody/midashboard",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'jenkinsapi',
        'RBTools',
        'urllib3',
        'packaging',
        'python-dateutil',
        'dash',
        'deepdiff',
    ],
    python_requires='>=3.7',
)
