#!/usr/bin/env python
"""Setup QA Final - Gera CPFs válidos e cria 50 alunos."""
import os, sys, django, random
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.core.exceptions import ValidationError
from apps.unidades.models import Unidade
from apps.cursos.models import Curso
from apps.turmas.models import Turma, Polo
from apps.usuarios.models import Usuario, Pessoa
from apps.matriculas.models import Matricula
from apps.accounts.utils import normalize_cpf

# ============================================================
# GERADOR DE CPF VÁLIDO
# ============================================================
def gerar_cpf_valido():
    """Gera um CPF válido (apenas dígitos)."""
    def calc_digito(parcial):
        peso = len(parcial) + 1
        total = sum(int(d) * (peso - i) for i, d in enumerate(parcial))
        resto = 11 - (total % 11)
        return '0' if resto >= 10 else str(resto)
    
    base = ''.join(str(random.randint(0, 9)) for _ in range(9))
    # Ensure not all same digits
    while len(set(base)) == 1:
        base = ''.join(str(random.randint(0, 9)) for _ in range(9))
    
    d1 = calc_digito(base)
    d2 = calc_digito(base + d1)
    return base + d1 + d2

# ============================================================
# 1. UNIDADE
# ============================================================
unidade, _ = Unidade.objects.get_or_create(codigo='sede', nome='Sede',
    defaults={'endereco': 'Av. Principal, 1000', 'cidade': 'Porto Velho', 'uf': 'RO'})
print(f'1. Unidade: {unidade.nome}')

# ============================================================
# 2. CURSOS
# ============================================================
cursos = {}
for sigla, nome, tipo, ch in [
    ('CTI', 'Curso Tecnico em Informatica', 'TECNICO', 1200),
    ('CIA', 'Curso Itinerante de Agroecologia', 'ITINERANTE', 800),
    ('CRG', 'Curso Remoto de Gestao Empresarial', 'FORMACAO_INICIAL', 600),
]:
    c, _ = Curso.objects.get_or_create(sigla=sigla,
        defaults={'nome': nome, 'tipo_curso': tipo, 'carga_horaria': ch, 'unidade': unidade})
    cursos[sigla] = c
    print(f'2. Curso: {c.nome}')

# ============================================================
# 3. POLOS
# ============================================================
polos = {}
for nome_polo, mun, uf in [
    ('Polo Norte - Porto Velho', 'Porto Velho', 'RO'),
    ('Polo Sul - Ji-Parana', 'Ji-Parana', 'RO'),
]:
    p, _ = Polo.objects.get_or_create(nome=nome_polo,
        defaults={'municipio': mun, 'uf': uf, 'ativo': True})
    polos[nome_polo] = p
    print(f'3. Polo: {p.nome}')

# ============================================================
# 4. TURMAS
# ============================================================
turmas_cache = {}
for nome, sigla, modalidade, cap, polo_nome in [
    ('TECNICO-A', 'CTI', 'PRESENCIAL', 40, None),
    ('TECNICO-B', 'CTI', 'PRESENCIAL', 40, None),
    ('ITINERANTE-NORTE', 'CIA', 'ITINERANTE', 30, 'Polo Norte - Porto Velho'),
    ('ITINERANTE-SUL', 'CIA', 'ITINERANTE', 30, 'Polo Sul - Ji-Parana'),
    ('REMOTO-A', 'CRG', 'REMOTO', 50, None),
]:
    defaults = {'ano_letivo': 2025, 'modalidade': modalidade, 'capacidade_maxima': cap}
    if polo_nome:
        defaults['polo'] = polos[polo_nome]
    t, _ = Turma.objects.get_or_create(nome=nome, curso=cursos[sigla], defaults=defaults)
    turmas_cache[nome] = t
    print(f'4. Turma: {t.nome}')

# ============================================================
# 5. ADMIN
# ============================================================
if not Usuario.objects.filter(tipo='ADMIN').exists():
    p = Pessoa.objects.create(nome_completo='Administrador Inicial', cpf='90000010057', email='admin@suap.com')
    admin = Usuario.objects.create_user(username='90000010057', cpf='90000010057', tipo='ADMIN', password='admin',
                                          is_active=True, is_staff=True, is_superuser=True, pessoa=p)
    print('5. Admin CRIADO')
else:
    print('5. Admin ja existe')

# ============================================================
# 6. 50 ALUNOS COM CPFs VÁLIDOS
# ============================================================
# Gera CPFs únicos
random.seed(12345)
cpfs_usados = set()

def novo_cpf():
    while True:
        c = gerar_cpf_valido()
        if c not in cpfs_usados and c != '90000010057':
            cpfs_usados.add(c)
            return c

# Gerar todos os CPFs
cpfs = [novo_cpf() for _ in range(50)]

alunos = [
    # (nome, cpf, email, tel, sigla, turma, status_mat, turno)
    # === TECNICO (20) ===
    ('Joao Pedro Almeida Santos',  cpfs[0],  'joao.santos@email.com',    '(69)98412-0001', 'CTI', 'TECNICO-A', 'ATIVA', 'MANHA'),
    ('Maria Clara Oliveira Lima',  cpfs[1],  'maria.lima@email.com',     '(69)98412-0002', 'CTI', 'TECNICO-A', 'ATIVA', 'MANHA'),
    ('Pedro Henrique Costa',       cpfs[2],  'pedro.costa@email.com',    '(69)98412-0003', 'CTI', 'TECNICO-A', 'ATIVA', 'MANHA'),
    ('Ana Beatriz Souza',          cpfs[3],  'ana.souza@email.com',      '(69)98412-0004', 'CTI', 'TECNICO-A', 'ATIVA', 'MANHA'),
    ('Lucas Gabriel Pereira',      cpfs[4],  'lucas.pereira@email.com',  '(69)98412-0005', 'CTI', 'TECNICO-A', 'ATIVA', 'MANHA'),
    ('Julia Fernandes Martins',    cpfs[5],  'julia.martins@email.com',  '(69)98412-0006', 'CTI', 'TECNICO-B', 'ATIVA', 'TARDE'),
    ('Rafael Augusto Dias',        cpfs[6],  'rafael.dias@email.com',    '(69)98412-0007', 'CTI', 'TECNICO-B', 'ATIVA', 'TARDE'),
    ('Camila Rodrigues Barbosa',   cpfs[7],  'camila.barbosa@email.com', '(69)98412-0008', 'CTI', 'TECNICO-B', 'TRANCADA', 'TARDE'),
    ('Felipe Eduardo Nascimento',  cpfs[8],  'felipe.nasc@email.com',    '(69)98412-0009', 'CTI', 'TECNICO-B', 'CONCLUIDA', 'TARDE'),
    ('Larissa Cristina Alves',     cpfs[9],  'larissa.alves@email.com',  '(69)98412-0010', 'CTI', 'TECNICO-B', 'ATIVA', 'TARDE'),
    ('Thiago Oliveira Rocha',      cpfs[10], 'thiago.rocha@email.com',   '(69)98412-0011', 'CTI', 'TECNICO-A', 'CANCELADA', 'MANHA'),
    ('Vanessa Soares Moreira',     cpfs[11], 'vanessa.moreira@email.com','(69)98412-0012', 'CTI', 'TECNICO-A', 'ATIVA', 'MANHA'),
    ('Gabriel Santos Lima',        cpfs[12], 'gabriel.lima@email.com',   '(69)98412-0013', 'CTI', 'TECNICO-A', 'ATIVA', 'MANHA'),
    ('Isabela Cristina Rios',      cpfs[13], 'isabela.rios@email.com',   '(69)98412-0014', 'CTI', 'TECNICO-B', 'ATIVA', 'TARDE'),
    ('Diego Almeida Costa',        cpfs[14], 'diego.costa@email.com',    '(69)98412-0015', 'CTI', 'TECNICO-B', 'ATIVA', 'TARDE'),
    ('Patricia Nogueira Silva',    cpfs[15], 'patricia.silva@email.com', '(69)98412-0016', 'CTI', 'TECNICO-B', 'ATIVA', 'TARDE'),
    ('Marcos Vinicius Teixeira',   cpfs[16], 'marcos.teixeira@email.com','(69)98412-0017', 'CTI', 'TECNICO-A', 'ATIVA', 'MANHA'),
    ('Bruna Rafaela Campos',       cpfs[17], 'bruna.campos@email.com',   '(69)98412-0018', 'CTI', 'TECNICO-A', 'ATIVA', 'MANHA'),
    ('Leonardo Augusto Faria',     cpfs[18], 'leonardo.faria@email.com', '(69)98412-0019', 'CTI', 'TECNICO-B', 'ATIVA', 'TARDE'),
    ('Aline Fernanda Duarte',      cpfs[19], 'aline.duarte@email.com',   '(69)98412-0020', 'CTI', 'TECNICO-B', 'PENDENTE', 'TARDE'),
    # === ITINERANTE (15) ===
    ('Roberto Carlos Mendes',      cpfs[20], 'roberto.mendes@email.com', '(69)98412-0021', 'CIA', 'ITINERANTE-NORTE', 'ATIVA', 'INTEGRAL'),
    ('Tatiane Oliveira Barbosa',   cpfs[21], 'tatiane.barbosa@email.com','(69)98412-0022', 'CIA', 'ITINERANTE-NORTE', 'ATIVA', 'INTEGRAL'),
    ('Carlos Eduardo Pires',       cpfs[22], 'carlos.pires@email.com',   '(69)98412-0023', 'CIA', 'ITINERANTE-NORTE', 'ATIVA', 'INTEGRAL'),
    ('Juliana Souza Martins',      cpfs[23], 'juliana.martins@email.com','(69)98412-0024', 'CIA', 'ITINERANTE-SUL', 'ATIVA', 'INTEGRAL'),
    ('Fabio Henrique Lopes',       cpfs[24], 'fabio.lopes@email.com',    '(69)98412-0025', 'CIA', 'ITINERANTE-SUL', 'ATIVA', 'INTEGRAL'),
    ('Priscila Almeida Rocha',     cpfs[25], 'priscila.rocha@email.com', '(69)98412-0026', 'CIA', 'ITINERANTE-SUL', 'ATIVA', 'INTEGRAL'),
    ('Anderson Luis Santos',       cpfs[26], 'anderson.santos@email.com','(69)98412-0027', 'CIA', 'ITINERANTE-NORTE', 'TRANCADA', 'INTEGRAL'),
    ('Renata Cristina Vieira',     cpfs[27], 'renata.vieira@email.com',  '(69)98412-0028', 'CIA', 'ITINERANTE-NORTE', 'ATIVA', 'INTEGRAL'),
    ('Sergio Marcio Nogueira',     cpfs[28], '',                         '',                'CIA', 'ITINERANTE-SUL', 'ATIVA', 'INTEGRAL'),
    ('Daniela Cristina Fonseca',   cpfs[29], 'daniela.fonseca@email.com','(69)98412-0030', 'CIA', 'ITINERANTE-SUL', 'PENDENTE', 'INTEGRAL'),
    ('Gustavo Henrique Castro',    cpfs[30], 'gustavo.castro@email.com', '(69)98412-0031', 'CIA', 'ITINERANTE-NORTE', 'ATIVA', 'INTEGRAL'),
    ('Elaine Cristina Pereira',    cpfs[31], 'elaine.pereira@email.com', '(69)98412-0032', 'CIA', 'ITINERANTE-NORTE', 'ATIVA', 'INTEGRAL'),
    ('Thiago Rafael Alves',        cpfs[32], 'thiago.alves@email.com',   '(69)98412-0033', 'CIA', 'ITINERANTE-SUL', 'CANCELADA', 'INTEGRAL'),
    ('Alessandra Souza Dias',      cpfs[33], 'alessandra.dias@email.com','(69)98412-0034', 'CIA', 'ITINERANTE-SUL', 'ATIVA', 'INTEGRAL'),
    ('Marcio Rogerio Barbosa',     cpfs[34], 'marcio.barbosa@email.com', '(69)98412-0035', 'CIA', 'ITINERANTE-NORTE', 'ATIVA', 'INTEGRAL'),
    # === REMOTO (15) ===
    ('Amanda Leticia Oliveira',    cpfs[35], 'amanda.oliveira@email.com','(69)98412-0036', 'CRG', 'REMOTO-A', 'ATIVA', 'NOITE'),
    ('Paulo Henrique Nunes',       cpfs[36], 'paulo.nunes@email.com',    '(69)98412-0037', 'CRG', 'REMOTO-A', 'ATIVA', 'NOITE'),
    ('Carla Simone Teixeira',      cpfs[37], 'carla.teixeira@email.com', '(69)98412-0038', 'CRG', 'REMOTO-A', 'ATIVA', 'NOITE'),
    ('Rodrigo Alves Batista',      cpfs[38], 'rodrigo.batista@email.com','(69)98412-0039', 'CRG', 'REMOTO-A', 'ATIVA', 'NOITE'),
    ('Fernanda Cristina Almeida',  cpfs[39], 'fernanda.almeida@email.com','(69)98412-0040', 'CRG', 'REMOTO-A', 'ATIVA', 'NOITE'),
    ('Luciano Marcio Dias',        cpfs[40], 'luciano.dias@email.com',   '(69)98412-0041', 'CRG', 'REMOTO-A', 'ATIVA', 'NOITE'),
    ('Simone Aparecida Rocha',     cpfs[41], '',                         '(69)98412-0042', 'CRG', 'REMOTO-A', 'ATIVA', 'NOITE'),
    ('Hugo Leonardo Santos',       cpfs[42], 'hugo.santos@email.com',    '(69)98412-0043', 'CRG', 'REMOTO-A', 'TRANCADA', 'NOITE'),
    ('Bianca Rafaela Torres',      cpfs[43], 'bianca.torres@email.com',  '(69)98412-0044', 'CRG', 'REMOTO-A', 'CONCLUIDA', 'NOITE'),
    ('Eduardo Fernando Lima',      cpfs[44], 'eduardo.lima@email.com',   '(69)98412-0045', 'CRG', 'REMOTO-A', 'PENDENTE', 'NOITE'),
    ('Viviane Cristina Moura',     cpfs[45], 'viviane.moura@email.com',  '(69)98412-0046', 'CRG', 'REMOTO-A', 'ATIVA', 'NOITE'),
    ('Cristiano Ronaldo Souza',    cpfs[46], 'cristiano.souza@email.com','(69)98412-0047', 'CRG', 'REMOTO-A', 'ATIVA', 'NOITE'),
    ('Lorena Gabriela Campos',     cpfs[47], 'invalido@teste.com',       '12345678901',    'CRG', 'REMOTO-A', 'ATIVA', 'NOITE'),
    ('Adriano Luiz Barros',        cpfs[48], 'adriano.barros@email.com', '(69)98412-0049', 'CRG', 'REMOTO-A', 'ATIVA', 'NOITE'),
    ('Nathalia Pereira Silva',     cpfs[49], 'nathalia.silva@email.com', '(69)98412-0050', 'CRG', 'REMOTO-A', 'ATIVA', 'NOITE'),
]

criados = 0
erros_list = []
for nome, cpf, email, tel, sigla, turma_nome, status_mat, turno in alunos:
    try:
        cpf_norm = normalize_cpf(cpf)
        pessoa, _ = Pessoa.objects.get_or_create(cpf=cpf_norm, defaults={
            'nome_completo': nome, 'email': email, 'telefone': tel,
        })
        usuario, created = Usuario.objects.get_or_create(cpf=cpf_norm, defaults={
            'username': cpf_norm, 'tipo': 'ALUNO', 'is_active': True,
            'pessoa': pessoa, 'first_name': nome.split()[0],
            'last_name': ' '.join(nome.split()[1:]) if len(nome.split()) > 1 else '',
            'email': email,
        })
        if created:
            usuario.set_password('123mudar')
            usuario.save()

        curso = cursos[sigla]
        turma = turmas_cache[turma_nome]
        mat = Matricula(aluno=usuario, curso=curso, turma=turma, status=status_mat, turno=turno)
        mat.save()
        criados += 1
        print(f'  OK {criados:2d}. {nome[:25]:25s} | CPF: {cpf_norm} | {sigla}')
    except Exception as e:
        erros_list.append(f'{nome}: {e}')
        print(f'  ERRO {nome[:25]:25s} | {e}')

print(f'\n=== RESULTADO ===')
print(f'Alunos criados: {criados} | Erros: {len(erros_list)}')
print(f'Usuarios ALUNO: {Usuario.objects.filter(tipo="ALUNO").count()} | Matriculas: {Matricula.objects.count()}')
for e in erros_list:
    print(f'  ERRO: {e}')
print('=== SETUP CONCLUIDO ===')
