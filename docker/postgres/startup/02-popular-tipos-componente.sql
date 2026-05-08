DO $$
BEGIN
    IF to_regclass('public.cursos_tipocomponente') IS NULL THEN
        RAISE NOTICE 'Tabela cursos_tipocomponente ainda não existe. Seed de tipos do componente ignorado.';
        RETURN;
    END IF;

    INSERT INTO cursos_tipocomponente (descricao)
    VALUES
        ('Disciplina'),
        ('Unidade Curricular'),
        ('Módulo'),
        ('Projeto Integrador'),
        ('Prática Profissional'),
        ('Estágio Supervisionado'),
        ('Trabalho de Conclusão de Curso'),
        ('Atividade Complementar'),
        ('Oficina'),
        ('Seminário')
    ON CONFLICT (descricao) DO NOTHING;
END$$;