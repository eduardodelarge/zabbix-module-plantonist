-- Testa a mesma consulta que o modulo executa.
-- Troque o nome da aplicacao e a data.

SELECT nome
FROM plantonista_escala
WHERE LOWER(aplicacao) = LOWER('Portal do Cliente')
  AND data_inicio <= '2026-09-10'
  AND data_final  >= '2026-09-10'
ORDER BY data_inicio DESC, id DESC
LIMIT 1;
