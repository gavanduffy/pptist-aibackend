"""Vercel serverless entrypoint for the FastAPI application."""

from mangum import Mangum

from main import app

handler = Mangum(app, lifespan="on")
