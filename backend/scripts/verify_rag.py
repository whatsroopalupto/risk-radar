"""Verify retrieval/generation without printing article bodies or credentials."""
import json
from pathlib import Path
from backend.app.db import init_db,SessionLocal,display_namespace,utcnow
from backend.app.evidence import answer_question

if __name__=="__main__":
    init_db()
    with SessionLocal() as db: namespace=display_namespace(db)
    result=answer_question("What evidence concerns oil shipping through Hormuz?",namespace)
    known={source["id"] for source in result["sources"]}
    report={"checked_at":utcnow().isoformat(),"dataset":namespace,"mode":result["mode"],
        "generation_status":result["generation_status"],"model":result["model"],
        "retrieved_sources":len(result["sources"]),"paragraphs":len(result["paragraphs"]),
        "all_citations_resolve":all(ref in known for paragraph in result["paragraphs"] for ref in paragraph["citations"])}
    output=Path("output/verification/rag.json")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))
