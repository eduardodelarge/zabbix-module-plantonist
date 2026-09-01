-- =====================================================================
--  Modulo Plantonista - estrutura para MySQL / MariaDB
--  Execute conectado ao banco do Zabbix (normalmente chamado "zabbix").
-- =====================================================================

CREATE TABLE IF NOT EXISTS plantonista_escala (
    id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome         VARCHAR(255) NOT NULL,
    data_inicio  DATE         NOT NULL,
    data_final   DATE         NOT NULL,
    celular      VARCHAR(50)  NOT NULL,
    aplicacao    VARCHAR(255) NOT NULL,
    PRIMARY KEY (id),
    KEY idx_app_data (aplicacao, data_inicio, data_final)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
--  Usuario dedicado para o importador (acesso apenas a esta tabela).
--  Troque a senha antes de executar.
-- ---------------------------------------------------------------------
-- CREATE USER 'plantonista_imp'@'%' IDENTIFIED BY 'TROQUE_ESTA_SENHA';
-- GRANT SELECT, INSERT, DELETE ON zabbix.plantonista_escala TO 'plantonista_imp'@'%';
-- FLUSH PRIVILEGES;
