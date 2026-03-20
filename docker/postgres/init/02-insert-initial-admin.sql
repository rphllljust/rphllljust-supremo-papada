-- Inserts initial admin user directly into the database if not present.
-- Generated to be executed by Postgres init scripts (mounted into the container).

DO $$
DECLARE
    _pessoa_id integer;
    _existing integer;
    _cpf text := '12345678909';
    _first_name text := 'Administrador';
    _last_name text := 'Inicial';
    _full_name text := 'Administrador Inicial';
    _password_hash text := 'pbkdf2_sha256$260000$suapinit$CvytpJA7JQBSW0j17x8RRqL7FUn26OGqTBnHW4ON7mE=';
BEGIN
    SELECT 1 INTO _existing FROM usuarios_usuario WHERE cpf = _cpf LIMIT 1;
    IF _existing IS NOT NULL THEN
        RAISE NOTICE 'Initial admin with CPF % already exists; skipping insert.', _cpf;
        RETURN;
    END IF;

    -- Create Pessoa
    INSERT INTO usuarios_pessoa (nome_completo, cpf, data_nascimento, email, telefone, ativo)
    VALUES (_full_name, _cpf, NULL, '', '', true)
    RETURNING id INTO _pessoa_id;

    -- Create Usuario (AbstractUser fields + custom fields)
    INSERT INTO usuarios_usuario (
        password, last_login, is_superuser, username, first_name, last_name, email,
        is_staff, is_active, date_joined, cpf, tipo, must_change_password, pessoa_id
    ) VALUES (
        _password_hash, NULL, true, _cpf, _first_name, _last_name, '', true, true, now(), _cpf, 'ADMIN', true, _pessoa_id
    );

    RAISE NOTICE 'Initial admin inserted with CPF % and pessoa_id %.', _cpf, _pessoa_id;
END$$;
