
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import dash_table
import plotly.graph_objects as go

# Initialisation de l'application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Chargement des données
df = pd.read_csv("C:/Users/arthu/Downloads/data.csv")
df['Prix_tot'] = df['Quantity'] * df['Avg_Price'] * (1 - (df['Discount_pct'] / 100))
df['Transaction_Date'] = pd.to_datetime(df['Transaction_Date'])  # Conversion en datetime
df['Week'] = df['Transaction_Date'].dt.to_period('W').apply(lambda r: r.start_time)  # Ajout de la colonne semaine

# Définition des options de villes
city_options = [
    {'label': 'Toutes les villes', 'value': 'all'},
    {'label': 'Chicago', 'value': 'Chicago'},
    {'label': 'California', 'value': 'California'},
    {'label': 'New York', 'value': 'New York'},
    {'label': 'New Jersey', 'value': 'New Jersey'},
    {'label': 'Washington DC', 'value': 'Washington DC'}
]

# Variables pour les noms et abréviations des mois
month_abbr = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
              7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
month_name = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
              7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}

# Fonction pour calculer le chiffre d'affaires
def calculer_chiffre_affaire(data):
    return data['Prix_tot'].sum()

# Fonction pour calculer la fréquence des meilleures ventes
def frequence_meilleure_vente(data, top=10, ascending=False):
    resultat = pd.crosstab(
        [data['Gender'], data['Product_Category']],
        'Total vente',
        values=data['Prix_tot'],
        aggfunc=lambda x: len(x)
    ).reset_index().groupby(
        ['Gender'], as_index=False
    ).apply(
        lambda x: x.sort_values('Total vente', ascending=ascending).iloc[:top]
    ).reset_index(drop=True)
    return resultat

def indicateur_du_mois(data, current_month=12, freq=True, abbr=False):
    previous_month = current_month - 1 if current_month > 1 else 12
    if freq:
        resultat = data['Month'][(data['Month'] == current_month) | (data['Month'] == previous_month)].value_counts()
        resultat = resultat.sort_index()
        resultat.index = [(month_abbr[i] if abbr else month_name[i]) for i in resultat.index]
        return resultat
    else:
        resultat = data[(data['Month'] == current_month) | (data['Month'] == previous_month)].groupby('Month').apply(calculer_chiffre_affaire)
        resultat.index = [(month_abbr[i] if abbr else month_name[i]) for i in resultat.index]
        return resultat

# Layout de l'application
app.layout = dbc.Container(
    fluid=True,
    children=[
        dbc.Row([
            dbc.Col(html.H3("ECAP STORE", className="text-left", style={"fontSize": "30px", "color": "black", "fontWeight": "bold"}), md=6,
                style={"height": "7vh", "display": "flex", "alignItems": "center", "justifyContent": "flex-start", "backgroundColor": "#ADD8E6", "paddingLeft": "15px"}),
            dbc.Col(dcc.Dropdown(id="zones", options=city_options, value="all", placeholder="Choisissez des zones",
                style={"fontSize": "16px", "height": "40px", "width": "80%", "borderRadius": "50px"}), md=6,
                style={"height": "7vh", "display": "flex", "alignItems": "center", "justifyContent": "center", "backgroundColor": "#ADD8E6"}),
        ], style={"marginBottom": "10px"}),

        dbc.Row([
            dbc.Col([
            # Indicateurs centrés
            dbc.Row([
                dbc.Col(dcc.Graph(id='CA_mois'), md=5, style={"min-height": "100px", "textAlign": "center"}, className="p-2"),
                dbc.Col(dcc.Graph(id='Ventes_mois'), md=5, style={"min-height": "100px", "textAlign": "center"}, className="p-2"),
            ], justify="center"),

            # Graphique des meilleures ventes
            dbc.Row([
                dbc.Col(dcc.Graph(id='top_sales'), md=12, style={"min-height": "400px"}, className="p-3"),
            ]),
        ], md=5),

            dbc.Col([
                dbc.Row([
                    dbc.Col(dcc.Graph(id='revenue_trend'), style={"min-height": "300px"})  # Graphique de chiffre d'affaires par semaine
                ], style={"display": "flex", "alignItems": "flex-start"}),
                dbc.Row([
                    dbc.Col([
                        html.H5("Table des 100 dernières ventes"),
                        dash_table.DataTable(
                            id='sales_table',
                            columns=[
                                {'name': 'Date', 'id': 'Transaction_Date'},
                                {'name': 'Genre', 'id': 'Gender'},
                                {'name': 'Location', 'id': 'Location'},
                                {'name': 'Catégorie de produit', 'id': 'Product_Category'},
                                {'name': 'Quantité', 'id': 'Quantity'},
                                {'name': 'Prix moyen', 'id': 'Avg_Price'},
                                {'name': 'Remise', 'id': 'Discount_pct'},
                            ],
                            page_size=10,
                            style_table={'height': '100%', 'overflowY': 'auto'},
                            style_cell={'textAlign': 'left'},
                            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
                        ),
                    ])
                ]),
            ], md=6),
        ], justify="center"),
    ]
)

# Callback pour mettre à jour les graphiques et le tableau
@app.callback(
    [Output('top_sales', 'figure'),
     Output('revenue_trend', 'figure'),  # Chiffre d'affaires par semaine
     Output('sales_table', 'data'),
     Output('CA_mois', 'figure'),
     Output('Ventes_mois', 'figure')],
    [Input('zones', 'value')]
)
def update_graphs(selected_zone):
    # Filtrer les données en fonction de la ville sélectionnée
    filtered_df = df if selected_zone == "all" else df[df['Location'] == selected_zone]

    df_plot = indicateur_du_mois(filtered_df, freq=False)
    CA_mois = go.Figure(
        go.Indicator(
            mode="number+delta",
            value=df_plot[1],
            delta={'reference': df_plot[0]},
            domain={'row': 0, 'column': 1},
            title=f"{df_plot.index[1]}",
        )
    ).update_layout(
        width=200, height=200, 
        margin=dict(l=0, r=10, t=10, b=0)
    )

    df_plot = indicateur_du_mois(filtered_df, freq=True, abbr=True)
    Ventes_mois = go.Figure(
        go.Indicator(
            mode="number+delta",
            value=df_plot[1],
            delta={'reference': df_plot[0]},
            domain={'row': 0, 'column': 1},
            title=f"{df_plot.index[1]}",
        )
    ).update_layout(
    width=200, height=200,
    margin=dict(l=0, r=10, t=10, b=0)
)

    # Calcul de la tendance du chiffre d'affaires par semaine
    revenue_trend = filtered_df.groupby('Week', as_index=False)['Prix_tot'].sum()
    revenue_trend_fig = px.line(
        revenue_trend, x='Week', y='Prix_tot', title="Évolution du chiffre d'affaires (par semaine)",
        labels={"Week": "Semaine", "Prix_tot": "Chiffre d'affaires"}
    ).update_layout( 
        width=900, height=400,
        margin=dict(t=60, b=0),
        
    )

    # Graphique des meilleures ventes
    df_plot = frequence_meilleure_vente(filtered_df, ascending=True)
    top_sales = px.bar(df_plot, x='Total vente', y='Product_Category', color='Gender', barmode='group', title="Top 10 des ventes",
                       labels={"x": "Fréquence", "y": "Catégorie", "color": "Sexe"}).update_layout(
        margin = dict(t=60)
    )

    return top_sales, revenue_trend_fig, filtered_df.to_dict('records'), CA_mois, Ventes_mois

# Lancement de l'application
if __name__ == '__main__':
    app.run_server(debug=True)
