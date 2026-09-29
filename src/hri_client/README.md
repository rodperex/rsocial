# hri_client

Cliente reutilizable para servicios de simple_hri (STT, TTS, Extract, YesNo).

## Descripción

Este paquete proporciona una clase `HRIClient` que encapsula la funcionalidad de interacción humano-robot (HRI) proporcionada por `simple_hri`, facilitando su uso en aplicaciones y behavior trees.

## Características

- **Speech-to-Text (STT)**: Transcribir audio a texto
- **Text-to-Speech (TTS)**: Convertir texto a audio y reproducirlo
- **Extract**: Extraer información específica de un texto (ej. nombres, colores, números)
- **YesNo**: Detectar respuestas afirmativas/negativas en un texto
- API asíncrona con métodos `start_*`, `is_*_done()` y `get_*_result()`
- Suscripción al topic `/listened_text` para recibir actualizaciones de STT

## Uso

La API es asíncrona y **no bloqueante**: se lanza una operación con `start_*()` y en
cada ciclo de control se consulta `is_*_done()`. Así el nodo sigue procesando
callbacks mientras el robot habla o escucha. Ver `hri_examples/hri_example_client.py`.

```python
import rclpy
from rclpy.node import Node
from hri_client.hri_client import HRIClient


class MyNode(Node):
    def __init__(self):
        super().__init__('my_node')
        self.hri = HRIClient(self)
        if not self.hri.wait_for_services(5.0):
            self.get_logger().error('Servicios HRI no disponibles')

        self.state = 'SAY'
        self.timer = self.create_timer(0.1, self.control_cycle)

    def control_cycle(self):
        if self.state == 'SAY':
            self.hri.start_speaking('Hola, ¿cómo te llamas?')
            self.state = 'WAIT_SAY'

        elif self.state == 'WAIT_SAY' and self.hri.is_speaking_done():
            self.hri.start_listen()  # graba por el micrófono y transcribe
            self.state = 'WAIT_LISTEN'

        elif self.state == 'WAIT_LISTEN' and self.hri.is_listen_done():
            self.hri.start_extract('nombre', self.hri.get_listened_text())
            self.state = 'WAIT_NAME'

        elif self.state == 'WAIT_NAME' and self.hri.is_extract_done():
            self.get_logger().info(f'Nombre: {self.hri.get_extracted_info()}')
            self.state = 'DONE'


def main():
    rclpy.init()
    rclpy.spin(MyNode())
```

| Operación | Iniciar | ¿Terminada? | Resultado |
|---|---|---|---|
| STT | `start_listen()` | `is_listen_done()` | `get_listened_text()` |
| TTS | `start_speaking(text)` | `is_speaking_done()` | `get_speaking_result()` |
| Extract | `start_extract(interest, text)` | `is_extract_done()` | `get_extracted_info()` |
| YesNo | `start_yesno(text)` | `is_yesno_done()` | `get_yesno_result()` (`"yes"`/`"no"`) |

Solo STT graba audio. Extract y YesNo trabajan sobre un texto, normalmente el
obtenido con `start_listen()`. Si falla, `simple_hri` devuelve un resultado que
empieza por `ERROR`, y la operación termina en error. Si Extract no encuentra
nada, devuelve `NONE`.

### Timeout, cancelación y *feedback*

Escuchar y hablar usan las **acciones** de `simple_hri` (`/stt_action`, `/tts_action`);
extraer información y sí/no usan sus **servicios**.

| Método | Comportamiento |
|---|---|
| `start_listen(timeout_sec)` | El servidor deja de grabar si nadie empieza a hablar en `timeout_sec` → `TIMEOUT`; si habla, espera a que termine |
| `cancel_listen()` | El servidor deja de grabar |
| `is_speaking_done()` | `True` cuando termina de verdad la reproducción |
| `cancel_speaking()` | El servidor corta el audio |
| `get_listen_feedback()` | `listening`, `speech_detected`, `transcribing` |
| `get_speaking_feedback()` | Segundos que faltan |

- Todos los `start_*()` aceptan `timeout_sec` (por defecto, sin límite). Si vence,
  `is_*_done()` devuelve `True` con el estado `TIMEOUT`. En Extract y YesNo el
  *timeout* es del cliente: la respuesta que llegue tarde se descarta.
- `cancel_*()` termina la operación con el estado `CANCELED`.
- `get_*_state()` devuelve el `OperationState` (`COMPLETED`, `ERROR`, `TIMEOUT`,
  `CANCELED`...) para saber cómo terminó cada operación.

```python
self.hri.start_listen(timeout_sec=8.0)
...
if self.hri.is_listen_done():
    if self.hri.get_listen_state() == OperationState.TIMEOUT:
        self.hri.start_speaking('No te he oído. ¿Quieres ir a comer?')  # reformular
```

## Dependencias

- rclpy
- std_msgs
- simple_hri_interfaces (con las acciones `Listen` y `Say`)
- action_msgs
