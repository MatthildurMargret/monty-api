from fastapi import FastAPI, HTTPException, Header, Query
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
def get_recommended_founders(
    x_api_key: str = Header(None),
    tree_path: str = Query(None),
    tree_path_prefix: str = Query(None)   # ← new param
):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403)

    with conn.cursor() as cur:
        base_query = """
            SELECT DISTINCT ON (name)
                company_name, tree_path, company_tags, profile_url,
                tree_result, name, location, access_date, description_1, verticals, building_since, repeat_founder, 
                industry_expertise_score, funding, source, technical, school_tags, past_success_indication_score,
                product, business_stage, company_tech_score, company_website, market, tree_justification, tree_thesis, twitter, headcount, embeddednews
            FROM founders
            WHERE founder = true AND history = 'recommended'
              AND tree_path != '' AND access_date IS NOT NULL
        """
        params = []

        # allow both full match and prefix match
        if tree_path:
            base_query += " AND tree_path ILIKE %s"
            params.append(f"%{tree_path}%")
        elif tree_path_prefix:
            base_query += " AND tree_path ILIKE %s"
            params.append(f"{tree_path_prefix}%")

        base_query += " ORDER BY name, id DESC;"
        cur.execute(base_query, params)
        rows = cur.fetchall()

    return {"data": rows}




@app.get("/unseen-founders")
def get_unseen_founders(x_api_key: str = Header(None)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT ON (name)
                company_name, tree_path, company_tags, profile_url,
                tree_result, name, location, access_date, description_1, verticals, building_since, repeat_founder, 
                industry_expertise_score, funding, source, technical, school_tags, past_success_indication_score,
                product, business_stage, company_tech_score, company_website, market, tree_justification, tree_thesis, twitter, headcount, embeddednews
            FROM founders
            WHERE founder = true AND history = '' 
              AND (tree_result = 'Strong recommend' OR tree_result = 'Recommend')
              AND access_date != '' AND access_date IS NOT NULL
            ORDER BY name, id DESC;
        """)
        rows = cur.fetchall()
    return {"data": rows}

@app.get("/filters")
def get_filter_options(x_api_key: str = Header(None)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT location
            FROM founders
            WHERE location IS NOT NULL AND TRIM(location) <> ''
            ORDER BY location;
        """)
        locations = [r["location"] for r in cur.fetchall()]

        cur.execute("""
            SELECT DISTINCT tree_path
            FROM founders
            WHERE tree_path IS NOT NULL AND TRIM(tree_path) <> ''
            ORDER BY tree_path;
        """)
        tree_paths = [r["tree_path"] for r in cur.fetchall()]

    return {"locations": locations, "tree_paths": tree_paths}




@app.get("/search")
def search_founders(
    keyword: str = Query(None),
    location: str = Query(None),
    tag: str = Query(None),
    tree_path: str = Query(None),
    tree_path_prefix: str = Query(None),  # ← new optional param
    x_api_key: str = Header(None)
):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403)
    
    base_query = """
        SELECT DISTINCT ON (name)
            company_name, tree_path, company_tags, profile_url,
                tree_result, name, location, access_date, description_1, verticals, building_since, repeat_founder, 
                industry_expertise_score, funding, source, technical, school_tags, past_success_indication_score,
                product, business_stage, company_tech_score, company_website, market, tree_justification, tree_thesis, twitter, headcount, embeddednews
        FROM founders
        WHERE founder = true
          AND access_date != '' AND access_date IS NOT NULL
    """
    filters, params = [], []

    if keyword:
        filters.append("(LOWER(name) LIKE %s OR LOWER(company_name) LIKE %s OR LOWER(description_1) LIKE %s)")
        kw = f"%{keyword.lower()}%"
        params += [kw, kw, kw]

    if location:
        filters.append("location ILIKE %s")
        params.append(f"%{location}%")

    # Existing full match filter
    if tree_path:
        filters.append("tree_path ILIKE %s")
        params.append(f"%{tree_path}%")

    # New prefix filter for hierarchical search
    elif tree_path_prefix:
        filters.append("tree_path ILIKE %s")
        params.append(f"{tree_path_prefix}%")

    if tag:
        filters.append("LOWER(company_tags) LIKE %s")
        params.append(f"%{tag.lower()}%")

    if filters:
        base_query += " AND " + " AND ".join(filters)
    
    base_query += " ORDER BY name, id DESC;"

    with conn.cursor() as cur:
        cur.execute(base_query, params)
        rows = cur.fetchall()
    
    return {"data": rows}

