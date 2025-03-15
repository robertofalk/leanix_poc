from persistence.inventory_item import Base
from sqlalchemy import create_engine
from contextlib import contextmanager
from sqlalchemy.orm import Session
from persistence.inventory_item import InventoryItem

class PersistenceManager:
    def __init__(self):
        self._engine = create_engine("sqlite:///local.db", echo=True)
        Base.metadata.create_all(bind=self._engine, checkfirst=True)

    def close_db(self):
        self._engine.dispose()
    
    @contextmanager
    def get_session(self, read_only: bool=True):
        session = Session(self._engine, expire_on_commit=False)
        try:
            yield session
            if not read_only:
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_data(self, model_class, filter_expressions=()):
        with self.get_session() as session:
            if filter_expressions != ():
                return session.query(model_class).filter(filter_expressions).first()
            return session.query(model_class).all()
    
    def delete_data(self, model_class, filter_expressions=()):
        with self.get_session(read_only=False) as session:
            if filter_expressions != ():
                session.query(model_class).filter(filter_expressions).delete()
            else:
                session.query(model_class).delete()

    def reset_revision(self):
        with self.get_session(read_only=False) as session:
            session.query(InventoryItem).update({InventoryItem.revision: 0})