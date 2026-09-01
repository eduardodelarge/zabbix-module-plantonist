<?php declare(strict_types = 1);

namespace Modules\Plantonista;

use APP;
use CMenuItem;
use Zabbix\Core\CModule;

/**
 * Modulo "Plantonista".
 *
 * Adiciona o item de menu Monitoring -> Plantonista, que abre a tela de consulta.
 */
class Module extends CModule {

	public function init(): void {
		APP::Component()->get('menu.main')
			->findOrAdd(_('Monitoring'))
			->getSubmenu()
			->add((new CMenuItem(_('Plantonista')))->setAction('plantonista.list'));
	}
}
