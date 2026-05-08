#!/usr/bin/env python
"""Setup QA - Cria 50 alunos, cursos, turmas e matrículas para teste."""
import os, sys, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.core.exceptions import ValidationError
from apps.unidades.models import Unidade
from apps.cursos.models import Curso
from apps.turmas.models import Turma
from apps.usuarios.models import Usuario, Pessoa, PerfilUsuario
from apps.matriculas.models import Matricula, DocumentoMatricula, DocumentoObrigatorioCurso, DocumentoEmitido, Transferencia
from apps.accounts.utils import normalize_cpf

# 1. CRIAR UNIDADE
try:
    unidade, _ = Unidade.objects.get_or_create(
        codigo='sede',
        nome='Sede',
        defaults={'endereco': 'Av. Principal, 1000', 'cidade': 'Porto Velho', 'uf': 'RO'}
    )
    print(f'1. Unidade: {unidade.nome} | codigo={unidade.codigo}')
except Exception as e:
    print(f'1. ERRO Unidade: {e}')
    sys.exit(1)

# 2. CRIAR CURSOS
cursos = {}
for sigla, nome, tipo, ch in [
    ('CTI', 'Curso Técnico em Informática', 'TECNICO', 1200),
    ('CIA', 'Curso Itinerante de Agroecologia', 'ITINERANTE', 800),
    ('CRG', 'Curso Remoto de Gestão Empresarial', 'FORMACAO_INICIAL', 600),
]:
    curso, _ = Curso.objects.get_or_create(sigla=sigla, defaults={
        'nome': nome, 'tipo_curso': tipo, 'carga_horaria': ch, 'unidade': unidade,
    })
    cursos[sigla] = curso
    print(f'2. Curso: {curso.nome} | {tipo} | {ch}h')

# 3. CRIAR TURMAS
turmas = {}
for nome, sigla, modalidade, cap in [
    ('TECNICO-A', 'CTI', 'PRESENCIAL', 40),
    ('TECNICO-B', 'CTI', 'PRESENCIAL', 40),
    ('ITINERANTE-NORTE', 'CIA', 'ITINERANTE', 30),
    ('ITINERANTE-SUL', 'CIA', 'ITINERANTE', 30),
    ('REMOTO-A', 'CRG', 'REMOTO', 50),
]:
    t, _ = Turma.objects.get_or_create(nome=nome, curso=cursos[sigla], defaults={
        'ano_letivo': 2025, 'modalidade': modalidade, 'capacidade_maxima': cap,
    })
    turmas[nome] = t
    print(f'3. Turma: {nome} | {cursos[sigla].nome} | {cap} vagas')

# 4. ADMIN
admin_exists = False
try:
    admin = Usuario.objects.filter(tipo='ADMIN').first()
    if admin:
        admin_exists = True
        print('4. Admin ja existe')
    else:
        p = Pessoa.objects.create(nome_completo='Administrador Inicial', cpf='90000010057', email='admin@suap.com')
        admin = Usuario.objects.create_user(username='90000010057', cpf='90000010057', tipo='ADMIN', password='admin', is_active=True, is_staff=True, is_superuser=True, pessoa=p)
        print('4. Admin CRIADO')
except Exception as e:
    print(f'4. ERRO Admin: {e}')

# 5. 50 ALUNOS
alunos = [
    # (nome, cpf, nasc, email, tel, curso_sigla, turma, status_mat, sit_fin, sit_doc, obs)
    # === TECNICO (20) ===
    ('Joao Pedro Almeida Santos',  '52998224725', 'joao@email.com',       '(69)984120001', 'CTI', 'TECNICO-A', 'ATIVA', 'REGULAR', 'COMPLETA'),
    ('Maria Clara Oliveira Lima',  '12345678909', 'maria@email.com',      '(69)984120002', 'CTI', 'TECNICO-A', 'ATIVA', 'REGULAR', 'COMPLETA'),
    ('Pedro Henrique Costa',       '98765432100', 'pedro@email.com',      '(69)984120003', 'CTI', 'TECNICO-A', 'ATIVA', 'BOLSISTA', 'COMPLETA'),
    ('Ana Beatriz Souza',          '11122233344', 'ana@email.com',        '(69)984120004', 'CTI', 'TECNICO-A', 'ATIVA', 'REGULAR', 'PENDENTE'),
    ('Lucas Gabriel Pereira',      '55566677788', 'lucas@email.com',      '(69)984120005', 'CTI', 'TECNICO-A', 'ATIVA', 'INADIMPLENTE', 'COMPLETA'),
    ('Julia Fernandes Martins',    '99988877766', 'julia@email.com',      '(69)984120006', 'CTI', 'TECNICO-B', 'ATIVA', 'REGULAR', 'COMPLETA'),
    ('Rafael Augusto Dias',        '44455566677', 'rafael@email.com',     '(69)984120007', 'CTI', 'TECNICO-B', 'ATIVA', 'BOLSISTA', 'COMPLETA'),
    ('Camila Rodrigues Barbosa',   '77788899900', 'camila@email.com',     '(69)984120008', 'CTI', 'TECNICO-B', 'TRANCADA', 'REGULAR', 'COMPLETA'),
    ('Felipe Eduardo Nascimento',  '22233344455', 'felipe@email.com',     '(69)984120009', 'CTI', 'TECNICO-B', 'CONCLUIDA', 'REGULAR', 'COMPLETA'),
    ('Larissa Cristina Alves',     '88899900011', 'larissa@email.com',    '(69)984120010', 'CTI', 'TECNICO-B', 'ATIVA', 'REGULAR', 'PENDENTE'),
    ('Thiago Oliveira Rocha',      '33344455566', 'thiago@email.com',     '(69)984120011', 'CTI', 'TECNICO-A', 'CANCELADA', 'INADIMPLENTE', 'INCOMPLETA'),
    ('Vanessa Soares Moreira',     '66677788899', 'vanessa@email.com',    '(69)984120012', 'CTI', 'TECNICO-A', 'ATIVA', 'REGULAR', 'COMPLETA'),
    ('Gabriel Santos Lima',        '11199988877', 'gabriel@email.com',    '(69)984120013', 'CTI', 'TECNICO-A', 'ATIVA', 'REGULAR', 'COMPLETA'),
    ('Isabela Cristina Rios',      '55511133399', 'isabela@email.com',    '(69)984120014', 'CTI', 'TECNICO-B', 'ATIVA', 'REGULAR', 'COMPLETA'),
    ('Diego Almeida Costa',        '77733355511', 'diego@email.com',      '(69)984120015', 'CTI', 'TECNICO-B', 'ATIVA', 'REGULAR', 'COMPLETA'),
    ('Patricia Nogueira Silva',    '99911155533', 'patricia@email.com',   '(69)984120016', 'CTI', 'TECNICO-B', 'ATIVA', 'BOLSISTA', 'PENDENTE'),
    ('Marcos Vinicius Teixeira',   '33399977755', 'marcos@email.com',     '(69)984120017', 'CTI', 'TECNICO-A', 'ATIVA', 'REGULAR', 'COMPLETA'),
    ('Bruna Rafaela Campos',       '77799933311', 'bruna@email.com',      '(69)984120018', 'CTI', 'TECNICO-A', 'ATIVA', 'INADIMPLENTE', 'PENDENTE'),
    ('Leonardo Augusto Faria',     '11155599933', 'leonardo@email.com',   '(69)984120019', 'CTI', 'TECNICO-B', 'ATIVA', 'REGULAR', 'COMPLETA'),
    ('Aline Fernanda Duarte',      '99933377711', 'aline@email.com',      '(69)984120020', 'CTI', 'TECNICO-B', 'PENDENTE', 'REGULAR', 'INCOMPLETA'),
    # === ITINERANTE (15) ===
    ('Roberto Carlos Mendes',      '44477711199', 'roberto@email.com',    '(69)984120021', 'CIA', 'ITINERANTE-NORTE', 'ATIVA', 'REGULAR', 'COMPLETA'),
    ('Tatiane Oliveira Barbosa',   '77744499922', 'tatiane@email.com',    '(69)984120022', 'CIA', 'ITINERANTE-NORTE', 'ATIVA', 'REGULAR', 'COMPLETA'),
    ('Carlos Eduardo Pires',       '22288855544', 'carlos@email.com',     '(69)984120023', 'CIA', 'ITINERANTE-NORTE', 'ATIVA', 'BOLSISTA', 'PENDENTE'),
    ('Juliana Souza Martins',      '66611188833', 'juliana@email.com',    '(69)984120024', 'CIA', 'ITINERANTE-SUL', 'ATIVA', 'REGULAR', 'COMPLETA'),
    ('Fabio Henrique Lopes',       '33388811166', 'fabio@email.com',      '(69)984120025', 'CIA', 'ITINERANTE-SUL', 'ATIVA', 'INADIMPLENTE', 'COMPLETA'),
    ('Priscila Almeida Rocha',     '99922244477', 'priscila@email.com',   '(69)984120026', 'CIA', 'ITINERANTE-SUL', 'ATIVA', 'REGULAR', 'PENDENTE'),
    ('Anderson Luis Santos',       '55522299988', 'anderson@email.com',   '(69)984120027', 'CIA', 'ITINERANTE-NORTE', 'TRANCADA', 'REGULAR', 'COMPLETA'),
    ('Renata Cristina Vieira',     '11144477722', 'renata@email.com',     '(69)984120028', 'CIA', 'ITINERANTE-NORTE', 'ATIVA', 'REGULAR', 'COMPLETA'),
    ('Sergio Marcio Nogueira',     '77711155544', '',                     '',              'CIA', 'ITINERANTE-SUL', 'ATIVA', 'REGULAR', 'INCOMPLETA'),
    ('Daniela Cristina Fonseca',   '44499911188', 'daniela@email.com',    '(69)984120030', 'CIA', 'ITINERANTE-SUL', 'PENDENTE', 'REGULAR', 'PENDENTE'),
    ('Gustavo Henrique Castro',    '22255588800', 'gustavo@email.com',    '(69)984120031', 'CIA', 'ITINERANTE-NORTE', 'ATIVA', 'BOLSISTA', 'COMPLETA'),
    ('Elaine Cristina Pereira',    '88855522211', 'elaine@email.com',     '(69)984120032', 'CIA', 'ITINERANTE-NORTE', 'ATIVA', 'INADIMPLENTE', 'COMPLETA'),
    ('Thiago Rafael Alves',        '66633399955', 'thiago@email.com',     '(69)984120033', 'CIA', 'ITINERANTE-SUL', 'CANCELADA', 'REGULAR', 'INCOMPLETA'),
    ('Alessandra Souza Dias',      '11177744499', 'alessandra@email.com', '(69)984120034', 'CIA', 'ITINERANTE-SUL', 'ATIVA', 'REGULAR', 'COMPLETA'),
    ('Marcio Rogerio Barbosa',     '55599922277', 'marcio@email.com',     '(69)984120035', 'CIA', 'ITINERANTE-NORTE', 'ATIVA', 'REGULAR', 'PENDENTE'),
    # === REMOTO (15) ===
    ('Amanda Leticia Oliveira',    '88833399944', 'amanda@email.com',     '(69)984120036', 'CRG', 'REMOTO-A', 'ATIVA', 'REGULAR', 'COMPLETA'),
    ('Paulo Henrique Nunes',       '33311177766', 'paulo@email.com',      '(69)984120037', 'CRG', 'REMOTO-A', 'ATIVA', 'REGULAR', 'COMPLETA'),
    ('Carla Simone Teixeira',      '77766611122', 'carla@email.com',      '(69)984120038', 'CRG', 'REMOTO-A', 'ATIVA', 'BOLSISTA', 'PENDENTE'),
    ('Rodrigo Alves Batista',      '55544488811', 'rodrigo@email.com',    '(69)984120039', 'CRG', 'REMOTO-A', 'ATIVA', 'INADIMPLENTE', 'COMPLETA'),
    ('Fernanda Cristina Almeida',  '99955533377', 'fernanda@email.com',   '(69)984120040', 'CRG', 'REMOTO-A', 'ATIVA', 'REGULAR', 'COMPLETA'),
    ('Luciano Marcio Dias',        '22299955588', 'luciano@email.com',    '(69)984120041', 'CRG', 'REMOTO-A', 'ATIVA', 'REGULAR', 'INCOMPLETA'),
    ('Simone Aparecida Rocha',     '44466699933', '',                     '(69)984120042', 'CRG', 'REMOTO-A', 'ATIVA', 'REGULAR', 'COMPLETA'),
    ('Hugo Leonardo Santos',       '77722244466', 'hugo@email.com',       '(69)984120043', 'CRG', 'REMOTO-A', 'TRANCADA', 'REGULAR', 'COMPLETA'),
    ('Bianca Rafaela Torres',      '11188866644', 'bianca@email.com',     '(69)984120044', 'CRG', 'REMOTO-A', 'CONCLUIDA', 'REGULAR', 'COMPLETA'),
    ('Eduardo Fernando Lima',      '33355577799', 'eduardo@email.com',    '(69)984120045', 'CRG', 'REMOTO-A', 'PENDENTE', 'REGULAR', 'PENDENTE'),
    ('Viviane Cristina Moura',     '66622288855', 'viviane@email.com',    '(69)984120046', 'CRG', 'REMOTO-A', 'ATIVA', 'BOLSISTA', 'COMPLETA'),
    ('Cristiano Ronaldo Souza',    '88844411177', 'cristiano@email.com',  '(69)984120047', 'CRG', 'REMOTO-A', 'ATIVA', 'INADIMPLENTE', 'PENDENTE'),
    ('Lorena Gabriela Campos',     '22277733300', 'invalido',             '12345678901',   'CRG', 'REMOTO-A', 'ATIVA', 'REGULAR', 'COMPLETA'),
    ('Adriano Luiz Barros',        '99944466622', 'adriano@email.com',    '(69)984120049', 'CRG', 'REMOTO-A', 'ATIVA', 'REGULAR', 'COMPLETA'),
    ('Nathalia Pereira Silva',     '55588822299', 'nathalia@email.com',   '(69)984120050', 'CRG', 'REMOTO-A', 'ATIVA', 'REGULAR', 'COMPLETA'),
]

criados = 0
erros_list = []
for nome, cpf, email, tel, sigla, turma_nome, status_mat, sit_fin, sit_doc in alunos:
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

        # Matricula
        curso = cursos[sigla]
        turma = turmas[turma_nome]
        mat = Matricula(aluno=usuario, curso=curso, turma=turma, status=status_mat)
        mat.save()
        criados += 1
    except Exception as e:
        erros_list.append(f'{nome}: {e}')

print(f'\n5. Alunos criados: {criados} | Erros: {len(erros_list)}')
for e in erros_list:
    print(f'   ERRO: {e}')

print(f'\nTotal banco: Usuarios={Usuario.objects.filter(tipo="ALUNO").count()} | Matriculas={Matricula.objects.count()}')
print('\n=== SETUP QA CONCLUIDO ===')
