"""
Context processors para templates.
"""
from django.urls import reverse


def breadcrumbs(request):
    """
    Gera breadcrumbs automaticamente baseado na URL atual.
    """
    path = request.path
    breadcrumbs_list = [
        {'title': 'Dashboard', 'url': reverse('estoque:dashboard')},
    ]

    # Mapeamento de rotas para breadcrumbs
    if '/itens/' in path:
        breadcrumbs_list.append({
            'title': 'Itens',
            'url': reverse('estoque:item_lista')
        })
        if '/novo/' in path:
            breadcrumbs_list.append({
                'title': 'Novo Item',
                'icon': 'plus-circle'
            })
        elif '/editar/' in path:
            breadcrumbs_list.append({
                'title': 'Editar Item',
                'icon': 'pencil'
            })
        elif path.endswith(path.split('/')[-2] + '/'):  # detalhe
            breadcrumbs_list.append({
                'title': 'Detalhes',
                'icon': 'eye'
            })

    elif '/movimentacoes/' in path:
        breadcrumbs_list.append({
            'title': 'Movimentações',
            'url': reverse('estoque:movimentacao_lista')
        })
        if '/nova/' in path:
            breadcrumbs_list.append({
                'title': 'Nova Movimentação',
                'icon': 'arrow-left-right'
            })

    elif '/almoxarifados/' in path:
        breadcrumbs_list.append({
            'title': 'Almoxarifados',
            'url': reverse('estoque:almoxarifado_lista')
        })
        if '/novo/' in path:
            breadcrumbs_list.append({
                'title': 'Novo Almoxarifado',
                'icon': 'plus-circle'
            })
        elif '/editar/' in path:
            breadcrumbs_list.append({
                'title': 'Editar',
                'icon': 'pencil'
            })

    elif '/categorias/' in path:
        breadcrumbs_list.append({
            'title': 'Categorias',
            'url': reverse('estoque:categoria_lista')
        })
        if '/nova/' in path:
            breadcrumbs_list.append({
                'title': 'Nova Categoria',
                'icon': 'plus-circle'
            })
        elif '/editar/' in path:
            breadcrumbs_list.append({
                'title': 'Editar',
                'icon': 'pencil'
            })

    elif '/fornecedores/' in path:
        breadcrumbs_list.append({
            'title': 'Fornecedores',
            'url': reverse('estoque:fornecedor_lista')
        })
        if '/novo/' in path:
            breadcrumbs_list.append({
                'title': 'Novo Fornecedor',
                'icon': 'plus-circle'
            })
        elif '/editar/' in path:
            breadcrumbs_list.append({
                'title': 'Editar',
                'icon': 'pencil'
            })

    elif '/usuarios/' in path:
        breadcrumbs_list.append({
            'title': 'Usuários',
            'url': reverse('estoque:usuario_lista')
        })
        if '/novo/' in path:
            breadcrumbs_list.append({
                'title': 'Novo Usuário',
                'icon': 'person-plus'
            })
        elif '/editar/' in path:
            breadcrumbs_list.append({
                'title': 'Editar',
                'icon': 'pencil'
            })

    elif '/relatorios/' in path:
        breadcrumbs_list.append({
            'title': 'Relatórios',
            'icon': 'file-earmark-bar-graph'
        })

    elif '/trocar-senha/' in path:
        breadcrumbs_list.append({
            'title': 'Trocar Senha',
            'icon': 'key'
        })

    return {'breadcrumbs': breadcrumbs_list}
