// Función para obtener el último usuario desde la API
async function fetchLatestUser() {
  try {
    const response = await fetch("/api/latest_user");
    if (!response.ok) {
      throw new Error("Error al obtener el último usuario");
    }

    const data = await response.json();

    // Actualizar datos en el DOM
    const welcomeMessage = document.getElementById("welcome-message");
    const avatarImg = document.getElementById("avatar");

    if (data.name) {
      welcomeMessage.textContent = `Bienvenido, ${data.name}!`;
    } else {
      welcomeMessage.textContent = "Bienvenido, Anónimo!";
    }

    if (data.avatar) {
      avatarImg.src = data.avatar;
      avatarImg.style.display = "block";
    } else {
      avatarImg.style.display = "none";
    }
  } catch (error) {
    console.error("Error al cargar el usuario:", error);
    document.getElementById("welcome-message").textContent =
      "No se pudo cargar el usuario. Intenta nuevamente.";
  }
}

// Función para generar un color aleatorio
function generateRandomColor() {
  const r = Math.floor(Math.random() * 256);
  const g = Math.floor(Math.random() * 256);
  const b = Math.floor(Math.random() * 256);
  return `rgb(${r}, ${g}, ${b})`;
}

// Convertir color HEX a RGB
function hexToRgb(hex) {
  const bigint = parseInt(hex.substring(1), 16);
  const r = (bigint >> 16) & 255;
  const g = (bigint >> 8) & 255;
  const b = bigint & 255;
  return { r, g, b };
}

// Calcular distancia entre colores RGB
function calculateColorDistance(rgb1, rgb2) {
  return Math.sqrt(
    Math.pow(rgb1.r - rgb2.r, 2) +
    Math.pow(rgb1.g - rgb2.g, 2) +
    Math.pow(rgb1.b - rgb2.b, 2)
  );
}

// Calcular puntaje basado en la distancia
function calculateScore(distance) {
  const maxDistance = Math.sqrt(3 * Math.pow(255, 2)); // Distancia máxima
  return Math.round(100 * (1 - distance / maxDistance));
}

// Inicializar el color objetivo
let targetColor = generateRandomColor();
document.getElementById("target-color").style.backgroundColor = targetColor;

// Función para verificar el color seleccionado
function checkUserColor() {
  const colorPicker = document.getElementById("color-picker");
  const userColor = hexToRgb(colorPicker.value);

  // Convertir color objetivo a RGB
  const targetRgb = targetColor.match(/\d+/g).map(Number);
  const targetColorRgb = { r: targetRgb[0], g: targetRgb[1], b: targetRgb[2] };

  // Calcular distancia y puntaje
  const distance = calculateColorDistance(userColor, targetColorRgb);
  const score = calculateScore(distance);

  // Actualizar puntaje en el DOM
  document.getElementById("score-value").textContent = score;

  alert(`Tu puntaje es: ${score}`);
}

// Agregar evento al botón de verificación
document.getElementById("check-color").addEventListener("click", checkUserColor);

// Cargar el usuario más reciente y mostrarlo en la página
fetchLatestUser();
