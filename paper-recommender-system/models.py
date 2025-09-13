from sqlalchemy import create_engine, Column, Integer, String, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Paper(Base):
    __tablename__ = 'papers'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    authors = Column(String)
    abstract = Column(String)
    year = Column(Integer)
    journal = Column(String)
    category = Column(String)
    premium = Column(Boolean, default=False)
    
    __table_args__ = (
        Index('idx_authors', 'authors'),
        Index('idx_year', 'year'),
        Index('idx_journal', 'journal'),
    )

    def __repr__(self):
        return f"<Paper(title='{self.title}', authors='{self.authors}')>"

if __name__ == '__main__':
    engine = create_engine('sqlite:///db.sqlite')
    Base.metadata.create_all(engine)
    print("Database schema created successfully.")