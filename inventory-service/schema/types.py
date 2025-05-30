from graphene_sqlalchemy import SQLAlchemyObjectType
from models.item import Item
from models.inventory_status import InventoryStatus
from models.inventory_log import InventoryLog

class ItemObject(SQLAlchemyObjectType):
    class Meta:
        model = Item
        interfaces = ()

class InventoryStatusObject(SQLAlchemyObjectType):
    class Meta:
        model = InventoryStatus
        interfaces = ()

class InventoryLogObject(SQLAlchemyObjectType):
    class Meta:
        model = InventoryLog
        interfaces = ()
