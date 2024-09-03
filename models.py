from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ProcessedEmail(Base):
    __tablename__ = 'processed_emails'

    id = Column(Integer, primary_key=True)
    uid = Column(String, unique=True, nullable=False)

# Инициализация базы данных
engine = create_engine('sqlite:///emails.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
