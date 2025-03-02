import flet as ft
import os
from dotenv import load_dotenv
import requests
from typing import Optional

# Carrega variáveis de ambiente
load_dotenv()

class GithubCleaner:
    def __init__(self):
        self.github_username = os.getenv("GITHUB_USERNAME", "")
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.github_api_url = "https://api.github.com"
        self.repos = []
        self.forks = []

    def get_user_repos(self):
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

    def has_valid_credentials(self) -> bool:
        return bool(self.github_username and self.github_token)

class GithubCleanerApp:
    def __init__(self):
        self.cleaner = GithubCleaner()
        self.page: Optional[ft.Page] = None

    def main(self, page: ft.Page):
        self.page = page
        page.title = "GitHub Cleaner"
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 20
        page.window_width = 1000
        page.window_height = 800
        page.window_resizable = True
        page.update()

        # Componentes da interface
        self.credentials_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Configuração de Credenciais", size=20, weight=ft.FontWeight.BOLD),
                        ft.Text("Configure suas credenciais do GitHub para começar", size=14),
                        ft.TextField(
                            label="Nome de usuário GitHub",
                            value=self.cleaner.github_username,
                            width=400,
                            on_change=lambda e: self.update_credentials_status()
                        ),
                        ft.TextField(
                            label="Token GitHub",
                            password=True,
                            can_reveal_password=True,
                            value=self.cleaner.github_token,
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

        self.status_text = ft.Text(
            size=16,
            color=ft.colors.BLUE_400
        )

        self.progress_ring = ft.ProgressRing(
            visible=False,
            width=16,
            height=16
        )

        # Lista de forks
        self.fork_list = ft.ListView(
            expand=1,
            spacing=10,
            padding=20,
        )

        # Estatísticas
        self.stats_row = ft.Row(
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

        # Barra de ações
        self.action_bar = ft.Row(
            controls=[
                ft.ElevatedButton(
                    "Buscar Repositórios",
                    icon=ft.icons.SEARCH,
                    on_click=self.scan_repos,
                    disabled=not self.cleaner.has_valid_credentials()
                ),
                self.progress_ring,
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=10,
        )

        # Layout principal
        page.add(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("GitHub Cleaner", size=32, weight=ft.FontWeight.BOLD),
                        ft.Text("Gerencie seus forks do GitHub com facilidade", size=16),
                        ft.Divider(),
                        self.credentials_card,
                        ft.Divider(),
                        self.stats_row,
                        self.action_bar,
                        self.status_text,
                        ft.Text("Seus Forks", size=20, weight=ft.FontWeight.BOLD),
                        self.fork_list,
                    ],
                    spacing=20,
                ),
                padding=20,
            )
        )

    def update_credentials_status(self):
        username = self.credentials_card.content.content.controls[2].value
        token = self.credentials_card.content.content.controls[3].value
        status_text = self.credentials_card.content.content.controls[5]
        
        if username and token:
            status_text.value = "Status: Credenciais configuradas"
            status_text.color = ft.colors.GREEN_400
            self.action_bar.controls[0].disabled = False
        else:
            status_text.value = "Status: Credenciais não configuradas"
            status_text.color = ft.colors.RED_400
            self.action_bar.controls[0].disabled = True
        
        self.page.update()

    async def save_credentials(self, e):
        username = self.credentials_card.content.content.controls[2].value
        token = self.credentials_card.content.content.controls[3].value
        
        self.cleaner.github_username = username
        self.cleaner.github_token = token
        
        self.update_credentials_status()
        self.status_text.value = "Credenciais salvas com sucesso!"
        self.status_text.color = ft.colors.GREEN_400
        self.page.update()

    async def scan_repos(self, e):
        self.progress_ring.visible = True
        self.status_text.value = "Buscando repositórios..."
        self.page.update()

        try:
            total_repos, total_forks = self.cleaner.get_user_repos()
            
            # Atualiza estatísticas
            self.stats_row.controls[0].content.controls[1].value = str(total_repos)
            self.stats_row.controls[1].content.controls[1].value = str(total_forks)
            
            self.status_text.value = f"Encontrados {total_repos} repositórios, sendo {total_forks} forks"
            
            # Limpa e atualiza a lista de forks
            self.fork_list.controls.clear()
            for fork in self.cleaner.forks:
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

        success, message = self.cleaner.add_star_and_delete_fork(repo_name)
        
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

if __name__ == "__main__":
    app = GithubCleanerApp()
    ft.app(target=app.main) 