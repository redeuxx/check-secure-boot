# main.py
# A FastAPI application that accepts POST/PUT requests to store
# Secure Boot certificate status in a SQLite database and provides
# a GET endpoint to retrieve/display HTML results and export CSV.

import csv
import io

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Boolean, Column, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# DB setup
DATABASE_URL = "sqlite:///./responses.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ComputerStatus(Base):
    __tablename__ = "computer_status"

    id = Column(Integer, primary_key=True, index=True)
    computer_name = Column(String, index=True, unique=True)
    active_db_status = Column(Boolean)
    default_db_status = Column(Boolean)
    notes = Column(String, nullable=True)


Base.metadata.create_all(bind=engine)

app = FastAPI()


# Pydantic Models
class ComputerStatusCreate(BaseModel):
    computer_name: str
    active_db_status: bool
    default_db_status: bool
    notes: str | None = None


class ComputerStatusResponse(BaseModel):
    id: int
    computer_name: str
    active_db_status: bool
    default_db_status: bool
    notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


# Get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# API endpoint
@app.post("/api", response_model=ComputerStatusResponse)
def create_computer_status(status: ComputerStatusCreate, db: Session = Depends(get_db)):
    db_status = (
        db.query(ComputerStatus)
        .filter(ComputerStatus.computer_name == status.computer_name)
        .first()
    )
    if db_status:
        raise HTTPException(status_code=400, detail="Computer name already registered")

    db_status = ComputerStatus(**status.model_dump())
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status


@app.put("/api", response_model=ComputerStatusResponse)
def update_computer_status(status: ComputerStatusCreate, db: Session = Depends(get_db)):
    db_status = (
        db.query(ComputerStatus)
        .filter(ComputerStatus.computer_name == status.computer_name)
        .first()
    )

    if db_status:
        db_status.active_db_status = status.active_db_status
        db_status.default_db_status = status.default_db_status
        db_status.notes = status.notes
    else:
        db_status = ComputerStatus(**status.model_dump())

    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status


# GET /results: HTML Table or CSV Export
@app.get("/results", response_class=HTMLResponse)
def get_results(db: Session = Depends(get_db), export_csv: bool = False):
    results = db.query(ComputerStatus).all()

    # If CSV export requested
    if export_csv:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            ["id", "computer_name", "active_db_status", "default_db_status", "notes"]
        )
        for result in results:
            writer.writerow(
                [
                    result.id,
                    result.computer_name,
                    result.active_db_status,
                    result.default_db_status,
                    result.notes,
                ]
            )
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=results.csv"},
        )

    # Precompute summary counters
    total_entries = len(results)
    total_active_true = sum(1 for r in results if r.active_db_status is True)
    total_active_not_true = sum(1 for r in results if r.active_db_status is not True)
    total_default_true = sum(1 for r in results if r.default_db_status is True)
    total_default_not_true = sum(1 for r in results if r.default_db_status is not True)

    # Build HTML table
    html_content = f"""
    <html>
        <head>
            <title>Results</title>
            <style>
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th, td {{
                    border: 1px solid #dddddd;
                    text-align: left;
                    padding: 8px;
                }}
                tr:nth-child(even) {{
                    background-color: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            <h2>Database Results</h2>
            Total: {total_entries} entries <br />
            Active DB = True: {total_active_true} <br />
            Active DB != True: {total_active_not_true} <br />
            Default DB = True: {total_default_true} <br />
            Default DB != True: {total_default_not_true} <br /><br />

            <table>
                <tr>
                    <th>ID</th>
                    <th>Computer Name</th>
                    <th>Active DB Status</th>
                    <th>Default DB Status</th>
                    <th>Notes</th>
                </tr>
    """

    for result in results:
        html_content += f"""
                <tr>
                    <td>{result.id}</td>
                    <td>{result.computer_name}</td>
                    <td>{result.active_db_status}</td>
                    <td>{result.default_db_status}</td>
                    <td>{result.notes}</td>
                </tr>
        """

    html_content += """
            </table>
        </body>
    </html>
    """

    return HTMLResponse(content=html_content, status_code=200)
