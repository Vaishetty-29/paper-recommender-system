import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Paper, Base

DATABASE_URL = "sqlite:///db.sqlite"

def ingest_data():
    """Reads data from CSV and ingests it into the SQLite database."""
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        df = pd.read_csv('papers.csv')
        papers_to_ingest = []
        for index, row in df.iterrows():
            paper = Paper(
                id=int(row['id']),
                title=row['title'],
                authors=row['authors'],
                abstract=row['abstract'],
                year=int(row['year']),
                journal=row['journal'],
                category=row['category'],
                premium=False if str(row['premium']).upper() == 'FALSE' else True
            )
            papers_to_ingest.append(paper)
        
        session.bulk_save_objects(papers_to_ingest)
        session.commit()
        print(f"Successfully ingested {len(papers_to_ingest)} papers.")
        
    except Exception as e:
        session.rollback()
        print(f"An error occurred: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    ingest_data()