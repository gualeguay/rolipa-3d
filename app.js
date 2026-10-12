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
  const cursorDevice = window.matchMedia("(hover: hover) and (pointer: fine)");
  let running = !preference.matches;
  const ship = merryScene.querySelector(".roaming-ship");
  let voyage;
  let frame;
  let lastTime;
  let x = 20;
  let y = window.innerHeight * .4;
  let targetX = x;
  let targetY = y;
  const limits = () => ({
    right: Math.max(0, window.innerWidth - ship.offsetWidth - 8),
    bottom: Math.max(0, window.innerHeight - ship.offsetHeight - 12)
  });
  const sailToCursor = (time) => {
    if (!running || !cursorDevice.matches || !ship) { frame = undefined; return; }
    const seconds = lastTime === undefined ? 0 : Math.min((time - lastTime) / 1000, .1);
    lastTime = time;
    const dx = targetX - x;
    const dy = targetY - y;
    const distance = Math.hypot(dx, dy);
    // Ease into the destination and cap sailing speed at 65 pixels per second.
    const step = Math.min(distance * (1 - Math.exp(-seconds * 1.15)), 65 * seconds);
    if (distance > .2) { x += dx / distance * step; y += dy / distance * step; }
    ship.style.transform = `translate3d(${x}px, ${y}px, 0)`;
    frame = window.requestAnimationFrame(sailToCursor);
  };
  const syncMovement = () => {
    if (!ship) return;
    if (voyage) { voyage.cancel(); voyage = undefined; }
    if (frame !== undefined) { window.cancelAnimationFrame(frame); frame = undefined; }
    lastTime = undefined;
    const bounds = limits();
    x = Math.max(0, Math.min(x, bounds.right));
    y = Math.max(0, Math.min(y, bounds.bottom));
    targetX = Math.max(0, Math.min(targetX, bounds.right));
    targetY = Math.max(0, Math.min(targetY, bounds.bottom));
    ship.style.transform = `translate3d(${x}px, ${y}px, 0)`;
    if (cursorDevice.matches) {
      if (running) frame = window.requestAnimationFrame(sailToCursor);
    } else if (ship.animate) {
      voyage = ship.animate([
        {transform:`translate3d(12px,${window.innerHeight * .16}px,0)`},
        {transform:`translate3d(${bounds.right}px,${window.innerHeight * .25}px,0)`},
        {transform:`translate3d(${bounds.right}px,${bounds.bottom}px,0)`},
        {transform:`translate3d(${bounds.right * .35}px,${bounds.bottom * .75}px,0)`},
        {transform:`translate3d(12px,${window.innerHeight * .4}px,0)`},
        {transform:`translate3d(12px,${window.innerHeight * .16}px,0)`}
      ], {duration:52000,iterations:Infinity,easing:"linear"});
      if (!running) voyage.pause();
    }
  };
  window.addEventListener("pointermove", (event) => {
    if (!ship || !cursorDevice.matches || event.pointerType === "touch") return;
    const bounds = limits();
    targetX = Math.max(0, Math.min(event.clientX - ship.offsetWidth / 2, bounds.right));
    targetY = Math.max(0, Math.min(event.clientY - ship.offsetHeight / 2 + 20, bounds.bottom));
  }, {passive:true});
  const updateMotion = () => {
    merryScene.classList.toggle("motion-playing", running);
    merryScene.classList.toggle("motion-paused", !running);
    motionToggle.textContent = running ? "Pausar animación" : "Animar barco";
    motionToggle.setAttribute("aria-pressed", String(running));
    syncMovement();
  };
  motionToggle.addEventListener("click", () => { running = !running; updateMotion(); });
  window.addEventListener("resize", syncMovement);
  if (cursorDevice.addEventListener) cursorDevice.addEventListener("change", syncMovement);
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

// Keep the header aligned with the section the visitor is reading.
if ("IntersectionObserver" in window) {
  const sectionLinks = Array.from(document.querySelectorAll("nav a[href^='#']"));
  const sectionObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      sectionLinks.forEach((link) => {
        const current = link.getAttribute("href") === `#${entry.target.id}`;
        link.classList.toggle("nav-current", current);
        if (current) link.setAttribute("aria-current", "location");
        else link.removeAttribute("aria-current");
      });
    });
  }, {rootMargin:"-15% 0px -55% 0px",threshold:0});
  document.querySelectorAll("#catalogo, #proceso, #contacto").forEach((section) => sectionObserver.observe(section));
}

const chestTrigger = document.querySelector(".chest-trigger");
const chestTreasures = document.querySelector("#chest-treasures");
if (chestTrigger && chestTreasures) {
  chestTrigger.addEventListener("click", () => {
    const opened = chestTrigger.getAttribute("aria-expanded") !== "true";
    chestTrigger.setAttribute("aria-expanded", String(opened));
    chestTreasures.hidden = !opened;
    chestTrigger.classList.toggle("chest-open", opened);
    chestTrigger.querySelector(".chest-action").textContent = opened ? "Cerrar el cofre ↑" : "Abrir el cofre ↓";
  });
}
document.querySelectorAll("[data-open-piece]").forEach((button) => {
  button.addEventListener("click", () => {
    const slug = button.dataset.openPiece;
    const index = galleryCards.findIndex(card => JSON.parse(card.dataset.photos).some(src => src.startsWith(`products/${slug}-angle-`)));
    if (index < 0 || !gallery) return;
    galleryOpener = button;
    showPiece(index);
    gallery.showModal();
    document.body.classList.add("gallery-is-open");
  });
});
