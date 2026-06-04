function prepararAlertas() {
  document.querySelectorAll("[data-alert-close]").forEach((botao) => {
    botao.addEventListener("click", () => {
      const alerta = botao.closest("[data-alert]");

      if (alerta) {
        alerta.remove();
      }
    });
  });
}

function montarDescricao(descricao, textoCompleto, limite, expandido) {
  descricao.textContent = "";

  const texto = document.createElement("span");
  const botao = document.createElement("button");

  texto.className = "break-words";
  texto.style.overflowWrap = "anywhere";
  botao.type = "button";
  botao.className = "inline text-blue-600 font-medium hover:underline";

  if (expandido) {
    texto.textContent = textoCompleto + " ";
    botao.textContent = "Ver menos";
  } else {
    texto.textContent = textoCompleto.slice(0, limite).trimEnd() + "... ";
    botao.textContent = "Ver mais";
  }

  botao.addEventListener("click", () => {
    montarDescricao(descricao, textoCompleto, limite, !expandido);
  });

  descricao.append(texto, botao);
}

function prepararDescricoes() {
  document.querySelectorAll("[data-description]").forEach((descricao) => {
    const limite = Number(descricao.dataset.limit || 180);
    const textoCompleto = descricao.textContent.trim();

    if (textoCompleto.length <= limite) {
      descricao.textContent = textoCompleto;
      return;
    }

    montarDescricao(descricao, textoCompleto, limite, false);
  });
}

function textoLikes(total) {
  return `${total} ${total === 1 ? "like" : "likes"}`;
}

function aplicarEstadoCurtida(botao, curtido) {
  botao.dataset.liked = curtido ? "true" : "false";
  botao.textContent = curtido ? "Curtido" : "Curtir";

  botao.classList.toggle("bg-blue-600", curtido);
  botao.classList.toggle("text-white", curtido);
  botao.classList.toggle("hover:bg-blue-700", curtido);
  botao.classList.toggle("shadow-sm", curtido);
  botao.classList.toggle("bg-slate-100", !curtido);
  botao.classList.toggle("text-slate-700", !curtido);
  botao.classList.toggle("hover:bg-slate-200", !curtido);
}

function prepararCurtidas() {
  document.querySelectorAll("[data-like-form]").forEach((formulario) => {
    formulario.addEventListener("submit", async (evento) => {
      evento.preventDefault();

      const botao = formulario.querySelector("button[type='submit']");
      const card = formulario.closest("article");
      const contador = card ? card.querySelector("[data-like-count]") : null;

      if (botao) {
        botao.disabled = true;
        botao.classList.add("opacity-60", "cursor-not-allowed");
      }

      try {
        const resposta = await fetch(formulario.action, {
          method: "POST",
          body: new FormData(formulario),
          headers: {
            Accept: "application/json",
            "X-Requested-With": "fetch",
          },
        });
        const dados = await resposta.json();

        if (contador && typeof dados.likes === "number") {
          contador.textContent = textoLikes(dados.likes);
        }

        if (resposta.status === 401 && dados.redirect) {
          window.location.href = dados.redirect;
          return;
        }

        if (resposta.ok && botao && typeof dados.liked === "boolean") {
          aplicarEstadoCurtida(botao, dados.liked);
        }
      } catch (erro) {
        formulario.submit();
      } finally {
        if (botao) {
          botao.disabled = false;
          botao.classList.remove("opacity-60", "cursor-not-allowed");
        }
      }
    });
  });
}

function prepararMidiasVisiveis() {
  const videos = document.querySelectorAll("[data-watch-video]");
  const gifs = document.querySelectorAll("[data-gif-src]");

  if (!("IntersectionObserver" in window)) {
    gifs.forEach((gif) => {
      gif.src = gif.dataset.gifSrc;
    });
    return;
  }

  const observadorVideo = new IntersectionObserver(
    (entradas) => {
      entradas.forEach((entrada) => {
        const video = entrada.target;

        if (entrada.isIntersecting) {
          video.play().catch(() => {});
        } else {
          video.pause();
        }
      });
    },
    { threshold: 0.55 }
  );

  const observadorGif = new IntersectionObserver(
    (entradas) => {
      entradas.forEach((entrada) => {
        const gif = entrada.target;

        if (entrada.isIntersecting) {
          gif.src = gif.dataset.gifSrc;
        } else {
          gif.src = "data:image/gif;base64,R0lGODlhAQABAAAAACw=";
        }
      });
    },
    { rootMargin: "120px 0px", threshold: 0.2 }
  );

  videos.forEach((video) => observadorVideo.observe(video));
  gifs.forEach((gif) => observadorGif.observe(gif));
}

document.addEventListener("DOMContentLoaded", () => {
  prepararAlertas();
  prepararDescricoes();
  prepararCurtidas();
  prepararMidiasVisiveis();
});
