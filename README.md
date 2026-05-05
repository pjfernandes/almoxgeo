# 📦 Sistema de Gestão de Estoque

Sistema web de gestão de estoque desenvolvido em Django para o Instituto de Geociências da Universidade Federal Fluminense (IGeo/UFF).

## ✨ Funcionalidades

- **Gestão de Itens** - Cadastro com QR codes e etiquetas para impressão
- **Múltiplos Almoxarifados** - Controle de estoque por localização
- **Movimentações** - Entradas, saídas, ajustes e transferências automáticas
- **Dashboard** - Gráficos e estatísticas em tempo real
- **Alertas** - Estoque baixo, itens vencidos e próximos a vencer
- **Relatórios** - Exportação em CSV e PDF
- **Busca Global** - Atalho `Ctrl+K` estilo Notion
- **Modo Escuro** - Interface adaptável
- **Responsivo** - Funciona em desktop, tablet e celular

## 🛠️ Tecnologias

- **Backend**: Python 3.12, Django 5.0
- **Frontend**: Bootstrap 5.3, Chart.js, Bootstrap Icons
- **Banco de Dados**: SQLite (dev) / PostgreSQL (produção)
- **Outros**: ReportLab (PDF), qrcode, django-filter, crispy-forms

## 🚀 Instalação

### Pré-requisitos
- Python 3.12+
- pip
- Git

### Passos

```bash
# 1. Clonar repositório
git clone https://github.com/pjfernandes/almoxgeo.git
cd almoxgeo

# 2. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar .env
cp .env.example .env
# Editar .env com suas configurações

# 5. Aplicar migrações
python manage.py migrate

# 6. Criar superusuário
python manage.py createsuperuser

# 7. (Opcional) Popular dados de demonstração
python manage.py setup_demo

# 8. Rodar servidor
python manage.py runserver
```

Acesse: `http://localhost:8000`

## 📚 Como Usar

1. **Login** com usuário admin
2. Cadastrar **categorias**, **fornecedores** e **almoxarifados**
3. Cadastrar **itens** no estoque
4. Registrar **movimentações** (entradas, saídas, transferências)
5. Acompanhar pelo **dashboard** e gerar **relatórios**

## 📁 Estrutura

```
almoxgeo/
├── almoxgeo/          # Configurações Django
├── estoque/           # App principal
│   ├── models.py      # Modelos de dados
│   ├── views.py       # Lógica das páginas
│   ├── forms.py       # Formulários
│   ├── filters.py     # Filtros de busca
│   ├── urls.py        # Rotas
│   └── templates/     # HTML
├── static/            # CSS, JS, imagens
├── media/             # Uploads de usuários
└── requirements.txt
```

## 🔑 Modelos Principais

- **Usuario** - Servidores com matrícula SIAPE
- **Almoxarifado** - Localizações físicas de estoque
- **Categoria** - Classificação de itens
- **Fornecedor** - Cadastro de fornecedores
- **Item** - Materiais em estoque
- **Movimentacao** - Histórico de entradas/saídas

## 🚢 Deploy em Produção

```bash
# Configurar ambiente
DEBUG=False
USE_SQLITE=False
SECRET_KEY=chave-segura
ALLOWED_HOSTS=seu-dominio.com

# Coletar estáticos
python manage.py collectstatic --noinput

# Iniciar com Gunicorn
gunicorn almoxgeo.wsgi --bind 0.0.0.0:8000
```

Recomendado: **PostgreSQL + Gunicorn + Nginx**

## 📝 Licença

MIT License

## 👨‍💻 Autor

**Pedro José Farias Fernandes** - [@pjfernandes](https://github.com/pjfernandes)

---

Desenvolvido para o **Instituto de Geociências - UFF**
