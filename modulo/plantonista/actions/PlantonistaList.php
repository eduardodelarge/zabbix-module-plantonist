<?php declare(strict_types = 1);

namespace Modules\Plantonista\Actions;

use CController;
use CControllerResponseData;

/**
 * Controller da tela de consulta de plantonista.
 *
 * Entrada (GET):
 *   - aplicacao : nome da aplicacao pesquisada
 *   - data      : data de referencia no formato Y-m-d (default: hoje)
 *
 * Saida (para a view):
 *   - plantonista : nome do plantonista ativo, ou null se nao encontrado
 */
class PlantonistaList extends CController {

	protected function init(): void {
		$this->disableCsrfValidation();
	}

	protected function checkInput(): bool {
		$fields = [
			'aplicacao' => 'string',
			'data'      => 'string'
		];

		return $this->validateInput($fields);
	}

	protected function checkPermissions(): bool {
		return $this->getUserType() >= USER_TYPE_ZABBIX_USER;
	}

	protected function doAction(): void {
		$aplicacao = trim($this->getInput('aplicacao', ''));
		$data_in   = trim($this->getInput('data', ''));

		// Normaliza a data. Se vier vazia ou invalida, usa a data de hoje.
		$ts = ($data_in !== '') ? strtotime($data_in) : time();
		$data = ($ts !== false) ? date('Y-m-d', $ts) : date('Y-m-d');

		$pesquisou   = ($aplicacao !== '');
		$plantonista = null;

		if ($pesquisou) {
			$row = DBfetch(DBselect(
				'SELECT nome'.
				' FROM plantonista_escala'.
				' WHERE LOWER(aplicacao)='.zbx_dbstr(mb_strtolower($aplicacao)).
					' AND data_inicio<='.zbx_dbstr($data).
					' AND data_final>='.zbx_dbstr($data).
				' ORDER BY data_inicio DESC, id DESC',
				1
			));

			$plantonista = ($row !== false) ? $row['nome'] : null;
		}

		$response = new CControllerResponseData([
			'aplicacao'   => $aplicacao,
			'data'        => $data,
			'pesquisou'   => $pesquisou,
			'plantonista' => $plantonista
		]);
		$response->setTitle(_('Consulta de plantonista'));

		$this->setResponse($response);
	}
}
