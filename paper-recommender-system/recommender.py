import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Paper, Base

DATABASE_URL = "sqlite:///db.sqlite"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def build_recommender():
    session = Session()
    try:
        papers = session.query(Paper.id, Paper.title, Paper.abstract).all()
        if not papers:
            print("No papers found. Please run ingest.py first.")
            return

        df = pd.DataFrame([(p.id, p.title, p.abstract) for p in papers], columns=['id', 'title', 'abstract'])
        
        # Combine title and abstract for a single feature
        df['combined_features'] = df['title'] + ' ' + df['abstract']
        
        # Build TF-IDF vectorizer (CPU-friendly with max_features)
        tfidf_vectorizer = TfidfVectorizer(stop_words='english', max_features=10000)
        tfidf_matrix = tfidf_vectorizer.fit_transform(df['combined_features'])
        
        # Save the vectorizer and matrix to files
        joblib.dump(tfidf_vectorizer, 'tfidf_vectorizer.joblib')
        joblib.dump(tfidf_matrix, 'tfidf_matrix.joblib')
        joblib.dump(df['id'].tolist(), 'paper_ids.joblib')
        
        print("Recommender system data built and saved successfully.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    build_recommender()