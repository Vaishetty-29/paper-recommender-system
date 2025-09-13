from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String(128))
    role = Column(String(10), default='basic')  # 'basic' or 'premium'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def init_db():
    engine = create_engine('sqlite:///db.sqlite')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    if session.query(User).filter_by(username='premium_user').first() is None:
        premium_user = User(username='premium_user', role='premium')
        premium_user.set_password('password123')
        session.add(premium_user)
        session.commit()
        print("Premium user created.")
    session.close()

if __name__ == '__main__':
    init_db()