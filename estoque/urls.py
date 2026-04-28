"""
URLs completas do app estoque — Sistema de Gestão de Estoque
"""
from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views
from .views import TrocarSenhaView

from django.conf import settings
from django.conf.urls.static import static

app_name = 'estoque'

urlpatterns = [
    # ── Raiz ──────────────────────────────────────────────────────────────────
    path('', views.redirecionar_raiz, name='raiz'),

    # ── Autenticação ──────────────────────────────────────────────────────────
    path('login/',       views.view_login,  name='login'),
    path('logout/',      views.view_logout, name='logout'),
    path('trocar-senha/', login_required(TrocarSenhaView.as_view()), name='trocar_senha'),

    # ── Dashboard ─────────────────────────────────────────────────────────────
    path('dashboard/', views.dashboard, name='dashboard'),

    # ── Almoxarifados ─────────────────────────────────────────────────────────
    path('almoxarifados/',               views.almoxarifado_lista,        name='almoxarifado_lista'),
    path('almoxarifados/novo/',          views.almoxarifado_criar,         name='almoxarifado_criar'),
    path('almoxarifados/<int:pk>/editar/', views.almoxarifado_editar,      name='almoxarifado_editar'),
    path('almoxarifados/<int:pk>/toggle/', views.almoxarifado_toggle_ativo, name='almoxarifado_toggle'),

    # ── Itens ─────────────────────────────────────────────────────────────────
    path('itens/',                  views.item_lista,    name='item_lista'),
    path('itens/novo/',             views.item_criar,    name='item_criar'),
    path('itens/<int:pk>/',         views.item_detalhe,  name='item_detalhe'),
    path('itens/<int:pk>/editar/',  views.item_editar,   name='item_editar'),
    path('itens/<int:pk>/qrcode/',  views.item_qrcode,   name='item_qrcode'),
    path('itens/<int:pk>/etiqueta/',views.item_etiqueta, name='item_etiqueta'),

    # ── Movimentações ─────────────────────────────────────────────────────────
    path('movimentacoes/',              views.movimentacao_lista,          name='movimentacao_lista'),
    path('movimentacoes/nova/',         views.movimentacao_criar,          name='movimentacao_criar'),
    path('movimentacoes/exportar/csv/', views.movimentacao_exportar_csv,   name='movimentacao_exportar_csv'),
    path('movimentacoes/exportar/pdf/', views.movimentacao_exportar_pdf,   name='movimentacao_exportar_pdf'),

    # ── Categorias ────────────────────────────────────────────────────────────
    path('categorias/',                  views.categoria_lista,   name='categoria_lista'),
    path('categorias/nova/',             views.categoria_criar,   name='categoria_criar'),
    path('categorias/<int:pk>/editar/',  views.categoria_editar,  name='categoria_editar'),
    path('categorias/<int:pk>/excluir/', views.categoria_excluir, name='categoria_excluir'),

    # ── Fornecedores ──────────────────────────────────────────────────────────
    path('fornecedores/',                  views.fornecedor_lista,   name='fornecedor_lista'),
    path('fornecedores/novo/',             views.fornecedor_criar,   name='fornecedor_criar'),
    path('fornecedores/<int:pk>/editar/',  views.fornecedor_editar,  name='fornecedor_editar'),
    path('fornecedores/<int:pk>/excluir/', views.fornecedor_excluir, name='fornecedor_excluir'),

    # ── Usuários (apenas admin) ───────────────────────────────────────────────
    path('usuarios/',                  views.usuario_lista,        name='usuario_lista'),
    path('usuarios/novo/',             views.usuario_criar,         name='usuario_criar'),
    path('usuarios/<int:pk>/editar/',  views.usuario_editar,        name='usuario_editar'),
    path('usuarios/<int:pk>/toggle/',  views.usuario_toggle_ativo,  name='usuario_toggle'),

    # ── Relatórios ────────────────────────────────────────────────────────────
    path('relatorios/', views.relatorio_estoque, name='relatorio_estoque'),

    # ── Busca Global ──────────────────────────────────────────────────────────
    path('busca/', views.busca_global, name='busca_global'),

    path('limpar-flag-item/', views.limpar_flag_item, name='limpar_flag_item'),
]
