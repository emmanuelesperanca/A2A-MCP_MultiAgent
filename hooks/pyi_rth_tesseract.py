import os
import sys
from pathlib import Path

print("\n" + "="*60)
print("🔍 HOOK: Configurando Tesseract OCR")
print("="*60)

# Configurar caminho do Tesseract no executável
if getattr(sys, 'frozen', False):
    # Estamos rodando como executável
    base_path = Path(sys._MEIPASS)
    tesseract_dir = base_path / "tesseract"
    tesseract_exe = tesseract_dir / "tesseract.exe"
    tessdata_dir = tesseract_dir / "tessdata"
    
    print(f"📁 Base path: {base_path}")
    print(f"📁 Tesseract dir: {tesseract_dir}")
    print(f"📁 Tesseract exe: {tesseract_exe}")
    print(f"📁 Tessdata dir: {tessdata_dir}")
    
    # Verificar se existe
    print(f"\n✓ Diretório tesseract existe: {tesseract_dir.exists()}")
    print(f"✓ Executável existe: {tesseract_exe.exists()}")
    print(f"✓ Tessdata existe: {tessdata_dir.exists()}")
    
    if tesseract_exe.exists():
        # Adicionar o diretório do Tesseract ao PATH para encontrar as DLLs
        tesseract_dir_str = str(tesseract_dir)
        current_path = os.environ.get('PATH', '')
        if tesseract_dir_str not in current_path:
            os.environ['PATH'] = tesseract_dir_str + os.pathsep + current_path
            print(f"✅ Adicionado ao PATH: {tesseract_dir_str}")
        
        # Configurar variável de ambiente TESSERACT_CMD
        os.environ['TESSERACT_CMD'] = str(tesseract_exe)
        print(f"✅ TESSERACT_CMD: {tesseract_exe}")
        
        # Configurar TESSDATA_PREFIX
        # Importante: Tesseract procura diretamente em $TESSDATA_PREFIX/*.traineddata
        # Então devemos apontar para a pasta tessdata/ em si
        os.environ['TESSDATA_PREFIX'] = str(tessdata_dir) + os.sep
        print(f"✅ TESSDATA_PREFIX: {tessdata_dir}{os.sep}")
        
        # Configurar pytesseract se disponível
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = str(tesseract_exe)
            print(f"✅ pytesseract.tesseract_cmd configurado")
            
            # Testar se funciona
            try:
                version = pytesseract.get_tesseract_version()
                print(f"✅ Tesseract versão: {version}")
            except Exception as e:
                print(f"⚠️ Erro ao verificar versão: {e}")
                
        except ImportError as e:
            print(f"⚠️ pytesseract não disponível: {e}")
        
        print("="*60)
        print("✅ Tesseract configurado com sucesso!")
        print("="*60 + "\n")
    else:
        print("="*60)
        print("❌ ERRO: tesseract.exe não encontrado!")
        print("="*60 + "\n")
else:
    print("ℹ️ Rodando em modo normal (não congelado)")
    print("="*60 + "\n")
