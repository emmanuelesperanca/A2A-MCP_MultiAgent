"""
Script para criar executável do ingest_data.py com suporte completo a OCR
Uso: python build_ingest_executable.py
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path

def check_tesseract():
    """Verifica se o Tesseract está instalado e retorna o caminho."""
    tesseract_paths = [
        r"C:\Users\u137147\AppData\Local\Programs\Tesseract-OCR",
        r"C:\Program Files\Tesseract-OCR",
        r"C:\Program Files (x86)\Tesseract-OCR"
    ]
    
    for path in tesseract_paths:
        if os.path.exists(os.path.join(path, "tesseract.exe")):
            print(f"✅ Tesseract encontrado em: {path}")
            return path
    
    print("❌ Tesseract não encontrado!")
    return None

def create_spec_file():
    """Cria arquivo .spec personalizado para PyInstaller."""
    tesseract_path = check_tesseract()
    if not tesseract_path:
        print("Erro: Tesseract não encontrado. Instale primeiro.")
        return False
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

# Caminhos base
base_dir = Path(__file__).parent
tesseract_dir = Path(r"{tesseract_path}")

# Dados adicionais para incluir no executável
added_files = []

# Incluir arquivos de configuração se existirem
if (base_dir / ".env").exists():
    added_files.append((".env", "."))

# Incluir binários do Tesseract
if tesseract_dir.exists():
    # Incluir executável principal
    added_files.append((str(tesseract_dir / "tesseract.exe"), "tesseract"))
    
    # Incluir DLLs necessárias
    for dll_file in tesseract_dir.glob("*.dll"):
        added_files.append((str(dll_file), "tesseract"))
    
    # Incluir dados de idioma
    tessdata_dir = tesseract_dir / "tessdata"
    if tessdata_dir.exists():
        for lang_file in tessdata_dir.glob("*.traineddata"):
            added_files.append((str(lang_file), "tesseract/tessdata"))

# Módulos ocultos necessários
hiddenimports = [
    'pytesseract',
    'pdf2image',
    'PIL',
    'PIL._tkinter_finder',
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.scrolledtext',
    'psycopg2',
    'psycopg2.extras',
    'pgvector',
    'pgvector.psycopg2',
    'openai',
    'dotenv',
    'langchain',
    'langchain.text_splitter',
    'pypdf',
    'docx'
]

a = Analysis(
    ['ingest_data.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ingest_data',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''
    
    with open("ingest_data.spec", "w", encoding="utf-8") as f:
        f.write(spec_content)
    
    print("✅ Arquivo ingest_data.spec criado com sucesso!")
    return True

def install_dependencies():
    """Instala dependências necessárias para o build."""
    print("📦 Instalando dependências para build...")
    
    dependencies = [
        "pyinstaller",
        "pytesseract", 
        "pdf2image",
        "pillow"
    ]
    
    for dep in dependencies:
        print(f"Instalando {dep}...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar {dep}: {e}")
            return False
    
    print("✅ Todas as dependências instaladas!")
    return True

def build_executable():
    """Executa o PyInstaller para criar o executável."""
    print("🔨 Iniciando build do executável...")
    
    try:
        # Usar o arquivo .spec personalizado
        subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "ingest_data.spec"
        ], check=True)
        
        print("✅ Build concluído com sucesso!")
        print("📁 Executável criado em: dist/ingest_data.exe")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro no build: {e}")
        return False

def create_runtime_hook():
    """Cria hook para configurar Tesseract em runtime."""
    hook_content = '''import os
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
'''
    
    # Criar diretório hooks se não existir
    os.makedirs("hooks", exist_ok=True)
    
    with open("hooks/pyi_rth_tesseract.py", "w", encoding="utf-8") as f:
        f.write(hook_content)
    
    print("✅ Hook de runtime criado!")

def main():
    """Função principal do script de build."""
    print("🚀 === BUILD DO INGEST_DATA COM OCR ===")
    print()
    
    # Verificar se estamos no diretório correto
    if not os.path.exists("ingest_data.py"):
        print("❌ Arquivo ingest_data.py não encontrado!")
        print("Execute este script no mesmo diretório do ingest_data.py")
        return False
    
    # Verificar Tesseract
    if not check_tesseract():
        return False
    
    # Instalar dependências
    if not install_dependencies():
        return False
    
    # Criar hook de runtime
    create_runtime_hook()
    
    # Criar arquivo .spec
    if not create_spec_file():
        return False
    
    # Build
    if not build_executable():
        return False
    
    print()
    print("🎉 === BUILD CONCLUÍDO ===")
    print("📁 Executável: dist/ingest_data.exe")
    print("📋 Para distribuir, inclua também:")
    print("   - Arquivo .env (se necessário)")
    print("   - Tesseract está incluído no executável")
    print()
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)