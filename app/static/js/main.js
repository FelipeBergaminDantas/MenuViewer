// Ponto de entrada. Cada módulo é independente e só age se encontrar seus
// elementos na página — a página funciona sem JavaScript; aqui só melhoramos.
import { iniciarPreferencias } from "./preferencias.js";
import { iniciarFocoInicial } from "./foco.js";
import { iniciarFotoAmpliada } from "./foto.js";
import { iniciarVoz } from "./voz/voz.js";

iniciarPreferencias();
iniciarFocoInicial();
iniciarFotoAmpliada();
iniciarVoz();

// Página do QR Code: o botão de imprimir só aparece quando há JS para acioná-lo.
const botaoImprimir = document.querySelector("[data-imprimir]");
if (botaoImprimir) {
    botaoImprimir.hidden = false;
    botaoImprimir.addEventListener("click", () => window.print());
}
