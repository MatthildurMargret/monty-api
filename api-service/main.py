from fastapi import FastAPI, HTTPException, Header
import psycopg2, os

app = FastAPI()
conn = psycopg2.connect(os.environ["DATABASE_URL"])

@app.get("/recommended-founders")
def get_data(x_api_key: str = Header(None)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403)
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT ON (name) * FROM founders WHERE founder = true AND history = 'recommended' ORDER BY name, id DESC;")
        rows = cur.fetchall()
    return {"data": rows}


@app.get("/unseen-founders")
def get_data(x_api_key: str = Header(None)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403)
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT ON (name) * FROM founders WHERE founder = true AND history = '' AND (tree_result = 'Strong recommend' OR tree_result = 'Recommend') ORDER BY name, id DESC;")
        rows = cur.fetchall()
    return {"data": rows}
