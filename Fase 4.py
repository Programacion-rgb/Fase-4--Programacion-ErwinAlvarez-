from abc import ABC, abstractmethod
from datetime import datetime
import logging

# ==========================================
# 0. CONFIGURACIÓN DEL SISTEMA DE LOGS
# ==========================================
logging.basicConfig(
    filename='sistema_fj.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ==========================================
# 1. EXCEPCIONES PERSONALIZADAS
# ==========================================
class SoftwareFJError(Exception):
    """Excepción base para todos los errores del sistema Software FJ."""
    pass

class ClienteInvalidoError(SoftwareFJError):
    """Se lanza cuando los datos personales del cliente no cumplen las validaciones."""
    pass

class ServicioNoDisponibleError(SoftwareFJError):
    """Se lanza cuando ocurre un error en la disponibilidad o cálculo del servicio."""
    pass

class ReservaInvalidaError(SoftwareFJError):
    """Se lanza cuando se intenta procesar una reserva de forma incorrecta."""
    pass


# ==========================================
# 2. CLASE ABSTRACTA GENERAL (ENTIDAD)
# ==========================================
class EntidadSistema(ABC):
    """Clase abstracta que representa entidades generales dentro del sistema."""
    
    @abstractmethod
    def obtener_detalles(self):
        """Método abstracto obligatorio para retornar detalles de la entidad."""
        pass


# ==========================================
# 3. CLASE CLIENTE (Con encapsulación y validación)
# ==========================================
class Cliente(EntidadSistema):
    """Representa a un cliente de Software FJ con validaciones estrictas."""
    
    def __init__(self, cedula, nombre, correo):
        self.__cedula = cedula
        self.__nombre = nombre
        self.__correo = correo
        self._validar_datos()

    # Getters para encapsulamiento seguro
    @property
    def cedula(self):
        return self.__cedula

    @property
    def nombre(self):
        return self.__nombre

    @property
    def correo(self):
        return self.__correo

    def _validar_datos(self):
        """Valida que los datos del cliente cumplan con los criterios mínimos."""
        if not self.__cedula or not str(self.__cedula).isdigit() or len(str(self.__cedula)) < 6:
            raise ClienteInvalidoError(f"Cédula inválida o vacía: {self.__cedula}")
        if not self.__nombre or len(self.__nombre.strip()) < 3:
            raise ClienteInvalidoError(f"Nombre de cliente inválido: {self.__nombre}")
        if "@" not in self.__correo or "." not in self.__correo:
            raise ClienteInvalidoError(f"Correo electrónico inválido: {self.__correo}")

    def obtener_detalles(self):
        return f"Cliente: {self.__nombre} (Cédula: {self.__cedula}, Correo: {self.__correo})"


# ==========================================
# 4. CLASE ABSTRACTA SERVICIO Y ESPECIALIZACIONES
# ==========================================
class Servicio(EntidadSistema, ABC):
    """Clase abstracta que define los servicios ofrecidos por Software FJ."""
    
    def __init__(self, nombre_servicio, costo_base):
        self.nombre_servicio = nombre_servicio
        self.costo_base = costo_base

    @abstractmethod
    def calcular_costo(self, cantidad, **kwargs):
        """Método polimórfico para calcular costos según el servicio."""
        pass

    @abstractmethod
    def describir(self):
        """Método abstracto para la descripción única del servicio."""
        pass

    def obtener_detalles(self):
        return self.describir()


# Servicio Especializado 1: Reserva de Salas (con sobrecarga por parámetros opcionales)
class ReservaSala(Servicio):
    def __init__(self, nombre_servicio, costo_base, capacidad_personas):
        super().__init__(nombre_servicio, costo_base)
        self.capacidad_personas = capacidad_personas

    def calcular_costo(self, cantidad, descuento_porcentaje=0.0, incluir_impuesto=True):
        """Calcula el costo permitiendo sobrecarga mediante parámetros opcionales."""
        try:
            if cantidad <= 0:
                raise ServicioNoDisponibleError("Las horas de reserva deben ser mayores a cero.")
            
            subtotal = self.costo_base * cantidad
            descuento = subtotal * (descuento_porcentaje / 100.0)
            total = subtotal - descuento
            
            if incluir_impuesto:
                total *= 1.19  # Aplicación de IVA del 19%
            return round(total, 2)
        except Exception as e:
            logging.error(f"Error al calcular costo de sala: {e}")
            raise

    def describir(self):
        return f"[Reserva de Sala] {self.nombre_servicio} - Capacidad: {self.capacidad_personas} personas - Base: ${self.costo_base}"


# Servicio Especializado 2: Alquiler de Equipos
class AlquilerEquipo(Servicio):
    def __init__(self, nombre_servicio, costo_base, tipo_equipo):
        super().__init__(nombre_servicio, costo_base)
        self.tipo_equipo = tipo_equipo

    def calcular_costo(self, cantidad, seguro_adicional=False):
        """Calcula el costo del alquiler con opción de seguro diario."""
        try:
            if cantidad <= 0:
                raise ServicioNoDisponibleError("Los días de alquiler deben ser mayores a cero.")
            
            costo_total = self.costo_base * cantidad
            if seguro_adicional:
                costo_total += 20.0 * cantidad  # Costo fijo de seguro por día
            return round(costo_total, 2)
        except Exception as e:
            logging.error(f"Error al calcular alquiler de equipo: {e}")
            raise

    def describir(self):
        return f"[Alquiler de Equipo] {self.nombre_servicio} ({self.tipo_equipo}) - Base diaria: ${self.costo_base}"


# Servicio Especializado 3: Asesorías Especializadas
class AsesoriaEspecializada(Servicio):
    def __init__(self, nombre_servicio, costo_base, area_especialidad):
        super().__init__(nombre_servicio, costo_base)
        self.area_especialidad = area_especialidad

    def calcular_costo(self, cantidad, nivel_senior=False):
        """Calcula el costo de la asesoría con multiplicador si es nivel senior."""
        try:
            if cantidad <= 0:
                raise ServicioNoDisponibleError("El número de sesiones debe ser mayor a cero.")
            
            multiplicador = 1.5 if nivel_senior else 1.0
            return round(self.costo_base * cantidad * multiplicador, 2)
        except Exception as e:
            logging.error(f"Error al calcular costo de asesoría: {e}")
            raise

    def describir(self):
        return f"[Asesoría Especializada] {self.nombre_servicio} en {self.area_especialidad} - Base: ${self.costo_base}"


# ==========================================
# 5. CLASE RESERVA (Gestión integral y excepciones avanzadas)
# ==========================================
class Reserva:
    """Integra cliente, servicio, duración y estado con manejo robusto de excepciones."""
    
    def __init__(self, cliente: Cliente, servicio: Servicio, duracion: float):
        self.cliente = cliente
        self.servicio = servicio
        self.duracion = duracion
        self.estado = "Creada"
        self.costo_total = 0.0

    def confirmar_reserva(self, **kwargs):
        """Procesa la confirmación implementando try/except/else/finally y encadenamiento."""
        try:
            # Pasa la duración como parámetro único y desempaqueta opciones adicionales
            self.costo_total = self.servicio.calcular_costo(self.duracion, **kwargs)
            self.estado = "Confirmada"
            logging.info(f"Reserva confirmada con éxito para el cliente {self.cliente.nombre}.")
        except SoftwareFJError as se:
            self.estado = "Fallida"
            logging.error(f"Error controlado de negocio en reserva: {se}")
            raise ReservaInvalidaError(f"No se pudo completar la reserva de {self.servicio.nombre_servicio}") from se
        except Exception as e:
            self.estado = "Error Crítico"
            logging.critical(f"Error inesperado procesando reserva: {e}")
            raise
        else:
            print(f"-> [ÉXITO] Reserva procesada para {self.cliente.nombre}. Total a pagar: ${self.costo_total}")
        finally:
            print(f"   [Auditoría Interna] Estado final del intento de reserva: {self.estado}\n")

    def cancelar_reserva(self):
        """Permite cancelar la reserva si se encuentra confirmada."""
        if self.estado == "Confirmada":
            self.estado = "Cancelada"
            logging.info(f"Reserva cancelada para el cliente {self.cliente.nombre}.")
            print(f"-> La reserva de {self.servicio.nombre_servicio} ha sido cancelada exitosamente.")
        else:
            print(f"-> No se puede cancelar una reserva que se encuentra en estado '{self.estado}'.")


# ==========================================
# 6. SIMULACIÓN DE 10 OPERACIONES (Válidas e Inválidas)
# ==========================================
if __name__ == "__main__":
    print("==================================================")
    print("=== SISTEMA INTEGRAL SOFTWARE FJ - SIMULACIÓN ===")
    print("==================================================\n")

    operaciones_simuladas = [
        # Op 1: Operación válida - Reserva de Sala con descuento
        lambda: Reserva(Cliente("10123456", "Carlos Vives", "carlos@vives.com"), ReservaSala("Sala Ejecutiva", 60.0, 12), 4).confirmar_reserva(descuento_porcentaje=10),
        
        # Op 2: Operación inválida - Cliente con cédula incorrecta
        lambda: Reserva(Cliente("123", "Ana María", "ana@correo.com"), AlquilerEquipo("MacBook Pro", 40.0, "Laptop"), 2),
        
        # Op 3: Operación válida - Alquiler de Equipo con seguro adicional
        lambda: Reserva(Cliente("10987654", "Lucía Marín", "lucia@marin.com"), AlquilerEquipo("Servidor Local", 120.0, "Servidor"), 3).confirmar_reserva(seguro_adicional=True),
        
        # Op 4: Operación inválida - Duración negativa en sala
        lambda: Reserva(Cliente("10223344", "Jorge Arango", "jorge@arango.com"), ReservaSala("Sala Creativa", 50.0, 8), -1).confirmar_reserva(),
        
        # Op 5: Operación válida - Asesoría especializada nivel Senior
        lambda: Reserva(Cliente("10556677", "Diana Rey", "diana@rey.com"), AsesoriaEspecializada("Arquitectura Cloud", 200.0, "Cloud Computing"), 2).confirmar_reserva(nivel_senior=True),
        
        # Op 6: Operación inválida - Correo electrónico malformado
        lambda: Reserva(Cliente("10445566", "Pedro Picapiedra", "pedro-correo.com"), ReservaSala("Sala Básica", 30.0, 4), 2).confirmar_reserva(),
        
        # Op 7: Operación válida con flujo de cancelación posterior
        lambda: (lambda r: (r.confirmar_reserva(incluir_impuesto=False), r.cancelar_reserva()))(Reserva(Cliente("10778899", "Sofía Vergara", "sofia@vergara.com"), ReservaSala("Sala VIP", 150.0, 20), 2)),
        
        # Op 8: Operación inválida - Nombre de cliente demasiado corto
        lambda: Cliente("10889900", "Jo", "jo@correo.com"),
        
        # Op 9: Operación válida - Asesoría estándar (Junior)
        lambda: Reserva(Cliente("10332211", "Andrés Cepeda", "andres@cepeda.com"), AsesoriaEspecializada("Seguridad Ofensiva", 100.0, "Ciberseguridad"), 3).confirmar_reserva(nivel_senior=False),
        
        # Op 10: Operación inválida - Alquiler de equipo por 0 días
        lambda: Reserva(Cliente("10990011", "Tatiana Navas", "tatiana@navas.com"), AlquilerEquipo("Impresora 3D", 25.0, "Impresora"), 0).confirmar_reserva()
    ]

    for idx, operacion in enumerate(operaciones_simuladas, start=1):
        print(f"--- Ejecutando Operación Simulada #{idx} ---")
        try:
            operacion()
        except SoftwareFJError as err:
            print(f"[EXCEPCIÓN CONTROLADA DE NEGOCIO]: {err}\n")
        except Exception as err:
            print(f"[EXCEPCIÓN CRÍTICA INESPERADA]: {err}\n")
        print("-" * 55)

    print("\n=== SIMULACIÓN COMPLETADA CON ÉXITO ===")
    print("Los eventos y errores han sido registrados de forma persistente en 'sistema_fj.log'.")