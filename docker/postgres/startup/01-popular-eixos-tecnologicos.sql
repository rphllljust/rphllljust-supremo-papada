DO $$
BEGIN
    IF to_regclass('public.cursos_eixotecnologico') IS NULL THEN
        RAISE NOTICE 'Tabela cursos_eixotecnologico ainda não existe. Seed de eixos tecnológicos ignorado.';
        RETURN;
    END IF;

    INSERT INTO cursos_eixotecnologico (descricao)
    VALUES
        ('Ambiente e Saúde'),
        ('Controle e Processos Industriais'),
        ('Desenvolvimento Educacional e Social'),
        ('Gestão e Negócios'),
        ('Informação e Comunicação'),
        ('Infraestrutura'),
        ('Militar'),
        ('Produção Alimentícia'),
        ('Produção Cultural e Design'),
        ('Produção Industrial'),
        ('Recursos Naturais'),
        ('Segurança'),
        ('Turismo, Hospitalidade e Lazer')
    ON CONFLICT (descricao) DO NOTHING;
END$$;