import flet as ft
import os
import re
import pandas as pd
import concurrent.futures
from datetime import datetime
import time
import gzip
from dotenv import load_dotenv
import requests
from typing import Optional
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf
from pyspark.sql.types import StringType

# Carrega variáveis de ambiente
load_dotenv()

class GithubAPI:
    def __init__(self):
        self.github_username = os.getenv("GITHUB_USERNAME", "")
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.github_api_url = "https://api.github.com"
        self.repos = []
        self.forks = []
        self.session = None
        
    def init_session(self):
        """Inicializa uma sessão persistente para reutilizar conexões HTTP"""
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"token {self.github_token}"})
        return self.session
        
    def has_valid_credentials(self) -> bool:
        return bool(self.github_username and self.github_token)
        
    def get_user_repos(self):
        """Retorna todos os repositórios da conta do usuário autenticado."""
        url = f"{self.github_api_url}/user/repos"
        headers = {"Authorization": f"token {self.github_token}"}
        params = {"per_page": 100, "type": "owner"}
        repos = []

        while url:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                raise Exception(f"Erro ao buscar repositórios: {response.json()}")
            repos.extend(response.json())
            url = response.links.get("next", {}).get("url")

        self.repos = repos
        self.forks = [repo for repo in repos if repo["fork"]]
        return len(self.repos), len(self.forks)
        
    def add_star_and_delete_fork(self, repo_name: str) -> tuple[bool, str]:
        """Adiciona uma estrela e remove um fork"""
        headers = {"Authorization": f"token {self.github_token}"}
        
        # Adiciona estrela
        star_url = f"{self.github_api_url}/user/starred/{repo_name}"
        star_response = requests.put(star_url, headers=headers)
        
        if star_response.status_code != 204:
            return False, f"Erro ao adicionar estrela: {star_response.status_code}"

        # Deleta o fork
        delete_url = f"{self.github_api_url}/repos/{repo_name}"
        delete_response = requests.delete(delete_url, headers=headers)
        
        if delete_response.status_code != 204:
            return False, f"Erro ao deletar fork: {delete_response.status_code}"
            
        return True, "Operação concluída com sucesso"
        
    def user_exists(self, username):
        """Verifica se o usuário existe"""
        url = f"{self.github_api_url}/users/{username}"
        session = self.session or self.init_session()
        response = session.get(url)
        return response.status_code == 200
        
    def repo_exists(self, owner, repo):
        """Verifica se o repositório existe"""
        url = f"{self.github_api_url}/repos/{owner}/{repo}"
        session = self.session or self.init_session()
        response = session.get(url)
        return response.status_code == 200
        
    def get_followers(self, username):
        """Obtém a lista de seguidores de um usuário"""
        url = f"{self.github_api_url}/users/{username}/followers"
        session = self.session or self.init_session()
        response = session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Erro ao obter seguidores: {response.status_code}")
            
    def get_user_details(self, username):
        """Obtém detalhes de um usuário"""
        url = f"{self.github_api_url}/users/{username}"
        session = self.session or self.init_session()
        
        for attempt in range(3):  # Tentativas de retry
            response = session.get(url)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Limitação de taxa
                time.sleep(60)  # Espera por 60 segundos
            else:
                return {}
        return {}
        
    def get_repo_details(self, owner, repo):
        """Obtém detalhes de um repositório"""
        url = f"{self.github_api_url}/repos/{owner}/{repo}"
        session = self.session or self.init_session()
        response = session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Erro ao obter detalhes do repositório: {response.status_code}")
            
    def get_contributors(self, owner, repo):
        """Obtém a lista de contribuidores de um repositório"""
        url = f"{self.github_api_url}/repos/{owner}/{repo}/contributors"
        session = self.session or self.init_session()
        response = session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Erro ao obter contribuidores: {response.status_code}")
            
    def remove_emojis(self, text):
        """Remove emojis e caracteres especiais de um texto"""
        if text:
            return re.sub(r'[^\x00-\x7F]+', '', text)
        return text
        
    def process_follower(self, follower):
        """Processa cada seguidor para extrair informações"""
        session = self.session or self.init_session()
        user_details = self.get_user_details(follower['login'])

        if user_details:
            return {
                'name': self.remove_emojis(user_details.get('name')),
                'company': self.remove_emojis(user_details.get('company')),
                'blog': self.remove_emojis(user_details.get('blog')),
                'email': self.remove_emojis(user_details.get('email')),
                'bio': self.remove_emojis(user_details.get('bio')),
                'public_repos': user_details.get('public_repos'),
                'followers': user_details.get('followers'),
                'following': user_details.get('following'),
                'created_at': user_details.get('created_at')
            }
        return {}

class GithubApp:
    def __init__(self):
        self.api = GithubAPI()
        self.page: Optional[ft.Page] = None
        self.current_tab = "cleaner"

    def main(self, page: ft.Page):
        self.page = page
        page.title = "GitHub Explorer"
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 20
        page.window_width = 1200
        page.window_height = 900
        page.window_resizable = True
        
        # Carrega o logo do GitHub
        page.window_bgcolor = ft.colors.BLACK
        page.bgcolor = ft.colors.BLACK
        
        # Componentes comuns
        self.status_text = ft.Text(
            size=16,
            color=ft.colors.BLUE_400
        )

        self.progress_ring = ft.ProgressRing(
            visible=False,
            width=16,
            height=16
        )
        
        # Componentes da interface de credenciais
        self.credentials_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Configuração de Credenciais", size=20, weight=ft.FontWeight.BOLD),
                        ft.Text("Configure suas credenciais do GitHub para começar", size=14),
                        ft.TextField(
                            label="Nome de usuário GitHub",
                            value=self.api.github_username,
                            width=400,
                            on_change=lambda e: self.update_credentials_status()
                        ),
                        ft.TextField(
                            label="Token GitHub",
                            password=True,
                            can_reveal_password=True,
                            value=self.api.github_token,
                            width=400,
                            on_change=lambda e: self.update_credentials_status()
                        ),
                        ft.Row(
                            controls=[
                                ft.ElevatedButton(
                                    "Salvar Credenciais",
                                    icon=ft.icons.SAVE,
                                    on_click=self.save_credentials
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        ft.Text(
                            "Status: Credenciais não configuradas",
                            color=ft.colors.RED_400,
                            size=14,
                        ),
                    ],
                    spacing=20,
                ),
                padding=20,
            )
        )
        
        # Componentes da interface do Cleaner
        self.fork_list = ft.ListView(
            expand=1,
            spacing=10,
            padding=20,
        )

        self.cleaner_stats_row = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Total de Repositórios", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text("0", size=24),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=10,
                    border=ft.border.all(1, ft.colors.BLUE_400),
                    border_radius=10,
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Forks Encontrados", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text("0", size=24),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=10,
                    border=ft.border.all(1, ft.colors.BLUE_400),
                    border_radius=10,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        )

        self.cleaner_action_bar = ft.Row(
            controls=[
                ft.ElevatedButton(
                    "Buscar Repositórios",
                    icon=ft.icons.SEARCH,
                    on_click=self.scan_repos,
                    disabled=not self.api.has_valid_credentials()
                ),
                self.progress_ring,
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=10,
        )
        
        # Componentes da interface de Análise de Seguidores
        self.followers_input = ft.TextField(
            label="Nome de usuário para analisar",
            width=400,
        )
        
        self.followers_action_bar = ft.Row(
            controls=[
                ft.ElevatedButton(
                    "Analisar Seguidores",
                    icon=ft.icons.PEOPLE,
                    on_click=self.analyze_followers,
                    disabled=not self.api.has_valid_credentials()
                ),
                self.progress_ring,
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=10,
        )
        
        self.followers_result = ft.Text(
            size=16,
        )
        
        # Componentes da interface de Análise de Contribuições
        self.repo_owner_input = ft.TextField(
            label="Proprietário do Repositório",
            width=400,
        )
        
        self.repo_name_input = ft.TextField(
            label="Nome do Repositório",
            width=400,
        )
        
        self.repo_action_bar = ft.Row(
            controls=[
                ft.ElevatedButton(
                    "Analisar Contribuições",
                    icon=ft.icons.CODE,
                    on_click=self.analyze_contributions,
                    disabled=not self.api.has_valid_credentials()
                ),
                self.progress_ring,
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=10,
        )
        
        self.repo_result = ft.Text(
            size=16,
        )
        
        # Criação das abas
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Limpador de Forks",
                    icon=ft.icons.CLEANING_SERVICES,
                    content=ft.Container(
                        content=ft.Column(
                            controls=[
                                self.cleaner_stats_row,
                                self.cleaner_action_bar,
                                ft.Text("Seus Forks", size=20, weight=ft.FontWeight.BOLD),
                                self.fork_list,
                            ],
                            spacing=20,
                        ),
                        padding=20,
                    ),
                ),
                ft.Tab(
                    text="Análise de Seguidores",
                    icon=ft.icons.PEOPLE,
                    content=ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Análise de Seguidores", size=20, weight=ft.FontWeight.BOLD),
                                ft.Text("Obtenha informações detalhadas sobre os seguidores de um usuário", size=14),
                                self.followers_input,
                                self.followers_action_bar,
                                self.followers_result,
                            ],
                            spacing=20,
                        ),
                        padding=20,
                    ),
                ),
                ft.Tab(
                    text="Análise de Contribuições",
                    icon=ft.icons.CODE,
                    content=ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Análise de Contribuições", size=20, weight=ft.FontWeight.BOLD),
                                ft.Text("Obtenha informações sobre contribuidores de um repositório", size=14),
                                self.repo_owner_input,
                                self.repo_name_input,
                                self.repo_action_bar,
                                self.repo_result,
                            ],
                            spacing=20,
                        ),
                        padding=20,
                    ),
                ),
            ],
            on_change=self.tab_changed,
        )
        
        # Layout principal
        page.add(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Image(
                                    src="assets/github-mark/github-mark-white.png",
                                    width=50,
                                    height=50,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text("GitHub Explorer", size=32, weight=ft.FontWeight.BOLD),
                                        ft.Text("Explore, analise e gerencie seus dados do GitHub", size=16),
                                    ],
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            spacing=10,
                        ),
                        ft.Divider(),
                        self.credentials_card,
                        ft.Divider(),
                        self.status_text,
                        tabs,
                    ],
                    spacing=20,
                ),
                padding=20,
            )
        )

    def tab_changed(self, e):
        self.current_tab = ["cleaner", "followers", "contributions"][e.control.selected_index]
        
    def update_credentials_status(self):
        username = self.credentials_card.content.content.controls[2].value
        token = self.credentials_card.content.content.controls[3].value
        status_text = self.credentials_card.content.content.controls[5]
        
        if username and token:
            status_text.value = "Status: Credenciais configuradas"
            status_text.color = ft.colors.GREEN_400
            self.cleaner_action_bar.controls[0].disabled = False
            self.followers_action_bar.controls[0].disabled = False
            self.repo_action_bar.controls[0].disabled = False
        else:
            status_text.value = "Status: Credenciais não configuradas"
            status_text.color = ft.colors.RED_400
            self.cleaner_action_bar.controls[0].disabled = True
            self.followers_action_bar.controls[0].disabled = True
            self.repo_action_bar.controls[0].disabled = True
        
        self.page.update()

    async def save_credentials(self, e):
        username = self.credentials_card.content.content.controls[2].value
        token = self.credentials_card.content.content.controls[3].value
        
        self.api.github_username = username
        self.api.github_token = token
        
        self.update_credentials_status()
        self.status_text.value = "Credenciais salvas com sucesso!"
        self.status_text.color = ft.colors.GREEN_400
        self.page.update()

    async def scan_repos(self, e):
        self.progress_ring.visible = True
        self.status_text.value = "Buscando repositórios..."
        self.page.update()

        try:
            total_repos, total_forks = self.api.get_user_repos()
            
            # Atualiza estatísticas
            self.cleaner_stats_row.controls[0].content.controls[1].value = str(total_repos)
            self.cleaner_stats_row.controls[1].content.controls[1].value = str(total_forks)
            
            self.status_text.value = f"Encontrados {total_repos} repositórios, sendo {total_forks} forks"
            
            # Limpa e atualiza a lista de forks
            self.fork_list.controls.clear()
            for fork in self.api.forks:
                self.fork_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.ListTile(
                                        leading=ft.Icon(ft.icons.SOURCE_FORK),
                                        title=ft.Text(fork["full_name"]),
                                        subtitle=ft.Text(
                                            fork.get("description", "Sem descrição"),
                                            size=12
                                        ),
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.TextButton(
                                                "Abrir no GitHub",
                                                icon=ft.icons.OPEN_IN_NEW,
                                                url=fork["html_url"]
                                            ),
                                            ft.TextButton(
                                                "Remover",
                                                icon=ft.icons.DELETE,
                                                on_click=lambda e, name=fork["full_name"]: self.delete_fork(e, name)
                                            )
                                        ],
                                        alignment=ft.MainAxisAlignment.END,
                                        spacing=10
                                    )
                                ]
                            ),
                            padding=10
                        )
                    )
                )
        except Exception as err:
            self.status_text.value = f"Erro: {str(err)}"
            self.status_text.color = ft.colors.RED_400
        
        self.progress_ring.visible = False
        self.page.update()

    async def delete_fork(self, e, repo_name):
        self.progress_ring.visible = True
        self.status_text.value = f"Processando {repo_name}..."
        self.page.update()

        success, message = self.api.add_star_and_delete_fork(repo_name)
        
        if success:
            self.status_text.value = f"Fork {repo_name} removido com sucesso!"
            self.status_text.color = ft.colors.GREEN_400
            # Atualiza a lista de forks
            await self.scan_repos(None)
        else:
            self.status_text.value = f"Erro ao processar {repo_name}: {message}"
            self.status_text.color = ft.colors.RED_400

        self.progress_ring.visible = False
        self.page.update()
        
    async def analyze_followers(self, e):
        username = self.followers_input.value
        if not username:
            self.status_text.value = "Por favor, informe um nome de usuário para analisar."
            self.status_text.color = ft.colors.RED_400
            self.page.update()
            return
            
        self.progress_ring.visible = True
        self.status_text.value = f"Analisando seguidores de {username}..."
        self.followers_result.value = "Processando... Isso pode levar alguns minutos."
        self.page.update()
        
        try:
            # Inicializa a sessão se necessário
            if not self.api.session:
                self.api.init_session()
                
            # Verifica se o usuário existe
            if not self.api.user_exists(username):
                self.status_text.value = f"Erro: Usuário '{username}' não encontrado."
                self.status_text.color = ft.colors.RED_400
                self.followers_result.value = ""
                self.progress_ring.visible = False
                self.page.update()
                return
                
            # Obtém a lista de seguidores
            followers = self.api.get_followers(username)
            
            if not followers:
                self.status_text.value = f"Usuário {username} não possui seguidores."
                self.followers_result.value = ""
                self.progress_ring.visible = False
                self.page.update()
                return
                
            # Processa os seguidores em paralelo
            followers_details = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(self.api.process_follower, follower) for follower in followers]
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        followers_details.append(result)
                        
            if not followers_details:
                self.status_text.value = "Nenhum detalhe de seguidor encontrado."
                self.followers_result.value = ""
                self.progress_ring.visible = False
                self.page.update()
                return
                
            # Cria um DataFrame com os dados
            spark = SparkSession.builder.appName('GitHub Followers').getOrCreate()
            df = spark.createDataFrame(pd.DataFrame(followers_details))
            
            # Limpa campo 'company'
            remove_at = udf(lambda x: x.replace('@', '') if x else x, StringType())
            df = df.withColumn('company', remove_at(col('company')))
            
            # Transforma campo 'created_at' para formato dia/mês/ano
            format_date = udf(lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ').strftime('%d/%m/%Y'), StringType())
            df = df.withColumn('created_at', format_date(col('created_at')))
            
            # Exporta para CSV com compressão gzip
            output_file = 'github_followers.csv.gz'
            df.toPandas().to_csv(output_file, index=False, compression='gzip')
            
            self.status_text.value = f"Análise de seguidores de {username} concluída com sucesso!"
            self.status_text.color = ft.colors.GREEN_400
            self.followers_result.value = f"Dados exportados para '{output_file}'\n\nTotal de seguidores analisados: {len(followers_details)}"
            
        except Exception as err:
            self.status_text.value = f"Erro na análise de seguidores: {str(err)}"
            self.status_text.color = ft.colors.RED_400
            self.followers_result.value = ""
            
        self.progress_ring.visible = False
        self.page.update()
        
    async def analyze_contributions(self, e):
        owner = self.repo_owner_input.value
        repo = self.repo_name_input.value
        
        if not owner or not repo:
            self.status_text.value = "Por favor, informe o proprietário e o nome do repositório."
            self.status_text.color = ft.colors.RED_400
            self.page.update()
            return
            
        self.progress_ring.visible = True
        self.status_text.value = f"Analisando contribuições do repositório {owner}/{repo}..."
        self.repo_result.value = "Processando..."
        self.page.update()
        
        try:
            # Inicializa a sessão se necessário
            if not self.api.session:
                self.api.init_session()
                
            # Verifica se o usuário e o repositório existem
            if not self.api.user_exists(owner):
                self.status_text.value = f"Erro: Usuário '{owner}' não encontrado."
                self.status_text.color = ft.colors.RED_400
                self.repo_result.value = ""
                self.progress_ring.visible = False
                self.page.update()
                return
                
            if not self.api.repo_exists(owner, repo):
                self.status_text.value = f"Erro: Repositório '{repo}' não encontrado para o usuário '{owner}'."
                self.status_text.color = ft.colors.RED_400
                self.repo_result.value = ""
                self.progress_ring.visible = False
                self.page.update()
                return
                
            # Obtém detalhes do repositório
            repo_details = self.api.get_repo_details(owner, repo)
            
            if not repo_details:
                self.status_text.value = "Erro ao obter detalhes do repositório."
                self.repo_result.value = ""
                self.progress_ring.visible = False
                self.page.update()
                return
                
            # Obtém a lista de contribuidores
            contributors = self.api.get_contributors(owner, repo)
            
            if not contributors:
                self.status_text.value = f"Repositório {owner}/{repo} não possui contribuidores."
                self.repo_result.value = ""
                self.progress_ring.visible = False
                self.page.update()
                return
                
            # Lista para armazenar os detalhes dos contribuidores e repositório
            contributors_details = []
            
            for contributor in contributors:
                contributors_details.append({
                    'contributor_login': contributor['login'],
                    'contributions': contributor['contributions'],
                    'repo_name': repo_details['name'],
                    'repo_description': repo_details.get('description', ''),
                    'repo_stars': repo_details['stargazers_count'],
                    'repo_forks': repo_details['forks_count'],
                    'repo_open_issues': repo_details['open_issues_count'],
                    'repo_created_at': datetime.strptime(repo_details['created_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%d/%m/%Y')
                })
                
            # Cria um DataFrame com os dados
            spark = SparkSession.builder.appName('GitHub Repo Contributions').getOrCreate()
            df = spark.createDataFrame(pd.DataFrame(contributors_details))
            
            # Exporta para CSV com compressão gzip
            output_file = 'github_repo_contributions.csv.gz'
            df.toPandas().to_csv(output_file, index=False, compression='gzip')
            
            self.status_text.value = f"Análise de contribuições do repositório {owner}/{repo} concluída com sucesso!"
            self.status_text.color = ft.colors.GREEN_400
            self.repo_result.value = f"Dados exportados para '{output_file}'\n\nTotal de contribuidores: {len(contributors_details)}\nEstrelas: {repo_details['stargazers_count']}\nForks: {repo_details['forks_count']}"
            
        except Exception as err:
            self.status_text.value = f"Erro na análise de contribuições: {str(err)}"
            self.status_text.color = ft.colors.RED_400
            self.repo_result.value = ""
            
        self.progress_ring.visible = False
        self.page.update()

if __name__ == "__main__":
    app = GithubApp()
    ft.app(target=app.main) 