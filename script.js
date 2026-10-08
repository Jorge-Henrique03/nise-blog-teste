const PHONE = '5563999361650';

const menuButton = document.querySelector('.menu-button');
const nav = document.querySelector('#main-nav');

menuButton?.addEventListener('click', () => {
  const isOpen = menuButton.getAttribute('aria-expanded') === 'true';
  menuButton.setAttribute('aria-expanded', String(!isOpen));
  nav?.classList.toggle('open', !isOpen);
});

nav?.querySelectorAll('a').forEach((link) => {
  link.addEventListener('click', () => {
    nav.classList.remove('open');
    menuButton?.setAttribute('aria-expanded', 'false');
  });
});

document.querySelectorAll('.whatsapp-link').forEach((link) => {
  link.addEventListener('click', (event) => {
    event.preventDefault();
    const message = encodeURIComponent(link.dataset.message || 'Olá! Vim pelo site da Nise Consultoria.');
    window.open(`https://wa.me/${PHONE}?text=${message}`, '_blank', 'noopener,noreferrer');
  });
});

document.querySelector('#lead-form')?.addEventListener('submit', (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const message = [
    'Olá! Vim pelo site da Nise Consultoria e gostaria de solicitar um pré-diagnóstico.',
    '',
    `Nome: ${form.get('nome')}`,
    `Empresa: ${form.get('empresa')}`,
    `Meu WhatsApp: ${form.get('whatsapp')}`,
    `Serviço de interesse: ${form.get('servico')}`,
    `Principal necessidade: ${form.get('necessidade') || 'Não informada'}`,
  ].join('\n');

  window.open(`https://wa.me/${PHONE}?text=${encodeURIComponent(message)}`, '_blank', 'noopener,noreferrer');
});
