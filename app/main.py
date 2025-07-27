from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Import the CORS middleware
from app.api.v1.api import api_router

app = FastAPI(title="Lab Management System API", openapi_url="/api/v1/openapi.json")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "Welcome to the Lab Management System API"}
