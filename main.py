import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Literal, Dict
from datetime import datetime

from database import create_document, get_documents, db
from schemas import Generation

app = FastAPI(title="VibeCraft API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    source_type: Literal['spline', 'three'] = Field('spline')
    input_url: Optional[HttpUrl] = None
    animation: Literal['framer', 'gsap'] = Field('framer')
    name: str = Field('GeneratedExperience', min_length=3, max_length=64)
    options: Optional[Dict] = None


@app.get("/")
def read_root():
    return {"message": "VibeCraft backend running", "version": app.version}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name or "Unknown"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


def build_react_component(req: GenerateRequest) -> str:
    name = ''.join(ch for ch in req.name.title() if ch.isalnum())
    use_spline = req.source_type == 'spline'
    is_framer = req.animation == 'framer'

    header_imports = []
    body = []

    if use_spline:
        header_imports.append("import Spline from '@splinetool/react-spline';")
    if is_framer:
        header_imports.append("import { motion } from 'framer-motion';")
    else:
        header_imports.append("import { useLayoutEffect, useRef } from 'react';")
        header_imports.append("import gsap from 'gsap';")

    header = "\n".join(header_imports)

    if is_framer:
        body.append(f"export default function {name}() {{")
        body.append("  return (")
        body.append("    <section className=\"relative w-full min-h-[60vh] overflow-hidden bg-gradient-to-b from-zinc-50 to-white dark:from-zinc-900 dark:to-zinc-950\">")
        if use_spline:
            url = req.input_url or "https://prod.spline.design/VyGeZv58yuk8j7Yy/scene.splinecode"
            body.append("      <div className=\"absolute inset-0\">")
            body.append(f"        <Spline scene=\"{url}\" style={{ width: '100%', height: '100%' }} />")
            body.append("      </div>")
            body.append("      <div className=\"pointer-events-none absolute inset-0 bg-gradient-to-b from-white/60 via-white/20 to-white/80 dark:from-zinc-900/70 dark:via-zinc-900/30 dark:to-zinc-950/80\" />")
        body.append("      <div className=\"relative z-10 mx-auto max-w-5xl px-6 py-24 text-center\">")
        body.append("        <motion.h2 initial={{opacity:0,y:16}} animate={{opacity:1,y:0}} transition={{duration:0.6}} className=\"text-3xl sm:text-5xl font-bold tracking-tight text-zinc-900 dark:text-white\">Generated Experience</motion.h2>")
        body.append("        <motion.p initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} transition={{duration:0.6,delay:0.1}} className=\"mt-3 text-zinc-600 dark:text-zinc-300\">Interactive, tech, futuristic, digital, minimalist.</motion.p>")
        body.append("      </div>")
        body.append("    </section>")
        body.append("  );")
        body.append("}")
    else:
        body.append("export default function " + name + "() {")
        body.append("  const rootRef = useRef(null);")
        body.append("  useLayoutEffect(() => {")
        body.append("    const ctx = gsap.context(() => {")
        body.append("      gsap.fromTo('[data-hero]', { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.8, ease: 'power2.out' });")
        body.append("    }, rootRef);")
        body.append("    return () => ctx.revert();")
        body.append("  }, []);")
        body.append("  return (")
        body.append("    <section ref={rootRef} className=\"relative w-full min-h-[60vh] overflow-hidden bg-gradient-to-b from-zinc-50 to-white dark:from-zinc-900 dark:to-zinc-950\">")
        if use_spline:
            url = req.input_url or "https://prod.spline.design/VyGeZv58yuk8j7Yy/scene.splinecode"
            body.append("      <div className=\"absolute inset-0\">")
            body.append(f"        <Spline scene=\"{url}\" style={{ width: '100%', height: '100%' }} />")
            body.append("      </div>")
            body.append("      <div className=\"pointer-events-none absolute inset-0 bg-gradient-to-b from-white/60 via-white/20 to-white/80 dark:from-zinc-900/70 dark:via-zinc-900/30 dark:to-zinc-950/80\" />")
        body.append("      <div data-hero className=\"relative z-10 mx-auto max-w-5xl px-6 py-24 text-center\">")
        body.append("        <h2 className=\"text-3xl sm:text-5xl font-bold tracking-tight text-zinc-900 dark:text-white\">Generated Experience</h2>")
        body.append("        <p className=\"mt-3 text-zinc-600 dark:text-zinc-300\">Interactive, tech, futuristic, digital, minimalist.</p>")
        body.append("      </div>")
        body.append("    </section>")
        body.append("  );")
        body.append("}")

    return header + "\n\n" + "\n".join(body) + "\n"


@app.post("/generate")
def generate_component(payload: GenerateRequest):
    try:
        code = build_react_component(payload)
        doc = Generation(
            source_type=payload.source_type,
            input_url=payload.input_url,
            animation=payload.animation,
            name=payload.name,
            options=payload.options or {},
            code=code,
        )
        # Persist to DB if available
        inserted_id = None
        if db is not None:
            try:
                inserted_id = create_document('generation', doc)
            except Exception:
                inserted_id = None

        return {
            "id": inserted_id,
            "name": doc.name,
            "source_type": doc.source_type,
            "animation": doc.animation,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "code": doc.code,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/generations")
def list_generations(limit: int = 20):
    if db is None:
        return {"items": [], "total": 0}
    try:
        docs = get_documents('generation', {}, limit)
        # Convert ObjectId to string and strip internal fields
        items = []
        for d in docs:
            d.pop('updated_at', None)
            _id = str(d.pop('_id', ''))
            items.append({"id": _id, **d})
        return {"items": items, "total": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
