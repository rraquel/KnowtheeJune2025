import os
import re
import shutil
import logging
from pathlib import Path
from datetime import datetime
from sqlalchemy import or_, and_, func
import argparse

from backend.db.session import init_db, SessionLocal
from backend.ingestion.parsers.cv_parser import parse_cv
from backend.ingestion.parsers.assessment_parser import parse_assessment
from backend.utils.validators import validate_file
from backend.utils.common import slugify

from backend.db.models import (
    Employee,
    EmployeeContact,
    EmployeeExperience,
    EmployeeEducation,
    EmployeeSkill,
    EmployeeAssessment,
    IDIScore,
    HoganScore,
    EmbeddingRun,
    EmbeddingDocument,
    EmbeddingChunk
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

class IngestService:
    def __init__(self, source_dir: Path, processed_dir: Path):
        self.source_dir = Path(source_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.db = SessionLocal()

    def process_all(self):
        logger.info(f"Processing files from {self.source_dir}")
        
        # First, process all CV files
        cv_files = sorted([f for f in self.source_dir.iterdir() if f.is_file() and f.stem.startswith("CV_")])
        for file_path in cv_files:
            try:
                self.process_single_file(file_path)
            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")
        
        # Then, process all assessment files
        assessment_files = sorted([f for f in self.source_dir.iterdir() 
                                 if f.is_file() and (f.stem.startswith("IDI_") or f.stem.startswith("Hogan_"))])
        for file_path in assessment_files:
            try:
                self.process_single_file(file_path)
            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")

    def process_single_file(self, file_path: Path):
        logger.info(f"Processing file: {file_path.name}")

        if not validate_file(file_path):
            raise ValueError(f"Failed validation: {file_path.name}")

        with SessionLocal() as db:
            try:
                if file_path.stem.startswith("CV_"):
                    parsed_data = parse_cv(file_path)
                    self._handle_cv_data(parsed_data, db)

                elif file_path.stem.startswith(("IDI_", "Hogan_")):
                    parsed_data = parse_assessment(file_path)
                    self._handle_assessment_data(parsed_data, db, file_path)

                db.commit()
                dst_path = self.processed_dir / file_path.name
                try:
                    shutil.move(str(file_path), str(dst_path))
                    logger.info(f"Successfully processed {file_path.name}")
                except FileExistsError:
                    # If file already exists in processed directory, just delete the source file
                    file_path.unlink()
                    logger.info(f"File {file_path.name} was already processed, removed source file")
            except Exception as e:
                db.rollback()
                logger.error(f"Error processing {file_path.name}: {e}")

    def _handle_cv_data(self, parsed_data, db):
        """Handle parsed CV data and create/update database records."""
        try:
            # Create or update employee record
            employee = db.query(Employee).filter_by(full_name=parsed_data["name"]).first()
            if not employee:
                employee = Employee(
                    full_name=parsed_data["name"],
                    email=parsed_data.get("email"),
                    location=parsed_data.get("location"),
                    current_position=parsed_data.get("position"),
                    department=parsed_data.get("department")
                )
                db.add(employee)
                db.flush()

            # Handle contacts
            for contact_data in parsed_data.get("contacts", []):
                # Check if contact already exists
                existing_contact = db.query(EmployeeContact).filter_by(
                    employee_id=employee.id,
                    type=contact_data["type"],
                    value=contact_data["value"]
                ).first()
                
                if not existing_contact:
                    contact = EmployeeContact(
                        employee_id=employee.id,
                        type=contact_data["type"],
                        value=contact_data["value"],
                        is_primary=contact_data.get("is_primary", False)
                    )
                    db.add(contact)

            # Handle education
            for edu_data in parsed_data.get("education", []):
                # Check if education already exists
                existing_edu = db.query(EmployeeEducation).filter_by(
                    employee_id=employee.id,
                    institution=edu_data["institution"],
                    degree=edu_data["degree"],
                    field=edu_data.get("field")
                ).first()
                
                if not existing_edu:
                    education = EmployeeEducation(
                        employee_id=employee.id,
                        institution=edu_data["institution"],
                        degree=edu_data["degree"],
                        field=edu_data.get("field"),
                        start_date=edu_data["start_date"],
                        end_date=edu_data["end_date"]
                    )
                    db.add(education)

            # Handle experiences
            for exp_data in parsed_data.get("experiences", []):
                # Check for similar experiences based on company, title, and overlapping dates
                query = db.query(EmployeeExperience).filter(
                    EmployeeExperience.employee_id == employee.id,
                    EmployeeExperience.company == exp_data["company"],
                    EmployeeExperience.title == exp_data["title"]
                )

                # Add date overlap conditions only if dates are not None
                if exp_data["start_date"] is not None and exp_data["end_date"] is not None:
                    query = query.filter(
                        or_(
                            # New experience starts during existing experience
                            and_(
                                EmployeeExperience.start_date <= exp_data["start_date"],
                                or_(
                                    EmployeeExperience.end_date >= exp_data["start_date"],
                                    EmployeeExperience.end_date.is_(None)
                                )
                            ),
                            # New experience ends during existing experience
                            and_(
                                EmployeeExperience.start_date <= exp_data["end_date"],
                                or_(
                                    EmployeeExperience.end_date >= exp_data["end_date"],
                                    EmployeeExperience.end_date.is_(None)
                                )
                            ),
                            # New experience completely contains existing experience
                            and_(
                                EmployeeExperience.start_date >= exp_data["start_date"],
                                or_(
                                    EmployeeExperience.end_date <= exp_data["end_date"],
                                    EmployeeExperience.end_date.is_(None)
                                )
                            )
                        )
                    )
                elif exp_data["start_date"] is not None:
                    query = query.filter(
                        EmployeeExperience.start_date == exp_data["start_date"]
                    )
                elif exp_data["end_date"] is not None:
                    query = query.filter(
                        EmployeeExperience.end_date == exp_data["end_date"]
                    )

                existing_exp = query.first()
                
                if not existing_exp:
                    experience = EmployeeExperience(
                        employee_id=employee.id,
                        title=exp_data["title"],
                        company=exp_data["company"],
                        start_date=exp_data["start_date"],
                        end_date=exp_data["end_date"],
                        description="\n".join(exp_data.get("description", []))
                    )
                    db.add(experience)

            # Handle skills
            for skill_data in parsed_data.get("skills", []):
                # Check if skill already exists
                existing_skill = db.query(EmployeeSkill).filter_by(
                    employee_id=employee.id,
                    skill=skill_data["name"],
                    type=skill_data.get("type", "technical")
                ).first()
                
                if not existing_skill:
                    skill = EmployeeSkill(
                        employee_id=employee.id,
                        skill=skill_data["name"],
                        type=skill_data.get("type", "technical")
                    )
                    db.add(skill)

            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error handling CV data: {str(e)}")
            return False

    def _handle_assessment_data(self, parsed_data, db, file_path):
        """Handle parsed assessment data and create/update database records."""
        try:
            employee_name = parsed_data["name"].strip().replace("_", " ")
            employee = db.query(Employee).filter(
                func.lower(Employee.full_name) == func.lower(employee_name)
            ).first()
            if not employee:
                logger.warning(f"Employee not found for assessment: {employee_name}")
                return False

            for assessment_data in parsed_data.get("assessments", []):
                existing_assessment = db.query(EmployeeAssessment).filter_by(
                    employee_id=employee.id,
                    assessment_type=assessment_data["type"],
                    assessment_date=assessment_data["date"]
                ).first()
                
                if not existing_assessment:
                    assessment = EmployeeAssessment(
                        employee_id=employee.id,
                        assessment_type=assessment_data["type"],
                        assessment_date=assessment_data["date"],
                        source_filename=file_path.name,
                        status="active"
                    )
                    db.add(assessment)
                    db.flush()
                else:
                    assessment = existing_assessment

                # Flatten and insert scores
                if assessment_data["type"] == "IDI":
                    for category, dimensions in assessment_data["scores"].items():
                        for dimension, score_value in dimensions.items():
                            score = IDIScore(
                                assessment_id=assessment.id,
                                category=category,
                                dimension=dimension,
                                score=score_value
                            )
                            db.add(score)
                elif assessment_data["type"] == "Hogan":
                    for trait, score_value in assessment_data["scores"].items():
                        score = HoganScore(
                            assessment_id=assessment.id,
                            trait=trait,
                            score=score_value
                        )
                        db.add(score)

            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error handling assessment data: {str(e)}")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest data files")
    parser.add_argument('--input-dir', type=str, default='backend/data/imports', help='Directory containing files to ingest')
    parser.add_argument('--processed-dir', type=str, default='backend/data/processed', help='Directory to move processed files')
    args = parser.parse_args()
    
    # Initialize database
    init_db()
    
    # Set up directories
    source_dir = Path(args.input_dir)
    processed_dir = Path(args.processed_dir)
    
    # Create and run ingest service
    ingest_service = IngestService(source_dir=source_dir, processed_dir=processed_dir)
    ingest_service.process_all()
