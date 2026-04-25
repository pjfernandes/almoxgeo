"""
Filtros django-filter para o sistema Sistema de Gestão de Estoque.
"""
import django_filters
from django import forms
from .models import Item, Movimentacao, Almoxarifado, Categoria


class ItemFilter(django_filters.FilterSet):
    """Filtros para a listagem de itens."""

    nome = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Nome do item',
        widget=forms.TextInput(attrs={'placeholder': 'Buscar por nome...'})
    )
    almoxarifado = django_filters.ModelChoiceFilter(
        queryset=Almoxarifado.objects.filter(ativo=True),
        label='Almoxarifado',
        empty_label='Todos os almoxarifados'
    )
    categoria = django_filters.ModelChoiceFilter(
        queryset=Categoria.objects.all(),
        label='Categoria',
        empty_label='Todas as categorias'
    )
    estoque = django_filters.CharFilter(
        method='filtrar_estoque',
        label='Situação do estoque',
        widget=forms.Select(choices=[
            ('', 'Todos'),
            ('baixo', 'Estoque baixo'),
            ('ok',    'Estoque normal'),
        ])
    )

    class Meta:
        model  = Item
        fields = ['nome', 'almoxarifado', 'categoria']

    def filtrar_estoque(self, queryset, name, value):
        from django.db.models import F
        if value == 'baixo':
            return queryset.filter(quantidade_atual__lt=F('quantidade_minima'))
        elif value == 'ok':
            return queryset.filter(quantidade_atual__gte=F('quantidade_minima'))
        return queryset


class MovimentacaoFilter(django_filters.FilterSet):
    """Filtros para a listagem de movimentações."""

    item__nome = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Nome do item',
        widget=forms.TextInput(attrs={'placeholder': 'Buscar item...'})
    )
    almoxarifado = django_filters.ModelChoiceFilter(
        queryset=Almoxarifado.objects.filter(ativo=True),
        label='Almoxarifado',
        empty_label='Todos'
    )
    tipo = django_filters.ChoiceFilter(
        choices=[('', 'Todos os tipos')] + list(Movimentacao.TIPO_CHOICES),
        label='Tipo'
    )
    data_inicio = django_filters.DateFilter(
        field_name='data_movimentacao',
        lookup_expr='date__gte',
        label='Data início',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    data_fim = django_filters.DateFilter(
        field_name='data_movimentacao',
        lookup_expr='date__lte',
        label='Data fim',
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model  = Movimentacao
        fields = []
