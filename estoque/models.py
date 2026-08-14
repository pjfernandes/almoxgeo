"""
Models do sistema Sistema de Gestão de Estoque — IGeo/UFF
Gestão de estoque de almoxarifados
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone


# ─────────────────────────────────────────────────────────────────────────────
# USUÁRIO CUSTOMIZADO
# ─────────────────────────────────────────────────────────────────────────────

class Usuario(AbstractUser):
    """
    Usuário do sistema — servidores públicos do IGeo/UFF.
    Estende o AbstractUser do Django adicionando campos institucionais.
    O campo 'username' do AbstractUser será usado como login.
    """
    # matricula = models.CharField(
    #     max_length=20,
    #     unique=True,
    #     verbose_name='Matrícula SIAPE',
    #     help_text='Matrícula SIAPE do servidor'
    # )
    nome_completo = models.CharField(
        max_length=200,
        verbose_name='Nome completo'
    )
    email = models.EmailField(
        unique=True,
        verbose_name='E-mail institucional'
    )
    cargo = models.CharField(
        max_length=100,
        verbose_name='Cargo',
        blank=True
    )
    is_ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        help_text='Desmarque para desativar o acesso do servidor ao sistema'
    )

    # ─── Nível de acesso ──────────────────────────────────────────
    NIVEL_CHOICES = [
        ('ADMIN',    'Administrador — acesso total, gerencia usuários'),
        ('GESTOR',   'Gestor — cadastra e movimenta, não edita/exclui nem gerencia usuários'),
        ('OPERADOR', 'Operador — apenas registra movimentações (entrada/saída)'),
    ]
    nivel_acesso = models.CharField(
        max_length=10,
        choices=NIVEL_CHOICES,
        default='OPERADOR',
        verbose_name='Nível de acesso'
    )

    # Campo obrigatório para login
    USERNAME_FIELD = 'username'
    #REQUIRED_FIELDS = ['email', 'matricula', 'nome_completo']
    REQUIRED_FIELDS = ['email', 'nome_completo']

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['nome_completo']

    # def __str__(self):
    #     return f'{self.nome_completo} ({self.matricula})'
    def __str__(self):
        return f'{self.nome_completo} ({self.username})'

    # ─── Propriedades de permissão ────────────────────────────────
    @property
    def eh_admin(self):
        """Administrador: acesso total, incluindo gestão de usuários."""
        return self.nivel_acesso == 'ADMIN' or self.is_superuser

    @property
    def pode_gerenciar_usuarios(self):
        return self.eh_admin

    @property
    def pode_movimentar(self):
        """Todos os níveis podem registrar movimentações."""
        return True

    @property
    def pode_cadastrar(self):
        """Criar itens, almoxarifados, categorias, fornecedores."""
        return self.nivel_acesso in ('ADMIN', 'GESTOR') or self.is_superuser

    @property
    def pode_editar(self):
        """Editar registros existentes — apenas administradores."""
        return self.eh_admin

    @property
    def pode_excluir(self):
        """Excluir registros — apenas administradores."""
        return self.eh_admin

    def save(self, *args, **kwargs):
        # Sincronizar is_ativo com is_active do Django
        self.is_active = self.is_ativo
        # Sincronizar is_staff com o nível de acesso
        if self.nivel_acesso == 'ADMIN':
            self.is_staff = True
        elif not self.is_superuser:
            self.is_staff = False
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# CATEGORIA
# ─────────────────────────────────────────────────────────────────────────────

class Categoria(models.Model):
    """
    Categoria de itens do estoque.
    Exemplo: Material de Escritório, Limpeza, Informática.
    """
    nome = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nome'
    )
    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )
    icone = models.CharField(
            max_length=50,
            default='box-seam',  # ← ícone padrão
            blank=True,          # ← não obrigatório
            verbose_name='Ícone Bootstrap Icons',
            help_text='Nome do ícone Bootstrap Icons'
        )

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['nome']

    def __str__(self):
        return self.nome


# ─────────────────────────────────────────────────────────────────────────────
# FORNECEDOR
# ─────────────────────────────────────────────────────────────────────────────

class Fornecedor(models.Model):
    """
    Fornecedor de materiais para o almoxarifado.
    """
    nome = models.CharField(
        max_length=200,
        verbose_name='Nome / Razão Social'
    )
    cnpj = models.CharField(
        max_length=18,
        blank=True,
        verbose_name='CNPJ',
        help_text='Formato: XX.XXX.XXX/XXXX-XX'
    )
    contato = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Contato',
        help_text='Telefone ou e-mail de contato'
    )
    observacao = models.TextField(
        blank=True,
        verbose_name='Observação'
    )

    class Meta:
        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'
        ordering = ['nome']

    def __str__(self):
        return self.nome


# ─────────────────────────────────────────────────────────────────────────────
# ALMOXARIFADO
# ─────────────────────────────────────────────────────────────────────────────

class Almoxarifado(models.Model):
    """
    Almoxarifado físico do IGeo/UFF.
    Um almoxarifado tem um responsável e pode ter vários itens.
    """
    nome = models.CharField(
        max_length=150,
        verbose_name='Nome do almoxarifado'
    )
    localizacao = models.CharField(
        max_length=200,
        verbose_name='Localização',
        help_text='Ex: Bloco A, Sala 102'
    )
    responsavel = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='almoxarifados_responsavel',
        verbose_name='Responsável'
    )
    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    class Meta:
        verbose_name = 'Almoxarifado'
        verbose_name_plural = 'Almoxarifados'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} — {self.localizacao}'


# ─────────────────────────────────────────────────────────────────────────────
# ITEM
# ─────────────────────────────────────────────────────────────────────────────

class Item(models.Model):
    """
    Item de estoque de um almoxarifado.
    O código interno é gerado automaticamente no save().
    """

    # Opções de unidade de medida
    UNIDADES = [
        ('un', 'Unidade'),
        ('cx', 'Caixa'),
        ('rs', 'Resma'),
        ('lt', 'Litro'),
        ('kg', 'Quilograma'),
        ('m',  'Metro'),
        ('pc', 'Pacote'),
        ('ou', 'Outros'),
    ]

    # Classificação patrimonial (NOVO)
    TIPO_MATERIAL_CHOICES = [
        ('CONSUMO', 'Material de Consumo'),
        ('PERMANENTE', 'Bem Permanente'),
    ]

    # Tipos de empenho (NOVO)
    TIPO_EMPENHO_CHOICES = [
        ('', '—'),
        ('ORDINARIO', 'Ordinário'),
        ('ESTIMATIVO', 'Estimativo'),
        ('GLOBAL', 'Global'),
    ]

    nome = models.CharField(
        max_length=200,
        verbose_name='Nome do item'
    )
    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='itens',
        verbose_name='Categoria'
    )
    almoxarifado = models.ForeignKey(
        Almoxarifado,
        on_delete=models.PROTECT,
        related_name='itens',
        verbose_name='Almoxarifado'
    )
    unidade_medida = models.CharField(
        max_length=2,
        choices=UNIDADES,
        default='un',
        verbose_name='Unidade de medida'
    )
    quantidade_atual = models.IntegerField(
        default=0,
        verbose_name='Quantidade atual'
    )
    quantidade_minima = models.IntegerField(
        default=0,
        verbose_name='Quantidade mínima',
        help_text='Abaixo desse valor, o item será marcado como estoque baixo'
    )
    codigo_interno = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        verbose_name='Código interno',
        help_text='Gerado automaticamente'
    )
    localizacao_fisica = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Localização física',
        help_text='Ex: Prateleira B, Coluna 3'
    )
    data_cadastro = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de cadastro'
    )
        # Rastreabilidade e controle de qualidade
    lote = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Lote',
        help_text='Número do lote de fabricação'
    )
    data_fabricacao = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de fabricação'
    )
    data_validade = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de validade',
        help_text='Para reagentes e materiais perecíveis'
    )

    # Controle patrimonial
    codigo_patrimonio = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Código de patrimônio',
        help_text='Número de tombamento patrimonial'
    )
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor unitário (R$)',
        help_text='Valor de aquisição por unidade'
    )

    # Fornecedor padrão do item
    fornecedor = models.ForeignKey(
        'Fornecedor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='itens',
        verbose_name='Fornecedor padrão'
    )

    # ─── Classificação patrimonial (NOVO) ───────────────────────
    tipo_material = models.CharField(
        max_length=15, choices=TIPO_MATERIAL_CHOICES, default='CONSUMO',
        verbose_name='Tipo de material',
        help_text='Material de Consumo (uso/desgaste) ou Bem Permanente (durável)'
    )

    # ─── Empenho (NOVO) ─────────────────────────────────────────
    numero_empenho = models.CharField(
        max_length=50, blank=True, verbose_name='Número do empenho',
        help_text='Ex: 2024NE000123'
    )
    tipo_empenho = models.CharField(
        max_length=15, choices=TIPO_EMPENHO_CHOICES, blank=True,
        verbose_name='Tipo de empenho'
    )

    # ─── Processo SEI (NOVO) ────────────────────────────────────
    processo_sei = models.CharField(
        max_length=50, blank=True, verbose_name='Processo SEI',
        help_text='Número do processo no SEI/UFF (ex: 23069.000123/2024-12)'
    )

    # ─── Nota fiscal (NOVO) ─────────────────────────────────────
    nf_numero = models.CharField(max_length=20, blank=True, verbose_name='Número da NF')
    nf_serie = models.CharField(max_length=10, blank=True, verbose_name='Série da NF')
    nf_data_emissao = models.DateField(null=True, blank=True, verbose_name='Data de emissão da NF')
    nf_data_entrada = models.DateField(
        null=True, blank=True, verbose_name='Data de entrada (recebimento)',
        help_text='Data em que o material foi recebido no almoxarifado'
    )
    nf_valor = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name='Valor total da NF (R$)'
    )

    # Documentação
    anexo = models.FileField(
        upload_to='itens/anexos/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Anexo',
        help_text='Nota fiscal, manual, FISPQ, foto do item (PDF ou imagem)'
    )

    ultima_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name='Última atualização'
    )

    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Itens'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} [{self.codigo_interno}]'

    @property
    def estoque_baixo(self):
        """Retorna True se a quantidade atual estiver abaixo do mínimo."""
        return self.quantidade_atual < self.quantidade_minima

    @property
    def validade_vencida(self):
        """Retorna True se a data de validade já passou."""
        if self.data_validade:
            from django.utils import timezone
            return self.data_validade < timezone.now().date()
        return False

    @property
    def validade_proxima_vencer(self):
        """Retorna True se a validade está a menos de 30 dias."""
        if self.data_validade:
            from django.utils import timezone
            import datetime
            limite = timezone.now().date() + datetime.timedelta(days=30)
            return self.data_validade <= limite and not self.validade_vencida
        return False

    @property
    def get_unidade_display_curto(self):
        """Retorna a sigla da unidade de medida."""
        return self.unidade_medida

    @property
    def eh_permanente(self):
        """True se for bem permanente (tombamento obrigatório)."""
        return self.tipo_material == 'PERMANENTE'

    def gerar_codigo_interno(self):
        """
        Gera um código interno único no formato:
        ALM<id_almoxarifado>-<4 primeiros chars do UUID>
        Exemplo: ALM1-A3F2
        """
        prefixo = f'ALM{self.almoxarifado_id}-'
        sufixo = str(uuid.uuid4()).upper()[:4]
        return f'{prefixo}{sufixo}'

    def save(self, *args, **kwargs):
        # Gerar código interno apenas na criação do item
        if not self.codigo_interno:
            codigo = self.gerar_codigo_interno()
            # Garantir unicidade (improvável colisão, mas seguro)
            while Item.objects.filter(codigo_interno=codigo).exists():
                codigo = self.gerar_codigo_interno()
            self.codigo_interno = codigo
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# MOVIMENTAÇÃO
# ─────────────────────────────────────────────────────────────────────────────

class Movimentacao(models.Model):
    """
    Registro de movimentação de estoque.

    Lógica automática no save():
    - ENTRADA:      quantidade_atual += quantidade
    - SAIDA:        quantidade_atual -= quantidade
    - AJUSTE:       quantidade_atual = quantidade (valor absoluto informado)
    - TRANSFERENCIA: debita do almoxarifado de origem e
                     localiza o item correspondente no destino e credita.
                     Se o item não existir no destino, lança ValidationError.

    Os campos quantidade_anterior, quantidade_posterior e almoxarifado
    são preenchidos automaticamente.
    """

    TIPO_CHOICES = [
        ('ENTRADA',      'Entrada'),
        ('SAIDA',        'Saída'),
        ('DESCARTE',     'Descarte'),
        ('AJUSTE',       'Ajuste'),
        ('TRANSFERENCIA','Transferência'),
    ]

    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        related_name='movimentacoes',
        verbose_name='Item'
    )
    almoxarifado = models.ForeignKey(
        Almoxarifado,
        on_delete=models.PROTECT,
        related_name='movimentacoes',
        verbose_name='Almoxarifado',
        help_text='Preenchido automaticamente a partir do item'
    )
    tipo = models.CharField(
        max_length=15,
        choices=TIPO_CHOICES,
        verbose_name='Tipo de movimentação'
    )
    quantidade = models.PositiveIntegerField(
        verbose_name='Quantidade'
    )
    quantidade_anterior = models.IntegerField(
        verbose_name='Quantidade anterior',
        editable=False
    )
    quantidade_posterior = models.IntegerField(
        verbose_name='Quantidade posterior',
        editable=False
    )
    responsavel = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='movimentacoes',
        verbose_name='Responsável pelo registro'
    )
    # destino_origem = models.CharField(
    #     max_length=200,
    #     blank=True,
    #     verbose_name='Destino / Origem',
    #     help_text='Para quem saiu o material ou de onde veio'
    # )
    solicitante_nome = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Nome do solicitante',
        help_text='Para quem foi destinado (em caso de saída)'
    )
    solicitante_departamento = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Departamento',
        help_text='Ex: Geologia, Análise Geoambiental, Geografia'
    )
    almoxarifado_destino = models.ForeignKey(
        Almoxarifado,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='transferencias_recebidas',
        verbose_name='Almoxarifado de destino',
        help_text='Usado apenas em transferências'
    )
    # fornecedor = models.ForeignKey(
    #     Fornecedor,
    #     on_delete=models.PROTECT,
    #     null=True,
    #     blank=True,
    #     related_name='movimentacoes',
    #     verbose_name='Fornecedor',
    #     help_text='Usado apenas em entradas'
    # )
    observacao = models.TextField(
        blank=True,
        verbose_name='Observação'
    )
    data_movimentacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data da movimentação'
    )

    class Meta:
        verbose_name = 'Movimentação'
        verbose_name_plural = 'Movimentações'
        ordering = ['-data_movimentacao']

    def __str__(self):
        destino = self.solicitante_nome or self.solicitante_departamento or '—'
        return (
            f'{self.get_tipo_display()} — {self.item.nome} '
            f'({self.quantidade} {self.item.unidade_medida}) '
            f'para {destino} em {self.data_movimentacao.strftime("%d/%m/%Y %H:%M")}'
        )

    def clean(self):
        """Validações de negócio antes de salvar."""
        # Saída e Descarte não podem deixar estoque negativo
        if self.tipo in ('SAIDA', 'DESCARTE'):
            if self.quantidade > self.item.quantidade_atual:
                raise ValidationError(
                    f'Quantidade insuficiente em estoque. '
                    f'Disponível: {self.item.quantidade_atual} '
                    f'{self.item.get_unidade_medida_display()}'
                )

        # Transferência exige almoxarifado de destino
        if self.tipo == 'TRANSFERENCIA':
            if not self.almoxarifado_destino:
                raise ValidationError(
                    'Informe o almoxarifado de destino para a transferência.'
                )
            if self.almoxarifado_destino == self.item.almoxarifado:
                raise ValidationError(
                    'O almoxarifado de destino deve ser diferente do de origem.'
                )
            if self.quantidade > self.item.quantidade_atual:
                raise ValidationError(
                    f'Quantidade insuficiente para transferência. '
                    f'Disponível: {self.item.quantidade_atual} '
                    f'{self.item.get_unidade_medida_display()}'
                )


    def save(self, *args, **kwargs):
        """
        Ao salvar uma movimentação:
        1. Preenche o almoxarifado a partir do item
        2. Registra quantidade_anterior
        3. Calcula e aplica a quantidade_posterior no item
        4. Em transferência, também atualiza o item no almoxarifado de destino
        Apenas para novas movimentações (pk is None) — movimentações não são editadas.
        """
        if self.pk is None:
            # Preencher almoxarifado automaticamente
            self.almoxarifado = self.item.almoxarifado

            # Registrar quantidade antes da operação
            self.quantidade_anterior = self.item.quantidade_atual

            # Calcular nova quantidade conforme o tipo
            if self.tipo == 'ENTRADA':
                nova_qtd = self.item.quantidade_atual + self.quantidade

            elif self.tipo in ('SAIDA', 'DESCARTE'):
                            nova_qtd = self.item.quantidade_atual - self.quantidade

            elif self.tipo == 'AJUSTE':
                # No ajuste, a quantidade informada é o novo valor absoluto
                nova_qtd = self.quantidade

            elif self.tipo == 'TRANSFERENCIA':
                # Debitar do item de origem
                nova_qtd = self.item.quantidade_atual - self.quantidade

                # Buscar ou criar automaticamente o item no almoxarifado de destino
                item_destino, criado = Item.objects.get_or_create(
                    nome=self.item.nome,
                    almoxarifado=self.almoxarifado_destino,
                    defaults={
                        'descricao': self.item.descricao,
                        'categoria': self.item.categoria,
                        'unidade_medida': self.item.unidade_medida,
                        'tipo_material': self.item.tipo_material,
                        'quantidade_atual': 0,
                        'quantidade_minima': self.item.quantidade_minima,
                        'localizacao_fisica': '',
                        # Copiar rastreabilidade
                        'lote': self.item.lote,
                        'data_fabricacao': self.item.data_fabricacao,
                        'data_validade': self.item.data_validade,
                        # Não duplicar patrimônio (cada item tem seu próprio tombamento)
                        'codigo_patrimonio': '',
                        'valor': self.item.valor,
                        'fornecedor': self.item.fornecedor,
                    }
                )

                # Creditar no item de destino
                item_destino.quantidade_atual += self.quantidade
                item_destino.save()

            else:
                nova_qtd = self.item.quantidade_atual

            # Registrar quantidade após a operação
            self.quantidade_posterior = nova_qtd

            # Atualizar o item de origem
            self.item.quantidade_atual = nova_qtd
            self.item.save()

        super().save(*args, **kwargs)
