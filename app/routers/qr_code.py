# Import necessary modules and functions from FastAPI and other standard libraries
from fastapi import APIRouter, HTTPException, Depends, Response, status
from fastapi.responses import JSONResponse
from typing import List
import logging

# Import classes and functions from our application's modules
from app.schema import QRCodeRequest, QRCodeResponse
from app.services.qr_service import generate_qr_code, list_qr_codes, delete_qr_code
from app.utils.common import decode_filename_to_url, encode_url_to_filename, generate_links
from app.config import QR_DIRECTORY, SERVER_BASE_URL, FILL_COLOR, BACK_COLOR, SERVER_DOWNLOAD_FOLDER
from app.routers.oauth import get_current_user

# Create an APIRouter instance to register our endpoints
router = APIRouter(
    prefix="/qr-codes",
    tags=["QR Codes"],
    responses={404: {"description": "Not found"}},
)

# Define an endpoint to create QR codes
# It responds to POST requests at "/" and returns data matching the QRCodeResponse model
# This endpoint returns HTTP 201 when a QR code is created successfully
@router.post("/", response_model=QRCodeResponse, status_code=status.HTTP_201_CREATED)
async def create_qr_code(request: QRCodeRequest, current_user: dict = Depends(get_current_user)):
    # Log the creation request
    logging.info(f"Creating QR code for URL: {request.url}")
    
    # Encode the URL to a safe filename format
    encoded_url = encode_url_to_filename(request.url)
    qr_filename = f"{encoded_url}.png"
    qr_code_full_path = QR_DIRECTORY / qr_filename

    # Construct the download URL for the QR code
    qr_code_download_url = f"{SERVER_BASE_URL}/{SERVER_DOWNLOAD_FOLDER}/{qr_filename}"
    
    # Generate HATEOAS (Hypermedia As The Engine Of Application State) links for this resource
    links = generate_links("create", qr_filename, SERVER_BASE_URL, qr_code_download_url)

    # Check if the QR code already exists to prevent duplicates
    if qr_code_full_path.exists():
        logging.info("QR code already exists.")
        # If it exists, return a conflict response
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "QR code already exists.", "qr_code_url": qr_code_download_url, "links": links}
        )

    # Generate the QR code if it does not exist
    generate_qr_code(request.url, qr_code_full_path, request.fill_color, request.back_color, request.size)
    # Return a response indicating successful creation
    return QRCodeResponse(message="QR code created successfully.", qr_code_url=qr_code_download_url, links=links)

# Define an endpoint to list all QR codes
# It responds to GET requests at "/" and returns a list of QRCodeResponse objects
@router.get("/", response_model=List[QRCodeResponse])
async def list_qr_codes_endpoint(current_user: dict = Depends(get_current_user)):
    logging.info("Listing all QR codes.")
    # Retrieve all QR code files
    qr_files = list_qr_codes(QR_DIRECTORY)
    # Create a response object for each QR code
    responses = [QRCodeResponse(
        message="QR code available",
        qr_code_url=f"{SERVER_BASE_URL}/{SERVER_DOWNLOAD_FOLDER}/{qr_file}",
        links=generate_links("list", qr_file, SERVER_BASE_URL, f"{SERVER_BASE_URL}/{SERVER_DOWNLOAD_FOLDER}/{qr_file}")
    ) for qr_file in qr_files]
    return responses

@router.delete("/{qr_filename}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_qr_code_endpoint(qr_filename: str, current_user: dict = Depends(get_current_user)):
    logging.info(f"Deleting QR code: {qr_filename}.")
    qr_code_path = QR_DIRECTORY / qr_filename
    if not qr_code_path.is_file():
        logging.warning(f"QR code not found: {qr_filename}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR code not found")

    delete_qr_code(qr_code_path)
    # No need to generate or return any links since the 204 response should not contain a body
    return Response(status_code=status.HTTP_204_NO_CONTENT)
