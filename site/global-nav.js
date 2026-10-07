document.querySelectorAll('.site-nav .mobile-panel a').forEach(function (link) {
  link.addEventListener('click', function () {
    const menu = link.closest('.mobile-nav');
    if (menu) menu.removeAttribute('open');
  });
});

document.querySelectorAll('.site-nav .mobile-nav').forEach(function (mobileMenu) {
  document.addEventListener('click', function (event) {
    if (mobileMenu.open && !mobileMenu.contains(event.target)) {
      mobileMenu.removeAttribute('open');
    }
  });

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && mobileMenu.open) {
      mobileMenu.removeAttribute('open');
      const trigger = mobileMenu.querySelector('summary');
      if (trigger) trigger.focus();
    }
  });
});
