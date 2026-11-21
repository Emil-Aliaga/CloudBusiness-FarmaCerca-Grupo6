from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, delete, func, or_, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DEFAULT_SQLITE_URL = f"sqlite:///{(BASE_DIR / 'farmacerca.db').as_posix()}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
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


def seed_demo_data(session: Session) -> None:
    if session.scalar(select(func.count(Branch.id))) == 0:
        session.add_all(
            [
                Branch(name="FarmaCerca Miraflores", district="Miraflores"),
                Branch(name="FarmaCerca San Isidro", district="San Isidro"),
                Branch(name="FarmaCerca Surco", district="Santiago de Surco"),
                Branch(name="FarmaCerca La Molina", district="La Molina"),
                Branch(name="FarmaCerca San Borja", district="San Borja"),
            ]
        )
        session.flush()

    if session.scalar(select(func.count(Product.id))) == 0:
        session.add_all(
            [
                Product(sku="MED-001", name="Paracetamol 500 mg", category="Medicamentos", price=4.50, min_stock=10),
                Product(sku="MED-002", name="Ibuprofeno 400 mg", category="Medicamentos", price=7.90, min_stock=12),
                Product(sku="MED-003", name="Loratadina 10 mg", category="Medicamentos", price=8.50, min_stock=8),
                Product(sku="CUI-001", name="Protector solar SPF 50", category="Cuidado personal", price=49.90, min_stock=6),
                Product(sku="BIE-001", name="Vitamina C 1000 mg", category="Bienestar y nutrición", price=29.90, min_stock=10),
                Product(sku="INF-001", name="Pañales talla M x 40", category="Cuidado infantil", price=54.90, min_stock=5),
                Product(sku="CUI-002", name="Shampoo dermatológico 400 ml", category="Cuidado personal", price=35.50, min_stock=7),
                Product(sku="BIE-002", name="Multivitamínico adulto x 30", category="Bienestar y nutrición", price=39.90, min_stock=8),
            ]
        )
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
                session.add(
                    Inventory(
                        product_id=product.id,
                        branch_id=branch.id,
                        stock=values[b_index],
                        expiry_date=today + timedelta(days=days),
                    )
                )


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with db_session() as session:
        seed_demo_data(session)


app = FastAPI(title="FarmaCerca Inventario", version="0.4.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def get_context(request: Request, active: str, **kwargs):
    database_label = "SQLite local" if DATABASE_URL.startswith("sqlite") else "PostgreSQL / RDS"
    environment_label = "Local" if ENVIRONMENT.lower() != "production" else "AWS / Producción"
    return {
        "request": request,
        "active": active,
        "message": request.query_params.get("message"),
        "error": request.query_params.get("error"),
        "database_label": database_label,
        "environment_label": environment_label,
        "is_cloud": not DATABASE_URL.startswith("sqlite"),
        "now": datetime.now(),
        **kwargs,
    }


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    today = date.today()
    expiry_limit = today + timedelta(days=60)
    with db_session() as session:
        branches_count = session.scalar(select(func.count(Branch.id))) or 0
        products_count = session.scalar(select(func.count(Product.id))) or 0
        records = session.scalars(select(Inventory)).all()

        low_stock = 0
        out_of_stock = 0
        expiring = 0
        for inv in records:
            if inv.stock == 0:
                out_of_stock += 1
            elif inv.stock <= inv.product.min_stock:
                low_stock += 1
            if inv.expiry_date and inv.expiry_date <= expiry_limit:
                expiring += 1

        healthy_records = sum(1 for inv in records if inv.stock > inv.product.min_stock)
        coverage = round((healthy_records / len(records) * 100), 1) if records else 0
        stats = {
            "branches": branches_count,
            "products": products_count,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock,
            "expiring": expiring,
            "coverage": coverage,
        }

        alert_rows = []
        for inv in session.scalars(select(Inventory).order_by(Inventory.stock.asc())).all():
            status = inventory_status(inv.stock, inv.product.min_stock)
            is_expiring = bool(inv.expiry_date and inv.expiry_date <= expiry_limit)
            if status in {"out", "low"} or is_expiring:
                alert_rows.append(
                    {
                        "product": inv.product.name,
                        "sku": inv.product.sku,
                        "district": inv.branch.district,
                        "stock": inv.stock,
                        "alert_type": "Agotado" if status == "out" else "Stock bajo" if status == "low" else "Próximo a vencer",
                    }
                )
        alerts = alert_rows[:8]

        branch_summary = []
        for branch in session.scalars(select(Branch).order_by(Branch.district)).all():
            invs = branch.inventory
            branch_summary.append(
                {
                    "id": branch.id,
                    "district": branch.district,
                    "total_units": sum(x.stock for x in invs),
                    "unavailable": sum(1 for x in invs if x.stock == 0),
                    "low_stock": sum(1 for x in invs if 0 < x.stock <= x.product.min_stock),
                    "health": round((sum(1 for x in invs if x.stock > x.product.min_stock) / len(invs) * 100), 1) if invs else 0,
                }
            )
        branch_summary.sort(key=lambda x: x["total_units"], reverse=True)

        recent_movements = session.scalars(select(Movement).order_by(Movement.id.desc()).limit(5)).all()
        recent = [
            {
                "product": m.product.name,
                "district": m.branch.district,
                "movement_type": m.movement_type,
                "quantity": m.quantity,
                "created_at": m.created_at,
            }
            for m in recent_movements
        ]

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        get_context(request, "dashboard", stats=stats, alerts=alerts, branch_summary=branch_summary, recent=recent),
    )


@app.get("/inventory", response_class=HTMLResponse)
def inventory_page(request: Request, q: str = "", branch: int | None = None, status: str = "all"):
    with db_session() as session:
        stmt = select(Inventory).join(Inventory.product).join(Inventory.branch)
        if q.strip():
            needle = f"%{q.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Product.name).like(needle),
                    func.lower(Product.sku).like(needle),
                    func.lower(Product.category).like(needle),
                )
            )
        if branch:
            stmt = stmt.where(Branch.id == branch)
        if status == "available":
            stmt = stmt.where(Inventory.stock > Product.min_stock)
        elif status == "low":
            stmt = stmt.where(Inventory.stock > 0, Inventory.stock <= Product.min_stock)
        elif status == "out":
            stmt = stmt.where(Inventory.stock == 0)

        inventories = session.scalars(stmt.order_by(Product.name, Branch.district)).all()
        rows = [
            {
                "inventory_id": inv.id,
                "product_id": inv.product.id,
                "sku": inv.product.sku,
                "name": inv.product.name,
                "category": inv.product.category,
                "price": inv.product.price,
                "min_stock": inv.product.min_stock,
                "branch_id": inv.branch.id,
                "district": inv.branch.district,
                "stock": inv.stock,
                "expiry_date": inv.expiry_date,
                "updated_at": inv.updated_at,
                "status": inventory_status(inv.stock, inv.product.min_stock),
            }
            for inv in inventories
        ]
        branches = session.scalars(select(Branch).order_by(Branch.district)).all()

    return templates.TemplateResponse(
        request,
        "inventory.html",
        get_context(
            request,
            "inventory",
            rows=rows,
            branches=branches,
            q=q,
            selected_branch=branch,
            selected_status=status,
        ),
    )


@app.post("/inventory/update")
def update_inventory(inventory_id: int = Form(...), new_stock: int = Form(...), return_to: str = Form("/inventory")):
    if new_stock < 0:
        return RedirectResponse(f"{return_to}?error={quote_plus('El stock no puede ser negativo')}", status_code=303)

    with db_session() as session:
        inv = session.get(Inventory, inventory_id)
        if not inv:
            return RedirectResponse(f"{return_to}?error={quote_plus('Registro no encontrado')}", status_code=303)
        difference = new_stock - inv.stock
        inv.stock = new_stock
        inv.updated_at = datetime.utcnow()
        if difference:
            session.add(
                Movement(
                    product_id=inv.product_id,
                    branch_id=inv.branch_id,
                    movement_type="AJUSTE",
                    quantity=difference,
                    note="Actualización manual desde el MVP",
                )
            )

    sep = "&" if "?" in return_to else "?"
    return RedirectResponse(f"{return_to}{sep}message={quote_plus('Stock actualizado correctamente')}", status_code=303)


@app.get("/products/{product_id}", response_class=HTMLResponse)
def product_detail(request: Request, product_id: int):
    today = date.today()
    expiry_limit = today + timedelta(days=60)
    with db_session() as session:
        product = session.get(Product, product_id)
        if not product:
            return RedirectResponse("/inventory?error=Producto+no+encontrado", status_code=303)

        inventory_rows = []
        for inv in sorted(product.inventory, key=lambda x: x.branch.district):
            inventory_rows.append(
                {
                    "inventory_id": inv.id,
                    "branch_id": inv.branch.id,
                    "district": inv.branch.district,
                    "stock": inv.stock,
                    "expiry_date": inv.expiry_date,
                    "status": inventory_status(inv.stock, product.min_stock),
                    "expiring": bool(inv.expiry_date and inv.expiry_date <= expiry_limit),
                }
            )

        total_stock = sum(x["stock"] for x in inventory_rows)
        available_branches = sum(1 for x in inventory_rows if x["stock"] > product.min_stock)
        critical_branches = sum(1 for x in inventory_rows if x["status"] in {"out", "low"})
        recent_movements = session.scalars(
            select(Movement).where(Movement.product_id == product_id).order_by(Movement.id.desc()).limit(8)
        ).all()
        recent = [
            {
                "district": m.branch.district,
                "movement_type": m.movement_type,
                "quantity": m.quantity,
                "note": m.note,
                "created_at": m.created_at,
            }
            for m in recent_movements
        ]

        candidate_sources = [x for x in inventory_rows if x["stock"] > product.min_stock]
        recommended_source = max(candidate_sources, key=lambda x: x["stock"], default=None)
        critical_destinations = sorted(
            [x for x in inventory_rows if x["status"] in {"out", "low"}],
            key=lambda x: x["stock"],
        )
        recommended_destination = critical_destinations[0] if critical_destinations else None
        suggested_quantity = 0
        if recommended_source and recommended_destination:
            target_level = product.min_stock + 5
            destination_need = max(target_level - recommended_destination["stock"], 0)
            source_surplus = max(recommended_source["stock"] - product.min_stock, 0)
            suggested_quantity = min(destination_need, source_surplus)

        product_data = {
            "id": product.id,
            "sku": product.sku,
            "name": product.name,
            "category": product.category,
            "price": product.price,
            "min_stock": product.min_stock,
        }

    return templates.TemplateResponse(
        request,
        "product_detail.html",
        get_context(
            request,
            "inventory",
            product=product_data,
            inventory_rows=inventory_rows,
            total_stock=total_stock,
            available_branches=available_branches,
            critical_branches=critical_branches,
            recent=recent,
            recommended_source=recommended_source,
            recommended_destination=recommended_destination,
            suggested_quantity=suggested_quantity,
        ),
    )


@app.get("/branches", response_class=HTMLResponse)
def branches_page(request: Request):
    with db_session() as session:
        rows = []
        for branch in session.scalars(select(Branch).order_by(Branch.district)).all():
            invs = branch.inventory
            rows.append(
                {
                    "id": branch.id,
                    "name": branch.name,
                    "district": branch.district,
                    "products": len(invs),
                    "units": sum(i.stock for i in invs),
                    "out": sum(1 for i in invs if i.stock == 0),
                    "low": sum(1 for i in invs if 0 < i.stock <= i.product.min_stock),
                    "health": round((sum(1 for i in invs if i.stock > i.product.min_stock) / len(invs) * 100), 1) if invs else 0,
                }
            )
    return templates.TemplateResponse(request, "branches.html", get_context(request, "branches", branches=rows))


@app.get("/alerts", response_class=HTMLResponse)
def alerts_page(request: Request):
    expiry_limit = date.today() + timedelta(days=60)
    with db_session() as session:
        alert_rows = []
        inventories = session.scalars(select(Inventory).order_by(Inventory.stock.asc())).all()
        for inv in inventories:
            status = inventory_status(inv.stock, inv.product.min_stock)
            is_expiring = bool(inv.expiry_date and inv.expiry_date <= expiry_limit)
            if status in {"out", "low"} or is_expiring:
                priority = "out" if status == "out" else "low" if status == "low" else "expiry"
                alert_rows.append(
                    {
                        "product_id": inv.product.id,
                        "branch_id": inv.branch.id,
                        "name": inv.product.name,
                        "sku": inv.product.sku,
                        "district": inv.branch.district,
                        "stock": inv.stock,
                        "min_stock": inv.product.min_stock,
                        "expiry_date": inv.expiry_date,
                        "status": priority,
                    }
                )
        order = {"out": 0, "low": 1, "expiry": 2}
        alert_rows.sort(key=lambda x: (order[x["status"]], x["expiry_date"] or date.max))

    return templates.TemplateResponse(request, "alerts.html", get_context(request, "alerts", alerts=alert_rows))


@app.get("/transfers", response_class=HTMLResponse)
def transfers_page(
    request: Request,
    product_id: int | None = None,
    source_branch_id: int | None = None,
    destination_branch_id: int | None = None,
    quantity: int | None = None,
):
    with db_session() as session:
        products = session.scalars(select(Product).order_by(Product.name)).all()
        branches = session.scalars(select(Branch).order_by(Branch.district)).all()
        movements = session.scalars(
            select(Movement)
            .where(Movement.movement_type.in_(["TRANSFERENCIA_SALIDA", "TRANSFERENCIA_ENTRADA"]))
            .order_by(Movement.id.desc())
            .limit(12)
        ).all()
        recent = [
            {
                "created_at": m.created_at,
                "product": m.product.name,
                "district": m.branch.district,
                "movement_type": m.movement_type,
                "quantity": m.quantity,
                "note": m.note,
            }
            for m in movements
        ]

    return templates.TemplateResponse(
        request,
        "transfers.html",
        get_context(
            request,
            "transfers",
            products=products,
            branches=branches,
            recent=recent,
            selected_product_id=product_id,
            selected_source_branch_id=source_branch_id,
            selected_destination_branch_id=destination_branch_id,
            suggested_quantity=quantity,
        ),
    )


@app.post("/transfers")
def create_transfer(
    product_id: int = Form(...),
    source_branch_id: int = Form(...),
    destination_branch_id: int = Form(...),
    quantity: int = Form(...),
):
    base_url = f"/transfers?product_id={product_id}&destination_branch_id={destination_branch_id}"
    if source_branch_id == destination_branch_id:
        return RedirectResponse(f"{base_url}&error={quote_plus('Origen y destino deben ser distintos')}", status_code=303)
    if quantity <= 0:
        return RedirectResponse(f"{base_url}&error={quote_plus('La cantidad debe ser mayor a cero')}", status_code=303)

    with db_session() as session:
        source = session.scalar(
            select(Inventory).where(Inventory.product_id == product_id, Inventory.branch_id == source_branch_id)
        )
        destination = session.scalar(
            select(Inventory).where(Inventory.product_id == product_id, Inventory.branch_id == destination_branch_id)
        )
        if not source or source.stock < quantity:
            return RedirectResponse(f"{base_url}&error={quote_plus('Stock insuficiente en la sucursal de origen')}", status_code=303)

        if not destination:
            destination = Inventory(
                product_id=product_id,
                branch_id=destination_branch_id,
                stock=0,
                expiry_date=source.expiry_date,
            )
            session.add(destination)
            session.flush()

        source.stock -= quantity
        destination.stock += quantity
        source.updated_at = datetime.utcnow()
        destination.updated_at = datetime.utcnow()

        source_branch = session.get(Branch, source_branch_id)
        destination_branch = session.get(Branch, destination_branch_id)
        session.add_all(
            [
                Movement(
                    product_id=product_id,
                    branch_id=source_branch_id,
                    movement_type="TRANSFERENCIA_SALIDA",
                    quantity=-quantity,
                    note=f"Transferencia a {destination_branch.district}",
                ),
                Movement(
                    product_id=product_id,
                    branch_id=destination_branch_id,
                    movement_type="TRANSFERENCIA_ENTRADA",
                    quantity=quantity,
                    note=f"Transferencia desde {source_branch.district}",
                ),
            ]
        )

    return RedirectResponse(f"{base_url}&message={quote_plus('Transferencia registrada correctamente')}", status_code=303)


@app.post("/demo/reset")
def reset_demo():
    with db_session() as session:
        session.execute(delete(Movement))
        session.execute(delete(Inventory))
        session.flush()
        seed_demo_data(session)
    return RedirectResponse("/?message=" + quote_plus("Demo restaurada al escenario inicial"), status_code=303)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": "FarmaCerca Inventario",
        "database": "sqlite" if DATABASE_URL.startswith("sqlite") else "postgresql",
    }
