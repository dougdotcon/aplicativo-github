import requests

# Configurações
GITHUB_USERNAME = "dougdotcon"  # Insira seu nome de usuário do GitHub
GITHUB_TOKEN = "fal"  # Insira seu token de acesso pessoal (PAT)
GITHUB_API_URL = "https://api.github.com"

def get_user_repos():
    """
    Retorna todos os repositórios da conta do usuário autenticado.
    """
    url = f"{GITHUB_API_URL}/user/repos"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    params = {"per_page": 100, "type": "owner"}  # Obtém repositórios do usuário
    repos = []

    while url:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Erro ao buscar repositórios: {response.json()}")
        repos.extend(response.json())
        url = response.links.get("next", {}).get("url")  # Paginação

    return repos

def add_star_to_repo(repo_name):
    """
    Adiciona uma estrela a um repositório.
    """
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = f"{GITHUB_API_URL}/user/starred/{repo_name}"
    response = requests.put(url, headers=headers)
    if response.status_code == 204:
        print(f"Estrela adicionada ao repositório {repo_name}.")
    else:
        print(f"Erro ao adicionar estrela ao {repo_name}: {response.json()}")

def delete_fork_repos(repos):
    """
    Remove todos os repositórios que são forks, adicionando uma estrela antes.
    """
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    for repo in repos:
        if repo["fork"]:  # Verifica se o repositório é um fork
            repo_name = repo["full_name"]
            add_star_to_repo(repo_name)  # Adiciona uma estrela
            delete_url = f"{GITHUB_API_URL}/repos/{repo_name}"
            response = requests.delete(delete_url, headers=headers)
            if response.status_code == 204:
                print(f"Repositório {repo_name} excluído com sucesso.")
            else:
                print(f"Erro ao excluir {repo_name}: {response.json()}")

def main():
    print("Buscando repositórios...")
    repos = get_user_repos()
    print(f"Encontrados {len(repos)} repositórios.")

    forks = [repo for repo in repos if repo["fork"]]
    print(f"Encontrados {len(forks)} forks para processar.")

    if not forks:
        print("Nenhum fork encontrado. Nada a excluir.")
        return

    confirm = input(f"Tem certeza de que deseja adicionar uma estrela e excluir {len(forks)} forks? (sim/não): ")
    if confirm.lower() == "sim":
        delete_fork_repos(forks)
        print("Processo concluído.")
    else:
        print("Operação cancelada.")

if __name__ == "__main__":
    main()
