"""
Configuração do Django Admin para o sistema Sistema de Gestão de Estoque.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Categoria, Fornecedor, Almoxarifado, Item, Movimentacao


# ─── Usuário ──────────────────────────────────────────────────────────────────

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Admin customizado para o modelo de usuário."""
    list_display  = ('username', 'nome_completo', 'matricula', 'cargo', 'email', 'is_ativo', 'is_staff')
    list_filter   = ('is_ativo', 'is_staff', 'cargo')
    search_fields = ('username', 'nome_completo', 'matricula', 'email')
    ordering      = ('nome_completo',)

    # Adicionar campos customizados aos fieldsets do UserAdmin
    fieldsets = UserAdmin.fieldsets + (
        ('Dados Institucionais', {
            'fields': ('matricula', 'nome_completo', 'cargo', 'is_ativo')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Dados Institucionais', {
            'fields': ('matricula', 'nome_completo', 'email', 'cargo', 'is_ativo')
        }),
    )


# ─── Categoria ────────────────────────────────────────────────────────────────

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display  = ('nome', 'icone', 'descricao')
    search_fields = ('nome',)
    ordering      = ('nome',)


# ─── Fornecedor ───────────────────────────────────────────────────────────────

@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display  = ('nome', 'cnpj', 'contato')
    search_fields = ('nome', 'cnpj')
    ordering      = ('nome',)


# ─── Almoxarifado ─────────────────────────────────────────────────────────────

@admin.register(Almoxarifado)
class AlmoxarifadoAdmin(admin.ModelAdmin):
    list_display  = ('nome', 'localizacao', 'responsavel', 'ativo')
    list_filter   = ('ativo',)
    search_fields = ('nome', 'localizacao')
    ordering      = ('nome',)


# ─── Item ─────────────────────────────────────────────────────────────────────

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display  = (
        'nome', 'codigo_interno', 'categoria', 'almoxarifado',
        'quantidade_atual', 'quantidade_minima', 'unidade_medida', 'estoque_baixo'
    )
    list_filter   = ('categoria', 'almoxarifado', 'unidade_medida')
    search_fields = ('nome', 'codigo_interno', 'descricao')
    ordering      = ('nome',)
    readonly_fields = ('codigo_interno', 'data_cadastro', 'ultima_atualizacao')

    @admin.display(boolean=True, description='Estoque baixo?')
    def estoque_baixo(self, obj):
        return obj.estoque_baixo


# ─── Movimentação ─────────────────────────────────────────────────────────────

@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display  = (
        'data_movimentacao', 'tipo', 'item', 'almoxarifado',
        'quantidade', 'quantidade_anterior', 'quantidade_posterior', 'responsavel'
    )
    list_filter   = ('tipo', 'almoxarifado', 'data_movimentacao')
    search_fields = ('item__nome', 'responsavel__nome_completo', 'destino_origem')
    ordering      = ('-data_movimentacao',)
    readonly_fields = (
        'almoxarifado', 'quantidade_anterior', 'quantidade_posterior', 'data_movimentacao'
    )

    def has_change_permission(self, request, obj=None):
        """Movimentações não devem ser editadas após criação — apenas visualizadas."""
        return False
