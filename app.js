const filterButtons = document.querySelectorAll("[data-filter]");
const productCards = document.querySelectorAll("[data-category]");
const contactForm = document.querySelector(".contact-form");
const message = document.querySelector("#mensaje");
const formStatus = document.querySelector(".form-status");

filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const filter = button.dataset.filter;
    filterButtons.forEach((item) => {
      item.classList.toggle("active", item === button);
      item.setAttribute("aria-pressed", String(item === button));
    });
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
  const fields = new FormData(contactForm);
  const lines = [
    "¡Hola ROLIPA 3D! Quiero consultar por una impresión.",
    `Nombre: ${String(fields.get("nombre") || "").trim()}`,
    fields.get("email") ? `Email: ${String(fields.get("email")).trim()}` : "",
    `Consulta: ${fields.get("tipo")}`,
    `Idea: ${String(fields.get("mensaje") || "").trim()}`
  ].filter(Boolean);
  const url = `https://wa.me/5493446519687?text=${encodeURIComponent(lines.join("\n"))}`;
  window.open(url, "_blank", "noopener,noreferrer");
  formStatus.textContent = "Tu consulta está lista. Revisá el mensaje y tocá enviar en WhatsApp. Si no se abrió, usá el enlace de abajo.";
  formStatus.classList.add("show");
  let fallback = contactForm.querySelector(".whatsapp-fallback");
  if (!fallback) {
    fallback = document.createElement("a");
    fallback.className = "whatsapp-fallback text-link";
    fallback.textContent = "Abrir mi consulta en WhatsApp ↗";
    fallback.target = "_blank";
    fallback.rel = "noopener noreferrer";
    contactForm.append(fallback);
  }
  fallback.href = url;
});

const motionToggle = document.querySelector(".motion-toggle");
const merryScene = document.querySelector(".merry-scene");
if (motionToggle && merryScene) {
  const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
  let running = !preference.matches;
  const updateMotion = () => {
    merryScene.classList.toggle("motion-playing", running);
    merryScene.classList.toggle("motion-paused", !running);
    motionToggle.textContent = running ? "Pausar animación" : "Animar barco";
    motionToggle.setAttribute("aria-pressed", String(running));
  };
  motionToggle.addEventListener("click", () => { running = !running; updateMotion(); });
  updateMotion();
}
