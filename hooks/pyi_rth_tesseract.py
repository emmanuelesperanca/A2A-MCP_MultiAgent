import os
import sys
from pathlib import Path

# Configurar caminho do Tesseract no executável
if getattr(sys, 'frozen', False):
    # Estamos rodando como executável
    base_path = Path(sys._MEIPASS)
    tesseract_path = base_path / "tesseract" / "tesseract.exe"
    
    if tesseract_path.exists():
        os.environ['TESSERACT_CMD'] = str(tesseract_path)
        
        # Configurar pytesseract se disponível
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = str(tesseract_path)
        except ImportError:
            pass
