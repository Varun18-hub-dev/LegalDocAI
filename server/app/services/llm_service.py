import os
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from app.models.context import QueryContext
from app.utils.logging import get_logger
from app.utils.exceptions import LLMTimeout

log = get_logger("llm_service")

class LLMService:
    """
    Adapter service for Google Gemini API, handling LLM completion calls,
    retries, and token accounting, with a mock fallback when no API key is available.
    """
    
    @staticmethod
    def generate(context: QueryContext) -> str:
        """
        Public contract method to generate LLM completions.
        Saves result inside context.llm_response and returns it.
        """
        context.start_stage("llm_generation")
        try:
            prompt = context.prompt or f"User Question: {context.question}"
            
            # Retrieve API Key from config / env
            api_key = os.getenv("GEMINI_API_KEY", "")
            
            # Check if API key is missing or dummy placeholder
            is_dummy_key = not api_key or api_key.lower() in ("your_api_key_here", "dummy", "placeholder", "")
            
            # Helper to generate mock response
            def get_mock_response():
                return (
                    f"[Mock LLM Mode - No valid Gemini API Key configured]\n\n"
                    f"The Query Orchestrator successfully classified the intent, retrieved relevant documents, "
                    f"and constructed the prompt below. Configure a valid GEMINI_API_KEY in the backend .env to generate live completions.\n\n"
                    f"=== Mock Answer ===\n"
                    f"Based on the retrieved context, this is a simulated response to the query: '{context.question}'."
                )

            if is_dummy_key:
                # Mock Mode - return prompt structure and dummy response
                log.warning("No valid GEMINI_API_KEY found. Operating in Mock LLM mode.")
                time.sleep(0.5) # Simulate latency
                response_text = get_mock_response()
                context.metadata["llm_model"] = "mock-mode"
                context.metadata["tokens_sent"] = len(prompt) // 4
                context.metadata["tokens_received"] = len(response_text) // 4
            else:
                try:
                    # Live Gemini Mode
                    log.info("Sending request to Gemini (gemini-2.5-flash)...")
                    response_text = LLMService._call_gemini_with_retry(prompt, api_key)
                    
                    # Simple token estimates (char length / 4)
                    context.metadata["llm_model"] = "gemini-2.5-flash"
                    context.metadata["tokens_sent"] = len(prompt) // 4
                    context.metadata["tokens_received"] = len(response_text) // 4
                except Exception as e:
                    err_str = str(e).lower()
                    if any(term in err_str for term in ("api_key_invalid", "api key not found", "invalid api key", "400")):
                        log.warning(f"Live Gemini API call failed with API Key error: {e}. Falling back to Mock LLM mode.")
                        time.sleep(0.5)
                        response_text = get_mock_response()
                        context.metadata["llm_model"] = "mock-mode-fallback"
                        context.metadata["tokens_sent"] = len(prompt) // 4
                        context.metadata["tokens_received"] = len(response_text) // 4
                    else:
                        raise e
                
            context.llm_response = response_text
            log.info("LLM generation complete.")
            return response_text
        except Exception as e:
            log.error(f"Gemini API invocation failed: {e}", exc_info=True)
            context.errors.append(f"LLM completion failed: {str(e)}")
            raise e
        finally:
            context.end_stage("llm_generation")

    @staticmethod
    def _call_gemini_with_retry(prompt: str, api_key: str, retries: int = 3, timeout_seconds: int = 30) -> str:
        """Call Gemini API with retry logic."""
        last_err = None
        for attempt in range(1, retries + 1):
            try:
                # Initialize model with timeout
                model = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    google_api_key=api_key,
                    temperature=0.2,
                    timeout=float(timeout_seconds)
                )
                response = model.invoke(prompt)
                return str(response.content)
            except Exception as e:
                last_err = e
                log.warning(f"Gemini API call attempt {attempt}/{retries} failed: {e}")
                if attempt < retries:
                    time.sleep(attempt * 1.5)  # Exponential backoff
                    
        log.error("All Gemini API call attempts exhausted.")
        raise LLMTimeout(f"Gemini API request timed out or failed: {str(last_err)}")
