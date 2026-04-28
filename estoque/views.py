"""
Views do app estoque — Sistema de Gestão de Estoque
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import LoginForm



from django.db import models


# ─── Utilitário: verificar se usuário é admin ─────────────────────────────────

def is_admin(user):
    """Verifica se o usuário é staff (administrador)."""
    return user.is_staff


# ─── Redirecionamento da raiz ─────────────────────────────────────────────────

def redirecionar_raiz(request):
    """Redireciona a raiz do site para o dashboard ou login."""
    if request.user.is_authenticated:
        return redirect('estoque:dashboard')
    return redirect('estoque:login')


# ─── Login ───────────────────────────────────────────────────────────────────

def view_login(request):
    """View de login — sem registro público."""
    # Se já está logado, vai para o dashboard
    if request.user.is_authenticated:
        return redirect('estoque:dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # Verificar se o usuário está ativo no sistema
            if not user.is_ativo:
                messages.error(request, 'Sua conta está desativada. Contate o administrador.')
                return render(request, 'estoque/login.html', {'form': form})
            login(request, user)
            messages.success(request, f'Bem-vindo(a), {user.nome_completo}!')
            # Redirecionar para a página solicitada originalmente, ou dashboard
            proxima = request.GET.get('next', 'estoque:dashboard')
            return redirect(proxima)
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    else:
        form = LoginForm()

    return render(request, 'estoque/login.html', {'form': form})


# ─── Logout ──────────────────────────────────────────────────────────────────

@login_required
def view_logout(request):
    """Logout — apenas via POST para evitar logout por GET."""
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'Você saiu do sistema.')
    return redirect('estoque:login')


# ─── Dashboard (placeholder — será expandido na Fase 6) ──────────────────────
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
import datetime, json
from .models import Almoxarifado, Item, Movimentacao, Categoria

@login_required
def dashboard(request):
    """
    Dashboard principal com estatísticas e gráficos.
    """
    hoje = timezone.now()
    trinta_dias_atras = hoje - datetime.timedelta(days=30)

    # ── Cards de resumo ───────────────────────────────────────────────────────
    total_almoxarifados = Almoxarifado.objects.filter(ativo=True).count()
    total_itens         = Item.objects.count()

    # Itens com estoque abaixo do mínimo
    itens_baixo_estoque = Item.objects.filter(
        quantidade_atual__lt=models.F('quantidade_minima')
    )
    total_baixo_estoque = itens_baixo_estoque.count()

    hoje = timezone.now().date()
    limite_validade = hoje + datetime.timedelta(days=30)

    itens_validade_critica = Item.objects.filter(
        Q(data_validade__lte=limite_validade) & Q(data_validade__gte=hoje)
    ).select_related('categoria', 'almoxarifado').order_by('data_validade')

    itens_vencidos = Item.objects.filter(
        data_validade__lt=hoje
    ).select_related('categoria', 'almoxarifado').order_by('data_validade')

    # ── Últimas 10 movimentações ──────────────────────────────────────────────
    ultimas_movimentacoes = Movimentacao.objects.select_related(
        'item', 'almoxarifado', 'responsavel'
    ).order_by('-data_movimentacao')[:10]

    # ── Dados para gráfico de barras: movimentações dos últimos 30 dias ──────
    # Agrupar por dia e tipo
    movs_por_dia = (
        Movimentacao.objects
        .filter(data_movimentacao__gte=trinta_dias_atras)
        .annotate(dia=TruncDate('data_movimentacao'))
        .values('dia', 'tipo')
        .annotate(total=Count('id'))
        .order_by('dia')
    )

    # Montar estrutura de dados para Chart.js
    dias_labels  = []
    entradas_data = []
    saidas_data   = []

    # Gerar todos os dias dos últimos 30 dias
    for i in range(30):
        dia = hoje - datetime.timedelta(days=29-i)
        dias_labels.append(dia.strftime('%d/%m'))

        entrada_dia = sum(
            m['total'] for m in movs_por_dia
            if m['dia'] == dia and m['tipo'] == 'ENTRADA'
        )
        saida_dia = sum(
            m['total'] for m in movs_por_dia
            if m['dia'] == dia and m['tipo'] in ('SAIDA', 'TRANSFERENCIA')
        )
        entradas_data.append(entrada_dia)
        saidas_data.append(saida_dia)

    # ── Dados para gráfico de pizza: itens por categoria ─────────────────────
    itens_por_categoria = (
        Categoria.objects
        .annotate(qtd_itens=Count('itens'))
        .filter(qtd_itens__gt=0)
        .values('nome', 'qtd_itens')
        .order_by('-qtd_itens')
    )

    pizza_labels = [c['nome'] for c in itens_por_categoria]
    pizza_data   = [c['qtd_itens'] for c in itens_por_categoria]

    # Paleta de cores para o gráfico de pizza
    pizza_cores = [
        '#003366','#004a99','#0066cc','#3399ff',
        '#66b2ff','#99ccff','#cce5ff','#e8f0fe',
    ]

    top_itens = (
        Movimentacao.objects
        .filter(data_movimentacao__gte=trinta_dias_atras)
        .values('item__nome', 'item__pk')
        .annotate(total_movimentacoes=Count('id'))
        .order_by('-total_movimentacoes')[:5]
    )

    # Valor total do estoque
    from django.db.models import Sum
    valor_total = (
        Item.objects
        .filter(valor__isnull=False)
        .aggregate(
            total=Sum(models.F('quantidade_atual') * models.F('valor'))
        )['total'] or 0
    )

    # Distribuição de movimentações por tipo (último mês)
    movs_por_tipo = list(
        Movimentacao.objects
        .filter(data_movimentacao__gte=trinta_dias_atras)
        .values('tipo')
        .annotate(qtd=Count('id'))
    )

    tipo_labels = [m['tipo'] for m in movs_por_tipo]
    tipo_data = [m['qtd'] for m in movs_por_tipo]

    contexto = {
        'total_almoxarifados':   total_almoxarifados,
        'total_itens':           total_itens,
        'total_baixo_estoque':   total_baixo_estoque,
        'itens_baixo_estoque':   itens_baixo_estoque[:5],  # prévia
        'ultimas_movimentacoes': ultimas_movimentacoes,

        # Chart.js — barras
        'grafico_dias_labels':   json.dumps(dias_labels),
        'grafico_entradas':      json.dumps(entradas_data),
        'grafico_saidas':        json.dumps(saidas_data),

        # Chart.js — pizza
        'pizza_labels': json.dumps(pizza_labels),
        'pizza_data':   json.dumps(pizza_data),
        'pizza_cores':  json.dumps(pizza_cores[:len(pizza_labels)]),

        'itens_validade_critica': itens_validade_critica[:5],
        'itens_vencidos': itens_vencidos[:5],
        'total_validade_critica': itens_validade_critica.count(),
        'total_vencidos': itens_vencidos.count(),
        'top_itens': top_itens,
        'valor_total_estoque': valor_total,
        'tipo_labels': json.dumps(tipo_labels),
        'tipo_data': json.dumps(tipo_data),
    }

    return render(request, 'estoque/dashboard.html', contexto)


# ─── Trocar senha ───────────────────────────────────────────────────────────────────
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.forms import PasswordChangeForm
from django.urls import reverse_lazy

class TrocarSenhaView(PasswordChangeView):
    """View de troca de senha com template customizado."""
    template_name = 'estoque/trocar_senha.html'
    success_url   = reverse_lazy('estoque:dashboard')
    form_class    = PasswordChangeForm

    def form_valid(self, form):
        messages.success(self.request, 'Senha alterada com sucesso!')
        return super().form_valid(form)

# ══════════════════════════════════════════════════════════════
# ALMOXARIFADOS
# ══════════════════════════════════════════════════════════════
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from .models import Almoxarifado, Categoria, Fornecedor, Item, Movimentacao
from .forms import AlmoxarifadoForm, CategoriaForm, FornecedorForm

@login_required
def almoxarifado_lista(request):
    """Lista todos os almoxarifados com paginação."""
    qs = Almoxarifado.objects.select_related('responsavel').order_by('nome')
    paginator = Paginator(qs, 10)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'estoque/almoxarifados/lista.html', {'page_obj': page})


@login_required
def almoxarifado_criar(request):
    """Cria um novo almoxarifado."""
    if request.method == 'POST':
        form = AlmoxarifadoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Almoxarifado criado com sucesso!')
            return redirect('estoque:almoxarifado_lista')
    else:
        form = AlmoxarifadoForm()
    return render(request, 'estoque/almoxarifados/form.html',
                  {'form': form, 'titulo': 'Novo Almoxarifado'})


@login_required
def almoxarifado_editar(request, pk):
    """Edita um almoxarifado existente."""
    alm = get_object_or_404(Almoxarifado, pk=pk)
    if request.method == 'POST':
        form = AlmoxarifadoForm(request.POST, instance=alm)
        if form.is_valid():
            form.save()
            messages.success(request, 'Almoxarifado atualizado!')
            return redirect('estoque:almoxarifado_lista')
    else:
        form = AlmoxarifadoForm(instance=alm)
    return render(request, 'estoque/almoxarifados/form.html',
                  {'form': form, 'titulo': 'Editar Almoxarifado', 'objeto': alm})


@login_required
def almoxarifado_toggle_ativo(request, pk):
    """Ativa ou desativa um almoxarifado (nunca exclui)."""
    alm = get_object_or_404(Almoxarifado, pk=pk)
    if request.method == 'POST':
        alm.ativo = not alm.ativo
        alm.save()
        estado = 'ativado' if alm.ativo else 'desativado'
        messages.success(request, f'Almoxarifado {estado} com sucesso!')
    return redirect('estoque:almoxarifado_lista')


# ══════════════════════════════════════════════════════════════
# CATEGORIAS
# ══════════════════════════════════════════════════════════════
@login_required
def categoria_lista(request):
    qs = Categoria.objects.annotate(qtd=Count('itens')).order_by('nome')
    paginator = Paginator(qs, 10)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'estoque/categorias/lista.html', {'page_obj': page})


@login_required
def categoria_criar(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoria criada com sucesso!')
            return redirect('estoque:categoria_lista')
    else:
        form = CategoriaForm()
    return render(request, 'estoque/categorias/form.html',
                  {'form': form, 'titulo': 'Nova Categoria'})


@login_required
def categoria_editar(request, pk):
    cat = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoria atualizada!')
            return redirect('estoque:categoria_lista')
    else:
        form = CategoriaForm(instance=cat)
    return render(request, 'estoque/categorias/form.html',
                  {'form': form, 'titulo': 'Editar Categoria', 'objeto': cat})


@login_required
def categoria_excluir(request, pk):
    cat = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        try:
            cat.delete()
            messages.success(request, 'Categoria excluída!')
        except Exception:
            messages.error(request, 'Não é possível excluir: categoria possui itens vinculados.')
    return redirect('estoque:categoria_lista')


# ══════════════════════════════════════════════════════════════
# FORNECEDORES
# ══════════════════════════════════════════════════════════════
@login_required
def fornecedor_lista(request):
    qs = Fornecedor.objects.order_by('nome')
    paginator = Paginator(qs, 10)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'estoque/fornecedores/lista.html', {'page_obj': page})


@login_required
def fornecedor_criar(request):
    if request.method == 'POST':
        form = FornecedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fornecedor criado com sucesso!')
            return redirect('estoque:fornecedor_lista')
    else:
        form = FornecedorForm()
    return render(request, 'estoque/fornecedores/form.html',
                  {'form': form, 'titulo': 'Novo Fornecedor'})


@login_required
def fornecedor_editar(request, pk):
    forn = get_object_or_404(Fornecedor, pk=pk)
    if request.method == 'POST':
        form = FornecedorForm(request.POST, instance=forn)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fornecedor atualizado!')
            return redirect('estoque:fornecedor_lista')
    else:
        form = FornecedorForm(instance=forn)
    return render(request, 'estoque/fornecedores/form.html',
                  {'form': form, 'titulo': 'Editar Fornecedor', 'objeto': forn})


@login_required
def fornecedor_excluir(request, pk):
    forn = get_object_or_404(Fornecedor, pk=pk)
    if request.method == 'POST':
        try:
            forn.delete()
            messages.success(request, 'Fornecedor excluído!')
        except Exception:
            messages.error(request, 'Não é possível excluir: fornecedor possui movimentações vinculadas.')
    return redirect('estoque:fornecedor_lista')


# ══════════════════════════════════════════════════════════════
# ITENS
# ══════════════════════════════════════════════════════════════
from .filters import ItemFilter
from .forms import ItemForm

@login_required
def item_lista(request):
    """Lista itens com filtros e paginação."""
    qs = Item.objects.select_related('categoria', 'almoxarifado').order_by('nome')
    filtro = ItemFilter(request.GET, queryset=qs)
    paginator = Paginator(filtro.qs, 10)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'estoque/itens/lista.html', {
        'page_obj': page,
        'filtro': filtro,
    })


@login_required
def item_detalhe(request, pk):
    item = get_object_or_404(
        Item.objects.select_related('categoria', 'almoxarifado', 'fornecedor'),
        pk=pk
    )

    # Buscar histórico de movimentações deste item
    movimentacoes = Movimentacao.objects.filter(
        item=item
    ).select_related(
        'responsavel',
        'almoxarifado',
        'almoxarifado_destino',
        'item__fornecedor'
    ).order_by('-data_movimentacao')[:50]

    # Calcular valor total do estoque
    valor_total_estoque = None
    if item.valor:
        valor_total_estoque = item.quantidade_atual * item.valor

    return render(request, 'estoque/itens/detalhe.html', {
        'item': item,
        'movimentacoes': movimentacoes,
        'valor_total_estoque': valor_total_estoque,
    })

@login_required
def item_criar(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save()
            messages.success(
                request,
                f'Item "{item.nome}" cadastrado com sucesso! Código: {item.codigo_interno}'
            )
            return redirect('estoque:item_detalhe', pk=item.pk)  # ← MODIFICADO: vai pro detalhe
    else:
        form = ItemForm()

    return render(request, 'estoque/itens/form.html', {
        'form': form,
        'titulo': 'Cadastrar Novo Item',
    })

@login_required
def item_editar(request, pk):
    """Edita os dados cadastrais de um item (não altera quantidade via aqui)."""
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item atualizado com sucesso!')
            return redirect('estoque:item_detalhe', pk=item.pk)
    else:
        form = ItemForm(instance=item)
    return render(request, 'estoque/itens/form.html',
                  {'form': form, 'titulo': 'Editar Item', 'objeto': item})


# ══════════════════════════════════════════════════════════════
# Movimentação
# ══════════════════════════════════════════════════════════════
from .filters import MovimentacaoFilter
from .forms import MovimentacaoForm

@login_required
def movimentacao_lista(request):
    """Lista movimentações com filtros e paginação."""
    qs = Movimentacao.objects.select_related(
        'item', 'almoxarifado', 'responsavel'
    ).order_by('-data_movimentacao')

    filtro = MovimentacaoFilter(request.GET, queryset=qs)
    paginator = Paginator(filtro.qs, 10)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'estoque/movimentacoes/lista.html', {
        'page_obj': page,
        'filtro': filtro,
    })


@login_required
def movimentacao_criar(request):
    """Registra uma nova movimentação de estoque."""
    item_pk = request.GET.get('item')

    if request.method == 'POST':
        form = MovimentacaoForm(request.POST)
        if form.is_valid():
            mov = form.save(commit=False)
            mov.responsavel = request.user  # registra quem está logado
            try:
                mov.save()
                messages.success(request, 'Movimentação registrada com sucesso!')
                return redirect('estoque:item_detalhe', pk=mov.item.pk)
            except Exception as e:
                messages.error(request, f'Erro ao registrar movimentação: {e}')
    else:
        form = MovimentacaoForm(item_pk=item_pk)

    return render(request, 'estoque/movimentacoes/form.html', {
        'form': form,
        'titulo': 'Nova Movimentação',
    })

#Views de Exportação
import csv
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER


@login_required
def movimentacao_exportar_csv(request):
    """Exporta as movimentações filtradas para CSV."""
    qs = Movimentacao.objects.select_related(
        'item', 'almoxarifado', 'responsavel', 'fornecedor', 'almoxarifado_destino'
    ).order_by('-data_movimentacao')

    # Aplicar os mesmos filtros da listagem
    filtro = MovimentacaoFilter(request.GET, queryset=qs)

    # Criar a resposta HTTP com content-type CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="movimentacoes.csv"'

    # BOM UTF-8 para Excel abrir corretamente
    response.write('\ufeff')

    writer = csv.writer(response, delimiter=';')
    # Cabeçalho
    writer.writerow([
         'Data', 'Tipo', 'Item', 'Código', 'Almoxarifado',
         'Quantidade', 'Qtd. Anterior', 'Qtd. Posterior',
        'Solicitante/Destino', 'Responsável', 'Observação'
     ])

    # for mov in filtro.qs:
    #     writer.writerow([
    #         mov.data_movimentacao.strftime('%d/%m/%Y %H:%M'),
    #         mov.get_tipo_display(),
    #         mov.item.nome,
    #         mov.item.codigo_interno,
    #         mov.almoxarifado.nome,
    #         mov.quantidade,
    #         mov.quantidade_anterior,
    #         mov.quantidade_posterior,
    #         mov.destino_origem or '',
    #         mov.fornecedor.nome if mov.fornecedor else '',
    #         mov.responsavel.nome_completo,
    #         mov.observacao or '',
    #     ])
    for mov in filtro.qs:
            solicitante = ''
            if mov.solicitante_nome:
                solicitante = f"{mov.solicitante_nome}"
                if mov.solicitante_departamento:
                    solicitante += f" ({mov.solicitante_departamento})"
            elif mov.almoxarifado_destino:
                solicitante = f"→ {mov.almoxarifado_destino.nome}"
            elif mov.fornecedor:
                solicitante = mov.fornecedor.nome

            writer.writerow([
                mov.data_movimentacao.strftime('%d/%m/%Y %H:%M'),
                mov.get_tipo_display(),
                mov.item.nome,
                mov.item.codigo_interno,
                mov.almoxarifado.nome,
                mov.quantidade,
                mov.quantidade_anterior,
                mov.quantidade_posterior,
                solicitante,
                mov.responsavel.nome_completo,
                mov.observacao or '',
            ])

    return response


@login_required
def movimentacao_exportar_pdf(request):
    """Exporta as movimentações filtradas para PDF com ReportLab."""
    qs = Movimentacao.objects.select_related(
        'item', 'almoxarifado', 'responsavel'
    ).order_by('-data_movimentacao')

    filtro = MovimentacaoFilter(request.GET, queryset=qs)
    movimentacoes = list(filtro.qs)

    # Resposta HTTP para PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="movimentacoes.pdf"'

    # Documento em modo paisagem (mais colunas)
    doc = SimpleDocTemplate(
        response,
        pagesize=landscape(A4),
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=2*cm,    bottomMargin=2*cm
    )

    estilos = getSampleStyleSheet()
    elementos = []

    # Título
    estilo_titulo = ParagraphStyle(
        'titulo', parent=estilos['Heading1'],
        fontSize=14, alignment=TA_CENTER,
        textColor=colors.HexColor('#003366'),
        spaceAfter=4
    )
    estilo_sub = ParagraphStyle(
        'sub', parent=estilos['Normal'],
        fontSize=9, alignment=TA_CENTER,
        textColor=colors.grey, spaceAfter=12
    )

    elementos.append(Paragraph('Sistema de Gestão de Estoque — Instituto de Geociências / UFF', estilo_titulo))
    elementos.append(Paragraph(
        f'Relatório de Movimentações — gerado em {timezone.localtime().strftime("%d/%m/%Y às %H:%M")}',
        estilo_sub
    ))

    # Tabela de dados
    cabecalho = ['Data', 'Tipo', 'Item', 'Almoxarifado', 'Qtd.', 'Anterior', 'Posterior', 'Solicitante/Destino','Responsável']
    dados = [cabecalho]

    for mov in movimentacoes:
        solicitante = ''
        if mov.solicitante_nome:
            solicitante = f"{mov.solicitante_nome}"
            if mov.solicitante_departamento:
                solicitante += f" ({mov.solicitante_departamento})"
        elif mov.almoxarifado_destino:
            solicitante = f"→ {mov.almoxarifado_destino.nome}"
        elif mov.fornecedor:
            solicitante = mov.fornecedor.nome

        dados.append([
            mov.data_movimentacao.strftime('%d/%m/%Y\n%H:%M'),
            mov.get_tipo_display(),
            mov.item.nome[:30],
            mov.almoxarifado.nome[:20],
            str(mov.quantidade),
            str(mov.quantidade_anterior),
            str(mov.quantidade_posterior),
            solicitante,
            mov.responsavel.nome_completo[:25],
        ])

    tabela = Table(dados, repeatRows=1)
    tabela.setStyle(TableStyle([
        # Cabeçalho
        ('BACKGROUND',   (0,0), (-1,0), colors.HexColor('#003366')),
        ('TEXTCOLOR',    (0,0), (-1,0), colors.white),
        ('FONTNAME',     (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,0), 8),
        ('ALIGN',        (0,0), (-1,0), 'CENTER'),
        ('BOTTOMPADDING',(0,0), (-1,0), 6),

        # Dados
        ('FONTSIZE',     (0,1), (-1,-1), 7.5),
        ('ALIGN',        (4,1), (6,-1), 'CENTER'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, colors.HexColor('#f4f6f9')]),

        # Bordas
        ('GRID',         (0,0), (-1,-1), 0.25, colors.HexColor('#dee2e6')),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
    ]))

    elementos.append(tabela)

    # Total de registros
    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(Paragraph(
        f'Total de registros: {len(movimentacoes)}',
        estilos['Normal']
    ))

    doc.build(elementos)
    return response

#Usuários
from .forms import UsuarioForm
from .models import Usuario


@login_required
@user_passes_test(is_admin)
def usuario_lista(request):
    """Lista usuários do sistema (apenas admin)."""
    qs = Usuario.objects.order_by('nome_completo')
    paginator = Paginator(qs, 10)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'estoque/usuarios/lista.html', {'page_obj': page})


@login_required
@user_passes_test(is_admin)
def usuario_criar(request):
    """Cria um novo usuário (apenas admin)."""
    if request.method == 'POST':
        form = UsuarioForm(request.POST, criando=True)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário criado com sucesso!')
            return redirect('estoque:usuario_lista')
    else:
        form = UsuarioForm(criando=True)
    return render(request, 'estoque/usuarios/form.html',
                  {'form': form, 'titulo': 'Novo Usuário'})


@login_required
@user_passes_test(is_admin)
def usuario_editar(request, pk):
    """Edita um usuário existente (apenas admin)."""
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário atualizado!')
            return redirect('estoque:usuario_lista')
    else:
        form = UsuarioForm(instance=usuario)
    return render(request, 'estoque/usuarios/form.html',
                  {'form': form, 'titulo': 'Editar Usuário', 'objeto': usuario})

from django.http import HttpResponse
from io import BytesIO
import qrcode
from django.urls import reverse


@login_required
def item_qrcode(request, pk):
    """Gera QR Code do item para impressão de etiqueta."""
    item = get_object_or_404(Item, pk=pk)

    # URL absoluta do item
    url = request.build_absolute_uri(
        reverse('estoque:item_detalhe', args=[item.pk])
    )

    # Gerar QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Retornar como PNG
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type='image/png')


@login_required
def item_etiqueta(request, pk):
    """Página para impressão de etiqueta com QR Code."""
    item = get_object_or_404(Item, pk=pk)
    return render(request, 'estoque/itens/etiqueta.html', {'item': item})


@login_required
@user_passes_test(is_admin)
def usuario_toggle_ativo(request, pk):
    """Ativa/desativa usuário sem excluí-lo."""
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        usuario.is_ativo  = not usuario.is_ativo
        usuario.is_active = usuario.is_ativo
        usuario.save()
        estado = 'ativado' if usuario.is_ativo else 'desativado'
        messages.success(request, f'Usuário {estado} com sucesso!')
    return redirect('estoque:usuario_lista')


#Relatórios
@login_required
def relatorio_estoque(request):
    """
    Relatório de estoque atual, agrupado por almoxarifado.
    Permite exportar em CSV ou PDF.
    """
    almoxarifados = Almoxarifado.objects.filter(ativo=True).prefetch_related(
        'itens__categoria'
    ).order_by('nome')

    exportar = request.GET.get('exportar')

    if exportar == 'csv':
        return _exportar_estoque_csv(almoxarifados)
    elif exportar == 'pdf':
        return _exportar_estoque_pdf(almoxarifados)

    return render(request, 'estoque/relatorios/estoque.html', {
        'almoxarifados': almoxarifados,
    })


def _exportar_estoque_csv(almoxarifados):
    """Gera CSV do relatório de estoque."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="estoque_atual.csv"'
    response.write('\ufeff')  # BOM UTF-8

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Almoxarifado', 'Código', 'Item', 'Categoria', 'Unidade',
                     'Qtd. Atual', 'Qtd. Mínima', 'Situação', 'Localização Física'])

    for alm in almoxarifados:
        for item in alm.itens.select_related('categoria').order_by('nome'):
            writer.writerow([
                alm.nome,
                item.codigo_interno,
                item.nome,
                item.categoria.nome,
                item.get_unidade_medida_display(),
                item.quantidade_atual,
                item.quantidade_minima,
                'BAIXO' if item.estoque_baixo else 'OK',
                item.localizacao_fisica or '',
            ])

    return response


def _exportar_estoque_pdf(almoxarifados):
    """Gera PDF do relatório de estoque com ReportLab."""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="estoque_atual.pdf"'

    doc = SimpleDocTemplate(
        response, pagesize=landscape(A4),
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    estilos = getSampleStyleSheet()
    elementos = []

    estilo_titulo = ParagraphStyle(
        'titulo', parent=estilos['Heading1'], fontSize=14,
        alignment=TA_CENTER, textColor=colors.HexColor('#003366'), spaceAfter=4
    )
    estilo_sub = ParagraphStyle(
        'sub', parent=estilos['Normal'], fontSize=9,
        alignment=TA_CENTER, textColor=colors.grey, spaceAfter=12
    )
    estilo_alm = ParagraphStyle(
        'alm', parent=estilos['Heading2'], fontSize=10,
        textColor=colors.HexColor('#003366'), spaceBefore=12, spaceAfter=4
    )

    elementos.append(Paragraph('Sistema de Gestão de Estoque — Instituto de Geociências / UFF', estilo_titulo))
    elementos.append(Paragraph(
        f'Relatório de Estoque Atual — {timezone.localtime().strftime("%d/%m/%Y às %H:%M")}',
        estilo_sub
    ))

    cabecalho = ['Código', 'Item', 'Categoria', 'Unid.', 'Qtd. Atual', 'Mínimo', 'Situação']

    for alm in almoxarifados:
        itens_alm = list(alm.itens.select_related('categoria').order_by('nome'))
        if not itens_alm:
            continue

        elementos.append(Paragraph(f'Almoxarifado: {alm.nome}', estilo_alm))

        dados = [cabecalho]
        for item in itens_alm:
            dados.append([
                item.codigo_interno,
                item.nome[:35],
                item.categoria.nome[:20],
                item.get_unidade_medida_display(),
                str(item.quantidade_atual),
                str(item.quantidade_minima),
                'BAIXO' if item.estoque_baixo else 'OK',
            ])

        tabela = Table(dados, repeatRows=1)
        tabela.setStyle(TableStyle([
            ('BACKGROUND',   (0,0), (-1,0), colors.HexColor('#003366')),
            ('TEXTCOLOR',    (0,0), (-1,0), colors.white),
            ('FONTNAME',     (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',     (0,0), (-1,-1), 7.5),
            ('ALIGN',        (4,0), (6,-1), 'CENTER'),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, colors.HexColor('#f4f6f9')]),
            ('GRID',         (0,0), (-1,-1), 0.25, colors.HexColor('#dee2e6')),
            # Marcar estoque baixo em vermelho
            *[
                ('TEXTCOLOR', (4, i+1), (4, i+1), colors.red)
                for i, item in enumerate(itens_alm) if item.estoque_baixo
            ],
        ]))
        elementos.append(tabela)

    doc.build(elementos)
    return response

@login_required
def busca_global(request):
    """Busca global de itens por nome ou código."""
    query = request.GET.get('q', '').strip()

    if not query:
        return redirect('estoque:dashboard')

    # Buscar itens
    itens = Item.objects.filter(
        Q(nome__icontains=query) |
        Q(codigo_interno__icontains=query) |
        Q(descricao__icontains=query) |
        Q(lote__icontains=query) |
        Q(codigo_patrimonio__icontains=query)
    ).select_related('categoria', 'almoxarifado')[:20]

    # Se for apenas 1 resultado, redirecionar direto
    if itens.count() == 1:
        return redirect('estoque:item_detalhe', pk=itens[0].pk)

    return render(request, 'estoque/busca.html', {
        'query': query,
        'itens': itens,
    })
