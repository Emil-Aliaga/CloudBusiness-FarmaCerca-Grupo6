from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, delete, func, or_, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DEFAULT_SQLITE_URL = f"sqlite:///{(BASE_DIR / 'farmacerca.db').as_posix()}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
SEED_DEMO_DATA = os.getenv("SEED_DEMO_DATA", "true").lower() in {"1", "true", "yes", "on"}
CORS_ORIGINS = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://127.0.0.1:5500,http://localhost:5500").split(",") if x.strip()]

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)

    inventory: Mapped[list["Inventory"]] = relationship(back_populates="branch")
    movements: Mapped[list["Movement"]] = relationship(back_populates="branch")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    min_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    inventory: Mapped[list["Inventory"]] = relationship(back_populates="product")
    movements: Mapped[list["Movement"]] = relationship(back_populates="product")


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (UniqueConstraint("product_id", "branch_id", name="uq_inventory_product_branch"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    product: Mapped[Product] = relationship(back_populates="inventory")
    branch: Mapped[Branch] = relationship(back_populates="inventory")


class Movement(Base):
    __tablename__ = "movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), nullable=False)
    movement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    product: Mapped[Product] = relationship(back_populates="movements")
    branch: Mapped[Branch] = relationship(back_populates="movements")


class StockUpdate(BaseModel):
    stock: int = Field(ge=0)


class TransferCreate(BaseModel):
    product_id: int
    source_branch_id: int
    destination_branch_id: int
    quantity: int = Field(gt=0)


@contextmanager
def db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def inventory_status(stock: int, min_stock: int) -> str:
    if stock == 0:
        return "out"
    if stock <= min_stock:
        return "low"
    return "available"


def serialize_inventory(inv: Inventory) -> dict:
    return {
        "inventory_id": inv.id,
        "product_id": inv.product.id,
        "sku": inv.product.sku,
        "name": inv.product.name,
        "category": inv.product.category,
        "price": inv.product.price,
        "min_stock": inv.product.min_stock,
        "branch_id": inv.branch.id,
        "branch_name": inv.branch.name,
        "district": inv.branch.district,
        "stock": inv.stock,
        "expiry_date": inv.expiry_date,
        "updated_at": inv.updated_at,
        "status": inventory_status(inv.stock, inv.product.min_stock),
    }


def seed_demo_data(session: Session) -> None:
    if session.scalar(select(func.count(Branch.id))) == 0:
        session.add_all([
            Branch(name="FarmaCerca Miraflores", district="Miraflores"),
            Branch(name="FarmaCerca San Isidro", district="San Isidro"),
            Branch(name="FarmaCerca Surco", district="Santiago de Surco"),
            Branch(name="FarmaCerca La Molina", district="La Molina"),
            Branch(name="FarmaCerca San Borja", district="San Borja"),
        ])
        session.flush()

    if session.scalar(select(func.count(Product.id))) == 0:
        session.add_all([
            Product(sku="MED-001", name="Paracetamol 500 mg", category="Medicamentos", price=4.50, min_stock=10),
            Product(sku="MED-002", name="Ibuprofeno 400 mg", category="Medicamentos", price=7.90, min_stock=12),
            Product(sku="MED-003", name="Loratadina 10 mg", category="Medicamentos", price=8.50, min_stock=8),
            Product(sku="CUI-001", name="Protector solar SPF 50", category="Cuidado personal", price=49.90, min_stock=6),
            Product(sku="BIE-001", name="Vitamina C 1000 mg", category="Bienestar y nutrición", price=29.90, min_stock=10),
            Product(sku="INF-001", name="Pañales talla M x 40", category="Cuidado infantil", price=54.90, min_stock=5),
            Product(sku="CUI-002", name="Shampoo dermatológico 400 ml", category="Cuidado personal", price=35.50, min_stock=7),
            Product(sku="BIE-002", name="Multivitamínico adulto x 30", category="Bienestar y nutrición", price=39.90, min_stock=8),
        ])
        session.flush()

    if session.scalar(select(func.count(Inventory.id))) == 0:
        branches = session.scalars(select(Branch).order_by(Branch.id)).all()
        products = session.scalars(select(Product).order_by(Product.id)).all()
        stock_matrix = {
            "MED-001": [42, 18, 4, 0, 27],
            "MED-002": [9, 31, 17, 6, 24],
            "MED-003": [16, 7, 11, 3, 20],
            "CUI-001": [8, 5, 0, 12, 9],
            "BIE-001": [25, 14, 8, 6, 19],
            "INF-001": [6, 4, 9, 2, 7],
            "CUI-002": [13, 8, 5, 11, 3],
            "BIE-002": [21, 6, 12, 0, 10],
        }
        today = date.today()
        for p_index, product in enumerate(products):
            values = stock_matrix[product.sku]
            for b_index, branch in enumerate(branches):
                days = 25 + ((p_index * 19 + b_index * 13) % 240)
                session.add(Inventory(
                    product_id=product.id,
                    branch_id=branch.id,
                    stock=values[b_index],
                    expiry_date=today + timedelta(days=days),
                ))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    if SEED_DEMO_DATA:
        with db_session() as session:
            seed_demo_data(session)


app = FastAPI(title="FarmaCerca API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "FarmaCerca API",
        "environment": ENVIRONMENT,
        "database": "sqlite" if DATABASE_URL.startswith("sqlite") else "postgresql",
    }


@app.get("/api/dashboard")
def dashboard():
    today = date.today()
    expiry_limit = today + timedelta(days=60)
    with db_session() as session:
        branches_count = session.scalar(select(func.count(Branch.id))) or 0
        products_count = session.scalar(select(func.count(Product.id))) or 0
        records = session.scalars(select(Inventory)).all()

        low_stock = sum(1 for inv in records if 0 < inv.stock <= inv.product.min_stock)
        out_of_stock = sum(1 for inv in records if inv.stock == 0)
        expiring = sum(1 for inv in records if inv.expiry_date and inv.expiry_date <= expiry_limit)
        healthy_records = sum(1 for inv in records if inv.stock > inv.product.min_stock)
        coverage = round((healthy_records / len(records) * 100), 1) if records else 0

        alerts = []
        for inv in session.scalars(select(Inventory).order_by(Inventory.stock.asc())).all():
            status = inventory_status(inv.stock, inv.product.min_stock)
            is_expiring = bool(inv.expiry_date and inv.expiry_date <= expiry_limit)
            if status in {"out", "low"} or is_expiring:
                alerts.append({
                    "product_id": inv.product.id,
                    "product": inv.product.name,
                    "sku": inv.product.sku,
                    "district": inv.branch.district,
                    "stock": inv.stock,
                    "alert_type": "Agotado" if status == "out" else "Stock bajo" if status == "low" else "Próximo a vencer",
                })

        branch_summary = []
        for branch in session.scalars(select(Branch).order_by(Branch.district)).all():
            invs = branch.inventory
            branch_summary.append({
                "id": branch.id,
                "district": branch.district,
                "total_units": sum(x.stock for x in invs),
                "unavailable": sum(1 for x in invs if x.stock == 0),
                "low_stock": sum(1 for x in invs if 0 < x.stock <= x.product.min_stock),
                "health": round((sum(1 for x in invs if x.stock > x.product.min_stock) / len(invs) * 100), 1) if invs else 0,
            })
        branch_summary.sort(key=lambda x: x["total_units"], reverse=True)

        movements = session.scalars(select(Movement).order_by(Movement.id.desc()).limit(8)).all()
        recent = [{
            "id": m.id,
            "product": m.product.name,
            "district": m.branch.district,
            "movement_type": m.movement_type,
            "quantity": m.quantity,
            "created_at": m.created_at,
        } for m in movements]

        return {
            "stats": {
                "branches": branches_count,
                "products": products_count,
                "low_stock": low_stock,
                "out_of_stock": out_of_stock,
                "expiring": expiring,
                "coverage": coverage,
            },
            "alerts": alerts[:8],
            "branch_summary": branch_summary,
            "recent": recent,
        }


@app.get("/api/inventory")
def inventory(
    q: str = "",
    branch: int | None = None,
    status: str = Query("all", pattern="^(all|available|low|out)$"),
):
    with db_session() as session:
        stmt = select(Inventory).join(Inventory.product).join(Inventory.branch)
        if q.strip():
            needle = f"%{q.strip().lower()}%"
            stmt = stmt.where(or_(
                func.lower(Product.name).like(needle),
                func.lower(Product.sku).like(needle),
                func.lower(Product.category).like(needle),
            ))
        if branch:
            stmt = stmt.where(Branch.id == branch)
        if status == "available":
            stmt = stmt.where(Inventory.stock > Product.min_stock)
        elif status == "low":
            stmt = stmt.where(Inventory.stock > 0, Inventory.stock <= Product.min_stock)
        elif status == "out":
            stmt = stmt.where(Inventory.stock == 0)

        rows = [serialize_inventory(inv) for inv in session.scalars(stmt.order_by(Product.name, Branch.district)).all()]
        branches = [{"id": b.id, "name": b.name, "district": b.district} for b in session.scalars(select(Branch).order_by(Branch.district)).all()]
        return {"rows": rows, "branches": branches}


@app.patch("/api/inventory/{inventory_id}")
def update_inventory(inventory_id: int, payload: StockUpdate):
    with db_session() as session:
        inv = session.get(Inventory, inventory_id)
        if not inv:
            raise HTTPException(status_code=404, detail="Registro de inventario no encontrado")
        difference = payload.stock - inv.stock
        inv.stock = payload.stock
        inv.updated_at = datetime.utcnow()
        if difference:
            session.add(Movement(
                product_id=inv.product_id,
                branch_id=inv.branch_id,
                movement_type="AJUSTE",
                quantity=difference,
                note="Actualización manual de inventario",
            ))
        session.flush()
        return {"message": "Stock actualizado correctamente", "inventory": serialize_inventory(inv)}


@app.get("/api/products/{product_id}")
def product_detail(product_id: int):
    expiry_limit = date.today() + timedelta(days=60)
    with db_session() as session:
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        inventory_rows = []
        for inv in sorted(product.inventory, key=lambda x: x.branch.district):
            inventory_rows.append({
                "inventory_id": inv.id,
                "branch_id": inv.branch.id,
                "district": inv.branch.district,
                "stock": inv.stock,
                "expiry_date": inv.expiry_date,
                "status": inventory_status(inv.stock, product.min_stock),
                "expiring": bool(inv.expiry_date and inv.expiry_date <= expiry_limit),
            })

        candidate_sources = [x for x in inventory_rows if x["stock"] > product.min_stock]
        recommended_source = max(candidate_sources, key=lambda x: x["stock"], default=None)
        destinations = sorted([x for x in inventory_rows if x["status"] in {"out", "low"}], key=lambda x: x["stock"])
        recommended_destination = destinations[0] if destinations else None
        suggested_quantity = 0
        if recommended_source and recommended_destination:
            target_level = product.min_stock + 5
            destination_need = max(target_level - recommended_destination["stock"], 0)
            source_surplus = max(recommended_source["stock"] - product.min_stock, 0)
            suggested_quantity = min(destination_need, source_surplus)

        movements = session.scalars(select(Movement).where(Movement.product_id == product_id).order_by(Movement.id.desc()).limit(8)).all()

        return {
            "product": {
                "id": product.id,
                "sku": product.sku,
                "name": product.name,
                "category": product.category,
                "price": product.price,
                "min_stock": product.min_stock,
            },
            "inventory": inventory_rows,
            "metrics": {
                "total_stock": sum(x["stock"] for x in inventory_rows),
                "available_branches": sum(1 for x in inventory_rows if x["stock"] > product.min_stock),
                "critical_branches": sum(1 for x in inventory_rows if x["status"] in {"out", "low"}),
            },
            "recommendation": {
                "source": recommended_source,
                "destination": recommended_destination,
                "quantity": suggested_quantity,
            },
            "recent": [{
                "id": m.id,
                "district": m.branch.district,
                "movement_type": m.movement_type,
                "quantity": m.quantity,
                "note": m.note,
                "created_at": m.created_at,
            } for m in movements],
        }


@app.get("/api/branches")
def branches():
    with db_session() as session:
        rows = []
        for branch in session.scalars(select(Branch).order_by(Branch.district)).all():
            invs = branch.inventory
            rows.append({
                "id": branch.id,
                "name": branch.name,
                "district": branch.district,
                "products": len(invs),
                "units": sum(i.stock for i in invs),
                "out": sum(1 for i in invs if i.stock == 0),
                "low": sum(1 for i in invs if 0 < i.stock <= i.product.min_stock),
                "health": round((sum(1 for i in invs if i.stock > i.product.min_stock) / len(invs) * 100), 1) if invs else 0,
            })
        return {"branches": rows}


@app.get("/api/alerts")
def alerts():
    expiry_limit = date.today() + timedelta(days=60)
    with db_session() as session:
        alert_rows = []
        for inv in session.scalars(select(Inventory).order_by(Inventory.stock.asc())).all():
            status = inventory_status(inv.stock, inv.product.min_stock)
            is_expiring = bool(inv.expiry_date and inv.expiry_date <= expiry_limit)
            if status in {"out", "low"} or is_expiring:
                priority = "out" if status == "out" else "low" if status == "low" else "expiry"
                alert_rows.append({
                    "product_id": inv.product.id,
                    "branch_id": inv.branch.id,
                    "name": inv.product.name,
                    "sku": inv.product.sku,
                    "district": inv.branch.district,
                    "stock": inv.stock,
                    "min_stock": inv.product.min_stock,
                    "expiry_date": inv.expiry_date,
                    "status": priority,
                })
        order = {"out": 0, "low": 1, "expiry": 2}
        alert_rows.sort(key=lambda x: (order[x["status"]], x["expiry_date"] or date.max))
        return {"alerts": alert_rows}


@app.get("/api/transfers")
def transfers():
    with db_session() as session:
        products = [{"id": p.id, "sku": p.sku, "name": p.name} for p in session.scalars(select(Product).order_by(Product.name)).all()]
        branches = [{"id": b.id, "name": b.name, "district": b.district} for b in session.scalars(select(Branch).order_by(Branch.district)).all()]
        movements = session.scalars(
            select(Movement)
            .where(Movement.movement_type.in_(["TRANSFERENCIA_SALIDA", "TRANSFERENCIA_ENTRADA"]))
            .order_by(Movement.id.desc())
            .limit(12)
        ).all()
        recent = [{
            "id": m.id,
            "created_at": m.created_at,
            "product": m.product.name,
            "district": m.branch.district,
            "movement_type": m.movement_type,
            "quantity": m.quantity,
            "note": m.note,
        } for m in movements]
        return {"products": products, "branches": branches, "recent": recent}


@app.post("/api/transfers", status_code=201)
def create_transfer(payload: TransferCreate):
    if payload.source_branch_id == payload.destination_branch_id:
        raise HTTPException(status_code=400, detail="Origen y destino deben ser distintos")

    with db_session() as session:
        source = session.scalar(select(Inventory).where(
            Inventory.product_id == payload.product_id,
            Inventory.branch_id == payload.source_branch_id,
        ))
        destination = session.scalar(select(Inventory).where(
            Inventory.product_id == payload.product_id,
            Inventory.branch_id == payload.destination_branch_id,
        ))
        if not source or source.stock < payload.quantity:
            raise HTTPException(status_code=400, detail="Stock insuficiente en la sucursal de origen")

        if not destination:
            destination = Inventory(
                product_id=payload.product_id,
                branch_id=payload.destination_branch_id,
                stock=0,
                expiry_date=source.expiry_date,
            )
            session.add(destination)
            session.flush()

        source.stock -= payload.quantity
        destination.stock += payload.quantity
        source.updated_at = datetime.utcnow()
        destination.updated_at = datetime.utcnow()

        source_branch = session.get(Branch, payload.source_branch_id)
        destination_branch = session.get(Branch, payload.destination_branch_id)
        session.add_all([
            Movement(
                product_id=payload.product_id,
                branch_id=payload.source_branch_id,
                movement_type="TRANSFERENCIA_SALIDA",
                quantity=-payload.quantity,
                note=f"Transferencia a {destination_branch.district}",
            ),
            Movement(
                product_id=payload.product_id,
                branch_id=payload.destination_branch_id,
                movement_type="TRANSFERENCIA_ENTRADA",
                quantity=payload.quantity,
                note=f"Transferencia desde {source_branch.district}",
            ),
        ])
        return {
            "message": "Transferencia registrada correctamente",
            "source_stock": source.stock,
            "destination_stock": destination.stock,
        }


@app.post("/api/demo/reset")
def reset_demo():
    if ENVIRONMENT == "production":
        raise HTTPException(status_code=403, detail="La restauración de demo está deshabilitada en producción")
    with db_session() as session:
        session.execute(delete(Movement))
        session.execute(delete(Inventory))
        session.flush()
        seed_demo_data(session)
    return {"message": "Datos demo restaurados"}
