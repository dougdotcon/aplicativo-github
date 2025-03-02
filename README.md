# GitHub Explorer

Uma aplicação completa para explorar, analisar e gerenciar seus dados do GitHub.

![GitHub Explorer](assets/github-mark/github-mark.png)

## Screenshot da Aplicação

![Tela da Aplicação](screenshots/tela.png)

## Funcionalidades

### 1. Limpador de Forks
- Visualize todos os seus repositórios fork
- Adicione uma estrela automaticamente antes de remover um fork
- Gerencie seus forks de forma eficiente e organizada

### 2. Análise de Seguidores
- Obtenha informações detalhadas sobre os seguidores de qualquer usuário
- Extraia dados como nome, empresa, blog, email, biografia e estatísticas
- Exporte os dados para CSV com compressão gzip

### 3. Análise de Contribuições
- Analise as contribuições em qualquer repositório público
- Obtenha informações sobre contribuidores, número de contribuições e detalhes do repositório
- Exporte os dados para CSV com compressão gzip

## Funcionalidades Futuras

Abaixo está uma checklist de funcionalidades que planejamos implementar nas próximas versões:

### Visualização de Estatísticas e Gráficos
- [ ] Gráfico de atividade de commits ao longo do tempo
- [ ] Mapa de calor de contribuições
- [ ] Gráfico de distribuição de linguagens
- [ ] Visualização da rede de seguidores

### Gerenciador de Issues e Pull Requests
- [ ] Listagem e filtragem de issues
- [ ] Interface para criação de novas issues
- [ ] Visualização e revisão de pull requests
- [ ] Sistema de notificações para issues e PRs

### Explorador de Tendências
- [ ] Listagem de repositórios em alta por linguagem e período
- [ ] Desenvolvedores em destaque
- [ ] Recomendações de projetos baseadas em interesses

### Backup de Repositórios
- [ ] Sistema de backup agendado
- [ ] Exportação seletiva de repositórios
- [ ] Histórico e restauração de backups

### Análise de Código
- [ ] Detecção de vulnerabilidades em dependências
- [ ] Cálculo de métricas de qualidade de código
- [ ] Sugestões para melhoria de código

### Gerenciador de Estrelas
- [ ] Categorização de repositórios favoritados
- [ ] Sistema de tags e anotações
- [ ] Busca avançada em repositórios com estrela
- [ ] Exportação e importação de favoritos

### Monitor de Eventos
- [ ] Feed de atividades em tempo real
- [ ] Alertas personalizados para eventos específicos
- [ ] Histórico de eventos

### Comparador de Repositórios
- [ ] Comparação de métricas entre repositórios
- [ ] Gráficos de crescimento comparativo
- [ ] Análise comparativa de contribuidores

### Gerenciador de Perfil
- [ ] Análise e sugestões para otimização de perfil
- [ ] Assistente para criação de README de perfil
- [ ] Estatísticas avançadas de contribuições

### Integração com GitHub Actions
- [ ] Interface visual para criação de workflows
- [ ] Monitoramento de execuções de workflows
- [ ] Biblioteca de templates para diferentes projetos

## Requisitos

- Python 3.7 ou superior
- Token de acesso pessoal do GitHub com permissões para gerenciar repositórios
- Dependências listadas em `requirements.txt`

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/github-explorer.git
cd github-explorer
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure suas credenciais:
- Renomeie o arquivo `.env.example` para `.env`
- Edite o arquivo `.env` e adicione suas credenciais:
  ```
  GITHUB_USERNAME=seu_usuario_github
  GITHUB_TOKEN=seu_token_github
  ```

## Uso

Execute o aplicativo com interface gráfica:
```bash
python app_gui.py
```

### Limpador de Forks

1. Configure suas credenciais do GitHub
2. Acesse a aba "Limpador de Forks"
3. Clique em "Buscar Repositórios" para listar seus forks
4. Para cada fork, você pode:
   - Abrir no GitHub
   - Remover (adiciona uma estrela automaticamente antes de remover)

### Análise de Seguidores

1. Configure suas credenciais do GitHub
2. Acesse a aba "Análise de Seguidores"
3. Digite o nome de usuário que deseja analisar
4. Clique em "Analisar Seguidores"
5. Os dados serão processados e exportados para `github_followers.csv.gz`

### Análise de Contribuições

1. Configure suas credenciais do GitHub
2. Acesse a aba "Análise de Contribuições"
3. Digite o proprietário e o nome do repositório
4. Clique em "Analisar Contribuições"
5. Os dados serão processados e exportados para `github_repo_contributions.csv.gz`

## Detalhes Técnicos

### Processamento de Dados

- **Paralelização**: Utiliza `ThreadPoolExecutor` para acelerar as requisições à API do GitHub
- **Persistência de Sessão**: Reutiliza conexões HTTP para melhor desempenho
- **Tratamento de Erros**: Implementa retry para lidar com limitações de taxa da API
- **Limpeza de Dados**: Remove emojis e caracteres especiais dos campos de texto
- **Exportação Eficiente**: Utiliza compressão gzip para reduzir o tamanho dos arquivos exportados

### Interface Gráfica

- Interface moderna e intuitiva construída com Flet
- Feedback visual do progresso das operações
- Organização em abas para fácil navegação entre funcionalidades
- Design responsivo e adaptável

## Segurança

- Nunca compartilhe seu token do GitHub
- Mantenha o arquivo `.env` seguro e não o inclua em commits
- O token do GitHub deve ter apenas as permissões necessárias

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para:
- Reportar bugs
- Sugerir novas funcionalidades
- Enviar pull requests

## Licença

Este projeto está licenciado sob a MIT License - veja o arquivo LICENSE para detalhes.

## Agradecimentos

- [GitHub](https://github.com) por fornecer a API
- [Flet](https://flet.dev) por facilitar a criação de interfaces gráficas com Python
- [PySpark](https://spark.apache.org/docs/latest/api/python/index.html) por fornecer ferramentas poderosas para processamento de dados
