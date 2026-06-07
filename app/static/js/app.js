// permite que o usuário feche os flashes
function prepararAlertas() {
  document.querySelectorAll("[data-alert-close]").forEach((botao) => {
    botao.addEventListener("click", () => {
      const alerta = botao.closest("[data-alert]");

      if (alerta) {
        alerta.remove(); // fecha
      }
    });
  });
}

// ver mais e ver menos
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
    // corta o texto
    texto.textContent = textoCompleto.slice(0, limite).trimEnd() + "... ";
    botao.textContent = "Ver mais";
  }

  botao.addEventListener("click", () => {
    montarDescricao(descricao, textoCompleto, limite, !expandido);
  });

  descricao.append(texto, botao);
}

// procura e corta as descrições longas
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

// TailwindCSS para pintar o botão de azul ou cinza
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

// intercepta os formulários de curtida para enviar os dados sem recarregar a tela inteira
function prepararCurtidas() {
  document.querySelectorAll("[data-like-form]").forEach((formulario) => {
    formulario.addEventListener("submit", async (evento) => {
      evento.preventDefault(); // previne que recarregue

      const botao = formulario.querySelector("button[type='submit']");
      const card = formulario.closest("article");
      const contador = card ? card.querySelector("[data-like-count]") : null;

      // desativa o botão
      if (botao) {
        botao.disabled = true;
        botao.classList.add("opacity-60", "cursor-not-allowed");
      }

      try {
        // envia a requisição silenciosamente para o servidor (PostController) usando a Fetch API
        const resposta = await fetch(formulario.action, {
          method: "POST",
          body: new FormData(formulario),
          headers: {
            Accept: "application/json",
            "X-Requested-With": "fetch", // avisa o Python que a requisição é do JS
          },
        });
        const dados = await resposta.json();

        // atualiza apenas o número de curtidas no HTML
        if (contador && typeof dados.likes === "number") {
          contador.textContent = textoLikes(dados.likes);
        }

        // se o servidor devolver 401 (não autorizado), redireciona pra tela de Login
        if (resposta.status === 401 && dados.redirect) {
          window.location.href = dados.redirect;
          return;
        }

        if (resposta.ok && botao && typeof dados.liked === "boolean") {
          aplicarEstadoCurtida(botao, dados.liked);
        }
      } catch (erro) {
        // se a requisição invisível falhar (ex: internet cair), tenta o envio normal recarregando a página
        formulario.submit();
      } finally {
        // reativa o botão independente de ter dado certo ou erro
        if (botao) {
          botao.disabled = false;
          botao.classList.remove("opacity-60", "cursor-not-allowed");
        }
      }
    });
  });
}

// Sistema de otimização pesada de performance para não travar o dispositivo do usuário
function prepararMidiasVisiveis() {
  const videos = document.querySelectorAll("[data-watch-video]");
  const gifs = document.querySelectorAll("[data-gif-src]");

  // Fallback: se for um navegador muito antigo, carrega tudo de uma vez
  if (!("IntersectionObserver" in window)) {
    gifs.forEach((gif) => {
      gif.src = gif.dataset.gifSrc;
    });
    return;
  }

  // O "IntersectionObserver" é um radar nativo que vigia quando um elemento entra na tela
  const observadorVideo = new IntersectionObserver(
    (entradas) => {
      entradas.forEach((entrada) => {
        const video = entrada.target;

        if (entrada.isIntersecting) {
          video.play().catch(() => {}); // Dá play automático se entrou na tela
        } else {
          video.pause(); // Pausa para economizar bateria se rolou para longe
        }
      });
    },
    { threshold: 0.55 } // Só engatilha quando 55% do vídeo estiver visível
  );

  const observadorGif = new IntersectionObserver(
    (entradas) => {
      entradas.forEach((entrada) => {
        const gif = entrada.target;

        if (entrada.isIntersecting) {
          gif.src = gif.dataset.gifSrc; // Baixa o GIF quando chega perto da tela
        } else {
          // Substitui o GIF por um pixel transparente quando sai da tela para liberar Memória RAM
          gif.src = "data:image/gif;base64,R0lGODlhAQABAAAAACw=";
        }
      });
    },
    { rootMargin: "120px 0px", threshold: 0.2 } // Começa a carregar 120px antes de aparecer pro usuário não perceber o delay
  );

  videos.forEach((video) => observadorVideo.observe(video));
  gifs.forEach((gif) => observadorGif.observe(gif));
}

// Só roda essas preparações depois que todo o HTML já foi desenhado pelo navegador
document.addEventListener("DOMContentLoaded", () => {
  prepararAlertas();
  prepararDescricoes();
  prepararCurtidas();
  prepararMidiasVisiveis();
});