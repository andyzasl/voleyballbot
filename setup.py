from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="volleyballbot",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Volleyball community player management bot with Telegram integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "python-telegram-bot[env]>=20.0",
        "sqlalchemy>=2.0.7",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "testing": [
            "pytest>=8.0",
            "pytest-cov>=4.0",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    entry_points={
        "console_scripts": [
            "volleybot=bot:main",
        ],
    },
)
