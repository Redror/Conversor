import os
import zipfile
import tempfile
import fitz  # PyMuPDF
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from natsort import natsorted

# --- CONFIGURAÇÕES GLOBAIS ---
ALTURA_MAXIMA_WEBP = 14000
ALTURA_MINIMA_FUSAO = 1000  # Se menor que isso, tenta juntar com a próxima

# --- FUNÇÕES UTILITÁRIAS ---

def obter_caminho_pasta():
    """Obtém o caminho de uma PASTA do usuário, limpando artefatos do PowerShell (&) e aspas."""
    raw_input = input("\nArraste a pasta para cá ou digite o caminho e pressione Enter: ")
    
    # 1. Remove espaços iniciais/finais
    caminho = raw_input.strip()
    
    # 2. Remove o '&' que o PowerShell coloca ao arrastar
    if caminho.startswith('&'):
        caminho = caminho[1:].strip()
        
    # 3. Remove aspas simples e duplas que sobram
    caminho = caminho.strip('"').strip("'").strip()
    
    # 4. Normaliza para o sistema operacional
    caminho = os.path.normpath(caminho)

    while not os.path.isdir(caminho):
        print(f"\n[x] Caminho inválido ou pasta não encontrada: {caminho}")
        
        raw_input = input("Por favor, informe um caminho de PASTA válido: ")
        caminho = raw_input.strip()
        if caminho.startswith('&'): caminho = caminho[1:].strip()
        caminho = caminho.strip('"').strip("'").strip()
        caminho = os.path.normpath(caminho)
        
    return caminho

def perguntar_modo_lote():
    """Retorna True se o usuário quiser incluir subpastas (lote), False se for apenas pasta atual."""
    while True:
        resp = input("Deseja incluir subpastas (modo recursivo)? [S/N]: ").strip().upper()
        if resp == 'S': return True
        if resp == 'N': return False

def listar_arquivos_inteligente(pasta_raiz, extensoes, recursivo):
    """Lista arquivos baseada na escolha de recursividade."""
    lista_arquivos = []
    if recursivo:
        for dirpath, _, filenames in os.walk(pasta_raiz):
            for filename in filenames:
                if filename.lower().endswith(extensoes):
                    lista_arquivos.append(os.path.join(dirpath, filename))
    else:
        for filename in os.listdir(pasta_raiz):
            full_path = os.path.join(pasta_raiz, filename)
            if os.path.isfile(full_path) and filename.lower().endswith(extensoes):
                lista_arquivos.append(full_path)
    return natsorted(lista_arquivos)

# --- LÓGICA DE PROCESSAMENTO DE IMAGEM (CORTE E FUSÃO) ---

def salvar_imagem_otimizada(img_pil, caminho_saida, formato):
    """Salva a imagem PIL no formato desejado."""
    try:
        if formato.upper() == 'WEBP':
            img_pil.save(caminho_saida, 'WEBP', quality=85, method=6)
        elif formato.upper() == 'JPEG' or formato.upper() == 'JPG':
            img_pil.convert('RGB').save(caminho_saida, 'JPEG', quality=90)
        else:
            img_pil.save(caminho_saida, formato)
        return True
    except Exception as e:
        print(f"[x] Erro ao salvar imagem {os.path.basename(caminho_saida)}: {e}")
        return False

def processar_lista_imagens_pil(lista_tuplas_pil_nome, pasta_saida, formato_saida, substituir_originais=False):
    """
    Recebe uma lista de TUPLAS: [(ObjetoPIL, CaminhoOriginal ou NomeBase), ...]
    Aplica Split/Merge mantendo nomes originais.
    Se substituir_originais=True, deleta os arquivos de origem após salvar os novos.
    """
    buffer_img = None
    buffer_nome_base = None
    buffer_caminhos_origem = [] # Lista de arquivos que compõem o buffer atual (para deletar depois)

    queue = lista_tuplas_pil_nome.copy()
    
    def finalizar_salvamento(img_para_salvar, nome_base, sufixo=""):
        # Define extensão e nome final
        ext = formato_saida.lower().replace('jpeg', 'jpg')
        nome_final = f"{nome_base}{sufixo}.{ext}"
        caminho_final = os.path.join(pasta_saida, nome_final)
        
        sucesso = salvar_imagem_otimizada(img_para_salvar, caminho_final, formato_saida)
        
        # Se salvou com sucesso e o modo é substituir, deleta os originais que compuseram essa imagem
        if sucesso and substituir_originais:
            for caminho_velho in buffer_caminhos_origem:
                # Cuidado para não deletar o arquivo que acabamos de criar (se for mesmo nome/extensão)
                if os.path.abspath(caminho_velho) != os.path.abspath(caminho_final):
                    try:
                        os.remove(caminho_velho)
                    except Exception as e:
                        print(f"[!] Não foi possível deletar original: {caminho_velho}")

    while queue or buffer_img:
        # Carregar próximo item no buffer se vazio
        if buffer_img is None:
            if not queue: break
            img_obj, caminho_origem = queue.pop(0)
            buffer_img = img_obj
            # Extrai apenas o nome do arquivo sem extensão para usar como base
            buffer_nome_base = os.path.splitext(os.path.basename(caminho_origem))[0]
            buffer_caminhos_origem = [caminho_origem]

        # 1. VERIFICAÇÃO DE CORTE (SPLIT)
        if buffer_img.height > ALTURA_MAXIMA_WEBP:
            topo = 0
            parte_idx = 1
            while topo < buffer_img.height:
                altura_restante = buffer_img.height - topo
                altura_corte = min(ALTURA_MAXIMA_WEBP, altura_restante)
                box = (0, topo, buffer_img.width, topo + altura_corte)
                parte = buffer_img.crop(box)
                
                # Se for a última parte e for pequena, tenta fundir
                if (topo + altura_corte >= buffer_img.height) and (altura_corte < ALTURA_MINIMA_FUSAO) and queue:
                    buffer_img = parte
                    # Mantém o buffer_nome_base atual
                    # Não limpamos buffer_caminhos_origem pois o original ainda não foi totalmente processado
                    break 
                else:
                    # Salva a parte com sufixo _01, _02...
                    finalizar_salvamento(parte, buffer_nome_base, f"_{parte_idx:02d}")
                    parte_idx += 1
                
                topo += altura_corte
            
            # Se processou tudo
            if topo >= buffer_img.height:
                buffer_img = None
                buffer_caminhos_origem = [] # Reset
            continue 

        # 2. VERIFICAÇÃO DE FUSÃO (MERGE)
        if buffer_img.height < ALTURA_MINIMA_FUSAO and queue:
            prox_img, prox_caminho = queue[0] # Espia a próxima
            
            if buffer_img.height + prox_img.height <= ALTURA_MAXIMA_WEBP:
                # Merge aceito
                queue.pop(0) # Remove da fila
                prox_caminho_removido = prox_caminho
                
                # Adiciona o caminho da próxima imagem à lista de "para deletar"
                buffer_caminhos_origem.append(prox_caminho_removido)
                
                # Cria imagem combinada
                nova_largura = max(buffer_img.width, prox_img.width)
                nova_altura = buffer_img.height + prox_img.height
                nova_img = Image.new('RGB', (nova_largura, nova_altura), (255, 255, 255))
                
                x_offset1 = (nova_largura - buffer_img.width) // 2
                x_offset2 = (nova_largura - prox_img.width) // 2
                
                nova_img.paste(buffer_img, (x_offset1, 0))
                nova_img.paste(prox_img, (x_offset2, buffer_img.height))
                
                buffer_img = nova_img 
                # Nota: O nome base continua sendo o da PRIMEIRA imagem da fusão
            else:
                # Não cabe, salva o atual
                finalizar_salvamento(buffer_img, buffer_nome_base)
                buffer_img = None
                buffer_caminhos_origem = []
        else:
            # Tamanho ok ou sem próxima, salva
            finalizar_salvamento(buffer_img, buffer_nome_base)
            buffer_img = None
            buffer_caminhos_origem = []

# --- WORKERS (CRIAÇÃO DE ARQUIVOS) ---

def criar_zip_de_imagens(caminho_pasta_imagens, caminho_zip_saida):
    if os.path.exists(caminho_zip_saida):
        print(f"[⏩] ZIP já existe, pulando: {os.path.basename(caminho_zip_saida)}")
        return
    try:
        with zipfile.ZipFile(caminho_zip_saida, 'w', zipfile.ZIP_DEFLATED) as zf:
            arquivos = natsorted(os.listdir(caminho_pasta_imagens))
            for nome_arquivo in arquivos:
                full_path = os.path.join(caminho_pasta_imagens, nome_arquivo)
                if os.path.isfile(full_path):
                    zf.write(full_path, arcname=nome_arquivo)
        print(f"[✔] ZIP criado: {os.path.basename(caminho_zip_saida)}")
    except Exception as e:
        print(f"[x] Erro ao criar ZIP: {e}")

def criar_pdf_simples(caminho_pasta_imagens, caminho_pdf_saida):
    if os.path.exists(caminho_pdf_saida): return
    imagens = natsorted([os.path.join(caminho_pasta_imagens, f) for f in os.listdir(caminho_pasta_imagens)])
    if not imagens: return
    
    with tempfile.TemporaryDirectory() as temp_pdf_dir:
        pdfs = []
        for img_path in imagens:
            try:
                with Image.open(img_path) as img:
                    # Usa o nome original do arquivo para o PDF temporário
                    nome_pdf_temp = os.path.splitext(os.path.basename(img_path))[0] + ".pdf"
                    pdf_path = os.path.join(temp_pdf_dir, nome_pdf_temp)
                    img.convert("RGB").save(pdf_path, "PDF", resolution=100.0)
                    pdfs.append(pdf_path)
            except: pass
            
        writer = PdfWriter()
        for pdf in pdfs:
            try:
                reader = PdfReader(pdf)
                writer.add_page(reader.pages[0])
            except: pass
        with open(caminho_pdf_saida, 'wb') as f: writer.write(f)
    print(f"[✔] PDF criado: {os.path.basename(caminho_pdf_saida)}")

# --- PROCESSADORES DE ARQUIVOS INDIVIDUAIS ---

def processar_pdf_para_zip(caminho_pdf):
    pasta_saida = os.path.dirname(caminho_pdf)
    nome_base = os.path.splitext(os.path.basename(caminho_pdf))[0]
    caminho_zip = os.path.join(pasta_saida, f"{nome_base}.zip")
    
    try:
        doc = fitz.open(caminho_pdf)
        lista_tuplas = []
        
        for i in range(len(doc)):
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            # Para PDF, usamos nomes de página genéricos pois não há "original"
            nome_pag = f"Pagina_{i+1:03d}"
            lista_tuplas.append((img, nome_pag))
            
        if not lista_tuplas:
            print("[x] PDF vazio ou ilegível.")
            return

        with tempfile.TemporaryDirectory() as temp_dir:
            # Não substituímos originais aqui (PDF é a origem)
            processar_lista_imagens_pil(lista_tuplas, temp_dir, "WEBP", substituir_originais=False)
            criar_zip_de_imagens(temp_dir, caminho_zip)
            
    except Exception as e:
        print(f"[x] Erro ao converter PDF {nome_base}: {e}")

def processar_zip_para_pdf(caminho_zip):
    pasta_saida = os.path.dirname(caminho_zip)
    nome_base = os.path.splitext(os.path.basename(caminho_zip))[0]
    caminho_pdf = os.path.join(pasta_saida, f"{nome_base}.pdf")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(caminho_zip, 'r') as zf:
                zf.extractall(temp_dir)
            criar_pdf_simples(temp_dir, caminho_pdf)
    except Exception as e:
        print(f"[x] Erro ao converter ZIP/CBZ: {e}")

# --- HANDLERS DE MENU ---

def converter_pasta_imagens_formatos():
    print("\n--- Converter Formato (Substituir Originais) ---")
    pasta = obter_caminho_pasta()
    recursivo = perguntar_modo_lote()
    
    formato = input("Para qual formato converter? (WEBP, JPG, PNG): ").strip().upper()
    if formato not in ['WEBP', 'JPG', 'JPEG', 'PNG']: formato = 'JPG'
    
    pastas_para_processar = [x[0] for x in os.walk(pasta)] if recursivo else [pasta]
        
    for p in pastas_para_processar:
        imgs_paths = natsorted([os.path.join(p, f) for f in os.listdir(p) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
        if not imgs_paths: continue
        
        lista_tuplas = []
        for ip in imgs_paths:
            try:
                # Armazena (Imagem, CaminhoCompleto)
                lista_tuplas.append((Image.open(ip), ip))
            except: pass
            
        if lista_tuplas:
            # Salva na PRÓPRIA pasta (p) e ativa substituir_originais=True
            processar_lista_imagens_pil(lista_tuplas, p, formato, substituir_originais=True)
            print(f"[✔] Imagens convertidas")

def converter_pdf_para_zip_handler():
    print("\n--- PDF para ZIP (Imagens WebP) ---")
    pasta = obter_caminho_pasta()
    recursivo = perguntar_modo_lote()
    pdfs = listar_arquivos_inteligente(pasta, ('.pdf'), recursivo)
    
    if not pdfs: print("[!] Nenhum PDF encontrado."); return
    for pdf in pdfs: processar_pdf_para_zip(pdf)

def converter_zip_para_pdf_handler():
    print("\n--- ZIP/CBZ para PDF ---")
    pasta = obter_caminho_pasta()
    recursivo = perguntar_modo_lote()
    zips = listar_arquivos_inteligente(pasta, ('.zip', '.cbz', '.rar'), recursivo)
    
    if not zips: print("[!] Nenhum arquivo comprimido encontrado."); return
    for z in zips: processar_zip_para_pdf(z)

def converter_pasta_para_zip_pdf_handler():
    print("\n--- Pasta de Imagens para ZIP/PDF ---")
    pasta_raiz = obter_caminho_pasta()
    recursivo = perguntar_modo_lote()
    
    tipo_saida = input("Saída: 1-ZIP, 2-PDF, 3-Ambos: ").strip()
    
    pastas = [x[0] for x in os.walk(pasta_raiz)] if recursivo else [pasta_raiz]
    
    for p in pastas:
        imgs = natsorted([os.path.join(p, f) for f in os.listdir(p) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
        if not imgs: continue
        
        nome_arquivo = os.path.basename(p)
        
        lista_tuplas = []
        for i in imgs:
            try: lista_tuplas.append((Image.open(i), i))
            except: pass
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Processa para pasta temporária mantendo nomes originais
            # Não substituímos os originais aqui, pois estamos apenas criando um pacote (ZIP/PDF)
            processar_lista_imagens_pil(lista_tuplas, temp_dir, "WEBP", substituir_originais=False)
            
            if tipo_saida in ['1', '3']:
                criar_zip_de_imagens(temp_dir, os.path.join(p, f"{nome_arquivo}.zip"))
            if tipo_saida in ['2', '3']:
                criar_pdf_simples(temp_dir, os.path.join(p, f"{nome_arquivo}.pdf"))

# --- MAIN ---

def main():
    print("=======================================")
    print("               CONVERSOR               ")
    print("=======================================")
    
    while True:
        print("\nMENU PRINCIPAL:")
        print("1 - Pasta de Imagens -> Arquivo Único (ZIP/PDF)")
        print("2 - Converter PDF(s) -> ZIP(s) (Imagens WebP)")
        print("3 - Converter ZIP/CBZ(s) -> PDF(s)")
        print("4 - Converter Formato e Substituir (JPG/PNG/WebP)")
        print("5 - Sair")
        
        op = input("Opção: ").strip()
        
        if op == '1': converter_pasta_para_zip_pdf_handler()
        elif op == '2': converter_pdf_para_zip_handler()
        elif op == '3': converter_zip_para_pdf_handler()
        elif op == '4': converter_pasta_imagens_formatos()
        elif op == '5': break
        else: print("Opção inválida.")
        
        print("-" * 30)

if __name__ == "__main__":
    main()