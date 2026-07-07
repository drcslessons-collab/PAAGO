from setuptools import setup, find_packages

setup(
    name="paago",
    version="2.0.0",
    packages=find_packages(include=["trainer", "trainer.*", "scripts", "scripts.*", "evaluation", "evaluation.*"]),
)
