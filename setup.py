from setuptools import setup, find_packages
setup(
    name="vincul",
    version="0.2.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=["cryptography>=41.0"],
)
