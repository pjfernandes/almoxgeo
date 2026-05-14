"""
Formulários do sistema Sistema de Gestão de Estoque.
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, Row, Column, Div, HTML
from .models import Almoxarifado, Categoria, Fornecedor, Item, Movimentacao, Usuario


class LoginForm(AuthenticationForm):
    """Formulário de login customizado com crispy-forms."""

    username = forms.CharField(
        label='Usuário',
        widget=forms.TextInput(attrs={'placeholder': 'Usuário', 'autofocus': True})
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'placeholder': 'Senha'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('username', css_class='form-control mb-3'),
            Field('password', css_class='form-control mb-3'),
            Submit('submit', 'Entrar', css_class='btn btn-primary w-100 py-2')
        )

class AlmoxarifadoForm(forms.ModelForm):
    class Meta:
        model  = Almoxarifado
        fields = ['nome', 'localizacao', 'responsavel', 'descricao', 'ativo']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apenas usuários ativos podem ser responsáveis
        self.fields['responsavel'].queryset = Usuario.objects.filter(is_ativo=True)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('nome',        css_class='col-md-6'),
                Column('localizacao', css_class='col-md-6'),
            ),
            Row(
                Column('responsavel', css_class='col-md-6'),
                Column('ativo',       css_class='col-md-6 d-flex align-items-end pb-2'),
            ),
            'descricao',
            Div(
                Submit('submit', 'Salvar', css_class='btn btn-primary'),
                HTML('<a href="{% url \'estoque:almoxarifado_lista\' %}" class="btn btn-secondary ms-2">Cancelar</a>'),
                css_class='d-flex mt-3'
            )
        )


class CategoriaForm(forms.ModelForm):
    class Meta:
        model  = Categoria
        fields = ['nome', 'icone', 'descricao']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'icone': forms.TextInput(attrs={'placeholder': 'ex: box-seam, printer, pencil'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('nome',  css_class='col-md-8'),
                Column('icone', css_class='col-md-4'),
            ),
            'descricao',
            Div(
                Submit('submit', 'Salvar', css_class='btn btn-primary'),
                HTML('<a href="{% url \'estoque:categoria_lista\' %}" class="btn btn-secondary ms-2">Cancelar</a>'),
                css_class='d-flex mt-3'
            )
        )


class FornecedorForm(forms.ModelForm):
    class Meta:
        model  = Fornecedor
        fields = ['nome', 'cnpj', 'contato', 'observacao']
        widgets = {
            'observacao': forms.Textarea(attrs={'rows': 3}),
            'cnpj':    forms.TextInput(attrs={'placeholder': 'XX.XXX.XXX/XXXX-XX'}),
            'contato': forms.TextInput(attrs={'placeholder': 'Telefone ou e-mail'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'nome',
            Row(
                Column('cnpj',    css_class='col-md-6'),
                Column('contato', css_class='col-md-6'),
            ),
            'observacao',
            Div(
                Submit('submit', 'Salvar', css_class='btn btn-primary'),
                HTML('<a href="{% url \'estoque:fornecedor_lista\' %}" class="btn btn-secondary ms-2">Cancelar</a>'),
                css_class='d-flex mt-3'
            )
        )

class ItemForm(forms.ModelForm):
    class Meta:
        model  = Item
        fields = [
            'nome', 'descricao', 'categoria', 'almoxarifado',
            'unidade_medida', 'tipo_material',
            'quantidade_atual', 'quantidade_minima', 'localizacao_fisica',
            'lote', 'data_fabricacao', 'data_validade',
            'codigo_patrimonio', 'valor', 'fornecedor',
            'numero_empenho', 'tipo_empenho',
            'processo_sei',
            'nf_numero', 'nf_serie', 'nf_data_emissao', 'nf_data_entrada', 'nf_valor',
            'anexo'
        ]
        help_texts = {
            'quantidade_atual': 'Estoque inicial. Se preenchido, será registrada automaticamente uma ENTRADA no histórico do item.',
            'quantidade_minima': 'Quando o estoque ficar abaixo deste valor, o sistema emitirá alerta.',
            'tipo_material': 'Material de Consumo (papel, caneta, reagente) ou Bem Permanente (microscópio, GPS).',
        }

        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'localizacao_fisica': forms.TextInput(attrs={'placeholder': 'Ex: Prateleira B, Coluna 3'}),
            'data_fabricacao': forms.DateInput(attrs={'type': 'date'}),
            'data_validade': forms.DateInput(attrs={'type': 'date'}),
            'codigo_patrimonio': forms.TextInput(attrs={'placeholder': 'Ex: 2024.001.123'}),
            'lote': forms.TextInput(attrs={'placeholder': 'Ex: LOTE-2024-A123'}),
              'numero_empenho': forms.TextInput(attrs={'placeholder': 'Ex: 2024NE000123'}),
            'processo_sei': forms.TextInput(attrs={'placeholder': 'Ex: 23069.000123/2024-12'}),
            'nf_numero': forms.TextInput(attrs={'placeholder': 'Ex: 123456'}),
            'nf_serie': forms.TextInput(attrs={'placeholder': 'Ex: 1'}),
            'nf_data_emissao': forms.DateInput(attrs={'type': 'date'}),
            'nf_data_entrada': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['almoxarifado'].queryset = Almoxarifado.objects.filter(ativo=True)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            # Identificação
            HTML('<h6 class="text-muted mb-3"><i class="bi bi-info-circle me-2"></i>Identificação</h6>'),
            Row(
                Column('nome',          css_class='col-md-8'),
                Column('unidade_medida',css_class='col-md-4'),
            ),
            Row(
                Column('categoria',     css_class='col-md-6'),
                Column('almoxarifado',  css_class='col-md-6'),
            ),
            Row(
                Column('tipo_material', css_class='col-md-12'),
            ),
            'descricao',

            # Estoque
            HTML('<hr class="my-3"><h6 class="text-muted mb-3"><i class="bi bi-box-seam me-2"></i>Estoque e Localização</h6>'),
            Row(
                Column('quantidade_atual',   css_class='col-md-4'),
                Column('quantidade_minima',  css_class='col-md-4'),
                Column('localizacao_fisica', css_class='col-md-4'),
            ),

            # Rastreabilidade
            HTML('<hr class="my-3"><h6 class="text-muted mb-3"><i class="bi bi-clipboard-check me-2"></i>Rastreabilidade e Qualidade</h6>'),
            Row(
                Column('lote',            css_class='col-md-4'),
                Column('data_fabricacao', css_class='col-md-4'),
                Column('data_validade',   css_class='col-md-4'),
            ),

            # Patrimonial
            HTML('<hr class="my-3"><h6 class="text-muted mb-3"><i class="bi bi-bank me-2"></i>Controle Patrimonial e Financeiro</h6>'),
            Row(
                Column('codigo_patrimonio', css_class='col-md-4'),
                Column('valor',             css_class='col-md-4'),
                Column('fornecedor',        css_class='col-md-4'),
            ),

            # Empenho
            HTML('<hr class="my-3"><h6 class="text-muted mb-3"><i class="bi bi-file-earmark-text me-2"></i>Empenho</h6>'),
            Row(
                Column('numero_empenho', css_class='col-md-6'),
                Column('tipo_empenho',   css_class='col-md-6'),
            ),

            # SEI
            HTML('<hr class="my-3"><h6 class="text-muted mb-3"><i class="bi bi-folder me-2"></i>Processo SEI</h6>'),
            'processo_sei',

            # Nota fiscal
            HTML('<hr class="my-3"><h6 class="text-muted mb-3"><i class="bi bi-receipt me-2"></i>Nota Fiscal</h6>'),
            Row(
                Column('nf_numero',       css_class='col-md-4'),
                Column('nf_serie',        css_class='col-md-4'),
                Column('nf_valor',        css_class='col-md-4'),
            ),
            Row(
                Column('nf_data_emissao', css_class='col-md-6'),
                Column('nf_data_entrada', css_class='col-md-6'),
            ),

            # Anexo
            HTML('<hr class="my-3"><h6 class="text-muted mb-3"><i class="bi bi-paperclip me-2"></i>Documentação</h6>'),
            'anexo',
            HTML('<small class="text-muted">Aceita PDF, imagens (JPG, PNG), documentos. Máx 10MB.</small>'),

            Div(
                Submit('submit', 'Salvar', css_class='btn btn-primary'),
                HTML('<a href="{% url \'estoque:item_lista\' %}" class="btn btn-secondary ms-2">Cancelar</a>'),
                css_class='d-flex mt-3'
            )
        )

class MovimentacaoForm(forms.ModelForm):
    class Meta:
        model = Movimentacao
        fields = [
            'tipo',
            'item',
            'almoxarifado',
            'quantidade',
            'almoxarifado_destino',
            'solicitante_nome',
            'solicitante_departamento',
            'observacao',
        ]
        widgets = {
            'observacao': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {
            'quantidade': 'Para AJUSTE, informe a quantidade total desejada (não a diferença)',
        }

    def __init__(self, *args, **kwargs):
        item_pk = kwargs.pop('item_pk', None)
        tipo_inicial = kwargs.pop('tipo_inicial', None)
        super().__init__(*args, **kwargs)

        # Se vier de um item específico, pré-selecionar e travar o item
        item_preselecionado = None
        if item_pk:
            try:
                item_preselecionado = Item.objects.select_related('almoxarifado').get(pk=item_pk)
                self.fields['item'].initial = item_preselecionado
                self.fields['almoxarifado'].initial = item_preselecionado.almoxarifado
                # Restringir queryset para mostrar apenas esse item
                self.fields['item'].queryset = Item.objects.filter(pk=item_pk)
            except Item.DoesNotExist:
                pass

        # Pré-selecionar tipo se vier na URL (ex: ?tipo=ENTRADA)
        if tipo_inicial and tipo_inicial in dict(Movimentacao.TIPO_CHOICES):
            self.fields['tipo'].initial = tipo_inicial

        # Configurar layout crispy
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(
                # Seção: Tipo de Movimentação (destaque visual)
                Div(
                    HTML('<h5 class="border-bottom pb-2 mb-3"><i class="bi bi-arrow-left-right me-2"></i>Tipo de Movimentação</h5>'),
                    Field('tipo', css_class='form-select-lg', wrapper_class='mb-4'),
                    css_class='mb-4'
                ),

                # Seção: Item e Almoxarifado
                Div(
                    HTML('<h6 class="text-muted mb-3"><i class="bi bi-box-seam me-2"></i>Item e Localização</h6>'),
                    Row(
                        Column('item', css_class='col-md-8'),
                        Column('almoxarifado', css_class='col-md-4'),
                    ),
                    css_class='mb-4'
                ),

                # Quantidade
                Div(
                    HTML('<h6 class="text-muted mb-3"><i class="bi bi-123 me-2"></i>Quantidade</h6>'),
                    Field('quantidade', css_class='form-control-lg'),
                    css_class='mb-4'
                ),

                # Campos condicionais (controlados por JavaScript)
                # SAÍDA: Solicitante
                Div(
                    HTML('<h6 class="text-muted mb-3"><i class="bi bi-person me-2"></i>Quem está retirando?</h6>'),
                    Row(
                        Column('solicitante_nome', css_class='col-md-6'),
                        Column('solicitante_departamento', css_class='col-md-6'),
                    ),
                    css_class='mb-4 campo-saida',
                    css_id='camposSaida',
                    style='display:none;'
                ),

                # TRANSFERÊNCIA: Destino
                Div(
                    HTML('<h6 class="text-muted mb-3"><i class="bi bi-arrow-right-circle me-2"></i>Para onde transferir?</h6>'),
                    Field('almoxarifado_destino'),
                    css_class='mb-4 campo-transferencia',
                    css_id='camposTransferencia',
                    style='display:none;'
                ),

                # Observações (sempre visível)
                Div(
                    HTML('<h6 class="text-muted mb-3"><i class="bi bi-chat-left-text me-2"></i>Observações (opcional)</h6>'),
                    Field('observacao', placeholder='Ex: Material para aula prática de dia 15/05'),
                    css_class='mb-4'
                ),

                # Botões
                Div(
                    Submit('submit', 'Registrar Movimentação', css_class='btn btn-primary btn-lg'),
                    HTML('<a href="{% url \'estoque:movimentacao_lista\' %}" class="btn btn-outline-secondary btn-lg ms-2">Cancelar</a>'),
                    css_class='d-flex gap-2'
                ),
            )
        )

        # Placeholders e labels melhorados
        self.fields['tipo'].label = 'Selecione o tipo de movimentação'
        self.fields['item'].label = 'Item'
        self.fields['item'].help_text = 'Digite para buscar'
        self.fields['almoxarifado'].label = 'Almoxarifado de origem'
        self.fields['quantidade'].label = 'Quantidade'
        self.fields['almoxarifado_destino'].label = 'Almoxarifado de destino'
        self.fields['solicitante_nome'].label = 'Nome completo'
        self.fields['solicitante_nome'].required = False
        self.fields['solicitante_departamento'].label = 'Departamento/Setor'
        self.fields['solicitante_departamento'].required = False
        self.fields['observacao'].label = 'Observações'
        self.fields['observacao'].required = False

        # Placeholders
        self.fields['tipo'].widget.attrs['placeholder'] = 'Escolha: Entrada, Saída, Ajuste ou Transferência'
        self.fields['solicitante_nome'].widget.attrs['placeholder'] = 'Ex: João Silva'
        self.fields['solicitante_departamento'].widget.attrs['placeholder'] = 'Ex: Laboratório de Geoquímica'
        self.fields['quantidade'].widget.attrs['placeholder'] = 'Ex: 10'

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        quantidade = cleaned_data.get('quantidade')
        item = cleaned_data.get('item')
        almoxarifado_destino = cleaned_data.get('almoxarifado_destino')
        almoxarifado = cleaned_data.get('almoxarifado')

        # Validações por tipo
        if tipo == 'SAIDA':
            if item and quantidade and item.quantidade_atual < quantidade:
                raise forms.ValidationError(
                    f'Estoque insuficiente! Disponível: {item.quantidade_atual} {item.get_unidade_medida_display()}'
                )

        if tipo == 'TRANSFERENCIA':
            if not almoxarifado_destino:
                raise forms.ValidationError('Para transferência, selecione o almoxarifado de destino.')
            if almoxarifado_destino == almoxarifado:
                raise forms.ValidationError('Almoxarifado de destino deve ser diferente da origem.')
            if item and quantidade and item.quantidade_atual < quantidade:
                raise forms.ValidationError(
                    f'Estoque insuficiente para transferência! Disponível: {item.quantidade_atual} {item.get_unidade_medida_display()}'
                )

        return cleaned_data

from django.contrib.auth.forms import UserCreationForm


class UsuarioForm(forms.ModelForm):
    """Formulário para criar/editar usuários (apenas admin)."""
    password1 = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput,
        required=False,
        help_text='Deixe em branco para manter a senha atual (na edição).'
    )
    password2 = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput,
        required=False
    )

    class Meta:
        model  = Usuario
        fields = ['username', 'nome_completo', 'matricula', 'email', 'cargo', 'is_ativo', 'is_staff']

    def __init__(self, *args, **kwargs):
        self.criando = kwargs.pop('criando', False)
        super().__init__(*args, **kwargs)
        if self.criando:
            self.fields['password1'].required = True
            self.fields['password2'].required = True
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('nome_completo', css_class='col-md-8'),
                Column('matricula',    css_class='col-md-4'),
            ),
            Row(
                Column('username', css_class='col-md-6'),
                Column('email',    css_class='col-md-6'),
            ),
            Row(
                Column('cargo',    css_class='col-md-6'),
                Column(
                    'is_ativo',
                    'is_staff',
                    css_class='col-md-6'
                ),
            ),
            Row(
                Column('password1', css_class='col-md-6'),
                Column('password2', css_class='col-md-6'),
            ),
            Div(
                Submit('submit', 'Salvar', css_class='btn btn-primary'),
                HTML('<a href="{% url \'estoque:usuario_lista\' %}" class="btn btn-secondary ms-2">Cancelar</a>'),
                css_class='d-flex mt-3'
            )
        )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError('As senhas não coincidem.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        p1 = self.cleaned_data.get('password1')
        if p1:
            user.set_password(p1)
        if commit:
            user.save()
        return user
