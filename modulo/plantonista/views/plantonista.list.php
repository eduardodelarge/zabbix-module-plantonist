<?php declare(strict_types = 1);

/**
 * Tela de consulta de plantonista.
 *
 * @var CView  $this
 * @var array  $data
 *
 * $data['aplicacao']   string
 * $data['data']        string  (Y-m-d)
 * $data['pesquisou']   bool
 * $data['plantonista'] string|null
 */

$form = (new CForm('get'))
	->cleanItems()
	->setName('plantonista_form')
	->addItem(
		(new CFormGrid())
			->addItem([
				new CLabel(_('Aplicacao'), 'aplicacao'),
				new CFormField(
					(new CTextBox('aplicacao', $data['aplicacao']))
						->setWidth(ZBX_TEXTAREA_MEDIUM_WIDTH)
						->setAttribute('autofocus', 'autofocus')
						->setAttribute('placeholder', _('Nome da aplicacao'))
				)
			])
			->addItem([
				new CLabel(_('Data'), 'data'),
				new CFormField(
					(new CTextBox('data', $data['data']))
						->setAttribute('type', 'date')
				)
			])
			->addItem(
				new CFormField(
					new CSubmitButton(_('Consultar'), 'action', 'plantonista.list')
				)
			)
	);

$resultado = null;

if ($data['pesquisou']) {
	if ($data['plantonista'] !== null) {
		$resultado = (new CDiv([
			(new CTag('p', true, _('Plantonista responsavel:')))->addStyle('margin:0 0 4px 0; color:#768d99;'),
			(new CTag('h1', true, $data['plantonista']))->addStyle('margin:0;')
		]))->addStyle('margin-top:20px;');
	}
	else {
		$resultado = (new CDiv(
			_s('Nenhum plantonista ativo em %1$s para a aplicacao "%2$s".', $data['data'], $data['aplicacao'])
		))
			->addClass(ZBX_STYLE_RED)
			->addStyle('margin-top:20px;');
	}
}

(new CHtmlPage())
	->setTitle(_('Consulta de plantonista'))
	->addItem($form)
	->addItem($resultado)
	->show();
