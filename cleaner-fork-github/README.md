# GitHub Cleaner

Uma ferramenta para gerenciar e limpar seus repositórios fork do GitHub de forma eficiente.

## Funcionalidades

- Interface gráfica moderna e intuitiva
- Visualização de todos os seus repositórios fork
- Adiciona uma estrela automaticamente antes de remover um fork
- Gerenciamento seguro de credenciais
- Feedback visual do progresso das operações

## Requisitos

- Python 3.7 ou superior
- Token de acesso pessoal do GitHub com permissões para gerenciar repositórios

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/cleaner-fork-github.git
cd cleaner-fork-github
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

### Interface Gráfica (Recomendado)

Execute o aplicativo com interface gráfica:
```bash
python app_gui.py
```

A interface gráfica permite:
- Configurar suas credenciais do GitHub
- Visualizar todos os seus forks
- Remover forks individualmente
- Acompanhar o progresso das operações

### Linha de Comando

Se preferir, você ainda pode usar a versão em linha de comando:
```bash
python app.py
```

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
