from llm.llm_retriever import LLMRetriever, NotFoundError, NoNewRevision

from jobs.scheduler import Scheduler

from enrichment.accuracy.meteor import Meteor
from persistence.persistence_manager import PersistenceManager
from persistence.inventory_item import InventoryItem

class LowerScoreError(RuntimeError):
    pass

class Enrichment:
    def __init__(self):
        self.llm_retriever = LLMRetriever()
        self.persistence_manager = PersistenceManager()
        self.job_scheduler = Scheduler()
        self.meteor = Meteor()

    def enrich(self, name: str):
        existing_item = self.persistence_manager.get_data(InventoryItem, InventoryItem.name==name)
        if not existing_item:
            new_item = self._enrich(InventoryItem(name=name))
            new_item.meteor_score = self.meteor.run(new_item.description, new_item.ref_text)

            with self.persistence_manager.get_session(read_only=False) as session:
                session.add(new_item)
            return new_item

        else:
            new_enriched_item = self._enrich(existing_item)
            new_enriched_item.meteor_score = self.meteor.run(new_enriched_item.description, new_enriched_item.ref_text)         
            
            if new_enriched_item.meteor_score < existing_item.meteor_score:
                raise LowerScoreError('Enrichment cancelled: New meteor score is lower than existing meteor score.')
            with self.persistence_manager.get_session(read_only=False) as session:
                session.merge(new_enriched_item)
            return new_enriched_item
            
    
    def _enrich(self, item: InventoryItem):
        try:
            enriched_item = self.llm_retriever.search(item)
        except NotFoundError as e:
            raise e
        except RuntimeError as e:
            raise e
        except NoNewRevision as e:
            raise e
        return enriched_item
    
    def read(self, name: str):
        item = self.persistence_manager.get_data(InventoryItem, InventoryItem.name==name)
        if not item:
            raise RuntimeError(f"Item with name {name} not found in database.")
        return item
    
    def batch_enrich(self):
        items = self.persistence_manager.get_data(InventoryItem)
        for item in items:
            try:
                self.enrich(item.name)
            except NoNewRevision as e:
                pass

    
    def get_job_status(self):
        return self.job_scheduler.get_status()
    
    def start_job(self,  ignore_revisions: bool = False):
        if ignore_revisions:
            self.persistence_manager.reset_revision()
        self.job_scheduler.start(self.batch_enrich)
    
    def stop_job(self):
        self.job_scheduler.stop()

    def delete(self, name: str = None):
        if name:
            self.persistence_manager.delete_data(InventoryItem, InventoryItem.name == name)
        else:
            self.persistence_manager.delete_data(InventoryItem)