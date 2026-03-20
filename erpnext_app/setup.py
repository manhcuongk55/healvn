from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="healvn",
    version="1.0.0",
    description="HealVN — Vietnam's Healing Tourism Platform (ERPNext Integration)",
    author="HealVN Team",
    author_email="hello@healvn.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
