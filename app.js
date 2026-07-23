const filterButtons = document.querySelectorAll("[data-filter]");
const productCards = document.querySelectorAll("[data-category]");
const contactForm = document.querySelector(".contact-form");
const message = document.querySelector("#mensaje");
const formStatus = document.querySelector(".form-status");

filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const filter = button.dataset.filter;
    filterButtons.forEach((item) => item.classList.toggle("active", item === button));
    productCards.forEach((card) => {
      card.hidden = filter !== "Todos" && card.dataset.category !== filter;
    });
  });
});

document.querySelectorAll("[data-product]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelector("#contacto").scrollIntoView({ behavior: "smooth" });
    window.setTimeout(() => {
      message.value = `Hola, quiero consultar por ${button.dataset.product}. `;
      message.focus();
    }, 450);
  });
});

contactForm.addEventListener("submit", (event) => {
  event.preventDefault();
  formStatus.classList.add("show");
  contactForm.reset();
});
