from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .agents import OrchestratorAgent
from .models import AnalyzeResponse, ContractState, PolicyPack, QuestionRequest, ReassessRequest, SampleContractResponse, TextAnalyzeRequest
from .sample_data import (
    SAMPLE_CONTRACT_FILE_NAME,
    SAMPLE_CONTRACT_TEXT,
    SAMPLE_POLICY,
    SAMPLE_SIMPLE_INBOUND_FILE_NAME,
    SAMPLE_SIMPLE_INBOUND_TEXT,
)


@dataclass
class StoredContract:
    state: ContractState
    retriever: object


app = FastAPI(title="Contract AI Assistant Prototype", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = OrchestratorAgent()
STORE: dict[str, StoredContract] = {}


@app.get("/api")
def api_root() -> dict[str, str]:
    return {"message": "Contract AI Assistant backend is running."}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/sample-contract", response_model=SampleContractResponse)
def sample_contract(kind: str = "default") -> SampleContractResponse:
    if kind == "simple_inbound":
        return SampleContractResponse(file_name=SAMPLE_SIMPLE_INBOUND_FILE_NAME, text=SAMPLE_SIMPLE_INBOUND_TEXT, policy_pack=SAMPLE_POLICY)
    return SampleContractResponse(file_name=SAMPLE_CONTRACT_FILE_NAME, text=SAMPLE_CONTRACT_TEXT, policy_pack=SAMPLE_POLICY)


@app.post("/api/analyze-text", response_model=AnalyzeResponse)
def analyze_text(request: TextAnalyzeRequest) -> AnalyzeResponse:
    state, retriever = orchestrator.analyze_text(request.file_name, request.text, request.policy_pack)
    STORE[state.contract_id] = StoredContract(state=state, retriever=retriever)
    return AnalyzeResponse(contract=state)


@app.post("/api/analyze-upload", response_model=AnalyzeResponse)
async def analyze_upload(
    file: UploadFile = File(...),
    policy_json: str | None = Form(default=None),
) -> AnalyzeResponse:
    file_bytes = await file.read()
    try:
        policy_pack = PolicyPack(**json.loads(policy_json)) if policy_json else PolicyPack()
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=f"Invalid policy_json payload: {exc}") from exc
    try:
        state, retriever = orchestrator.analyze_upload(file.filename or "uploaded_contract", file_bytes, policy_pack)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    STORE[state.contract_id] = StoredContract(state=state, retriever=retriever)
    return AnalyzeResponse(contract=state)


@app.get("/api/contracts/{contract_id}", response_model=AnalyzeResponse)
def get_contract(contract_id: str) -> AnalyzeResponse:
    stored = STORE.get(contract_id)
    if not stored:
        raise HTTPException(status_code=404, detail="Contract not found")
    return AnalyzeResponse(contract=stored.state)


@app.post("/api/contracts/{contract_id}/question", response_model=AnalyzeResponse)
def ask_question(contract_id: str, request: QuestionRequest) -> AnalyzeResponse:
    stored = STORE.get(contract_id)
    if not stored:
        raise HTTPException(status_code=404, detail="Contract not found")
    state = orchestrator.answer_question(stored.state, stored.retriever, request.question)
    STORE[contract_id] = StoredContract(state=state, retriever=stored.retriever)
    return AnalyzeResponse(contract=state)


@app.post("/api/contracts/{contract_id}/reassess", response_model=AnalyzeResponse)
def reassess(contract_id: str, request: ReassessRequest) -> AnalyzeResponse:
    stored = STORE.get(contract_id)
    if not stored:
        raise HTTPException(status_code=404, detail="Contract not found")
    state = orchestrator.reassess(stored.state, request.policy_pack)
    STORE[contract_id] = StoredContract(state=state, retriever=stored.retriever)
    return AnalyzeResponse(contract=state)


FRONTEND_DIST_CANDIDATES = [
    Path(__file__).resolve().parent.parent / "frontend_dist",
    Path(__file__).resolve().parent.parent.parent / "frontend_dist",
]
FRONTEND_DIST = next((path for path in FRONTEND_DIST_CANDIDATES if path.exists()), FRONTEND_DIST_CANDIDATES[0])
ASSETS_DIR = FRONTEND_DIST / "assets"
INDEX_FILE = FRONTEND_DIST / "index.html"

if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


@app.get("/")
def ui_root():
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return JSONResponse({"message": "Contract AI Assistant backend is running. Frontend assets not found."})


@app.get("/{full_path:path}")
def spa_fallback(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    requested = FRONTEND_DIST / full_path
    if requested.is_file():
        return FileResponse(requested)
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    raise HTTPException(status_code=404, detail="Frontend assets not found")
