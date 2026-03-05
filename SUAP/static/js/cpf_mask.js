(function () {
  function onlyDigits(value) {
    return (value || "").replace(/\D/g, "");
  }

  function formatCpf(value) {
    var digits = onlyDigits(value).slice(0, 11);
    if (!digits) return "";

    var part1 = digits.slice(0, 3);
    var part2 = digits.slice(3, 6);
    var part3 = digits.slice(6, 9);
    var part4 = digits.slice(9, 11);

    var out = part1;
    if (part2) out += "." + part2;
    if (part3) out += "." + part3;
    if (part4) out += "-" + part4;
    return out;
  }

  function applyMask(input) {
    input.value = formatCpf(input.value);
  }

  function bindCpfMask(input) {
    applyMask(input);

    input.addEventListener("input", function () {
      applyMask(input);
    });

    input.addEventListener("paste", function (event) {
      event.preventDefault();
      var text = (event.clipboardData || window.clipboardData).getData("text");
      input.value = formatCpf(text);
    });
  }

  function sanitizeOnSubmit(form) {
    form.addEventListener("submit", function () {
      var cpfInputs = form.querySelectorAll("[data-cpf-mask='true']");
      cpfInputs.forEach(function (input) {
        input.value = onlyDigits(input.value);
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var cpfInputs = document.querySelectorAll("[data-cpf-mask='true']");
    cpfInputs.forEach(bindCpfMask);

    var forms = new Set();
    cpfInputs.forEach(function (input) {
      if (input.form) {
        forms.add(input.form);
      }
    });

    forms.forEach(sanitizeOnSubmit);
  });
})();

