import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import click
from backend.ingestion.ingest import IngestService
from backend.services.db.session import init_db

@click.group()
def cli():
    """Knowthee Admin CLI"""
    pass

@cli.command()
@click.option("--source", default="backend/data/imports", help="Folder with input files")
@click.option("--processed", default="backend/data/processed", help="Folder to store processed files")
def ingest(source, processed):
    """Ingest CVs and Assessments from input files."""
    init_db()
    service = IngestService(Path(source), Path(processed))
    service.process_all()
    click.echo("✅ Ingestion complete.")

if __name__ == "__main__":
    cli()
