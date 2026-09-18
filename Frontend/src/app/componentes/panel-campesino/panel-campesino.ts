import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { SiteFooterComponent } from '../site-footer/site-footer';
import { AuthService } from '../../services/auth';
import { CrudService } from '../../services/crud';
import { timeout } from 'rxjs';

@Component({
  selector: 'app-panel-campesino',
  standalone: true,
  imports: [FormsModule, RouterLink, SiteFooterComponent],
  templateUrl: './panel-campesino.html',
  styleUrl: '../panels.css'
})
export class PanelCampesinoComponent implements OnInit {
  usuario;
  residuosDisponibles: any[] = [];
  readonly tiposSensoresDisponibles = ['Temperatura', 'pH', 'Humedad'];
  mensajeError = '';
  mensajeExito = '';
  mensajeConfirmacionSensor = '';
  seccionActual: 'sensores' | 'materiales' | 'solicitarSensor' | 'solicitarResiduo' = 'sensores';
  solicitud = { tipo_sensores: [] as string[], fecha_entrega_deseada: '' };
  solicitudResiduo = { tipo_residuo: '', presencia_citricos: '', cantidad_kg: null as number | null, precio_ofrecido_campesino: null as number | null, ubicacion: '', latitud: null as number | null, longitud: null as number | null };
  precioOfrecidoTexto = '';
  solicitudSensorEnviada = false;
  solicitudSensorEnviandose = false;
  solicitudResiduoEnviada = false;
  asignaciones: any[] = [];
  solicitudesResiduo: any[] = [];
  solicitudesSensor: any[] = [];
  conexionThingSpeak: Record<number, { thingspeak_channel_id: string; thingspeak_read_api_key: string }> = {};
  recomendacionesIa: any[] = [];
  fechaMinimaEntrega = this.obtenerFechaLocalActual();
  diagnosticoCultivo: any = null;
  diagnosticoCargando = false;
  mensajeDiagnostico = '';
  tipoMensajeDiagnostico: 'error' | 'success' = 'error';
  formularioDiagnostico = {
    tipo_cultivo: 'Papa',
    fase_cultivo: 'Crecimiento',
    area_cultivo_m2: null as number | null,
    origen_datos: 'SENSOR' as 'SENSOR' | 'MANUAL',
    temperatura: null as number | null,
    humedad_ambiente: null as number | null,
    ph_suelo: null as number | null,
    observaciones_visuales: '',
    latitud: null as number | null,
    longitud: null as number | null,
  };

  constructor(
    public auth: AuthService,
    private crud: CrudService,
    private cdr: ChangeDetectorRef
  ) {
    this.usuario = this.auth.obtenerUsuario();
  }

  ngOnInit(): void {
    this.cargar();
    this.obtenerUbicacionResiduo();
    this.cargarLecturaThingSpeak();
  }

  cambiarSeccion(seccion: 'sensores' | 'materiales' | 'solicitarSensor' | 'solicitarResiduo'): void {
    this.seccionActual = seccion;
    this.mensajeError = '';
    this.mensajeExito = '';
    this.mensajeConfirmacionSensor = '';
  }

  cargar(): void {
    this.crud.listarResiduosDisponibles().subscribe({
      next: (datos) => {
        this.residuosDisponibles = datos;
        this.cdr.detectChanges();
      },
      error: () => this.mensajeError = 'No se pudieron cargar los residuos disponibles.'
    });

    this.crud.listarMisAsignaciones().subscribe({
      next: (datos) => {
        this.asignaciones = datos;
        this.cdr.detectChanges();
      },
      error: () => this.mensajeError = 'No se pudieron cargar las asignaciones.'
    });

    this.crud.listarSolicitudesSensor().subscribe({
      next: (datos) => {
        this.solicitudesSensor = datos;
        this.cdr.detectChanges();
      },
      error: (error) => this.mensajeError = this.obtenerMensajeError(error, 'No se pudieron cargar las solicitudes de sensores.')
    });

    this.crud.listarSolicitudesResiduo().subscribe({
      next: (datos) => {
        this.solicitudesResiduo = datos;
        this.cdr.detectChanges();
      },
      error: (error) => this.mensajeError = this.obtenerMensajeError(error, 'No se pudieron cargar las solicitudes de residuos.')
    });

    this.cargarRecomendacionesIa();
  }

  cargarRecomendacionesIa(): void {
    this.crud.listarRecomendacionesIa().subscribe({
      next: (datos) => {
        this.recomendacionesIa = datos;
        this.cdr.detectChanges();
      },
      error: () => this.mensajeDiagnostico = 'No se pudo cargar el historial de informes de la IA.'
    });
  }

  obtenerUbicacionResiduo(): void {
    if (!navigator.geolocation) {
      this.mensajeError = 'Tu navegador no admite geolocalización.';
      return;
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        // El backend almacena coordenadas con seis decimales; el GPS puede entregar más.
        const latitud = Number(coords.latitude.toFixed(6));
        const longitud = Number(coords.longitude.toFixed(6));
        this.solicitudResiduo.latitud = latitud;
        this.solicitudResiduo.longitud = longitud;
        this.solicitudResiduo.ubicacion = `${latitud.toFixed(6)}, ${longitud.toFixed(6)}`;
        this.mensajeError = '';
        this.cdr.detectChanges();
      },
      () => { this.mensajeError = 'No se pudo obtener tu ubicación. Autoriza el permiso de GPS e inténtalo de nuevo.'; this.cdr.detectChanges(); },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 },
    );
  }

  obtenerUbicacionDiagnostico(): void {
    if (!navigator.geolocation) {
      this.mensajeDiagnostico = 'Tu navegador no admite geolocalización.';
      this.tipoMensajeDiagnostico = 'error';
      this.cdr.detectChanges();
      return;
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        this.formularioDiagnostico.latitud = Number(coords.latitude.toFixed(6));
        this.formularioDiagnostico.longitud = Number(coords.longitude.toFixed(6));
        this.mensajeDiagnostico = 'Ubicación GPS capturada correctamente.';
        this.tipoMensajeDiagnostico = 'success';
        this.cdr.detectChanges();
      },
      () => {
        this.mensajeDiagnostico = 'No se pudo obtener la ubicación. Autoriza el permiso GPS e inténtalo de nuevo.';
        this.tipoMensajeDiagnostico = 'error';
        this.cdr.detectChanges();
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 },
    );
  }

  cambiarOrigenDiagnostico(origen: 'SENSOR' | 'MANUAL'): void {
    if (origen === 'SENSOR') {
      this.cargarLecturaThingSpeak();
    }
  }

  cargarLecturaThingSpeak(): void {
    if (this.formularioDiagnostico.origen_datos !== 'SENSOR') return;

    this.crud.obtenerUltimaLecturaThingSpeak().subscribe({
      next: (lectura) => {
        this.formularioDiagnostico.temperatura = lectura.temperatura;
        this.formularioDiagnostico.humedad_ambiente = lectura.humedad_ambiente;
        this.mensajeDiagnostico = '';
        this.cdr.detectChanges();
      },
      error: (error) => {
        this.formularioDiagnostico.temperatura = null;
        this.formularioDiagnostico.humedad_ambiente = null;
        this.mensajeDiagnostico = this.obtenerMensajeError(
          error,
          'No se pudo obtener la última medición de ThingSpeak.'
        );
        this.tipoMensajeDiagnostico = 'error';
        this.cdr.detectChanges();
      },
    });
  }

  solicitarDiagnosticoCultivo(): void {
    if (!this.formularioDiagnostico.area_cultivo_m2 || this.formularioDiagnostico.area_cultivo_m2 <= 0) {
      this.mensajeDiagnostico = 'Ingresa un área de cultivo válida en m².';
      this.tipoMensajeDiagnostico = 'error';
      return;
    }
    this.diagnosticoCargando = true;
    this.mensajeDiagnostico = '';
    this.tipoMensajeDiagnostico = 'error';
    this.diagnosticoCultivo = null;
    // Red de seguridad de UI: ninguna solicitud puede dejar el botón bloqueado.
    const datosDiagnostico = { ...this.formularioDiagnostico };
    // La vista previa es informativa; el backend vuelve a leer ThingSpeak al analizar.
    if (datosDiagnostico.origen_datos === 'SENSOR') {
      datosDiagnostico.temperatura = null;
      datosDiagnostico.humedad_ambiente = null;
    }
    this.crud.diagnosticarCultivo(datosDiagnostico).pipe(timeout(40000)).subscribe({
      next: (resultado) => {
        this.diagnosticoCultivo = resultado;
        this.diagnosticoCargando = false;
        this.cargarRecomendacionesIa();
        this.cdr.detectChanges();
      },
      error: (error) => {
        this.diagnosticoCargando = false;
        this.mensajeDiagnostico = error?.name === 'TimeoutError'
          ? 'El análisis tardó demasiado. Inténtalo de nuevo; el sistema usará el respaldo local si Gemini no responde.'
          : this.obtenerMensajeError(error, 'No se pudo generar el diagnóstico.');
        this.tipoMensajeDiagnostico = 'error';
        this.cdr.detectChanges();
      },
    });
  }

  abrirReporte(recomendacion: any): void {
    if (!recomendacion?.id_recomendacion) {
      this.mensajeDiagnostico = 'El informe seleccionado no está disponible.';
      this.tipoMensajeDiagnostico = 'error';
      return;
    }

    // Abrir la pestaña durante el clic evita que el navegador bloquee el PDF.
    const ventanaReporte = window.open('', '_blank');
    if (!ventanaReporte) {
      this.mensajeDiagnostico = 'El navegador bloqueó la ventana del informe. Permite las ventanas emergentes e inténtalo de nuevo.';
      this.tipoMensajeDiagnostico = 'error';
      return;
    }
    ventanaReporte.document.title = 'Generando informe…';
    ventanaReporte.document.body.innerHTML = '<p style="font-family:sans-serif;padding:2rem">Generando informe PDF…</p>';

    this.crud.obtenerReporteIa(recomendacion.id_recomendacion).subscribe({
      next: (pdf) => {
        const urlPdf = URL.createObjectURL(pdf);
        ventanaReporte.location.replace(urlPdf);
        window.setTimeout(() => URL.revokeObjectURL(urlPdf), 60_000);
      },
      error: () => {
        ventanaReporte.close();
        this.mensajeDiagnostico = 'No fue posible abrir el informe PDF. Inténtalo nuevamente.';
        this.tipoMensajeDiagnostico = 'error';
        this.cdr.detectChanges();
      },
    });
  }

  formatearFechaRecomendacion(fecha: string | null | undefined): string {
    if (!fecha) return 'Fecha no disponible';
    const fechaConvertida = new Date(fecha);
    return Number.isNaN(fechaConvertida.getTime())
      ? 'Fecha no disponible'
      : fechaConvertida.toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' });
  }

  alternarSensorSolicitud(tipoSensor: string, seleccionado: boolean): void {
    const sensores = new Set(this.solicitud.tipo_sensores);
    if (seleccionado) {
      sensores.add(tipoSensor);
    } else {
      sensores.delete(tipoSensor);
    }
    this.solicitud.tipo_sensores = this.tiposSensoresDisponibles.filter((sensor) => sensores.has(sensor));
  }

  sensoresSeleccionadosSolicitud(): string[] {
    return this.solicitud.tipo_sensores.filter((sensor) => this.tiposSensoresDisponibles.includes(sensor));
  }

  haySensoresSeleccionados(): boolean {
    return this.sensoresSeleccionadosSolicitud().length > 0;
  }

  solicitarSensor(): void {
    if (this.solicitudSensorEnviada || this.solicitudSensorEnviandose) {
      return;
    }

    const sensoresSeleccionados = this.sensoresSeleccionadosSolicitud();
    if (!sensoresSeleccionados.length) {
      this.mensajeError = 'Selecciona al menos un tipo de sensor.';
      return;
    }

    if (!this.solicitud.fecha_entrega_deseada) {
      this.mensajeError = 'Selecciona la fecha deseada de recepcion.';
      return;
    }
    if (this.solicitud.fecha_entrega_deseada < this.fechaMinimaEntrega) {
      this.mensajeError = 'La fecha deseada de recepcion no puede estar en el pasado.';
      return;
    }

    this.solicitudSensorEnviandose = true;
    this.crud.solicitarSensor({
      tipo_sensores: sensoresSeleccionados,
      fecha_entrega_deseada: this.solicitud.fecha_entrega_deseada,
    }).subscribe({
      next: () => {
        this.solicitudSensorEnviada = true;
        this.mensajeConfirmacionSensor = '¡Su sensor ha sido solicitado con éxito! El administrador revisará su petición.';
        this.mensajeError = '';
        this.solicitudSensorEnviandose = false;
        this.cargar();
      },
      error: (error) => {
        this.solicitudSensorEnviandose = false;
        this.mensajeError = this.obtenerMensajeError(error, 'No se pudo enviar la solicitud.');
      }
    });
  }

  puedeConfirmarEntrega(solicitud: any): boolean {
    return ['ACEPTADO', 'EN_CAMINO', 'ENTREGADO'].includes(solicitud.estado)
      && solicitud.fecha_entrega_deseada === this.obtenerFechaLocalActual()
      && !solicitud.fecha_recepcion_confirmada;
  }

  confirmarEntregaSensor(solicitud: any): void {
    this.crud.confirmarEntregaSensor(solicitud.id_solicitud_sensor).subscribe({
      next: () => {
        this.mensajeExito = 'Recepción confirmada. Ahora puedes conectar este sensor a ThingSpeak.';
        this.mensajeError = '';
        this.cargar();
      },
      error: (error) => this.mensajeError = this.obtenerMensajeError(error, 'No se pudo confirmar la recepción del sensor.')
    });
  }

  conectarSensorThingSpeak(solicitud: any): void {
    const datos = this.conexionThingSpeak[solicitud.id_solicitud_sensor] || { thingspeak_channel_id: '', thingspeak_read_api_key: '' };
    if (!datos.thingspeak_channel_id.trim()) {
      this.mensajeError = 'Ingresa el ID de tu canal de ThingSpeak.';
      return;
    }
    this.crud.conectarSensorThingSpeak(solicitud.sensor.id_sensor, datos).subscribe({
      next: () => {
        this.mensajeExito = 'Sensor conectado a tu canal propio de ThingSpeak.';
        this.mensajeError = '';
        this.cargar();
      },
      error: (error) => this.mensajeError = this.obtenerMensajeError(error, 'No se pudo conectar el sensor a ThingSpeak.')
    });
  }

  solicitudConexion(idSolicitud: number): { thingspeak_channel_id: string; thingspeak_read_api_key: string } {
    return this.conexionThingSpeak[idSolicitud] ||= { thingspeak_channel_id: '', thingspeak_read_api_key: '' };
  }

  solicitarResiduo(): void {
    if (this.solicitudResiduoEnviada) {
      this.mensajeExito = 'Ya se envió la solicitud de residuo. La alcaldía revisará la solicitud.';
      return;
    }

    if (!this.solicitudResiduo.tipo_residuo?.trim()) {
      this.mensajeError = 'Selecciona un tipo de residuo.';
      return;
    }
    if (this.solicitudResiduo.tipo_residuo === 'HUMEDO' && !this.solicitudResiduo.presencia_citricos) {
      this.mensajeError = 'Selecciona la categoría de cítricos del residuo húmedo.';
      return;
    }
    if (this.solicitudResiduo.cantidad_kg == null || Number(this.solicitudResiduo.cantidad_kg) <= 0) {
      this.mensajeError = 'Ingresa la cantidad en kg que necesitas.';
      return;
    }
    if (this.solicitudResiduo.precio_ofrecido_campesino == null || Number(this.solicitudResiduo.precio_ofrecido_campesino) <= 0) {
      this.mensajeError = 'Ingresa el precio que ofreces pagar.';
      return;
    }
    if (!this.solicitudResiduo.ubicacion?.trim()) {
      this.mensajeError = 'Ingresa tu ubicación.';
      return;
    }

    this.crud.solicitarResiduo(this.solicitudResiduo).subscribe({
      next: () => {
        this.solicitudResiduoEnviada = true;
        this.mensajeExito = 'Ya se envió la solicitud de residuo. La alcaldía revisará la solicitud.';
        this.mensajeError = '';
        this.cargar();
      },
      error: () => this.mensajeError = 'No se pudo enviar la solicitud de residuo.'
    });
  }

  actualizarPrecioOfrecido(valor: string): void {
    this.precioOfrecidoTexto = valor;
    this.solicitudResiduo.precio_ofrecido_campesino = this.convertirMonedaANumero(valor);
  }

  editarPrecioOfrecido(): void {
    const precio = this.solicitudResiduo.precio_ofrecido_campesino;
    this.precioOfrecidoTexto = precio == null ? '' : String(precio);
  }

  formatearPrecioOfrecido(): void {
    const precio = this.convertirMonedaANumero(this.precioOfrecidoTexto);
    this.solicitudResiduo.precio_ofrecido_campesino = precio;
    this.precioOfrecidoTexto = precio == null ? '' : this.formatearMoneda(precio);
  }

  formatearPrecio(valor: number | string | null | undefined): string {
    if (valor === null || valor === undefined || valor === '') return '—';
    const precio = Number(valor);
    return Number.isFinite(precio) ? this.formatearMoneda(precio) : '—';
  }

  obtenerPrecioFinal(solicitud: any): number | string | null {
    return solicitud.contraoferta_alcaldia ?? solicitud.precio_ofrecido_campesino;
  }

  responderContraofertaSolicitud(solicitud: any, decision: 'aceptar' | 'rechazar'): void {
    this.crud.responderContraofertaSolicitudResiduo(solicitud.id_solicitud_residuo, decision).subscribe({
      next: () => {
        this.mensajeError = '';
        this.mensajeExito = decision === 'aceptar' ? 'Precio aceptado correctamente.' : 'Solicitud rechazada correctamente.';
        this.cargar();
      },
      error: (error) => this.mensajeError = this.obtenerMensajeError(error, 'No se pudo responder la contraoferta.')
    });
  }

  private obtenerFechaLocalActual(): string {
    const ahora = new Date();
    const fechaLocal = new Date(ahora.getTime() - ahora.getTimezoneOffset() * 60000);
    return fechaLocal.toISOString().slice(0, 10);
  }

  private formatearMoneda(valor: number): string {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(valor);
  }

  private convertirMonedaANumero(valor: string): number | null {
    const texto = (valor || '').replace(/[^0-9,.-]/g, '');
    if (!texto || !/\d/.test(texto)) return null;

    const ultimoPunto = texto.lastIndexOf('.');
    const ultimaComa = texto.lastIndexOf(',');
    const indiceDecimal = Math.max(ultimoPunto, ultimaComa);
    const decimales = indiceDecimal >= 0 ? texto.length - indiceDecimal - 1 : 0;
    const tieneDecimal = indiceDecimal >= 0 && decimales > 0 && decimales <= 2;
    const normalizado = tieneDecimal
      ? `${texto.slice(0, indiceDecimal).replace(/[^0-9]/g, '')}.${texto.slice(indiceDecimal + 1).replace(/[^0-9]/g, '')}`
      : texto.replace(/[^0-9]/g, '');
    const numero = Number(normalizado);
    return Number.isFinite(numero) ? numero : null;
  }

  private obtenerMensajeError(error: any, mensajePorDefecto: string): string {
    const detalle = error?.error?.error || error?.error?.detail || error?.message;
    return detalle ? `${mensajePorDefecto} ${detalle}` : mensajePorDefecto;
  }
}
