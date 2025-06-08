import graphene
from db import db
from models.item import Item
from models.inventory_status import InventoryStatus
from models.inventory_log import InventoryLog

from schema.types import ItemObject, InventoryStatusObject, InventoryLogObject

class Query(graphene.ObjectType):
    # Query semua item
    items = graphene.List(ItemObject)
    
    # Barang low stock (current < min_stock)
    lowStockItems = graphene.List(ItemObject)

    # Status stok terkini
    inventoryStatus = graphene.List(InventoryStatusObject)

    # Riwayat transaksi barang masuk/keluar
    inventoryLogs = graphene.List(InventoryLogObject)

    # Resolver untuk semua item
    def resolve_items(self, info):
        return Item.query.all()

    # Resolver untuk barang low stock
    def resolve_lowStockItems(self, info):
        return db.session.query(Item).select_from(Item, InventoryStatus).filter(
            Item.item_id == InventoryStatus.item_id,
            InventoryStatus.current_stock < Item.min_stock
        ).all()

    # Resolver untuk status stok terkini
    def resolve_inventoryStatus(self, info):
        return InventoryStatus.query.all()

    # Resolver untuk histori log
    def resolve_inventoryLogs(self, info):
        return InventoryLog.query.order_by(InventoryLog.created_at.desc()).all()
