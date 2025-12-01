from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.tax_engine import TaxInput, calculate_tax

app = FastAPI(title="Irish Tax Calculator API (Simplified 2025)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/calc")
def calc(
    employed_income: float = 0.0,
    self_employed_income: float = 0.0,
    status: str = "single",              # <-- FIXED
    children_under18: int = 0,
    year: int = 2025,
):
    ti = TaxInput(
        employed_income=employed_income,
        self_employed_income=self_employed_income,
        status=status,
        children_under18=children_under18,
        year=year,
    )
    return calculate_tax(ti)