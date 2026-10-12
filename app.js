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
    const count = Array.from(productCards).filter(card => !card.hidden).length;
    const counter = document.querySelector(".catalog-count");
    if (counter) counter.textContent = `${count} ${count === 1 ? "pieza" : "piezas"} · ${filter === "Todos" ? "Todas las categorías" : filter}`;
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
  const ship = merryScene.querySelector(".roaming-ship");
  let voyage;
  const setVoyage = () => {
    if (!ship || !ship.animate) return;
    if (voyage) voyage.cancel();
    const right = Math.max(0, window.innerWidth - ship.offsetWidth - 12);
    const bottom = Math.max(0, window.innerHeight - ship.offsetHeight - 80);
    voyage = ship.animate([
      {transform:`translate3d(12px,${window.innerHeight * .16}px,0)`},
      {transform:`translate3d(${right}px,${window.innerHeight * .25}px,0)`},
      {transform:`translate3d(${right}px,${bottom}px,0)`},
      {transform:`translate3d(${right * .35}px,${bottom * .75}px,0)`},
      {transform:`translate3d(12px,${window.innerHeight * .4}px,0)`},
      {transform:`translate3d(12px,${window.innerHeight * .16}px,0)`}
    ], {duration:22000,iterations:Infinity,easing:"linear"});
    if (!running) voyage.pause();
  };
  const updateMotion = () => {
    merryScene.classList.toggle("motion-playing", running);
    merryScene.classList.toggle("motion-paused", !running);
    motionToggle.textContent = running ? "Pausar animación" : "Animar barco";
    motionToggle.setAttribute("aria-pressed", String(running));
    if (voyage) running ? voyage.play() : voyage.pause();
  };
  motionToggle.addEventListener("click", () => { running = !running; updateMotion(); });
  setVoyage();
  window.addEventListener("resize", setVoyage);
  updateMotion();
}

const gallery = document.querySelector(".piece-gallery");
const galleryCards = Array.from(document.querySelectorAll(".real-product"));
let galleryIndex = 0;
let photoIndex = 0;
let galleryOpener;
let activePhotos = [];
const showPhoto = (index) => {
  photoIndex = (index + activePhotos.length) % activePhotos.length;
  const title = galleryCards[galleryIndex].querySelector("h3").textContent;
  const image = gallery.querySelector(".gallery-image");
  image.src = activePhotos[photoIndex];
  image.alt = `${title} · Vista ${photoIndex + 1}`;
  gallery.querySelector(".gallery-counter").textContent = `Foto ${photoIndex + 1} de ${activePhotos.length}`;
  gallery.querySelectorAll(".gallery-thumbnails button").forEach((button, i) => {
    button.classList.toggle("selected", i === photoIndex);
    button.setAttribute("aria-pressed", String(i === photoIndex));
  });
  gallery.querySelector(".gallery-prev").disabled = activePhotos.length < 2;
  gallery.querySelector(".gallery-next").disabled = activePhotos.length < 2;
};
const showPiece = (index) => {
  galleryIndex = index;
  const card = galleryCards[index];
  activePhotos = JSON.parse(card.dataset.photos);
  gallery.querySelector("#gallery-title").textContent = card.querySelector("h3").textContent;
  gallery.querySelector(".gallery-instagram").href = card.querySelector(".instagram-source").href;
  const thumbnails = gallery.querySelector(".gallery-thumbnails");
  thumbnails.replaceChildren();
  activePhotos.forEach((src, i) => {
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("aria-label", `Ver ángulo ${i + 1}`);
    const image = document.createElement("img");
    image.src = src;
    image.alt = "";
    button.append(image);
    button.addEventListener("click", () => showPhoto(i));
    thumbnails.append(button);
  });
  showPhoto(0);
};
if (gallery && galleryCards.length) {
  galleryCards.forEach((card, index) => {
    card.querySelectorAll("[data-gallery-open], .piece-gallery-button").forEach((opener) => {
      opener.addEventListener("click", (event) => {
        event.preventDefault();
        galleryOpener = opener;
        showPiece(index);
        gallery.showModal();
        document.body.classList.add("gallery-is-open");
      });
    });
  });
  gallery.querySelector(".gallery-close").addEventListener("click", () => gallery.close());
  gallery.querySelector(".gallery-prev").addEventListener("click", () => showPhoto(photoIndex - 1));
  gallery.querySelector(".gallery-next").addEventListener("click", () => showPhoto(photoIndex + 1));
  gallery.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft") { event.preventDefault(); showPhoto(photoIndex - 1); }
    if (event.key === "ArrowRight") { event.preventDefault(); showPhoto(photoIndex + 1); }
  });
  let touchStartX;
  const photoArea = gallery.querySelector(".gallery-image-wrap");
  photoArea.addEventListener("touchstart", (event) => { touchStartX = event.changedTouches[0].clientX; }, {passive:true});
  photoArea.addEventListener("touchend", (event) => {
    const distance = event.changedTouches[0].clientX - touchStartX;
    if (Math.abs(distance) > 50) showPhoto(photoIndex + (distance < 0 ? 1 : -1));
  }, {passive:true});
  gallery.addEventListener("click", (event) => { if (event.target === gallery) gallery.close(); });
  gallery.addEventListener("close", () => {
    document.body.classList.remove("gallery-is-open");
    if (galleryOpener) galleryOpener.focus();
  });
}
