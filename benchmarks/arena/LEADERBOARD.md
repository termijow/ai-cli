# 🏆 Leaderboard Consolidado de la Arena de Modelos Locales (Loop Engineering Harness)

Evaluación en hardware real: **AMD Radeon RX 6600 (8 GB VRAM)** bajo Vulkan en Windows 11.  
Incluye verificación profunda mediante **simulación de DOM en Node.js**, chequeo de scope en JavaScript, prevención de CSS bloqueante (`pointer-events: none`), Web Audio API procedimental y bucle continuo con acumulador de tiempo.

| Pos | Modelo | Puntuación | Iteraciones | Tokens Sesión | Velocidad Media | Tiempo Total | Jugabilidad / Calificación Humana | Archivo Generado |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---|:---|
| **1** | **gemma-4-E2B-it-UD-Q6_K_XL.gguf** | **100/100** | 2 | 14,674 | **33.38 t/s** | **303.0 s (5.0 min)** | ⭐ **Top Viable** (Rápido, 100% interactivo, audio, partículas) | [snake.html](file:///C:/Users/USUARIO/Documents/ai-cli/benchmarks/arena/gemma-4-E2B-it-UD-Q6_K_XL/snake.html) |
| **2** | **Qwen3.6-35B-A3B-UD-IQ2_XXS.gguf** | **100/100** | 3 | 30,227 | 1.01 t/s | 29,880 s (8.3 h) | 🏆 **Top Calidad Visual/Lógica** (Perfecto, pero muy lento para tareas interactivas) | [snake.html](file:///C:/Users/USUARIO/Documents/ai-cli/benchmarks/arena/Qwen3.6-35B-A3B-UD-IQ2_XXS/snake.html) |
| **3** | **gemma-4-E4B-it-UD-Q6_K_XL.gguf** | **93/100** | 4 | 43,682 | **15.68 t/s** | 1,426.8 s (23.7 min) | ⭐ **Top 2** (UI Cyberpunk cuidada, audio procedimental, D-Pad) | [snake.html](file:///C:/Users/USUARIO/Documents/ai-cli/benchmarks/arena/gemma-4-E4B-it-UD-Q6_K_XL/snake.html) |
| 4 | **gemma-4-E4B-it-Q6_K.gguf** | **100/100** | 2 | 15,224 | 16.57 t/s | 918.4 s (15.3 min) | Funcional tras reparación en iteración 2 | [snake.html](file:///C:/Users/USUARIO/Documents/ai-cli/benchmarks/arena/gemma-4-E4B-it-Q6_K/snake.html) |
| 5 | **gemma-4-E2B-it-Q8_0.gguf** | **100/100** | 2 | 13,875 | 34.05 t/s | 407.5 s (6.8 min) | Parcheado (tenía pointer-events: none en overlay) | [snake.html](file:///C:/Users/USUARIO/Documents/ai-cli/benchmarks/arena/gemma-4-E2B-it-Q8_0/snake.html) |
| 6 | **Qwen3.5-9B-Q4_K_M.gguf** | 85/100 | 1 | 8,920 | 8.92 t/s | 1,000.0 s | Parcheado (tenía variable `btns` fuera de scope) | [snake.html](file:///C:/Users/USUARIO/Documents/ai-cli/benchmarks/arena/Qwen3.5-9B-Q4_K_M/snake.html) |
| 7 | **Ternary-Bonsai-2-27B-PTQ1_0.gguf** | 75/100 | 2 | 16,400 | 5.42 t/s | 3,025.0 s | UI bonita, pero el loop de juego tiene fallos | [snake.html](file:///C:/Users/USUARIO/Documents/ai-cli/benchmarks/arena/Ternary-Bonsai-2-27B-PTQ1_0/snake.html) |
| 8 | **gemma-4-26B-A4B-it-UD-IQ2_XXS.gguf** | 60/100 | 2 | 18,200 | 1.84 t/s | 9,890.0 s | Juego no jugable, visualmente deficiente | [snake.html](file:///C:/Users/USUARIO/Documents/ai-cli/benchmarks/arena/gemma-4-26B-A4B-it-UD-IQ2_XXS/snake.html) |
| 9 | **Ling-3.0-tiny-Q4_K_M.gguf** | 40/100 | 1 | 9,150 | 18.20 t/s | 502.0 s | Muy pobre en calidad lógica y visual | [snake.html](file:///C:/Users/USUARIO/Documents/ai-cli/benchmarks/arena/Ling-3.0-tiny-Q4_K_M/snake.html) |
| 10 | **Qwen3.5-0.8B-Q4_K_M.gguf** | 25/100 | 1 | 4,200 | 45.00 t/s | 93.0 s | Demasiado pequeño, no comprende la totalidad del reto | [snake.html](file:///C:/Users/USUARIO/Documents/ai-cli/benchmarks/arena/Qwen3.5-0.8B-Q4_K_M/snake.html) |
