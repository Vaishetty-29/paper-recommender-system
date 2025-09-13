import random
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Paper, Base

DATABASE_URL = "sqlite:///db.sqlite"

def generate_papers(num_papers=10000):
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    titles = ["Research on AI", "Data Science Trends", "The Future of Python", "Quantum Computing Basics", "Deep Learning Algorithms"]
    authors = ["John Smith", "Jane Doe", "Emily Jones", "Chris Miller"]
    journals = ["J. Comp. Science", "AI Today", "Data Magazine"]
    categories = ["AI", "Programming", "Mathematics", "Physics"]
    years = range(2010, datetime.date.today().year + 1)
    abstract_words = ["This paper explores", "We present a new method for", "An analysis of", "The study investigates the impact of"]

    papers_to_ingest = []
    for i in range(1, num_papers + 1):
        paper = Paper(
            id=i + 3,  # Offset to avoid conflicts with existing data
            title=random.choice(titles) + " " + str(i),
            authors=random.choice(authors),
            abstract=random.choice(abstract_words) + " " + " ".join(random.choices(titles + authors, k=10)),
            year=random.choice(years),
            journal=random.choice(journals),
            category=random.choice(categories),
            premium=False
        )
        papers_to_ingest.append(paper)
    
    try:
        session.bulk_save_objects(papers_to_ingest)
        session.commit()
        print(f"Successfully generated and ingested {len(papers_to_ingest)} mock papers.")
    except Exception as e:
        session.rollback()
        print(f"An error occurred: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    generate_papers(num_papers=10000)