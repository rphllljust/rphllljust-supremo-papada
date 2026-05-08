DO $$
BEGIN
    IF to_regclass('public.cursos_nivelensino') IS NULL THEN
        RAISE NOTICE 'Tabela cursos_nivelensino ainda não existe. Seed de níveis de ensino ignorado.';
        RETURN;
    END IF;

    INSERT INTO cursos_nivelensino (descricao)
    VALUES
        ('Formação Inicial e Continuada'),
        ('Qualificação Profissional'),
        ('Técnico'),
        ('Técnico Integrado ao Ensino Médio'),
        ('Técnico Subsequente'),
        ('Tecnólogo'),
        ('Bacharelado'),
        ('Licenciatura'),
        ('Pós-graduação')
    ON CONFLICT (descricao) DO NOTHING;
END$$;