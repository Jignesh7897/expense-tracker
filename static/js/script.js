// Client-side form validation
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('form[novalidate]').forEach(form => {
    form.addEventListener('submit', e => {
      const amtInput = form.querySelector('input[name="amount"]');
      if (amtInput) {
        const val = parseFloat(amtInput.value);
        if (!amtInput.value || isNaN(val) || val <= 0) {
          e.preventDefault();
          amtInput.classList.add('is-invalid');
          let fb = amtInput.nextElementSibling;
          if (!fb || !fb.classList.contains('invalid-feedback')) {
            fb = document.createElement('div');
            fb.className = 'invalid-feedback';
            amtInput.after(fb);
          }
          fb.textContent = 'Please enter a valid amount greater than 0.';
          amtInput.focus();
          return;
        } else {
          amtInput.classList.remove('is-invalid');
        }
      }
    });
  });

  // Auto-dismiss alerts after 4 seconds
  document.querySelectorAll('.alert').forEach(el => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      bsAlert.close();
    }, 4000);
  });
});
