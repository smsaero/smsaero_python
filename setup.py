"""Setup script for the SmsAero API client package."""

from setuptools import setup, find_packages


with open("README.md", "r", encoding="utf-8") as file:
    long_description = file.read()


setup(
    name="smsaero_api",
    version="3.0.0",
    description="SmsAero API client",
    keywords=[
        "smsaero",
        "api",
        "smsaero_api",
        "sms",
        "hlr",
        "viber",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="SmsAero",
    author_email="admin@smsaero.ru",
    help_center="https://smsaero.ru/support/",
    url="https://github.com/smsaero/smsaero_python/",
    license="MIT",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.6",
    include_package_data=True,
    install_requires=[
        "setuptools",
        "requests",
        "phonenumbers",
        "email-validator",
    ],
    extras_require={
        "dev": [
            "pytest >= 8.2.2",
            "requests >= 2.0.0",
            "types-requests >= 2.2.2",
            "flake8 >= 7.1.0",
            "ruff >= 0.4.10",
            "pylint >= 3.2.4",
            "tox >= 4.15.1",
            "mypy >= 1.10.0",
            "coverage >= 7.5.4",
            "bandit >= 1.7.9",
            "build >= 1.2.1",
            "twine >= 5.1.1",
        ],
    },
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Telephony",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points={
        "console_scripts": [
            "smsaero_send=smsaero.command_line:main",
        ],
    },
    options={
        "bdist_wheel": {"universal": True},
    },
)
