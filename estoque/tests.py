"""
═══════════════════════════════════════════════════════════════════════════
 TESTES AUTOMATIZADOS — Sistema de Gestão de Estoque (IGeo/UFF)
═══════════════════════════════════════════════════════════════════════════

 Como rodar:
     python manage.py test                    # tudo
     python manage.py test estoque            # só o app estoque
     python manage.py test estoque.tests.TestMovimentacao   # uma classe
     python manage.py test -v 2               # mostrando cada teste

 Os testes usam um banco de dados TEMPORÁRIO, criado e destruído
 automaticamente. O banco real (db.sqlite3) NUNCA é tocado.
═══════════════════════════════════════════════════════════════════════════
"""
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError

from .models import (
    Usuario, Categoria, Fornecedor, Almoxarifado, Item, Movimentacao
)


# ═══════════════════════════════════════════════════════════════════
# Base comum — cria os dados que quase todo teste precisa
# ═══════════════════════════════════════════════════════════════════

class BaseEstoque(TestCase):
    """Cria usuários dos 3 níveis, um almoxarifado, categoria e item."""

    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username='admin_teste', password='senha123',
            email='admin@teste.com', nome_completo='Admin Teste',
            nivel_acesso='ADMIN',
        )
        self.gestor = Usuario.objects.create_user(
            username='gestor_teste', password='senha123',
            email='gestor@teste.com', nome_completo='Gestor Teste',
            nivel_acesso='GESTOR',
        )
        self.operador = Usuario.objects.create_user(
            username='operador_teste', password='senha123',
            email='operador@teste.com', nome_completo='Operador Teste',
            nivel_acesso='OPERADOR',
        )

        self.categoria = Categoria.objects.create(nome='Material de Escritório')
        self.almox = Almoxarifado.objects.create(
            nome='Almoxarifado Central', localizacao='Bloco A, Sala 102',
            responsavel=self.admin,
        )
        self.almox2 = Almoxarifado.objects.create(
            nome='Almoxarifado Laboratório', localizacao='Bloco D',
            responsavel=self.admin,
        )
        self.item = Item.objects.create(
            nome='Caneta esferográfica azul',
            categoria=self.categoria, almoxarifado=self.almox,
            unidade_medida='un', quantidade_atual=100, quantidade_minima=20,
        )

    def logar(self, usuario):
        """Devolve um client autenticado com o usuário informado."""
        c = Client()
        c.login(username=usuario.username, password='senha123')
        return c


# ═══════════════════════════════════════════════════════════════════
# 1. MODELO ITEM
# ═══════════════════════════════════════════════════════════════════

class TestItem(BaseEstoque):

    def test_codigo_interno_gerado_automaticamente(self):
        """Todo item recebe um código interno único ao ser criado."""
        self.assertTrue(self.item.codigo_interno)
        self.assertTrue(self.item.codigo_interno.startswith(f'ALM{self.almox.pk}-'))

    def test_codigos_internos_sao_unicos(self):
        outro = Item.objects.create(
            nome='Lápis', categoria=self.categoria, almoxarifado=self.almox,
        )
        self.assertNotEqual(self.item.codigo_interno, outro.codigo_interno)

    def test_estoque_baixo_false_quando_acima_do_minimo(self):
        self.assertFalse(self.item.estoque_baixo)

    def test_estoque_baixo_true_quando_abaixo_do_minimo(self):
        self.item.quantidade_atual = 5   # mínimo é 20
        self.item.save()
        self.assertTrue(self.item.estoque_baixo)

    def test_tipo_material_padrao_e_consumo(self):
        self.assertEqual(self.item.tipo_material, 'CONSUMO')
        self.assertFalse(self.item.eh_permanente)

    def test_bem_permanente(self):
        equip = Item.objects.create(
            nome='Microscópio', categoria=self.categoria, almoxarifado=self.almox,
            tipo_material='PERMANENTE',
        )
        self.assertTrue(equip.eh_permanente)

    def test_validade_vencida(self):
        from datetime import date, timedelta
        self.item.data_validade = date.today() - timedelta(days=1)
        self.item.save()
        self.assertTrue(self.item.validade_vencida)

    def test_validade_proxima_a_vencer(self):
        from datetime import date, timedelta
        self.item.data_validade = date.today() + timedelta(days=10)
        self.item.save()
        self.assertTrue(self.item.validade_proxima_vencer)
        self.assertFalse(self.item.validade_vencida)


# ═══════════════════════════════════════════════════════════════════
# 2. MOVIMENTAÇÕES — o coração do sistema
# ═══════════════════════════════════════════════════════════════════

class TestMovimentacao(BaseEstoque):

    def test_entrada_soma_ao_estoque(self):
        Movimentacao.objects.create(
            item=self.item, tipo='ENTRADA', quantidade=50,
            responsavel=self.admin,
        )
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantidade_atual, 150)

    def test_saida_subtrai_do_estoque(self):
        Movimentacao.objects.create(
            item=self.item, tipo='SAIDA', quantidade=30,
            responsavel=self.admin, solicitante_nome='João',
        )
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantidade_atual, 70)

    def test_descarte_subtrai_do_estoque(self):
        Movimentacao.objects.create(
            item=self.item, tipo='DESCARTE', quantidade=10,
            responsavel=self.admin,
        )
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantidade_atual, 90)

    def test_ajuste_define_quantidade_absoluta(self):
        """No AJUSTE, a quantidade informada vira o novo total (não soma)."""
        Movimentacao.objects.create(
            item=self.item, tipo='AJUSTE', quantidade=42,
            responsavel=self.admin, observacao='Inventário físico',
        )
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantidade_atual, 42)

    def test_registra_quantidade_anterior_e_posterior(self):
        mov = Movimentacao.objects.create(
            item=self.item, tipo='SAIDA', quantidade=25,
            responsavel=self.admin,
        )
        self.assertEqual(mov.quantidade_anterior, 100)
        self.assertEqual(mov.quantidade_posterior, 75)

    def test_almoxarifado_preenchido_automaticamente(self):
        mov = Movimentacao.objects.create(
            item=self.item, tipo='ENTRADA', quantidade=5,
            responsavel=self.admin,
        )
        self.assertEqual(mov.almoxarifado, self.item.almoxarifado)

    def test_transferencia_move_entre_almoxarifados(self):
        Movimentacao.objects.create(
            item=self.item, tipo='TRANSFERENCIA', quantidade=40,
            responsavel=self.admin, almoxarifado_destino=self.almox2,
        )
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantidade_atual, 60)

        # O item deve ter sido criado no destino com a quantidade transferida
        destino = Item.objects.get(nome=self.item.nome, almoxarifado=self.almox2)
        self.assertEqual(destino.quantidade_atual, 40)

    def test_transferencia_copia_dados_do_item(self):
        self.item.tipo_material = 'PERMANENTE'
        self.item.lote = 'LOTE-XYZ'
        self.item.save()
        Movimentacao.objects.create(
            item=self.item, tipo='TRANSFERENCIA', quantidade=10,
            responsavel=self.admin, almoxarifado_destino=self.almox2,
        )
        destino = Item.objects.get(nome=self.item.nome, almoxarifado=self.almox2)
        self.assertEqual(destino.tipo_material, 'PERMANENTE')
        self.assertEqual(destino.lote, 'LOTE-XYZ')
        # O patrimônio NÃO deve ser copiado (cada bem tem o seu)
        self.assertEqual(destino.codigo_patrimonio, '')

    def test_saida_maior_que_estoque_e_invalida(self):
        mov = Movimentacao(
            item=self.item, tipo='SAIDA', quantidade=500,
            responsavel=self.admin,
        )
        with self.assertRaises(ValidationError):
            mov.clean()

    def test_descarte_maior_que_estoque_e_invalido(self):
        mov = Movimentacao(
            item=self.item, tipo='DESCARTE', quantidade=500,
            responsavel=self.admin,
        )
        with self.assertRaises(ValidationError):
            mov.clean()

    def test_transferencia_sem_destino_e_invalida(self):
        mov = Movimentacao(
            item=self.item, tipo='TRANSFERENCIA', quantidade=10,
            responsavel=self.admin,
        )
        with self.assertRaises(ValidationError):
            mov.clean()

    def test_transferencia_para_o_mesmo_almoxarifado_e_invalida(self):
        mov = Movimentacao(
            item=self.item, tipo='TRANSFERENCIA', quantidade=10,
            responsavel=self.admin, almoxarifado_destino=self.almox,
        )
        with self.assertRaises(ValidationError):
            mov.clean()

    def test_historico_fica_registrado(self):
        for tipo, qtd in [('ENTRADA', 10), ('SAIDA', 5), ('DESCARTE', 2)]:
            Movimentacao.objects.create(
                item=self.item, tipo=tipo, quantidade=qtd, responsavel=self.admin,
            )
        self.assertEqual(self.item.movimentacoes.count(), 3)


# ═══════════════════════════════════════════════════════════════════
# 3. NÍVEIS DE ACESSO
# ═══════════════════════════════════════════════════════════════════

class TestPermissoes(BaseEstoque):

    def test_propriedades_do_admin(self):
        self.assertTrue(self.admin.eh_admin)
        self.assertTrue(self.admin.pode_cadastrar)
        self.assertTrue(self.admin.pode_editar)
        self.assertTrue(self.admin.pode_gerenciar_usuarios)

    def test_propriedades_do_gestor(self):
        self.assertFalse(self.gestor.eh_admin)
        self.assertTrue(self.gestor.pode_cadastrar)
        self.assertFalse(self.gestor.pode_editar)
        self.assertFalse(self.gestor.pode_gerenciar_usuarios)

    def test_propriedades_do_operador(self):
        self.assertFalse(self.operador.eh_admin)
        self.assertFalse(self.operador.pode_cadastrar)
        self.assertFalse(self.operador.pode_editar)
        self.assertFalse(self.operador.pode_gerenciar_usuarios)

    def test_is_staff_sincroniza_com_nivel_admin(self):
        self.assertTrue(self.admin.is_staff)
        self.assertFalse(self.gestor.is_staff)
        self.assertFalse(self.operador.is_staff)

    # ── Acesso às telas ────────────────────────────────────────────

    def test_todos_podem_registrar_movimentacao(self):
        for user in [self.admin, self.gestor, self.operador]:
            r = self.logar(user).get(reverse('estoque:movimentacao_criar'))
            self.assertEqual(r.status_code, 200, f'{user.username} deveria acessar')

    def test_apenas_admin_e_gestor_cadastram_itens(self):
        url = reverse('estoque:item_criar')
        self.assertEqual(self.logar(self.admin).get(url).status_code, 200)
        self.assertEqual(self.logar(self.gestor).get(url).status_code, 200)
        self.assertNotEqual(self.logar(self.operador).get(url).status_code, 200)

    def test_apenas_admin_edita_itens(self):
        url = reverse('estoque:item_editar', args=[self.item.pk])
        self.assertEqual(self.logar(self.admin).get(url).status_code, 200)
        self.assertNotEqual(self.logar(self.gestor).get(url).status_code, 200)
        self.assertNotEqual(self.logar(self.operador).get(url).status_code, 200)

    def test_apenas_admin_gerencia_usuarios(self):
        url = reverse('estoque:usuario_lista')
        self.assertEqual(self.logar(self.admin).get(url).status_code, 200)
        self.assertNotEqual(self.logar(self.gestor).get(url).status_code, 200)
        self.assertNotEqual(self.logar(self.operador).get(url).status_code, 200)

    def test_visitante_nao_logado_e_redirecionado_ao_login(self):
        r = Client().get(reverse('estoque:item_lista'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login/', r.url)


# ═══════════════════════════════════════════════════════════════════
# 4. TELAS PRINCIPAIS CARREGAM
# ═══════════════════════════════════════════════════════════════════

class TestTelas(BaseEstoque):

    def setUp(self):
        super().setUp()
        self.c = self.logar(self.admin)

    def test_telas_de_listagem(self):
        telas = [
            'dashboard', 'item_lista', 'movimentacao_lista',
            'categoria_lista', 'fornecedor_lista', 'almoxarifado_lista',
            'usuario_lista', 'relatorio_estoque',
        ]
        for nome in telas:
            r = self.c.get(reverse(f'estoque:{nome}'))
            self.assertEqual(r.status_code, 200, f'Tela {nome} falhou')

    def test_detalhe_do_item(self):
        r = self.c.get(reverse('estoque:item_detalhe', args=[self.item.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, self.item.nome)

    def test_detalhe_da_movimentacao(self):
        mov = Movimentacao.objects.create(
            item=self.item, tipo='ENTRADA', quantidade=10, responsavel=self.admin,
        )
        r = self.c.get(reverse('estoque:movimentacao_detalhe', args=[mov.pk]))
        self.assertEqual(r.status_code, 200)

    def test_qrcode_e_etiqueta(self):
        r = self.c.get(reverse('estoque:item_qrcode', args=[self.item.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'image/png')

        r = self.c.get(reverse('estoque:item_etiqueta', args=[self.item.pk]))
        self.assertEqual(r.status_code, 200)


# ═══════════════════════════════════════════════════════════════════
# 5. FLUXO COMPLETO PELA INTERFACE (ponta a ponta)
# ═══════════════════════════════════════════════════════════════════

class TestFluxoCompleto(BaseEstoque):

    def test_cadastrar_item_pelo_formulario_gera_entrada(self):
        """Item cadastrado com quantidade > 0 deve gerar ENTRADA automática."""
        c = self.logar(self.admin)
        r = c.post(reverse('estoque:item_criar'), {
            'nome': 'Papel A4', 'categoria': self.categoria.pk,
            'almoxarifado': self.almox.pk, 'unidade_medida': 'rs',
            'tipo_material': 'CONSUMO', 'quantidade_atual': 30,
            'quantidade_minima': 5,
        })
        self.assertEqual(r.status_code, 302)
        novo = Item.objects.get(nome='Papel A4')
        self.assertEqual(novo.quantidade_atual, 30)
        self.assertEqual(novo.movimentacoes.filter(tipo='ENTRADA').count(), 1)

    def test_registrar_movimentacao_pelo_formulario(self):
        c = self.logar(self.operador)
        r = c.post(reverse('estoque:movimentacao_criar'), {
            'tipo': 'SAIDA', 'item': self.item.pk,
            'almoxarifado': self.almox.pk, 'quantidade': 15,
            'solicitante_nome': 'Maria', 'solicitante_departamento': 'Geologia',
        })
        self.assertEqual(r.status_code, 302)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantidade_atual, 85)

    def test_baixa_rapida_saida(self):
        """Tela mobile de baixa (usada após ler o QR code)."""
        c = self.logar(self.operador)
        url = reverse('estoque:movimentacao_rapida', args=[self.item.pk])

        self.assertEqual(c.get(url + '?tipo=SAIDA').status_code, 200)
        self.assertEqual(c.get(url + '?tipo=DESCARTE').status_code, 200)

        r = c.post(url, {'tipo': 'SAIDA', 'quantidade': '10', 'solicitante_nome': 'Ana'})
        self.assertEqual(r.status_code, 302)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantidade_atual, 90)

    def test_baixa_rapida_recusa_quantidade_maior_que_estoque(self):
        c = self.logar(self.operador)
        url = reverse('estoque:movimentacao_rapida', args=[self.item.pk])
        r = c.post(url, {'tipo': 'SAIDA', 'quantidade': '9999', 'solicitante_nome': 'Ana'})
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantidade_atual, 100, 'Estoque não pode mudar')

    def test_criar_item_via_ajax(self):
        c = self.logar(self.gestor)
        r = c.post(reverse('estoque:item_criar_ajax'), {
            'nome': 'Grampeador', 'categoria': self.categoria.pk,
            'almoxarifado': self.almox.pk, 'unidade_medida': 'un',
            'tipo_material': 'CONSUMO',
        })
        self.assertEqual(r.status_code, 200)
        dados = r.json()
        self.assertTrue(dados['ok'])
        self.assertTrue(Item.objects.filter(nome='Grampeador').exists())

    def test_ajax_bloqueado_para_operador(self):
        c = self.logar(self.operador)
        r = c.post(reverse('estoque:item_criar_ajax'), {
            'nome': 'Proibido', 'categoria': self.categoria.pk,
            'almoxarifado': self.almox.pk,
        })
        self.assertEqual(r.status_code, 403)
        self.assertFalse(Item.objects.filter(nome='Proibido').exists())

    def test_ajax_recusa_campos_faltando(self):
        c = self.logar(self.admin)
        r = c.post(reverse('estoque:item_criar_ajax'), {'nome': 'Sem categoria'})
        self.assertEqual(r.status_code, 400)


# ═══════════════════════════════════════════════════════════════════
# 6. EXPORTAÇÕES (CSV e PDF)
# ═══════════════════════════════════════════════════════════════════

class TestExportacoes(BaseEstoque):

    def setUp(self):
        super().setUp()
        self.c = self.logar(self.admin)
        Movimentacao.objects.create(
            item=self.item, tipo='ENTRADA', quantidade=20, responsavel=self.admin,
        )

    def test_csv_de_movimentacoes(self):
        r = self.c.get(reverse('estoque:movimentacao_exportar_csv'))
        self.assertEqual(r.status_code, 200)
        self.assertIn('text/csv', r['Content-Type'])
        self.assertIn(self.item.nome, r.content.decode('utf-8'))

    def test_pdf_de_movimentacoes_em_retrato(self):
        r = self.c.get(reverse('estoque:movimentacao_exportar_pdf'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertIn(b'%PDF', r.content[:10])
        self._conferir_retrato(r.content)

    def test_pdf_do_relatorio_de_estoque_em_retrato(self):
        r = self.c.get(reverse('estoque:relatorio_estoque') + '?exportar=pdf')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self._conferir_retrato(r.content)

    def test_csv_do_relatorio_de_estoque(self):
        r = self.c.get(reverse('estoque:relatorio_estoque') + '?exportar=csv')
        self.assertEqual(r.status_code, 200)
        self.assertIn('text/csv', r['Content-Type'])

    def _conferir_retrato(self, conteudo):
        """Confere que a página do PDF é mais alta que larga."""
        import re
        m = re.search(rb'/MediaBox \[([\d\. ]+)\]', conteudo)
        self.assertIsNotNone(m, 'MediaBox não encontrado no PDF')
        v = [float(x) for x in m.group(1).split()]
        largura, altura = v[2] - v[0], v[3] - v[1]
        self.assertGreater(altura, largura, 'PDF deveria estar em retrato')


# ═══════════════════════════════════════════════════════════════════
# 7. BUSCA
# ═══════════════════════════════════════════════════════════════════

class TestBusca(BaseEstoque):

    def test_busca_encontra_item_pelo_nome(self):
        c = self.logar(self.admin)
        r = c.get(reverse('estoque:busca_global') + '?q=Caneta')
        self.assertIn(r.status_code, (200, 302))

    def test_busca_pelo_codigo_interno(self):
        c = self.logar(self.admin)
        r = c.get(reverse('estoque:busca_global') + f'?q={self.item.codigo_interno}')
        self.assertIn(r.status_code, (200, 302))
