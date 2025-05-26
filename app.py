from shiny import App, ui, render, reactive
import pandas as pd
import matplotlib.pyplot as plt
import datetime

# Dados iniciais
produtos_mock = [
    {"Produto": "Mouse Gamer", "Quantidade": 25},
    {"Produto": "Teclado Mecânico", "Quantidade": 15},
    {"Produto": "Monitor 27''", "Quantidade": 10},
    {"Produto": "Notebook i5", "Quantidade": 8},
    {"Produto": "Headset", "Quantidade": 30},
]

dados = reactive.Value(pd.DataFrame(produtos_mock))
historico = reactive.Value([])

app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.link(
            rel="stylesheet",
            href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
        ),
        ui.tags.script(
            src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"
        ),
    ),
    ui.h2("🛍️ Mini CMS de Produtos - Estilo Magento"),
    ui.navset_tab(
        ui.nav_panel(
            "📦 Produtos",
            ui.row(
                ui.column(6, ui.output_data_frame("tabela_dados")),
                ui.column(6, ui.output_plot("grafico_estoque"))
            ),
            ui.output_ui("alerta_estoque"),
        ),
        ui.nav_panel(
            "➕ Adicionar / Remover",
            ui.card(
                ui.h4("Adicionar Produto"),
                ui.input_text("nome", "Nome do Produto:"),
                ui.input_numeric("quantidade", "Quantidade:", value=1),
                ui.input_action_button("adicionar", "Adicionar", class_="btn btn-success")
            ),
            ui.card(
                ui.h4("Remover Produto"),
                ui.input_text("del_nome", "Nome do Produto:"),
                ui.input_action_button("remover", "Remover", class_="btn btn-danger")
            ),
            ui.card(
                ui.h4("Adicionar em Lote"),
                ui.input_action_button("adicionar_lote", "Adicionar Lote de Produtos", class_="btn btn-secondary")
            )
        ),
        ui.nav_panel(
            "🛒 Simular Compra",
            ui.output_ui("select_produto_compra"),
            ui.input_numeric("quantidade_compra", "Quantidade a Comprar:", value=1),
            ui.input_action_button("comprar", "Comprar", class_="btn btn-warning")
        ),
        ui.nav_panel(
            "🕓 Histórico",
            ui.output_data_frame("tabela_historico")
        )
    )
)

def server(input, output, session):
    @output
    @render.data_frame
    def tabela_dados():
        return render.DataTable(dados(), width="100%", editable=True)

    @output
    @render.plot
    def grafico_estoque():
        df = dados()
        fig, ax = plt.subplots()
        ax.bar(df["Produto"], df["Quantidade"], color="skyblue")
        ax.set_title("Estoque Atual")
        ax.set_ylabel("Quantidade")
        plt.xticks(rotation=45)
        return fig

    @output
    @render.ui
    def alerta_estoque():
        df = dados()
        baixos = df[df["Quantidade"] < 5]
        if not baixos.empty:
            return ui.tags.div(
                {"class": "alert alert-warning"},
                "⚠️ Produtos com estoque baixo: ", ", ".join(baixos["Produto"])
            )

    @output
    @render.data_frame
    def tabela_historico():
        hist = historico()
        if hist:
            df_hist = pd.DataFrame(hist)
            return render.DataTable(df_hist)
        return render.DataTable(pd.DataFrame(columns=["Data", "Ação", "Produto", "Quantidade"]))

    @output
    @render.ui
    def select_produto_compra():
        produtos = dados()["Produto"].tolist()
        return ui.input_select("produto_compra", "Escolha o Produto:", produtos)

    @reactive.effect
    @reactive.event(input.adicionar)
    def adicionar_produto():
        df = dados().copy()
        nome = input.nome()
        qtd = input.quantidade()
        if nome:
            if nome in df["Produto"].values:
                df.loc[df["Produto"] == nome, "Quantidade"] += qtd
            else:
                df.loc[len(df)] = [nome, qtd]
            dados.set(df)
            historico.set(historico() + [{
                "Data": datetime.datetime.now(),
                "Ação": "Adicionado",
                "Produto": nome,
                "Quantidade": qtd
            }])

    @reactive.effect
    @reactive.event(input.remover)
    def remover_produto():
        df = dados()
        nome = input.del_nome()
        if nome in df["Produto"].values:
            qtd = df.loc[df["Produto"] == nome, "Quantidade"].values[0]
            df = df[df["Produto"] != nome]
            dados.set(df.reset_index(drop=True))
            historico.set(historico() + [{
                "Data": datetime.datetime.now(),
                "Ação": "Removido",
                "Produto": nome,
                "Quantidade": qtd
            }])

    @reactive.effect
    @reactive.event(input.comprar)
    def simular_compra():
        nome = input["produto_compra"]()
        if not nome:
            return  # Nenhum produto selecionado ainda

        df = dados()
        qtd = input.quantidade_compra()
        if nome in df["Produto"].values:
            atual = df.loc[df["Produto"] == nome, "Quantidade"].values[0]
            nova_qtd = max(0, atual - qtd)
            df.loc[df["Produto"] == nome, "Quantidade"] = nova_qtd
            dados.set(df)
            historico.set(historico() + [{
                "Data": datetime.datetime.now(),
                "Ação": "Compra",
                "Produto": nome,
                "Quantidade": qtd
            }])

    @reactive.effect
    @reactive.event(input.adicionar_lote)
    def adicionar_lote():
        df = dados().copy()
        novos_produtos = [
            {"Produto": "Webcam Full HD", "Quantidade": 12},
            {"Produto": "Cadeira Gamer", "Quantidade": 7},
            {"Produto": "Hub USB-C", "Quantidade": 20},
        ]
        for item in novos_produtos:
            nome = item["Produto"]
            qtd = item["Quantidade"]
            if nome in df["Produto"].values:
                df.loc[df["Produto"] == nome, "Quantidade"] += qtd
            else:
                df.loc[len(df)] = [nome, qtd]
            historico.set(historico() + [{
                "Data": datetime.datetime.now(),
                "Ação": "Adicionado em Lote",
                "Produto": nome,
                "Quantidade": qtd
            }])
        dados.set(df)

app = App(app_ui, server)
