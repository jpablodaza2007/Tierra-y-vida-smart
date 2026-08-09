import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { RouterLink } from '@angular/router';
import { SiteFooterComponent } from '../site-footer/site-footer';
import { AuthService } from '../../services/auth';
import { CrudService } from '../../services/crud';

@Component({
  selector: 'app-panel-campesino',
  standalone: true,
  imports: [FormsModule, RouterLink, SiteFooterComponent],
  templateUrl: './panel-campesino.html',
  styleUrl: '../panels.css'
})
export class PanelCampesinoComponent implements OnInit {
  usuario;
  sensores: any[] = [];
  residuosDisponibles: any[] = [];
  editandoId: number | null = null;
  tipoSensor = '';
  readonly tiposSensoresDisponibles = ['Temperatura', 'pH', 'Humedad'];
  mensajeError = '';
  mensajeExito = '';
  mensajeConfirmacionSensor = '';
  seccionActual: 'sensores' | 'materiales' | 'solicitarSensor' | 'solicitarResiduo' = 'sensores';
  solicitud = { tipo_sensores: [] as string[], fecha_entrega_deseada: '' };
  solicitudResiduo = { tipo_residuo: '', cantidad_kg: null as number | null, precio_ofrecido_campesino: null as number | null, ubicacion: '', latitud: null as number | null, longitud: null as number | null };
  precioOfrecidoTexto = '';
  solicitudSensorEnviada = false;
  solicitudSensorEnviandose = false;
  solicitudResiduoEnviada = false;
  asignaciones: any[] = [];
  solicitudesResiduo: any[] = [];
  solicitudesSensor: any[] = [];
  pdfUrlSegura: SafeResourceUrl = '';
  fechaMinimaEntrega = this.obtenerFechaLocalActual();

  constructor(
    public auth: AuthService,
    private crud: CrudService,
    private sanitizer: DomSanitizer,
    private cdr: ChangeDetectorRef
  ) {
    this.usuario = this.auth.obtenerUsuario();
    this.pdfUrlSegura = this.sanitizer.bypassSecurityTrustResourceUrl('http://127.0.0.1:8000/media/materiales/i3388s.pdf');
  }

  ngOnInit(): void {
    this.cargar();
    this.obtenerUbicacionResiduo();
  }

  cambiarSeccion(seccion: 'sensores' | 'materiales' | 'solicitarSensor' | 'solicitarResiduo'): void {
    this.seccionActual = seccion;
    this.mensajeError = '';
    this.mensajeExito = '';
    this.mensajeConfirmacionSensor = '';
  }

  cargar(): void {
    this.crud.listarSensores().subscribe({
      next: (datos) => {
        this.sensores = datos;
        this.cdr.detectChanges();
      },
      error: () => this.mensajeError = 'No se pudieron cargar los sensores.'
    });

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
  }

  guardar(): void {
    const datos = { tipo_sensor: this.tipoSensor };
    const peticion = this.editandoId
      ? this.crud.actualizarSensor(this.editandoId, datos)
      : this.crud.crearSensor(datos);

    peticion.subscribe({
      next: () => {
        this.cancelar();
        this.seccionActual = 'sensores';
        this.cargar();
      },
      error: () => this.mensajeError = 'No se pudo guardar el sensor.'
    });
  }

  mostrarFormularioSensor(): boolean {
    return this.editandoId !== null;
  }

  obtenerUbicacionResiduo(): void {
    if (!navigator.geolocation) {
      this.mensajeError = 'Tu navegador no admite geolocalización.';
      return;
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        this.solicitudResiduo.latitud = coords.latitude;
        this.solicitudResiduo.longitud = coords.longitude;
        this.solicitudResiduo.ubicacion = `${coords.latitude.toFixed(6)}, ${coords.longitude.toFixed(6)}`;
        this.mensajeError = '';
        this.cdr.detectChanges();
      },
      () => { this.mensajeError = 'No se pudo obtener tu ubicación. Autoriza el permiso de GPS e inténtalo de nuevo.'; this.cdr.detectChanges(); },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 },
    );
  }

  puedeVincular(solicitud: any): boolean {
    if (solicitud.estado === 'ENTREGADO') return true;
    return ['ACEPTADO', 'EN_CAMINO'].includes(solicitud.estado)
      && solicitud.fecha_entrega_deseada <= this.obtenerFechaLocalActual();
  }

  vincularSensor(solicitud: any): void {
    this.crud.vincularSensor(solicitud.id_solicitud_sensor).subscribe({
      next: () => { this.mensajeExito = 'Sensor vinculado correctamente. Ya está activo en el monitoreo.'; this.cargar(); },
      error: (error) => this.mensajeError = this.obtenerMensajeError(error, 'No se pudo vincular el sensor.'),
    });
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

  solicitarResiduo(): void {
    if (this.solicitudResiduoEnviada) {
      this.mensajeExito = 'Ya se envió la solicitud de residuo. La alcaldía revisará la solicitud.';
      return;
    }

    if (!this.solicitudResiduo.tipo_residuo?.trim()) {
      this.mensajeError = 'Selecciona un tipo de residuo.';
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

  editar(sensor: any): void {
    this.editandoId = sensor.id_sensor;
    this.tipoSensor = sensor.tipo_sensor;
  }

  eliminar(id: number): void {
    if (!confirm('¿Deseas eliminar este sensor?')) return;
    this.crud.eliminarSensor(id).subscribe({
      next: () => this.cargar(),
      error: () => this.mensajeError = 'No se pudo eliminar el sensor.'
    });
  }

  cancelar(): void {
    this.editandoId = null;
    this.tipoSensor = '';
    this.mensajeError = '';
    this.mensajeExito = '';
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
