from setuptools import setup, find_packages

setup(
    name="knowthee",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy==2.0.27",
        "alembic==1.13.1",
        "psycopg2-binary==2.9.9",
        "python-dotenv==1.0.1",
        "pydantic==2.6.1",
        "spacy==3.7.2",
        "python-dateutil==2.8.2",
        "uuid==1.30",
        "python-magic==0.4.27",
        "click==8.1.7",
        "pgvector>=0.4.1,<0.5",
    ],
) 