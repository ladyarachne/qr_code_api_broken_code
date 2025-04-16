import logging
import logging.config
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import QR_DIRECTORY
from app.routers import qr_code, oauth  # Make sure these imports match your project structure.
from app.services.qr_service import create_directory
from app.utils.common import setup_logging

# This function sets up logging based on the configuration specified in your logging configuration file.
# It's important for monitoring and debugging.
setup_logging()

# This ensures that the directory for storing QR codes exists when the application starts.
# If it doesn't exist, it will be created.
create_directory(QR_DIRECTORY)

# This creates an instance of the FastAPI application.
app = FastAPI(
    title="QR Code Manager",
    description="A FastAPI application for creating, listing available codes, and deleting QR codes. "
                "It also supports OAuth for secure access.",
    version="0.0.1",
    redoc_url=None,
    contact={
        "name": "API Support",
        "url": "http://www.example.com/support",
        "email": "support@example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    }
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Global exception handler to catch and log all unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred."},
    )

# Here, we include the routers for our application. Routers define the paths and operations your API provides.
# We have two routers in this case: one for managing QR codes and another for handling OAuth authentication.
app.include_router(qr_code.router, prefix="/api/v1")  # QR code management routes
app.include_router(oauth.router, prefix="/api/v1/auth")  # OAuth authentication routes

@app.get("/")
async def root():
    return {"message": "Welcome to QR Code Generator API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
