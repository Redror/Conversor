import os
import tempfile
import fitz  # PyMuPDF
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter, Transformation
from natsort import natsorted
import pillow_avif

# --- FUNÇÕES DE OBTENÇÃO DE CAMINHO ---

def obter_caminho_pasta():
    """Obtém o caminho de uma PASTA do usuário, limpando formatação do PowerShell."""
    entrada = input("\nArraste a pasta para cá ou digite o caminho e pressione Enter: ")
    
    # Limpeza de caracteres inseridos pelo PowerShell ao arrastar
    caminho = entrada.replace("&", "").replace("'", "").replace('"', "").strip()
    
    while not os.path.isdir(caminho):
        print(f"\n[x] Caminho inválido ou pasta não encontrada: {caminho}")
        entrada = input("Por favor, informe um caminho de PASTA válido: ")
        caminho = entrada.replace("&", "").replace("'", "").replace('"', "").strip()
        
    return caminho

# --- FUNÇÕES DE CRIAÇÃO (WORKERS) ---

def criar_pdf_de_imagens(lista_imagens, pasta_base_imagens, caminho_pdf_saida):
    if os.path.exists(caminho_pdf_saida):
        print(f"[⏩] PDF já existe, pulando: {os.path.basename(caminho_pdf_saida)}")
        return
        
    print(f"    Processing {len(lista_imagens)} imagens para PDF...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        pdfs_temp = []
        # 1. Converter imagens para PDFs temporários
        for nome_arquivo in lista_imagens:
            img_path = os.path.join(pasta_base_imagens, nome_arquivo)
            try:
                with Image.open(img_path) as img:
                    img_convertida = img.convert("RGB")
                    pdf_temp = os.path.join(temp_dir, f"{os.path.splitext(nome_arquivo)[0]}.pdf")
                    img_convertida.save(pdf_temp, "PDF", resolution=100.0)
                    pdfs_temp.append(pdf_temp)
            except Exception as e:
                print(f"[x] Erro ao processar imagem {nome_arquivo}: {e}")
        
        if not pdfs_temp: return

        # 2. Juntar e Redimensionar
        writer = PdfWriter()
        largura_padrao = None
        
        for pdf_path in pdfs_temp:
            try:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    # CORREÇÃO: Forçar conversão para float para evitar erro Decimal
                    largura_atual = float(page.mediabox.width)
                    
                    # Define a largura da primeira página como padrão
                    if largura_padrao is None:
                        largura_padrao = largura_atual
                    
                    # Redimensiona se necessário (com margem de erro pequena)
                    if largura_padrao > 0 and abs(largura_atual - largura_padrao) > 0.1:
                        fator_escala = largura_padrao / largura_atual
                        page.scale_by(float(fator_escala))
                    
                    writer.add_page(page)
            except Exception as e:
                print(f"[x] Erro ao ler PDF temporário {os.path.basename(pdf_path)}: {e}")
                
        with open(caminho_pdf_saida, 'wb') as output_file: writer.write(output_file)
    print(f"[✔] PDF criado: {os.path.basename(caminho_pdf_saida)}")

# --- FUNÇÃO: JUNTAR PDFS ---

def juntar_pdfs_em_uma_pasta():
    """Pede uma pasta, une os PDFs e ajusta a largura de todas as páginas."""
    print("\n--- Juntar Vários PDFs (Padronizando Largura) ---")
    pasta_raiz = obter_caminho_pasta()
    
    arquivos_pdf = natsorted([
        f for f in os.listdir(pasta_raiz) 
        if f.lower().endswith('.pdf') and os.path.isfile(os.path.join(pasta_raiz, f))
    ])
    
    if not arquivos_pdf:
        print("\n[!] Nenhum arquivo .pdf encontrado nesta pasta.")
        return
    
    if len(arquivos_pdf) < 2:
        print("\n[!] Encontrado apenas 1 PDF. É necessário pelo menos 2 para juntar.")
        return

    print(f"\n[i] Encontrados {len(arquivos_pdf)} PDFs. Iniciando junção...")
    
    nome_saida = f"{os.path.basename(os.path.normpath(pasta_raiz))}_UNIFICADO.pdf"
    caminho_saida = os.path.join(pasta_raiz, nome_saida)

    writer = PdfWriter()
    largura_padrao = None 
    
    for nome_pdf in arquivos_pdf:
        caminho_completo = os.path.join(pasta_raiz, nome_pdf)
        if nome_pdf == nome_saida: continue
            
        try:
            reader = PdfReader(caminho_completo)
            for page in reader.pages:
                
                # CORREÇÃO: Converter Decimal para float explicitamente
                largura_atual = float(page.mediabox.width)
                
                if largura_padrao is None:
                    largura_padrao = largura_atual
                
                # Verifica diferença e redimensiona
                if largura_padrao > 0 and abs(largura_atual - largura_padrao) > 0.1:
                    fator_escala = largura_padrao / largura_atual
                    page.scale_by(float(fator_escala))
                
                writer.add_page(page)
            print(f"[+] Adicionado: {nome_pdf}")
        except Exception as e:
            print(f"[x] Erro ao ler {nome_pdf}: {e}")
            
    try:
        with open(caminho_saida, 'wb') as output_file:
            writer.write(output_file)
        print(f"\n[✅] Sucesso! Arquivo criado: {nome_saida}")
    except Exception as e:
        print(f"\n[x] Erro ao salvar o arquivo final: {e}")


# --- FUNÇÃO DE CONVERSÃO DE IMAGENS (Main Handler) ---

def converter_pasta_de_imagens():
    """Converte pastas de imagens para PDF com redimensionamento."""
    print("\n--- Conversão de Pasta de Imagens para PDF ---")
    pasta_principal = obter_caminho_pasta()
    print(f"\n[→] Processando pasta principal: {pasta_principal}")
    
    # Processa imagens na pasta raiz
    imagens_na_raiz = natsorted([f for f in os.listdir(pasta_principal) if os.path.isfile(os.path.join(pasta_principal, f)) and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.avif'))])
    if imagens_na_raiz:
        print(f"\n[i] Encontradas {len(imagens_na_raiz)} imagens na pasta principal.")
        nome_base = os.path.basename(os.path.normpath(pasta_principal))
        criar_pdf_de_imagens(imagens_na_raiz, pasta_principal, os.path.join(pasta_principal, f"{nome_base}.pdf"))
        
    # Processa subpastas
    print("\n[→] Procurando por subpastas com imagens...")
    for nome_item in os.listdir(pasta_principal):
        caminho_item = os.path.join(pasta_principal, nome_item)
        if os.path.isdir(caminho_item):
            # Verifica se há imagens antes de processar
            imagens_sub = natsorted([f for f in os.listdir(caminho_item) if f.lower().endswith(('.jpg', '.jpeg', 'png', '.webp', '.avif'))])
            if not imagens_sub:
                continue
            
            print(f"\n[→] Processando subpasta: {os.path.basename(caminho_item)}")
            criar_pdf_de_imagens(imagens_sub, caminho_item, os.path.join(pasta_principal, f"{nome_item}.pdf"))

# --- MAIN ---

def main():
    print("=======================================")
    print("        CONVERSOR & JUNTADOR DE PDF    ")
    print("=======================================")
    
    while True:
        print("\nO que você deseja fazer?")
        print("=======================================")
        print("1 - Converter Pasta com Imagens (para PDF)")
        print("2 - Juntar vários PDFs em um só (Largura Igual)")
        print("3 - Sair")
        
        escolha = input("Sua escolha (1-3): ").strip()
        
        if escolha == '1':
            converter_pasta_de_imagens()
        elif escolha == '2':
            juntar_pdfs_em_uma_pasta()
        elif escolha == '3':
            break
        else:
            print("[x] Opção inválida, por favor escolha de 1 a 3.")
            
        print("\n" + "="*40)
        continuar = input("Deseja realizar outra operação? (S/N): ").strip().upper()
        if continuar != 'S':
            break

    print("\nObrigado por usar o programa!")
    input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()