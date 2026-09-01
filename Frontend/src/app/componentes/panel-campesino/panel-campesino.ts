import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
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
    private sanitizer: DomSanitizer,
    private cdr: ChangeDetectorRef
  ) {
    this.usuario = this.auth.obtenerUsuario();
    this.pdfUrlSegura = this.sanitizer.bypassSecurityTrustResourceUrl('http://127.0.0.1:8000/media/materiales/i3388s.pdf');
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

  descargarReporteDiagnostico(): void {
    if (!this.diagnosticoCultivo) return;

    const receta = this.diagnosticoCultivo.receta_compost || {};
    const lineas = [
      'REPORTE DE DIAGNOSTICO AGRONOMICO',
      `Generado: ${new Date().toLocaleString('es-CO')}`,
      '',
      `Cultivo: ${this.formularioDiagnostico.tipo_cultivo}`,
      `Fase: ${this.formularioDiagnostico.fase_cultivo}`,
      `Area sembrada: ${this.formularioDiagnostico.area_cultivo_m2 ?? 'No especificada'} m2`,
      `Fuente del analisis: ${this.diagnosticoCultivo.fuente_diagnostico === 'GEMINI' ? 'Gemini IA' : 'Motor local'}`,
      '',
      `Estado del cultivo: ${this.diagnosticoCultivo.estado_salud_cultivo || 'No disponible'}`,
      'Diagnostico general:',
      this.diagnosticoCultivo.diagnostico_general || 'No disponible',
      '',
      `RECETA DE COMPOST (${receta.total_compost_requerido_kg ?? 0} kg)`,
      `Material verde: ${receta.kg_material_verde ?? 0} kg (40%)`,
      `Material cafe: ${receta.kg_material_cafe ?? 0} kg (60%)`,
      '',
      'ARMADO PASO A PASO:',
      ...(receta.instrucciones_armado || []).map((paso: string, indice: number) => `${indice + 1}. ${paso}`),
      '',
      'RECOMENDACIONES INMEDIATAS:',
      ...(this.diagnosticoCultivo.recomendaciones_inmediatas || []).map((recomendacion: string) => `- ${recomendacion}`),
      '',
      `Alerta de plagas: ${this.diagnosticoCultivo.alerta_plagas || 'NINGUNA'}`,
    ];

    const pdf = this.crearPdf(lineas);
    const enlace = document.createElement('a');
    enlace.href = URL.createObjectURL(new Blob([pdf], { type: 'application/pdf' }));
    enlace.download = `reporte-agronomico-${this.fechaParaArchivo()}.pdf`;
    enlace.click();
    setTimeout(() => URL.revokeObjectURL(enlace.href), 0);
  }

  private crearPdf(lineas: string[]): string {
    const anchoMaximo = 88;
    const lineasAjustadas = lineas.flatMap((linea) => this.ajustarLineaPdf(linea, anchoMaximo));
    const lineasPorPagina = 57;
    const paginas = Array.from(
      { length: Math.max(1, Math.ceil(lineasAjustadas.length / lineasPorPagina)) },
      (_, indice) => lineasAjustadas.slice(indice * lineasPorPagina, (indice + 1) * lineasPorPagina),
    );
    const objetos: string[] = [
      '<< /Type /Catalog /Pages 2 0 R >>',
      `<< /Type /Pages /Kids [${paginas.map((_, indice) => `${3 + indice * 2} 0 R`).join(' ')}] /Count ${paginas.length} >>`,
    ];
    const idFuente = 3 + paginas.length * 2;

    paginas.forEach((pagina, indice) => {
      const idPagina = 3 + indice * 2;
      const idContenido = idPagina + 1;
      const contenido = `BT\n/F1 10 Tf\n50 790 Td\n13 TL\n${pagina.map((linea) => `(${this.escaparTextoPdf(linea)}) Tj\nT*`).join('\n')}\nET`;
      objetos[idPagina - 1] = `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 ${idFuente} 0 R >> >> /Contents ${idContenido} 0 R >>`;
      objetos[idContenido - 1] = `<< /Length ${contenido.length} >>\nstream\n${contenido}\nendstream`;
    });
    objetos[idFuente - 1] = '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>';

    let pdf = '%PDF-1.4\n%PDF generated by Tierra y Vida Smart\n';
    const posiciones: number[] = [0];
    objetos.forEach((objeto, indice) => {
      posiciones.push(pdf.length);
      pdf += `${indice + 1} 0 obj\n${objeto}\nendobj\n`;
    });
    const inicioXref = pdf.length;
    pdf += `xref\n0 ${objetos.length + 1}\n0000000000 65535 f \n`;
    posiciones.slice(1).forEach((posicion) => { pdf += `${String(posicion).padStart(10, '0')} 00000 n \n`; });
    pdf += `trailer\n<< /Size ${objetos.length + 1} /Root 1 0 R >>\nstartxref\n${inicioXref}\n%%EOF`;
    return pdf;
  }

  private ajustarLineaPdf(linea: string, anchoMaximo: number): string[] {
    if (!linea) return [''];
    const palabras = this.normalizarTextoPdf(linea).split(/\s+/);
    const resultado: string[] = [];
    let actual = '';
    palabras.forEach((palabra) => {
      const candidata = actual ? `${actual} ${palabra}` : palabra;
      if (candidata.length > anchoMaximo && actual) {
        resultado.push(actual);
        actual = palabra;
      } else {
        actual = candidata;
      }
    });
    if (actual) resultado.push(actual);
    return resultado;
  }

  private normalizarTextoPdf(texto: string): string {
    return texto.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^\x20-\x7E]/g, '');
  }

  private escaparTextoPdf(texto: string): string {
    return texto.replace(/([\\()])/g, '\\$1');
  }

  private fechaParaArchivo(): string {
    return new Date().toISOString().slice(0, 10);
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
