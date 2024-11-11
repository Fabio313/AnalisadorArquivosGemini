document
  .getElementById("uploadForm")
  .addEventListener("submit", async function (event) {
    event.preventDefault();

    const fileInput = document.getElementById("fileInput");
    const resultSection = document.getElementById("result");

    // Verificar se há um arquivo
    if (fileInput.files.length === 0) {
      resultSection.innerHTML = "<p>Por favor, envie um arquivo.</p>";
      return;
    }

    const file = fileInput.files[0];

    // Extraindo a extensão do arquivo
    const fileExtension = file.name.split(".").pop();

    // Exibindo a extensão do arquivo na tela
    resultSection.innerHTML = `<p>Extensão do arquivo: .${fileExtension}</p>`;
    resultSection.classList.add("result-show");

    // Fazer a requisição à API (comentado)
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("http://127.0.0.1:8000/process-file/", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Erro ao processar o arquivo");
      }

      const data = await response.json();
      resultSection.innerHTML = `<p>Resultado: ${data.analysis}</p>`;
    } catch (error) {
      resultSection.innerHTML = error;
    }
  });
