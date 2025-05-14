from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl, Field
from dotenv import load_dotenv
import os
import asyncio
import json

# --- HyperBrowser SDK Imports ---
from hyperbrowser import Hyperbrowser
from hyperbrowser.models import StartExtractJobParams

# --- Pangram SDK Imports ---
from pangram import PangramText # Corrected import based on common SDK patterns or pangram.text_classifier.PangramText

# --- Environment Variable Loading and Debugging ---
# Get the directory where main.py is located (backend/)
script_dir = os.path.dirname(__file__)
# Construct the path to the .env file in the project root (one level up from script_dir)
dotenv_path_in_root = os.path.abspath(os.path.join(script_dir, '..', '.env'))

found_dotenv = load_dotenv(dotenv_path=dotenv_path_in_root, verbose=True)

print(f"DEBUG: Attempted to load .env from project root: {dotenv_path_in_root}")
print(f"DEBUG: load_dotenv() found and loaded .env file from root: {found_dotenv}")
print(f"DEBUG: HYPERBROWSER_API_KEY after load_dotenv: {os.getenv('HYPERBROWSER_API_KEY')}")
print(f"DEBUG: PANGRAM_API_KEY after load_dotenv: {os.getenv('PANGRAM_API_KEY')}")
# --- End Environment Variable Loading and Debugging ---

# Initialize FastAPI app
app = FastAPI(
    title="Pangram Sales Widget API",
    description="API for processing URLs with HyperBrowser and analyzing text with Pangram.",
    version="0.1.0"
)

# --- API Key Management (Example - secure appropriately for production) ---
HYPERBROWSER_API_KEY = os.getenv("HYPERBROWSER_API_KEY")
PANGRAM_API_KEY = os.getenv("PANGRAM_API_KEY")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # Uncomment if using OpenAI

# --- Pydantic Models for Request/Response ---
class ProcessUrlRequest(BaseModel):
    url: HttpUrl
    target_object_description: str
    username: str | None = None
    password: str | None = None

# --- HyperBrowser Extraction Schema ---
class ExtractionSchema(BaseModel):
    extracted_text: str = Field(description="The text content extracted based on the user's prompt.")
    # We could add more fields here if needed, e.g., title, specific data points

class HyperBrowserResult(BaseModel):
    status: str
    # raw_content: str | None = None # Full HTML/Markdown from HyperBrowser
    extracted_text: str | None = None
    error_message: str | None = None

class PangramAnalysis(BaseModel):
    prediction: str | None = None
    ai_likelihood: float | None = None
    # Add other fields from Pangram API as needed
    # max_ai_likelihood: float | None = None
    # avg_ai_likelihood: float | None = None
    # fraction_ai_content: float | None = None
    error_message: str | None = None

class ProcessUrlResponse(BaseModel):
    hyperbrowser_result: HyperBrowserResult
    pangram_analysis: PangramAnalysis
    overall_status: str
    error_message: str | None = None

# --- API Endpoints ---
@app.get("/ping", summary="Health check endpoint", tags=["Health"])
async def ping():
    """
    Simple health check.
    """
    return {"message": "pong"}

@app.post("/api/process-url", response_model=ProcessUrlResponse, summary="Process a URL to extract text and analyze with Pangram", tags=["Processing"])
async def process_url(request: ProcessUrlRequest):
    """
    Processes a given URL:
    1.  (TODO) Uses HyperBrowser to fetch content and/or interact with the page based on `target_object_description`.
    2.  (TODO) Uses an LLM to extract the specific text from HyperBrowser's output based on `target_object_description`.
    3.  (TODO) Sends the extracted text to Pangram for analysis.
    4.  Returns the results from HyperBrowser and Pangram.
    """
    print(f"Received request for URL: {request.url}")
    print(f"Target object description: {request.target_object_description}")
    if request.username:
        print(f"Username provided: {request.username}")
    # (Avoid printing password directly to logs in a real app for security)
    # if request.password:
    #     print(f"Password provided.")

    if not HYPERBROWSER_API_KEY:
        raise HTTPException(status_code=500, detail="HyperBrowser API key is not configured.")
    if not PANGRAM_API_KEY:
        raise HTTPException(status_code=500, detail="Pangram API key is not configured.")

    hyperbrowser_data = HyperBrowserResult(status="pending_hyperbrowser")
    pangram_data = PangramAnalysis(prediction=None, ai_likelihood=None)
    extracted_text_for_pangram = None

    try:
        # --- 1. HyperBrowser Interaction ---        
        hyper_client = Hyperbrowser(api_key=HYPERBROWSER_API_KEY)

        prompt_parts = []
        if request.username and request.password:
            # Note: Effectiveness of login via prompt depends on HyperBrowser's LLM capabilities.
            # Be cautious with sensitive data in prompts.
            prompt_parts.append(
                f"The target site is {request.url}. "
                f"If a login is encountered or required to access the main content, please attempt to log in. "
                f"Use username '{request.username}'. The password is '{request.password}'. "
                f"After handling any login, or if no login is needed, "
            )
        else:
            prompt_parts.append(f"For the content at {request.url}, ")
        
        prompt_parts.append(f"please extract the following: {request.target_object_description}.")
        prompt_parts.append("Focus on returning only the specifically requested text as a single string in the 'extracted_text' field.")
        full_prompt = " ".join(prompt_parts)

        print(f"Constructed HyperBrowser Prompt: {full_prompt}") # For debugging

        extract_params = StartExtractJobParams(
            urls=[str(request.url)], # API expects a list of URL strings
            prompt=full_prompt,
            schema_=ExtractionSchema # Pass the Pydantic model class itself
        )

        print("Starting HyperBrowser extract.start_and_wait...")
        try:
            loop = asyncio.get_event_loop()
            # Run the blocking HyperBrowser SDK call in a thread pool executor
            hb_response_obj = await loop.run_in_executor(None, hyper_client.extract.start_and_wait, extract_params)
            
            print(f"HyperBrowser raw response status: {hb_response_obj.status}")
            # For debugging, you might want to see the raw data, ensure it's not too large:
            # if hb_response_obj.data:
            #     print(f"HyperBrowser raw data: {json.dumps(hb_response_obj.data, indent=2)}")
            # else:
            #     print("HyperBrowser returned no data object.")

            # Treat "succeeded" or "completed" as states where data *might* be present
            if hb_response_obj.status in ["succeeded", "completed"] and hb_response_obj.data:
                # The .data attribute should be an instance of our ExtractionSchema
                # or a list containing such instances if multiple URLs were processed (we send one)
                data_payload = hb_response_obj.data
                if isinstance(data_payload, list):
                    if len(data_payload) > 0:
                        data_payload = data_payload[0] # Take the first result for our single URL
                    else:
                        raise ValueError("HyperBrowser succeeded but returned an empty list in data.")
                
                # Now data_payload should be a dict or an object that can be parsed by ExtractionSchema
                try:
                    parsed_data = ExtractionSchema.parse_obj(data_payload)
                    extracted_text_for_pangram = parsed_data.extracted_text
                    hyperbrowser_data = HyperBrowserResult(status="success", extracted_text=extracted_text_for_pangram)
                    print(f"Successfully extracted text: '{extracted_text_for_pangram[:200]}...'") # Log snippet
                except Exception as parse_error:
                    print(f"HyperBrowser succeeded but failed to parse data against schema: {parse_error}. Data: {data_payload}")
                    hyperbrowser_data = HyperBrowserResult(status="error", error_message=f"Data parsing error: {parse_error}")
            elif hb_response_obj.status == "failed":
                error_detail = getattr(hb_response_obj, 'error', "Unknown HyperBrowser extraction error")
                print(f"HyperBrowser extraction failed: {error_detail}")
                hyperbrowser_data = HyperBrowserResult(status="error", error_message=str(error_detail))
            else:
                # This case should ideally not be reached if start_and_wait behaves as expected
                print(f"HyperBrowser returned an unexpected status that was not handled: {hb_response_obj.status}")
                hyperbrowser_data = HyperBrowserResult(status="error", error_message=f"Unexpected HyperBrowser status: {hb_response_obj.status}")
        
        except Exception as hb_error:
            print(f"Error during HyperBrowser interaction: {hb_error}")
            hyperbrowser_data = HyperBrowserResult(status="error", error_message=str(hb_error))

        # --- 2. Pangram Analysis (Placeholder, uses extracted_text_for_pangram) ---
        if extracted_text_for_pangram:
            print(f"Proceeding to Pangram analysis with extracted text (length: {len(extracted_text_for_pangram)}).")
            try:
                pangram_client = PangramText(api_key=PANGRAM_API_KEY)
                loop = asyncio.get_event_loop()
                # Run the blocking Pangram SDK call in a thread pool executor
                analysis_result = await loop.run_in_executor(None, pangram_client.predict, extracted_text_for_pangram)
                
                print(f"Pangram analysis raw result: {analysis_result}") # For debugging

                pangram_data = PangramAnalysis(
                    prediction=analysis_result.get("prediction"),
                    ai_likelihood=analysis_result.get("ai_likelihood")
                )
                print(f"Pangram analysis successful: Prediction - {pangram_data.prediction}, Likelihood - {pangram_data.ai_likelihood}")
            except Exception as pangram_error:
                print(f"Error during Pangram analysis: {pangram_error}")
                pangram_data = PangramAnalysis(prediction="Error", error_message=str(pangram_error))
        else:
            print("Skipping Pangram analysis as no text was extracted.")
            pangram_data = PangramAnalysis(prediction="Skipped", error_message="No text from HyperBrowser")

        overall_status = "success"
        if hyperbrowser_data.status != "success" or not extracted_text_for_pangram:
            overall_status = f"error_hyperbrowser_{hyperbrowser_data.status}"
        elif pangram_data.prediction == "Error" or pangram_data.prediction == "Skipped":
             overall_status = f"error_pangram_analysis"
        
        return ProcessUrlResponse(
            hyperbrowser_result=hyperbrowser_data,
            pangram_analysis=pangram_data,
            overall_status=overall_status
        )

    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        print(f"Overall error processing URL {request.url}: {e}")
        # Ensure hyperbrowser_data and pangram_data are defined even if an early exception occurs
        if not hasattr(hyperbrowser_data, 'status') or hyperbrowser_data.status == "pending_hyperbrowser":
             hyperbrowser_data = HyperBrowserResult(status="error", error_message=str(e) if not hyperbrowser_data.error_message else hyperbrowser_data.error_message)
        if not hasattr(pangram_data, 'prediction') or pangram_data.prediction is None:
             pangram_data = PangramAnalysis(prediction="Error", error_message="Server exception before Pangram analysis" if not pangram_data.error_message else pangram_data.error_message)

        return ProcessUrlResponse(
            hyperbrowser_result=hyperbrowser_data,
            pangram_analysis=pangram_data,
            overall_status="error_server_exception",
            error_message=str(e)
        )

# --- Main block for Uvicorn (if running directly) ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 