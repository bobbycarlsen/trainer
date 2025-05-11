import os
import json
import config

# Check if Azure OpenAI is enabled and API key is available
def is_azure_openai_configured():
    """
    Check if Azure OpenAI is properly configured.
    """
    if not config.AZURE_OPENAI_ENABLED:
        return False
    
    # Check for API key in environment variable first
    api_key = os.environ.get("AZURE_OPENAI_API_KEY", config.AZURE_OPENAI_API_KEY)
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", config.AZURE_OPENAI_ENDPOINT)
    
    return bool(api_key and endpoint)

def analyze_position(fen, selected_move, top_move):
    """
    Use Azure OpenAI to analyze a chess position.
    Returns analysis text or error message.
    """
    if not is_azure_openai_configured():
        return "Azure OpenAI is not configured. Please set API key and endpoint in config or environment variables."
    
    try:
        # Create prompt
        prompt = config.ANALYSIS_PROMPT_TEMPLATE.format(
            fen=fen,
            selected_move=selected_move,
            top_move=top_move
        )
        
        # In a real implementation, this would call the Azure OpenAI API
        # For this example, we'll return a placeholder response
        
        # Placeholder analysis text
        analysis = f"""
Analysis of position with FEN: {fen}

The top engine move {top_move} is considered best because it develops a piece while maintaining control of the center. This move improves your piece coordination and prepares for castling.

{"This is a good choice!" if selected_move == top_move else f"Your selected move {selected_move} is not optimal because it doesn't address the key needs of the position. The engine's choice {top_move} provides better development and control."}

Key concepts to recognize in this position:
1. Piece development is a priority in the opening phase
2. Center control should be maintained
3. King safety should be addressed through castling when possible
4. Connected pawns provide stronger structure than isolated pawns

Similar positions often appear in the {fen.split('/')[0][:3]} opening variations. Study this opening to improve your understanding of the typical plans and ideas.
"""
        
        return analysis
    
    except Exception as e:
        return f"Error calling Azure OpenAI API: {str(e)}"