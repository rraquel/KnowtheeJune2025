"""add_employee_id_to_embedding_chunks

Revision ID: 0e9bcbc652b4
Revises: 4ad1db7788da
Create Date: 2025-06-19 12:56:52.859830

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0e9bcbc652b4'
down_revision: Union[str, None] = '4ad1db7788da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add employee_id column to embedding_chunks table
    op.add_column('embedding_chunks', sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_embedding_chunks_employee_id_employees',
        'embedding_chunks', 'employees',
        ['employee_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Populate employee_id from embedding_documents
    op.execute("""
        UPDATE embedding_chunks 
        SET employee_id = embedding_documents.employee_id
        FROM embedding_documents 
        WHERE embedding_chunks.external_document_id = embedding_documents.external_document_id
    """)
    
    # Make employee_id not nullable after populating
    op.alter_column('embedding_chunks', 'employee_id', nullable=False)


def downgrade() -> None:
    # Remove foreign key constraint
    op.drop_constraint('fk_embedding_chunks_employee_id_employees', 'embedding_chunks', type_='foreignkey')
    
    # Remove employee_id column
    op.drop_column('embedding_chunks', 'employee_id')
