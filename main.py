from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import math
import time
import hashlib
from datetime import datetime

# --- DATABASE CONFIGURATION ---
# Format: postgresql://username:password@host/database_name
SQLALCHEMY_DATABASE_URL = "postgresql://muai_node:Epistemic2026!@127.0.0.1/muai_ledger"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- DATABASE MODELS (The Immutable Ledger) ---
class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    action_type = Column(String)  # e.g., BUY_INTENT, AURA_MINT
    delta_aura = Column(Float, default=0.0)
    delta_kes = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    prev_hash = Column(String)
    current_hash = Column(String, unique=True, index=True)

# Create the tables in the database
Base.metadata.create_all(bind=engine)

# --- FASTAPI APP INITIATION ---
app = FastAPI(
    title="MuAI Sovereign Epistemic Engine",
    description="API Kernel + Immutable Ledger for the Moi University Agent Network",
    version="2.0.0"
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- PYDANTIC SCHEMAS (For Kotlin Client Inputs) ---
class EventPayload(BaseModel):
    user_id: str
    action_type: str
    delta_aura: float
    delta_kes: float

class SpneRequest(BaseModel):
    min_price: float
    max_price: float
    buyer_discount_factor: float
    seller_discount_factor: float

# --- CORE API ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "Engine & Ledger Online", "layer": "L7 Application + Postgres"}

@app.post("/engine/market/spne")
def calculate_nash_equilibrium(req: SpneRequest):
    """Computes the Subgame Perfect Nash Equilibrium (SPNE)."""
    if req.seller_discount_factor * req.buyer_discount_factor >= 1.0:
        raise HTTPException(status_code=400, detail="Invalid discount factors.")

    surplus_fraction = (1.0 - req.buyer_discount_factor) / (1.0 - (req.seller_discount_factor * req.buyer_discount_factor))
    clearing_price = req.min_price + (req.max_price - req.min_price) * surplus_fraction

    return {
        "status": "CONSENSUS_REACHED",
        "clearing_price": round(clearing_price, 2)
    }

@app.post("/engine/ledger/commit")
def commit_to_ledger(event: EventPayload, db: Session = Depends(get_db)):
    """
    Writes an event to the immutable hash-chained Postgres ledger.
    """
    # 1. Fetch the hash of the last entry in the DB to maintain the chain
    last_entry = db.query(LedgerEntry).order_by(LedgerEntry.id.desc()).first()
    prev_hash = last_entry.current_hash if last_entry else "0000000000000000000000000000000000000000000000000000000000000000"

    # 2. Cryptographically hash the new payload combined with the prev_hash
    data_string = f"{prev_hash}|{event.user_id}|{event.action_type}|{event.delta_aura}|{event.delta_kes}|{time.time()}"
    current_hash = hashlib.sha256(data_string.encode()).hexdigest()

    # 3. Create the Database Record
    new_entry = LedgerEntry(
        user_id=event.user_id,
        action_type=event.action_type,
        delta_aura=event.delta_aura,
        delta_kes=event.delta_kes,
        prev_hash=prev_hash,
        current_hash=current_hash
    )

    # 4. Commit to Postgres
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    return {
        "status": "STATE_COMMITTED",
        "transaction_hash": current_hash,
        "entry_id": new_entry.id
    }