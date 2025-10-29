from fastapi import FastAPI, HTTPException, Header
import psycopg2, os

app = FastAPI()
conn = psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")

@app.get("/data")
def get_data(x_api_key: str = Header(None)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403)
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM your_table ORDER BY id DESC LIMIT 100;")
        rows = cur.fetchall()
    return {"data": rows}
