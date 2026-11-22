/**
 * Envio do arquivo de vídeo direto para a Cloudflare Stream.
 *
 * O backend apenas negocia a URL de upload de uso único (o arquivo nunca passa
 * pelo nosso servidor). Usa `XMLHttpRequest` para reportar o progresso, já que
 * `fetch` não expõe o andamento do envio.
 *
 * Método básico por `POST` multipart: recomendado para arquivos até 200 MB,
 * o que cobre com folga o limite de 15 minutos por aula.
 */

export function uploadVideoToCloudflare(
  uploadUrl: string,
  file: File,
  onProgress: (percent: number) => void,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open("POST", uploadUrl);

    request.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    });

    request.addEventListener("load", () => {
      if (request.status >= 200 && request.status < 300) {
        resolve();
      } else {
        reject(new Error(`A Cloudflare recusou o envio do vídeo (status ${request.status}).`));
      }
    });

    request.addEventListener("error", () => {
      reject(new Error("Falha de rede ao enviar o vídeo. Tente novamente."));
    });

    // O navegador define o `Content-Type` (multipart) com o boundary correto.
    const form = new FormData();
    form.append("file", file);
    request.send(form);
  });
}
