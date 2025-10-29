from fastapi import FastAPI, HTTPException, Header
import psycopg2, os
import math
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later replace "*" with your website domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conn = psycopg2.connect(os.environ["DATABASE_URL"], cursor_factory=RealDictCursor)


def sanitize_value(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


@app.get("/recommended-founders")
def get_recommended_founders(x_api_key: str = Header(None)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT ON (name)
                * 
            FROM founders
            WHERE founder = true AND history = 'recommended' AND tree_path != ''
            AND access_date != '' AND access_date IS NOT NULL
            ORDER BY name, id DESC;
        """)
        rows = cur.fetchall()
    return {"data": rows}


@app.get("/unseen-founders")
def get_unseen_founders(x_api_key: str = Header(None)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT ON (name)
                *
            FROM founders
            WHERE founder = true AND history = '' 
              AND (tree_result = 'Strong recommend' OR tree_result = 'Recommend')
              AND access_date != '' AND access_date IS NOT NULL
            ORDER BY name, id DESC;
        """)
        rows = cur.fetchall()
    return {"data": rows}
