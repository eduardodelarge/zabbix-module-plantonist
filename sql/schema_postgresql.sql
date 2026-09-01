-- =====================================================================
--  Modulo Plantonista - estrutura para PostgreSQL
--  Execute conectado ao banco do Zabbix (normalmente chamado "zabbix").
-- =====================================================================

CREATE TABLE IF NOT EXISTS plantonista_escala (
    id           BIGSERIAL    PRIMARY KEY,
    nome         VARCHAR(255) NOT NULL,
    data_inicio  DATE         NOT NULL,
    data_final   DATE         NOT NULL,
    celular      VARCHAR(50)  NOT NULL,
    aplicacao    VARCHAR(255) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_app_data
    ON plantonista_escala (aplicacao, data_inicio, data_final);

-- ---------------------------------------------------------------------
--  Usuario dedicado para o importador (acesso apenas a esta tabela).
--  Troque a senha antes de executar.
-- ---------------------------------------------------------------------
-- CREATE USER plantonista_imp WITH PASSWORD 'TROQUE_ESTA_SENHA';
-- GRANT SELECT, INSERT, DELETE ON plantonista_escala TO plantonista_imp;
-- GRANT USAGE, SELECT ON SEQUENCE plantonista_escala_id_seq TO plantonista_imp;
