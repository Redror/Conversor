import os
import tempfile
import fitz  # PyMuPDF
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from natsort import natsorted

# REMOVIDO: import pillow_avif (Para reduzir tamanho do executável)

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

# --- WORKERS (CRIAÇÃO DE ARQUIVOS) ---

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
                    largura_atual = float(page.mediabox.width)
                    
                    if largura_padrao is None:
                        largura_padrao = largura_atual
                    
                    if largura_padrao > 0 and abs(largura_atual - largura_padrao) > 0.1:
                        fator_escala = largura_padrao / largura_atual
                        page.scale_by(float(fator_escala))
                    
                    writer.add_page(page)
            except Exception as e:
                print(f"[x] Erro ao ler PDF temporário {os.path.basename(pdf_path)}: {e}")
                
        with open(caminho_pdf_saida, 'wb') as output_file: writer.write(output_file)
    print(f"[✔] PDF criado: {os.path.basename(caminho_pdf_saida)}")

# --- FUNÇÃO 2: JUNTAR PDFS ---

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
                largura_atual = float(page.mediabox.width)
                
                if largura_padrao is None:
                    largura_padrao = largura_atual
                
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

# --- FUNÇÃO 3: DIVIDIR PDF (NOVA) ---

def dividir_pdfs_da_pasta():
    """Separa cada página de um PDF em arquivos individuais."""
    print("\n--- Dividir PDFs em Páginas Individuais ---")
    pasta_raiz = obter_caminho_pasta()
    
    arquivos_pdf = natsorted([
        f for f in os.listdir(pasta_raiz) 
        if f.lower().endswith('.pdf') and os.path.isfile(os.path.join(pasta_raiz, f))
    ])
    
    if not arquivos_pdf:
        print("\n[!] Nenhum arquivo .pdf encontrado nesta pasta.")
        return

    print(f"\n[i] Encontrados {len(arquivos_pdf)} PDFs para processar.")

    for nome_pdf in arquivos_pdf:
        caminho_completo = os.path.join(pasta_raiz, nome_pdf)
        # Ignora arquivos que pareçam ser resultado de uma junção anterior (opcional)
        if "_UNIFICADO" in nome_pdf:
            print(f"[⏩] Pulando arquivo unificado: {nome_pdf}")
            continue

        try:
            reader = PdfReader(caminho_completo)
            total_paginas = len(reader.pages)
            
            # Cria uma pasta com o nome do arquivo para guardar as páginas
            nome_pasta_saida = os.path.splitext(nome_pdf)[0] + "_PAGINAS"
            caminho_pasta_saida = os.path.join(pasta_raiz, nome_pasta_saida)
            
            if not os.path.exists(caminho_pasta_saida):
                os.makedirs(caminho_pasta_saida)
                
            print(f"\n[→] Dividindo: {nome_pdf} ({total_paginas} páginas)")
            print(f"    Salvando em: {nome_pasta_saida}")

            for i, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)
                
                # Nome do arquivo: Exemplo_pag_01.pdf
                nome_pag = f"{os.path.splitext(nome_pdf)[0]}_{i+1:02d}.pdf"
                caminho_pag = os.path.join(caminho_pasta_saida, nome_pag)
                
                with open(caminho_pag, 'wb') as out_f:
                    writer.write(out_f)
            
            print(f"[✅] Concluído: {nome_pdf}")

        except Exception as e:
            print(f"[x] Erro ao dividir {nome_pdf}: {e}")


# --- FUNÇÃO DE CONVERSÃO DE IMAGENS (Main Handler) ---

def converter_pasta_de_imagens():
    """Converte pastas de imagens para PDF com redimensionamento."""
    print("\n--- Conversão de Pasta de Imagens para PDF ---")
    pasta_principal = obter_caminho_pasta()
    print(f"\n[→] Processando pasta principal: {pasta_principal}")
    
    # REMOVIDO .avif DA LISTA ABAIXO
    extensoes_validas = ('.jpg', '.jpeg', '.png', '.webp')

    # Processa imagens na pasta raiz
    imagens_na_raiz = natsorted([f for f in os.listdir(pasta_principal) 
                                 if os.path.isfile(os.path.join(pasta_principal, f)) 
                                 and f.lower().endswith(extensoes_validas)])
    
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
            imagens_sub = natsorted([f for f in os.listdir(caminho_item) 
                                     if f.lower().endswith(extensoes_validas)])
            if not imagens_sub:
                continue
            
            print(f"\n[→] Processando subpasta: {os.path.basename(caminho_item)}")
            criar_pdf_de_imagens(imagens_sub, caminho_item, os.path.join(pasta_principal, f"{nome_item}.pdf"))

# --- MAIN ---

def main():
    print("=======================================")
    print("      CONVERSOR, JUNTADOR & DIVISOR    ")
    print("=======================================")
    
    while True:
        print("\nO que você deseja fazer?")
        print("=======================================")
        print("1 - Converter Pasta com Imagens (para PDF)")
        print("2 - Juntar vários PDFs em um só (Largura Igual)")
        print("3 - Dividir PDF (Separar páginas)")
        print("4 - Sair")
        
        escolha = input("Sua escolha (1-4): ").strip()
        
        if escolha == '1':
            converter_pasta_de_imagens()
        elif escolha == '2':
            juntar_pdfs_em_uma_pasta()
        elif escolha == '3':
            dividir_pdfs_da_pasta()
        elif escolha == '4':
            break
        else:
            print("[x] Opção inválida, por favor escolha de 1 a 4.")
            
        print("\n" + "="*40)
        continuar = input("Deseja realizar outra operação? (S/N): ").strip().upper()
        if continuar != 'S':
            break

    print("\nObrigado por usar o programa!")
    input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()