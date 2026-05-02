from setuptools import setup, find_packages

setup(
    name="fastapi-foundation",
    version="0.0.1",
    packages=find_packages(),
    install_requires=[
        "pymongo>=4.12.0",
        "motor>=3.7.0",
        "fastapi>=0.100.0",
        "httpx>=0.24.1",
        "pydantic>=2.0.0",
        "pydantic-core>=2.0.0",
        "uvicorn>=0.23.0",
        "pydantic-settings>=2.0.0",
        "python-dotenv>=1.0.0",
        "dependency-injector",
        "python-multipart",
        "uvloop",
        "httptools",
        "python-jose==3.3.0",
        "passlib[bcrypt]==1.7.4",
        "boto3",
        "cryptography",
        "pydantic[email]",
        "requests",
        "pytz",
        "scalar_fastapi",
    ],
    extras_require={
        # Install the async driver for your target database alongside this extra:
        #   PostgreSQL:  pip install "fastapi-foundation[sql]" asyncpg
        #   MySQL:       pip install "fastapi-foundation[sql]" aiomysql
        "sql": [
            "sqlalchemy[asyncio]>=2.0.0",
        ],
        "postgresql": [
            "sqlalchemy[asyncio]>=2.0.0",
            "asyncpg>=0.29.0",
        ],
        "mysql": [
            "sqlalchemy[asyncio]>=2.0.0",
            "aiomysql>=0.2.0",
        ],
    },
    author="Shahadat Hossain",
    author_email="mshossain110@gmail.com",
    description="A collection of common utilities and components for FastAPI applications, including database integration, authentication, and more.",
)
