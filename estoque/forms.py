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
            'unidade_medida', 'quantidade_atual', 'quantidade_minima',
            'localizacao_fisica'
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'localizacao_fisica': forms.TextInput(attrs={'placeholder': 'Ex: Prateleira B, Coluna 3'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['almoxarifado'].queryset = Almoxarifado.objects.filter(ativo=True)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('nome',          css_class='col-md-8'),
                Column('unidade_medida',css_class='col-md-4'),
            ),
            Row(
                Column('categoria',     css_class='col-md-6'),
                Column('almoxarifado',  css_class='col-md-6'),
            ),
            Row(
                Column('quantidade_atual',   css_class='col-md-4'),
                Column('quantidade_minima',  css_class='col-md-4'),
                Column('localizacao_fisica', css_class='col-md-4'),
            ),
            'descricao',
            Div(
                Submit('submit', 'Salvar', css_class='btn btn-primary'),
                HTML('<a href="{% url \'estoque:item_lista\' %}" class="btn btn-secondary ms-2">Cancelar</a>'),
                css_class='d-flex mt-3'
            )
        )


class MovimentacaoForm(forms.ModelForm):
    class Meta:
        model  = Movimentacao
        fields = [
            'item', 'tipo', 'quantidade',
            'destino_origem', 'almoxarifado_destino',
            'fornecedor', 'observacao'
        ]
        widgets = {
            'observacao': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        # Permite pré-selecionar item via querystring (?item=pk)
        item_pk = kwargs.pop('item_pk', None)
        super().__init__(*args, **kwargs)

        if item_pk:
            self.fields['item'].initial = item_pk

        self.fields['almoxarifado_destino'].queryset = Almoxarifado.objects.filter(ativo=True)
        self.fields['almoxarifado_destino'].required  = False
        self.fields['fornecedor'].required = False

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('item',       css_class='col-md-8'),
                Column('tipo',       css_class='col-md-4'),
            ),
            Row(
                Column('quantidade',          css_class='col-md-4'),
                Column('destino_origem',      css_class='col-md-8'),
            ),
            Row(
                Column('almoxarifado_destino',css_class='col-md-6'),
                Column('fornecedor',          css_class='col-md-6'),
            ),
            'observacao',
            Div(
                Submit('submit', 'Registrar Movimentação', css_class='btn btn-primary'),
                HTML('<a href="{% url \'estoque:movimentacao_lista\' %}" class="btn btn-secondary ms-2">Cancelar</a>'),
                css_class='d-flex mt-3'
            )
        )

    def clean(self):
        """Delega a validação de negócio ao model."""
        cleaned = super().clean()
        # Instância temporária para chamar o clean() do model
        if cleaned.get('item') and cleaned.get('tipo') and cleaned.get('quantidade'):
            obj = Movimentacao(
                item=cleaned['item'],
                tipo=cleaned['tipo'],
                quantidade=cleaned['quantidade'],
                almoxarifado_destino=cleaned.get('almoxarifado_destino'),
            )
            try:
                obj.clean()
            except Exception as e:
                raise forms.ValidationError(str(e))
        return cleaned

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
