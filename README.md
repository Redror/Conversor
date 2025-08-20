# Conversor

## 📖 O que este programa faz?

Este programa é uma ferramenta de linha de comando para converter arquivos de forma rápida e em lote.

Suas principais funções são:

  * **Converter pastas de imagens** (`.jpg`, `.png`, etc.) para um único arquivo **PDF** ou **CBZ**.
  * **Converter arquivos `.pdf`** para o formato `.cbz` em lote, procurando em todas as subpastas.
  * **Converter arquivos `.cbz`** para o formato `.pdf` em lote, também procurando em todas as subpastas.

## 🚀 Como Usar (Guia Rápido)

#### Passo 1: Execute o programa

Dê um duplo clique no arquivo `Conversor.exe`. Uma janela de terminal preta irá se abrir com o menu principal.

 \#\#\#\# Passo 2: Escolha uma opção
Digite o número da conversão que você deseja fazer e pressione **Enter**.

> **1 - Converter Pasta com Imagens (para PDF/CBZ)**
> **2 - Converter PDF(s) para CBZ(s)**
> **3 - Converter CBZ(s) para PDF(s)**

#### Passo 3: Informe a pasta

O programa irá pedir o caminho da pasta que contém os arquivos a serem convertidos.

  * **O jeito mais fácil:** Clique e **arraste a pasta** que você quer processar para dentro da janela do terminal e pressione **Enter**.

#### Passo 4: Aguarde a conversão
O programa irá processar todos os arquivos encontrados na pasta (e também nas subpastas, se for o caso). Ele exibirá o progresso na tela.

Os arquivos convertidos serão salvos **no mesmo local** dos arquivos originais.

-----

## ⚙️ Funcionalidades Detalhadas

#### 1\. Converter Pasta com Imagens

  * **Como funciona:** O programa busca por imagens (`.jpg`, `.jpeg`, `.png`, `.webp`, `.avif`) dentro da pasta que você informou e também dentro das subpastas diretas.
  * **Resultado:** Ele cria um arquivo `.pdf` ou `.cbz` (ou ambos) para cada pasta que contém imagens. O nome do arquivo gerado será o mesmo nome da pasta.

#### 2\. Converter PDF(s) para CBZ(s)

  * **Como funciona:** O programa procura **todos os arquivos `.pdf`** dentro da pasta que você informou e em **todas as suas subpastas**, não importa o quão profundas elas estejam.
  * **Resultado:** Para cada `exemplo.pdf` encontrado, um `exemplo.cbz` será criado no mesmo diretório.

#### 3\. Converter CBZ(s) para PDF(s)

  * **Como funciona:** Assim como a opção anterior, o programa varre a pasta principal e **todas as suas subpastas** em busca de arquivos `.cbz`.
  * **Resultado:** Para cada `exemplo.cbz` encontrado, um `exemplo.pdf` será criado no mesmo diretório.

-----

## ⚠️ Solução de Problemas

**Aviso "O Windows protegeu o computador" ao abrir o `.exe`**

Se você vir uma tela azul do Windows SmartScreen, isso é um aviso de segurança padrão para programas baixados da internet.

1.  Clique em **"Mais informações"**.
2.  Depois, clique no botão **"Executar mesmo assim"**.
