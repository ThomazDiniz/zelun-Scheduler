# Agendador de Vídeos em Massa para YouTube

Um script Python para fazer upload e agendar automaticamente múltiplos vídeos no seu canal do YouTube. O script processa vídeos de uma pasta local, faz upload deles para o YouTube, agenda a publicação em horários especificados e organiza os vídeos enviados em uma pasta "sent".

> 🇺🇸 **English**: [README.md](README.md)

## Funcionalidades

- ✅ **Upload em Massa**: Processa múltiplos vídeos em uma única execução
- ✅ **Agendamento Automático**: Agenda vídeos para dias consecutivos em horários configuráveis
- ✅ **Gerenciamento de Cota**: Verifica automaticamente os horários de reset da cota da API do YouTube
- ✅ **Tratamento de Erros**: Tratamento de erros elegante com mensagens claras
- ✅ **Caminhos Relativos**: Usa caminhos relativos ao script para portabilidade
- ✅ **Configurável**: Argumentos de linha de comando para todas as configurações
- ✅ **Código em Inglês**: Totalmente documentado em inglês

## Limitações

- **Limite Diário de Upload**: A API do YouTube tem um limite de cota de 6 vídeos por dia
- O script para automaticamente quando o limite diário é atingido
- A cota é resetada às 05:00 horário local (quando usando o fuso horário do Brasil)

## Requisitos

- Python 3.7 ou superior
- Projeto no Google Cloud com YouTube Data API v3 habilitada
- Credenciais OAuth 2.0 do Google Cloud Console
- Arquivos de vídeo em uma pasta `clips`

## Instalação

1. **Clone ou baixe este repositório**

2. **Instale as dependências do Python**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure as credenciais do Google Cloud**:
   - Acesse o [Google Cloud Console](https://console.cloud.google.com/)
   - Crie um novo projeto ou selecione um existente
   - Habilite a **YouTube Data API v3**
   - Crie **credenciais OAuth 2.0** (tipo Aplicativo desktop)
   - Baixe o arquivo JSON das credenciais
   - Renomeie para `client_secret.json` e coloque no diretório do script
   - Veja `client_secret_sample.json` para o formato esperado

4. **Configure as configurações padrão (opcional)**:
   - Edite `config.json` com suas configurações preferidas
   - O arquivo vem com padrões sensatos para o fuso horário do Brasil
   - Isso permite pular argumentos de linha de comando em cada execução
   - Veja a seção [Configuração](#configuração) no README.md para exemplos

5. **Crie a estrutura de pastas**:
   ```
   youtube-bulk-scheduler/
   ├── youtube_bulk_scheduler.py
   ├── client_secret.json          # Suas credenciais (não está no git)
   ├── clips/                      # Coloque os vídeos aqui
   │   ├── video1.mp4
   │   └── video2.mp4
   └── sent/                       # Vídeos enviados movidos para cá (criado automaticamente)
   ```

## Configuração

O arquivo `config.json` contém valores padrão para o script. Você pode editá-lo para personalizar suas preferências sem precisar passar argumentos de linha de comando toda vez.

Edite `config.json` com suas preferências:
   ```json
   {
     "default_timezone": "America/Sao_Paulo",
     "default_hour_slots": [8, 18],
     "default_category_id": "20",
     "quota_reset_hour": 5,
     "video_extensions": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"],
     "privacy_status": "private"
   }
   ```

3. **Nota**: Argumentos de linha de comando sempre sobrescrevem valores do arquivo de configuração.

### Opções de Configuração

- **`default_timezone`**: Fuso horário padrão para agendamento (ex.: `"America/Sao_Paulo"`)
- **`default_hour_slots`**: Horários padrão por dia (array de inteiros, 0-23)
- **`default_category_id`**: ID da categoria padrão do YouTube (string)
- **`quota_reset_hour`**: Hora em que a cota do YouTube é resetada (0-23, padrão: 5)
- **`video_extensions`**: Lista de extensões de arquivo de vídeo para processar
- **`privacy_status`**: Status de privacidade padrão (`"private"`, `"unlisted"`, ou `"public"`)

## Uso

### Uso Básico (Todos os Padrões)

Execute com as configurações padrão:
- Data de início: Hoje
- Fuso horário: GMT Brasil (America/Sao_Paulo)
- Horários: 8:00 e 18:00 (2 vídeos por dia)
- Categoria: Jogos (ID: 20)

```bash
python youtube_bulk_scheduler.py
```

### Argumentos de Linha de Comando

Todos os parâmetros podem ser personalizados via argumentos de linha de comando:

#### `--start-date` (Opcional)
Data de início para o primeiro vídeo no formato `YYYY-MM-DD`. Padrão: hoje.

```bash
python youtube_bulk_scheduler.py --start-date 2025-12-01
```

#### `--timezone` (Opcional)
Fuso horário para agendamento. Padrão: `America/Sao_Paulo` (GMT Brasil)

Fusos horários comuns:
- `America/Sao_Paulo` - Brasil (GMT-3)
- `America/New_York` - Horário do Leste (GMT-5/4)
- `Europe/London` - Reino Unido (GMT+0/1)
- `Asia/Tokyo` - Japão (GMT+9)

```bash
python youtube_bulk_scheduler.py --timezone America/New_York
```

#### `--hour-slots` (Opcional)
Horários por dia (formato 24 horas). Padrão: `8 18` (8h e 18h)

```bash
# Um vídeo por dia às 10h
python youtube_bulk_scheduler.py --hour-slots 10

# Três vídeos por dia às 9h, 12h e 18h
python youtube_bulk_scheduler.py --hour-slots 9 12 18

# Quatro vídeos por dia
python youtube_bulk_scheduler.py --hour-slots 8 12 16 20
```

#### `--category-id` (Opcional)
ID da categoria do YouTube. Padrão: `20` (Jogos)

Categorias comuns:
- `1` - Filmes e Animações
- `2` - Automóveis e Veículos
- `10` - Música
- `15` - Animais de Estimação
- `17` - Esportes
- `19` - Viagens e Eventos
- `20` - Jogos
- `22` - Pessoas e Blogs
- `23` - Comédia
- `24` - Entretenimento
- `25` - Notícias e Política
- `26` - Como Fazer e Estilo
- `27` - Educação
- `28` - Ciência e Tecnologia

```bash
python youtube_bulk_scheduler.py --category-id 24
```

### Exemplos Completos

**Exemplo 1**: Data de início personalizada com horários padrão
```bash
python youtube_bulk_scheduler.py --start-date 2025-12-15
```

**Exemplo 2**: Fuso horário e horários personalizados
```bash
python youtube_bulk_scheduler.py --timezone America/New_York --hour-slots 10 14 18
```

**Exemplo 3**: Personalização completa
```bash
python youtube_bulk_scheduler.py \
  --start-date 2025-12-01 \
  --timezone America/Sao_Paulo \
  --hour-slots 8 12 16 20 \
  --category-id 20
```

**Exemplo 4**: Um vídeo por dia ao meio-dia
```bash
python youtube_bulk_scheduler.py --hour-slots 12
```

## Como Funciona

### Fluxo de Processamento de Vídeos

1. **Execução do Script**: O script é executado a partir do seu diretório
2. **Descoberta de Vídeos**: Escaneia a pasta `clips/` em busca de arquivos de vídeo
3. **Lógica de Agendamento**: 
   - Os vídeos são agendados a partir da `--start-date` (ou hoje)
   - Os vídeos são distribuídos entre os dias com base em `--hour-slots`
   - Exemplo: Com horários `[8, 18]` e 5 vídeos:
     - Vídeo 1: Dia 1 às 8:00
     - Vídeo 2: Dia 1 às 18:00
     - Vídeo 3: Dia 2 às 8:00
     - Vídeo 4: Dia 2 às 18:00
     - Vídeo 5: Dia 3 às 8:00
4. **Upload**: Cada vídeo é enviado como privado e agendado para publicação
5. **Organização de Arquivos**: Vídeos enviados com sucesso são movidos para a pasta `sent/`

### Autenticação

1. Primeira execução: O script abre um navegador para autenticação OAuth
2. Após autenticação: Um arquivo `token.json` é criado (ignorado automaticamente pelo git)
3. Execuções subsequentes: Usa o token salvo (atualiza automaticamente se expirado)

### Gerenciamento de Cota

- A API do YouTube tem um limite de cota diária (tipicamente 6 uploads por dia)
- O script verifica se a cota foi resetada (05:00 horário local)
- Se a cota for excedida, o script para e mostra uma mensagem
- Retome executando o script novamente após o reset da cota

## Estrutura do Projeto

```
youtube-bulk-scheduler/
├── youtube_bulk_scheduler.py   # Script principal
├── requirements.txt             # Dependências do Python
├── README.md                    # Este arquivo (inglês)
├── README.pt-BR.md             # Este arquivo (português)
├── .gitignore                   # Regras de ignore do Git
├── config.json                  # Configuração padrão (editável)
├── client_secret.json          # Suas credenciais OAuth (não está no git)
├── token.json                  # Cache do token OAuth (não está no git)
├── client_secret_sample.json   # Formato de exemplo das credenciais
├── token_sample.json           # Formato de exemplo do token
├── clips/                      # Arquivos de vídeo para enviar
│   ├── video1.mp4
│   └── video2.mp4
└── sent/                       # Vídeos enviados com sucesso
    └── video1.mp4
```

## Visão Geral do Código

### Funções Principais

- **`parse_arguments()`**: Analisa argumentos de linha de comando com padrões
- **`parse_start_date()`**: Trata o parsing de datas com validação
- **`quota_reset_ok()`**: Verifica se a cota da API do YouTube foi resetada
- **`get_authenticated_service()`**: Trata a autenticação OAuth
- **`upload_and_schedule()`**: Faz upload do vídeo e define o horário de publicação
- **`main()`**: Orquestra todo o processo de upload

### Constantes de Configuração

- **`SCOPES`**: Escopo da API do YouTube para uploads de vídeo
- **`SCRIPT_DIR`**: Diretório onde o script está localizado (para caminhos relativos)
- **`CLIPS_FOLDER`**: Caminho para a pasta contendo vídeos (`script_dir/clips`)
- **`SENT_FOLDER`**: Caminho para a pasta de vídeos enviados (`script_dir/sent`)

### Tratamento de Erros

O script inclui tratamento abrangente de erros:

- `client_secret.json` ausente: Instruções claras sobre como obtê-lo
- Pasta `clips/` ausente: Explica onde criá-la
- Fuso horário inválido: Lista fusos horários comuns e fornece link para lista completa
- Formato de data inválido: Explica o formato esperado
- Horários inválidos: Valida o intervalo (0-23)
- Cota excedida: Para graciosamente com informações sobre o horário de reset

## Solução de Problemas

### "client_secret.json não encontrado"
- Baixe as credenciais OAuth do Google Cloud Console
- Salve como `client_secret.json` no diretório do script
- Veja `client_secret_sample.json` para referência de formato

### "Pasta clips não encontrada"
- Crie uma pasta `clips` no mesmo diretório do script
- Coloque seus arquivos de vídeo na pasta `clips`

### "Fuso horário inválido"
- Use um fuso horário válido do [banco de dados tz](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
- Formato comum: `Continente/Cidade` (ex.: `America/Sao_Paulo`)

### "Cota diária excedida"
- A API do YouTube permite ~6 uploads por dia
- Aguarde até 05:00 horário local para o reset da cota
- Execute o script novamente após o reset

### Erros de autenticação
- Delete `token.json` e autentique novamente
- Verifique se `client_secret.json` é válido
- Certifique-se de que a YouTube Data API v3 está habilitada no Google Cloud Console

## Notas de Segurança

- **Nunca faça commit de credenciais**: `token.json` e `client_secret.json` estão no `.gitignore`
- **Mantenha as credenciais privadas**: Esses arquivos contêm informações sensíveis do OAuth
- **Use arquivos de exemplo**: Faça commit dos arquivos `*_sample.json` apenas como templates
- **Arquivo de configuração**: `config.json` é commitado pois contém apenas preferências não sensíveis

## Licença

Este projeto é fornecido como está para uso pessoal.

## Suporte

Para problemas ou dúvidas:
1. Verifique a seção de solução de problemas acima
2. Verifique suas configurações do Google Cloud Console
3. Certifique-se de que todas as dependências estão instaladas corretamente

