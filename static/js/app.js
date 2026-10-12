document.addEventListener("DOMContentLoaded", () => {
  const menu = document.querySelector(".menu");
  const sidebar = document.querySelector(".sidebar");
  if (menu && sidebar) menu.addEventListener("click", () => sidebar.classList.toggle("open"));

  const password = document.querySelector("#id_password1");
  const bars = document.querySelectorAll(".strength span");
  if (password) password.addEventListener("input", () => {
    const value = password.value;
    const score = [value.length >= 8, /[A-Z]/.test(value), /[0-9]/.test(value), /[^A-Za-z0-9]/.test(value)].filter(Boolean).length;
    bars.forEach((bar, index) => { bar.style.background = index < score ? (score < 3 ? "#f07a5a" : "#14b8a6") : "#dbe5e3"; });
  });
});
