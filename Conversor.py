import os
import zipfile
import tempfile
import fitz  # PyMuPDF
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from natsort import natsorted
import pillow_avif

# --- FUNÇÕES DE OBTENÇÃO DE CAMINHO ---

def obter_caminho_pasta():
    """Obtém o caminho de uma PASTA do usuário, com validação."""
    caminho = input("\nArraste a pasta para cá ou digite o caminho e pressione Enter: ").strip('"').strip()
    while not os.path.isdir(caminho):
        print(f"\n[x] Caminho inválido ou pasta não encontrada: {caminho}")
        caminho = input("Por favor, informe um caminho de PASTA válido: ").strip('"').strip()
    return caminho

# --- FUNÇÕES DE CRIAÇÃO (WORKERS) ---
# (Estas funções não precisam de alteração)

def criar_pdf_de_imagens(lista_imagens, pasta_base_imagens, caminho_pdf_saida):
    if os.path.exists(caminho_pdf_saida):
        print(f"[⏩] PDF já existe, pulando: {os.path.basename(caminho_pdf_saida)}")
        return
    with tempfile.TemporaryDirectory() as temp_dir:
        pdfs_temp = []
        for nome_arquivo in lista_imagens:
            img_path = os.path.join(pasta_base_imagens, nome_arquivo)
            try:
                with Image.open(img_path) as img:
                    img_convertida = img.convert("RGB")
                    pdf_temp = os.path.join(temp_dir, f"{os.path.splitext(nome_arquivo)[0]}.pdf")
                    img_convertida.save(pdf_temp, "PDF", resolution=100.0)
                    pdfs_temp.append(pdf_temp)
            except Exception as e:
                print(f"[x] Erro ao processar o arquivo {nome_arquivo} para PDF: {e}")
        if not pdfs_temp: return
        writer = PdfWriter()
        for pdf_path in pdfs_temp:
            try:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    writer.add_page(page)
            except Exception as e:
                print(f"[x] Erro ao ler o PDF temporário {os.path.basename(pdf_path)}: {e}")
        with open(caminho_pdf_saida, 'wb') as output_file: writer.write(output_file)
    print(f"[✔] PDF criado com sucesso: {os.path.basename(caminho_pdf_saida)}")

def criar_cbz_de_imagens(lista_imagens, pasta_base_imagens, caminho_cbz_saida):
    if os.path.exists(caminho_cbz_saida):
        print(f"[⏩] CBZ já existe, pulando: {os.path.basename(caminho_cbz_saida)}")
        return
    try:
        with zipfile.ZipFile(caminho_cbz_saida, 'w', zipfile.ZIP_DEFLATED) as zf:
            for nome_arquivo in lista_imagens:
                caminho_completo = os.path.join(pasta_base_imagens, nome_arquivo)
                zf.write(caminho_completo, arcname=nome_arquivo)
        print(f"[✔] CBZ criado com sucesso: {os.path.basename(caminho_cbz_saida)}")
    except Exception as e:
        print(f"[x] Erro ao criar o arquivo CBZ {os.path.basename(caminho_cbz_saida)}: {e}")


# --- FUNÇÕES DE PROCESSAMENTO DE ARQUIVO ÚNICO ---
# (Estas funções não precisam de alteração)

def processar_arquivo_pdf(caminho_pdf):
    pasta_saida = os.path.dirname(caminho_pdf)
    nome_arquivo_sem_ext = os.path.splitext(os.path.basename(caminho_pdf))[0]
    caminho_cbz_saida = os.path.join(pasta_saida, f"{nome_arquivo_sem_ext}.cbz")
    print(f"\n[→] Processando PDF: {os.path.basename(caminho_pdf)} (em {os.path.basename(pasta_saida)})")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            with fitz.open(caminho_pdf) as pdf_document:
                imagens_geradas = []
                for page_num in range(len(pdf_document)):
                    page = pdf_document.load_page(page_num)
                    pix = page.get_pixmap(dpi=150)
                    nome_imagem = f"pág_{page_num+1}.jpg"
                    caminho_imagem = os.path.join(temp_dir, nome_imagem)
                    pix.save(caminho_imagem, jpg_quality=85)
                    imagens_geradas.append(nome_imagem)
            if imagens_geradas:
                criar_cbz_de_imagens(imagens_geradas, temp_dir, caminho_cbz_saida)
            else:
                print("[x] Nenhuma página foi extraída do PDF.")
    except Exception as e:
        print(f"[x] Ocorreu um erro ao converter o PDF: {e}")

def processar_arquivo_cbz(caminho_cbz):
    pasta_saida = os.path.dirname(caminho_cbz)
    nome_arquivo_sem_ext = os.path.splitext(os.path.basename(caminho_cbz))[0]
    caminho_pdf_saida = os.path.join(pasta_saida, f"{nome_arquivo_sem_ext}.pdf")
    print(f"\n[→] Processando CBZ: {os.path.basename(caminho_cbz)} (em {os.path.basename(pasta_saida)})")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(caminho_cbz, 'r') as zf:
                zf.extractall(temp_dir)
            arquivos_extraidos = natsorted([f for f in os.listdir(temp_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.avif'))])
            if arquivos_extraidos:
                criar_pdf_de_imagens(arquivos_extraidos, temp_dir, caminho_pdf_saida)
            else:
                print("[x] Nenhuma imagem encontrada dentro do arquivo CBZ.")
    except Exception as e:
        print(f"[x] Ocorreu um erro ao converter o CBZ: {e}")

# --- FUNÇÕES PRINCIPAIS DE CONVERSÃO (Handlers) ---

def iniciar_conversao_pdf_para_cbz_em_lote():
    """Pede uma pasta e converte todos os PDFs nela e em suas subpastas."""
    print("\n--- Conversão em Lote: PDF para CBZ (com subpastas) ---")
    pasta_raiz = obter_caminho_pasta()
    
    # *** ALTERAÇÃO PRINCIPAL AQUI: Usando os.walk() ***
    arquivos_pdf_encontrados = []
    for dirpath, _, filenames in os.walk(pasta_raiz):
        for filename in filenames:
            if filename.lower().endswith('.pdf'):
                arquivos_pdf_encontrados.append(os.path.join(dirpath, filename))
    
    if not arquivos_pdf_encontrados:
        print("\n[!] Nenhum arquivo .pdf encontrado na pasta ou em suas subpastas.")
        return
        
    print(f"\n[i] Encontrados {len(arquivos_pdf_encontrados)} arquivo(s) .pdf para conversão.")
    for caminho_completo_pdf in arquivos_pdf_encontrados:
        processar_arquivo_pdf(caminho_completo_pdf)
    print("\n[✅] Conversão de todos os PDFs concluída.")

def iniciar_conversao_cbz_para_pdf_em_lote():
    """Pede uma pasta e converte todos os CBZs nela e em suas subpastas."""
    print("\n--- Conversão em Lote: CBZ para PDF (com subpastas) ---")
    pasta_raiz = obter_caminho_pasta()
    
    # *** ALTERAÇÃO PRINCIPAL AQUI: Usando os.walk() ***
    arquivos_cbz_encontrados = []
    for dirpath, _, filenames in os.walk(pasta_raiz):
        for filename in filenames:
            if filename.lower().endswith('.cbz'):
                arquivos_cbz_encontrados.append(os.path.join(dirpath, filename))
    
    if not arquivos_cbz_encontrados:
        print("\n[!] Nenhum arquivo .cbz encontrado na pasta ou em suas subpastas.")
        return
        
    print(f"\n[i] Encontrados {len(arquivos_cbz_encontrados)} arquivo(s) .cbz para conversão.")
    for caminho_completo_cbz in arquivos_cbz_encontrados:
        processar_arquivo_cbz(caminho_completo_cbz)
    print("\n[✅] Conversão de todos os CBZs concluída.")


def converter_pasta_de_imagens():
    """Função original que converte pastas de imagens para PDF e/ou CBZ."""
    print("\n--- Conversão de Pasta de Imagens ---")
    # (Esta função permanece a mesma)
    print("\nEscolha o formato de saída:")
    print("1 - PDF\n2 - CBZ\n3 - Ambos (PDF e CBZ)")
    while True:
        opcao = input("Sua escolha (1, 2 ou 3): ").strip()
        if opcao == '1': formato_saida = 'PDF'; break
        elif opcao == '2': formato_saida = 'CBZ'; break
        elif opcao == '3': formato_saida = 'AMBOS'; break
        else: print("Opção inválida!")

    pasta_principal = obter_caminho_pasta()
    print(f"\n[→] Processando pasta principal: {pasta_principal}")
    # Processa imagens na pasta raiz
    imagens_na_raiz = natsorted([f for f in os.listdir(pasta_principal) if os.path.isfile(os.path.join(pasta_principal, f)) and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.avif'))])
    if imagens_na_raiz:
        print(f"\n[i] Encontradas {len(imagens_na_raiz)} imagens na pasta principal.")
        nome_base = os.path.basename(os.path.normpath(pasta_principal))
        if formato_saida in ['PDF', 'AMBOS']: criar_pdf_de_imagens(imagens_na_raiz, pasta_principal, os.path.join(pasta_principal, f"{nome_base}.pdf"))
        if formato_saida in ['CBZ', 'AMBOS']: criar_cbz_de_imagens(imagens_na_raiz, pasta_principal, os.path.join(pasta_principal, f"{nome_base}.cbz"))
    # Processa subpastas
    print("\n[→] Procurando por subpastas com imagens...")
    for nome_item in os.listdir(pasta_principal):
        caminho_item = os.path.join(pasta_principal, nome_item)
        if os.path.isdir(caminho_item):
            print(f"\n[→] Processando subpasta: {os.path.basename(caminho_item)}")
            imagens_sub = natsorted([f for f in os.listdir(caminho_item) if f.lower().endswith(('.jpg', '.jpeg', 'png', '.webp', '.avif'))])
            if not imagens_sub:
                print(f"[!] Nenhuma imagem encontrada em: {os.path.basename(caminho_item)}")
                continue
            if formato_saida in ['PDF', 'AMBOS']: criar_pdf_de_imagens(imagens_sub, caminho_item, os.path.join(pasta_principal, f"{nome_item}.pdf"))
            if formato_saida in ['CBZ', 'AMBOS']: criar_cbz_de_imagens(imagens_sub, caminho_item, os.path.join(pasta_principal, f"{nome_item}.cbz"))

# --- FUNÇÃO PRINCIPAL (main) ---

def main():
    """Menu principal que direciona para a função de conversão correta."""
    print("=======================================")
    print("        CONVERSOR DE ARQUIVOS          ")
    print("=======================================")
    
    while True:
        print("\nQual tipo de conversão você deseja fazer?")
        print("Todas as opções suportam subpastas.")
        print("=======================================")
        print("1 - Converter Pasta com Imagens (para PDF/CBZ)")
        print("2 - Converter PDF(s) para CBZ(s)")
        print("3 - Converter CBZ(s) para PDF(s)")
        print("4 - Sair")
        
        escolha = input("Sua escolha (1-4): ").strip()
        
        if escolha == '1':
            converter_pasta_de_imagens()
        elif escolha == '2':
            iniciar_conversao_pdf_para_cbz_em_lote()
        elif escolha == '3':
            iniciar_conversao_cbz_para_pdf_em_lote()
        elif escolha == '4':
            break
        else:
            print("[x] Opção inválida, por favor escolha de 1 a 4.")
            
        print("\n" + "="*40)
        continuar = input("Deseja realizar outra operação? (S/N): ").strip().upper()
        if continuar != 'S':
            break

    print("\nObrigado por usar o conversor!")
    input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()
