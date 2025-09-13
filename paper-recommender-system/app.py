import os
import joblib
from flask import Flask, jsonify, request, redirect, url_for
from flask_cors import CORS
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from models import Base, Paper
from sklearn.metrics.pairwise import cosine_similarity
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from auth import User

# Load the pre-trained recommender model data
try:
    tfidf_vectorizer = joblib.load('tfidf_vectorizer.joblib')
    tfidf_matrix = joblib.load('tfidf_matrix.joblib')
    paper_ids = joblib.load('paper_ids.joblib')
    paper_id_to_index = {id: i for i, id in enumerate(paper_ids)}
except FileNotFoundError:
    tfidf_vectorizer = None
    tfidf_matrix = None
    paper_ids = None
    paper_id_to_index = {}
    print("WARNING: Recommender model files not found. Run recommender.py first.")

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-very-secret-key' 
    CORS(app)

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        session = Session()
        return session.query(User).get(int(user_id))

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db.sqlite")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)

    @app.route("/health")
    def health_check():
        return jsonify({"status": "healthy", "message": "API is running."})

    @app.route("/search")
    def search_papers():
        session = app.session
        
        q = request.args.get('q', '')
        author = request.args.get('author', '')
        year = request.args.get('year', type=int)
        journal = request.args.get('journal', '')
        category = request.args.get('category', '')
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        query = session.query(Paper)

        if q:
            search_pattern = f"%{q}%"
            query = query.filter(
                or_(
                    Paper.title.ilike(search_pattern),
                    Paper.abstract.ilike(search_pattern)
                )
            )
        
        if author:
            query = query.filter(Paper.authors.ilike(f"%{author}%"))
        
        if year:
            query = query.filter(Paper.year == year)
            
        if journal:
            query = query.filter(Paper.journal.ilike(f"%{journal}%"))

        if category:
            query = query.filter(Paper.category.ilike(f"%{category}%"))

        # Check for premium access and filter results
        if not (current_user.is_authenticated and current_user.role == 'premium'):
            query = query.filter(Paper.premium == False)

        paginated_query = query.limit(per_page).offset((page - 1) * per_page)
        papers = paginated_query.all()

        if not papers:
            return jsonify({"results": [], "message": "No results found."})

        results = [
            {
                "id": p.id,
                "title": p.title,
                "authors": p.authors,
                "abstract": p.abstract,
                "year": p.year,
                "journal": p.journal,
                "category": p.category,
                "premium": p.premium
            } for p in papers
        ]

        total_results = query.count()
        total_pages = (total_results + per_page - 1) // per_page

        return jsonify({
            "results": results,
            "total_results": total_results,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        })

    @app.route("/recommend/<int:paper_id>")
    @login_required
    def recommend_papers(paper_id):
        if not (current_user.is_authenticated and current_user.role == 'premium'):
            return jsonify({"message": "Access denied. This is a premium feature."}), 403

        if not tfidf_matrix or paper_id not in paper_id_to_index:
            return jsonify({"message": "Recommender model not available or paper ID not found."}), 404

        index = paper_id_to_index[paper_id]
        
        # Calculate cosine similarity with all papers
        cosine_similarities = cosine_similarity(tfidf_matrix[index:index+1], tfidf_matrix).flatten()
        
        # Get the indices of the top N most similar papers (excluding the paper itself)
        similar_indices = cosine_similarities.argsort()[:-6:-1]
        
        # Get the actual paper IDs from the indices
        similar_paper_ids = [paper_ids[i] for i in similar_indices]

        # Query the database for the papers
        session = app.session
        recommended_papers = session.query(Paper).filter(Paper.id.in_(similar_paper_ids)).all()
        
        # Sort results to match similarity order
        recommendation_map = {p.id: p for p in recommended_papers}
        sorted_recommendations = [recommendation_map[id] for id in similar_paper_ids if id in recommendation_map]

        results = [
            {
                "id": p.id,
                "title": p.title,
                "authors": p.authors,
                "year": p.year,
                "journal": p.journal,
            } for p in sorted(sorted_recommendations, key=lambda p: similar_paper_ids.index(p.id))
        ]
        
        return jsonify({"recommendations": results})
        
    @app.route("/login", methods=['POST'])
    def login():
        session = app.session
        username = request.json.get('username', None)
        password = request.json.get('password', None)
        user = session.query(User).filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return jsonify({"message": "Logged in successfully."})
        return jsonify({"message": "Invalid username or password."}), 401

    @app.route("/logout", methods=['POST'])
    @login_required
    def logout():
        logout_user()
        return jsonify({"message": "Logged out successfully."})

    @app.before_request
    def before_request():
        app.session = Session()

    @app.teardown_request
    def teardown_request(exception=None):
        if hasattr(app, 'session'):
            app.session.close()
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)