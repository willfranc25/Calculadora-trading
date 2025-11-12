# Arena All-Star Battle Engine

Este repositorio ahora contiene un prototipo de motor de combate por turnos inspirado en los juegos gacha de arena. El objetivo es ofrecer una base modular y fácilmente extensible para experimentar con batallas 6v6 llenas de sinergias, eventos y decisiones estratégicas autónomas.

## Características destacadas

- **IA autónoma**: cada combatiente analiza la batalla y decide qué habilidad usar gracias a un módulo de IA heurística.
- **Sistema de turnos ATB**: la línea de tiempo dinámica permite que los personajes rápidos actúen con más frecuencia.
- **Eventos y triggers**: habilidades, pasivas y efectos de campo pueden reaccionar a más de 20 eventos distintos (inicio/final de turno, recibir daño, curación, muerte de aliados, etc.).
- **Habilidades y estados**: soporte para ataques, curaciones, buffs/debuffs con duración, acumulación y modificadores de estadísticas.
- **Recursos personalizados**: cada personaje puede definir barras como maná, furia o energía con regeneración, costos y ganancias por evento.
- **Efectos de campo**: climas, auras y zonas que alteran estadísticas o interacciones por etiquetas.
- **UI textual**: registro descriptivo de combate y ventana de estadísticas actualizada en tiempo real.

## Estructura del proyecto

- `arena/` contiene los módulos del motor (eventos, habilidades, recursos, efectos, IA, etc.).
- `main.py` ejecuta una simulación de ejemplo entre dos equipos preconfigurados.

## Ejecutar la demo

```bash
python main.py
```

Al finalizar se imprimirá el registro de combate y el estado completo de cada combatiente, incluyendo estadísticas, efectos activos, recursos y enfriamientos.

## Próximos pasos sugeridos

- Añadir más tipos de habilidades (control, invocaciones, transformaciones).
- Implementar un sistema visual con animaciones usando un motor gráfico.
- Persistir configuraciones de personajes en archivos YAML/JSON para facilitar el modding.
