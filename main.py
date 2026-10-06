from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import math
import time

app = FastAPI(
    title="MuAI Sovereign Epistemic Engine",
    description="API Kernel for the Moi University Agent Network",
    version="1.0.0"
)

# --- MATHEMATICAL CONSTANTS ---
CAMPUS_MEAN_AURA = 100.0
HALF_LIFE_DAYS = 112.0 # 16 weeks
THETA = math.log(2) / HALF_LIFE_DAYS

# --- DATA MODELS (Payload Schemas for Kotlin) ---
class StudentState(BaseModel):
    student_id: str
    current_aura: float
    last_active_timestamp: float # Unix epoch

class SpneRequest(BaseModel):
    min_price: float
    max_price: float
    buyer_discount_factor: float # 0.0 to 1.0 (Urgency)
    seller_discount_factor: float # 0.0 to 1.0 (Urgency)

# --- CORE API ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "Engine Online", "layer": "L7 Application"}

@app.post("/engine/aura/calculate_decay")
def calculate_aura_decay(state: StudentState):
    """
    Calculates the thermodynamic decay of a student's Aura based on the SDE model.
    A(t) = Mean + (A_0 - Mean) * e^(-theta * delta_t)
    """
    current_time = time.time()
    # Convert seconds to days
    delta_days = (current_time - state.last_active_timestamp) / 86400.0 
    
    if delta_days < 0:
        raise HTTPException(status_code=400, detail="Temporal anomaly: Future timestamp detected.")

    # The Jump-Diffusion Decay Equation
    decayed_aura = CAMPUS_MEAN_AURA + (state.current_aura - CAMPUS_MEAN_AURA) * math.exp(-THETA * delta_days)
    
    return {
        "student_id": state.student_id,
        "original_aura": round(state.current_aura, 2),
        "decayed_aura": round(decayed_aura, 2),
        "days_elapsed": round(delta_days, 2),
        "aura_velocity_per_day": round((decayed_aura - state.current_aura) / delta_days if delta_days > 0 else 0, 4)
    }

@app.post("/engine/market/spne")
def calculate_nash_equilibrium(req: SpneRequest):
    """
    Computes the Subgame Perfect Nash Equilibrium (SPNE) for agent negotiations.
    P* = P_min + (P_max - P_min) * [(1 - delta_B) / (1 - delta_S * delta_B)]
    """
    if req.seller_discount_factor * req.buyer_discount_factor >= 1.0:
        raise HTTPException(status_code=400, detail="Discount factors must be strictly less than 1.0 combined to resolve.")

    delta_b = req.buyer_discount_factor
    delta_s = req.seller_discount_factor
    
    # The Rubinstein Alternating-Offers calculation
    surplus_fraction = (1.0 - delta_b) / (1.0 - (delta_s * delta_b))
    clearing_price = req.min_price + (req.max_price - req.min_price) * surplus_fraction

    return {
        "status": "CONSENSUS_REACHED",
        "clearing_price": round(clearing_price, 2),
        "seller_surplus_captured": round(surplus_fraction * 100, 2),
        "message": "Mathematical compromise achieved without LLM hallucination."
    }