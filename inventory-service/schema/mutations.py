import graphene
from db import db
from models.inventory_status import InventoryStatus
from models.inventory_log import InventoryLog
from models.item import Item

# ----------------------------
# MUTATION: ADD INBOUND LOG
# ----------------------------

class AddInboundLog(graphene.Mutation):
    class Arguments:
        item_id = graphene.Int(required=True)
        quantity = graphene.Int(required=True)
        reference = graphene.String()
        created_by = graphene.Int()

    ok = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, item_id, quantity, reference="", created_by=0):
        status = InventoryStatus.query.filter_by(item_id=item_id).first()
        if not status:
            status = InventoryStatus(item_id=item_id, current_stock=0)
            db.session.add(status)
        status.current_stock += quantity

        log = InventoryLog(
            item_id=item_id,
            log_type='inbound',
            quantity=quantity,
            reference=reference,
            created_by=created_by
        )
        db.session.add(log)
        db.session.commit()
        return AddInboundLog(ok=True, message="Inbound berhasil")

# ----------------------------
# MUTATION: ADD OUTBOUND LOG
# ----------------------------

class AddOutboundLog(graphene.Mutation):
    class Arguments:
        item_id = graphene.Int(required=True)
        quantity = graphene.Int(required=True)
        reference = graphene.String()
        created_by = graphene.Int()

    ok = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, item_id, quantity, reference="", created_by=0):
        status = InventoryStatus.query.filter_by(item_id=item_id).first()

        if not status:
            return AddOutboundLog(ok=False, message="Item tidak ditemukan di stok.")
        
        if status.current_stock < quantity:
            return AddOutboundLog(ok=False, message="Stok tidak mencukupi.")

        status.current_stock -= quantity

        log = InventoryLog(
            item_id=item_id,
            log_type="outbound",
            quantity=quantity,
            reference=reference,
            created_by=created_by
        )
        db.session.add(log)
        db.session.commit()

        return AddOutboundLog(ok=True, message="Outbound log berhasil ditambahkan.")

class AddItem(graphene.Mutation):
    class Arguments:
        item_code = graphene.String(required=True)
        name = graphene.String(required=True)
        description = graphene.String()
        unit = graphene.String()
        min_stock = graphene.Int()
        location = graphene.String()

    ok = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, item_code, name, description="", unit="", min_stock=0, location=""):
        # Cek apakah item_code sudah ada
        existing = Item.query.filter_by(item_code=item_code).first()
        if existing:
            return AddItem(ok=False, message="Item code sudah terdaftar.")

        item = Item(
            item_code=item_code,
            name=name,
            description=description,
            unit=unit,
            min_stock=min_stock,
            location=location
        )
        db.session.add(item)
        db.session.commit()

        return AddItem(ok=True, message="Item berhasil ditambahkan.")

# ----------------------------
# REGISTER SEMUA MUTATION
# ----------------------------

class Mutation(graphene.ObjectType):
    add_item = AddItem.Field()
    add_inbound_log = AddInboundLog.Field()
    add_outbound_log = AddOutboundLog.Field()
