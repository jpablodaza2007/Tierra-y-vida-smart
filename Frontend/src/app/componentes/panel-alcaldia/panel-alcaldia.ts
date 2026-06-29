import { Component, OnInit } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth';
import { CrudService } from '../../services/crud';

@Component({
  selector: 'app-panel-alcaldia',
  standalone: true,
  imports: [FormsModule, DatePipe, RouterLink],
  templateUrl: './panel-alcaldia.html',
  styleUrl: '../panels.css'
})
export class PanelAlcaldiaComponent implements OnInit {
  usuario;
  gestiones: any[] = [];
  inventario: any[] = [];
  campesinos: any[] = [];
  solicitudesResiduo: any[] = [];
  residuosAuditoria: any[] = [];
  diagnosticoSeleccionado: any = null;
  editandoId: number | null = null;
  mensajeError = '';
  mensajeExito = '';
  mensajeExitoDatos: any = null;
  solicitudSeleccionadaId: number | null = null;
  formAsignacion = this.nuevoFormulario();

  constructor(
    public auth: AuthService,
    private crud: CrudService
  ) {
    this.usuario = this.auth.obtenerUsuario();
  }

  ngOnInit(): void {
    this.cargar();
    this.cargarCampesinos();
  }

  nuevoFormulario() {
    return {
      tipo_residuo: '' as 'SECO' | 'HUMEDO' | '',
      cantidad_kg: null as number | null,
      id_campesino: '' as string | number,
      fecha_asignacion: '',
      ubicacion: ''
    };
  }

  cargarCampesinos(): void {
    this.crud.listarCampesinos().subscribe({
      next: (datos: any) => {
        const usuarios = this.extraerListaCampesinos(datos);
        this.campesinos = usuarios.filter((usuario: any) => {
          const rol = (usuario?.tipo_rol ?? usuario?.rol ?? usuario?.role ?? '').toString().toLowerCase();
          return !rol || rol === 'campesino';
        });
      },
      error: () => this.mensajeError = 'No se pudieron cargar los campesinos disponibles.'
    });
  }

  extraerListaCampesinos(datos: any): any[] {
    if (Array.isArray(datos)) return datos;
    if (Array.isArray(datos?.campesinos)) return datos.campesinos;
    if (Array.isArray(datos?.usuarios)) return datos.usuarios;
    if (Array.isArray(datos?.results)) return datos.results;
    return [];
  }

  obtenerIdCampesino(campesino: any): string | number {
    return campesino?.id ?? campesino?.id_usuario ?? campesino?.user_id ?? campesino?.uuid ?? '';
  }

  obtenerNombreCampesino(campesino: any): string {
    return campesino?.nombre ?? campesino?.nombre_completo ?? campesino?.username ?? campesino?.email ?? 'Campesino sin nombre';
  }

  obtenerUbicacionCampesino(campesino: any): string {
    return campesino?.ubicacion ?? campesino?.ubicacion_entrega ?? campesino?.barrio ?? campesino?.direccion ?? campesino?.direccion_entrega ?? campesino?.campesino?.ubicacion ?? '';
  }

  buscarCampesinoPorId(idCampesino: string | number): any | undefined {
    const idNormalizado = this.normalizarIdCampesino(idCampesino);
    return this.campesinos.find((campesino) => this.normalizarIdCampesino(this.obtenerIdCampesino(campesino)) === idNormalizado);
  }

  onCampesinoChange(event: Event): void {
    const select = event.target as HTMLSelectElement;
    const idSeleccionado = parseInt(select.value, 10);
    const campesinoSeleccionado = this.campesinos.find(
      (c) => this.normalizarIdCampesino(this.obtenerIdCampesino(c)) === idSeleccionado
    );

    this.formAsignacion.id_campesino = Number.isNaN(idSeleccionado) ? '' : idSeleccionado;
    this.formAsignacion.ubicacion = campesinoSeleccionado
      ? this.obtenerUbicacionCampesino(campesinoSeleccionado)
      : '';
    this.mensajeExito = '';
    this.mensajeExitoDatos = null;
  }

  // Equivalente a patchValue para el formulario con ngModel: actualiza la ubicacion al elegir campesino.
  autocompletarUbicacionCampesino(idCampesino: string | number): void {
    const campesinoSeleccionado = this.buscarCampesinoPorId(idCampesino);
    this.formAsignacion.ubicacion = campesinoSeleccionado
      ? this.obtenerUbicacionCampesino(campesinoSeleccionado)
      : '';
    this.mensajeExito = '';
    this.mensajeExitoDatos = null;
  }

  normalizarIdCampesino(id: string | number): string | number {
    if (typeof id === 'number') return id;
    const valor = id.toString();
    return /^\d+$/.test(valor) ? Number(valor) : valor;
  }

  cargar(): void {
    this.cargarGestionesInventario();
    this.obtenerSolicitudesPendientes();
    this.obtenerResiduosAuditoria();
  }

  cargarGestionesInventario(): void {
    this.crud.listarGestiones().subscribe({
      next: (datos) => this.gestiones = datos,
      error: () => this.mensajeError = 'No se pudieron cargar las asignaciones.'
    });
    this.crud.listarInventario().subscribe({
      next: (datos) => this.inventario = datos,
      error: () => this.mensajeError = 'No se pudo cargar el inventario.'
    });
  }

  obtenerSolicitudesPendientes(): void {
    this.crud.listarSolicitudesResiduo().subscribe({
      next: (datos) => this.solicitudesResiduo = datos,
      error: () => this.mensajeError = 'No se pudieron cargar las solicitudes de residuos.'
    });
  }

  obtenerResiduosAuditoria(): void {
    this.crud.listarResiduosAuditoria().subscribe({
      next: (datos) => this.residuosAuditoria = datos,
      error: () => this.mensajeError = 'No se pudieron cargar los residuos pendientes de auditoria.'
    });
  }

  verDiagnostico(residuo: any): void {
    this.diagnosticoSeleccionado = residuo;
  }

  cerrarDiagnostico(): void {
    this.diagnosticoSeleccionado = null;
  }

  aceptarResiduo(residuo: any): void {
    this.crud.decidirResiduoAuditoria(residuo.id_residuo, { estado: 'Aceptado' }).subscribe({
      next: () => {
        this.mensajeError = '';
        this.mensajeExito = 'Residuo aceptado y sumado al inventario central.';
        this.cerrarDiagnostico();
        this.cargarGestionesInventario();
        this.obtenerResiduosAuditoria();
      },
      error: (err) => {
        this.mensajeError = this.obtenerMensajeError(err) || 'No se pudo aceptar el residuo.';
        this.mensajeExito = '';
      }
    });
  }

  rechazarResiduo(residuo: any): void {
    const motivo = (prompt('Escribe el motivo del rechazo') || '').trim();
    if (!motivo) {
      this.mensajeError = 'El motivo de rechazo es obligatorio.';
      return;
    }

    this.crud.decidirResiduoAuditoria(residuo.id_residuo, {
      estado: 'Rechazado',
      motivo_rechazo: motivo,
    }).subscribe({
      next: () => {
        this.mensajeError = '';
        this.mensajeExito = 'Residuo rechazado. El contribuyente podra ver el motivo.';
        this.cerrarDiagnostico();
        this.obtenerResiduosAuditoria();
      },
      error: (err) => {
        this.mensajeError = this.obtenerMensajeError(err) || 'No se pudo rechazar el residuo.';
        this.mensajeExito = '';
      }
    });
  }

  guardar(): void {
    const campesinoSeleccionado = this.buscarCampesinoPorId(this.formAsignacion.id_campesino);
    const nombreCampesino = campesinoSeleccionado
      ? this.obtenerNombreCampesino(campesinoSeleccionado)
      : 'seleccionado';
    const ubicacionEntrega = (this.formAsignacion.ubicacion || this.obtenerUbicacionCampesino(campesinoSeleccionado) || '').trim();
    this.formAsignacion.ubicacion = ubicacionEntrega;

    if (!ubicacionEntrega) {
      this.mensajeError = 'El campesino seleccionado no tiene ubicación registrada.';
      this.mensajeExito = '';
      this.mensajeExitoDatos = null;
      return;
    }

    const payload = {
      tipo_residuo: this.formAsignacion.tipo_residuo,
      cantidad_kg: Number(this.formAsignacion.cantidad_kg),
      campesino_id: this.normalizarIdCampesino(this.formAsignacion.id_campesino),
      fecha_asignacion: this.formAsignacion.fecha_asignacion ? new Date(this.formAsignacion.fecha_asignacion).toISOString() : null,
      ubicacion: ubicacionEntrega,
      ubicacion_entrega: ubicacionEntrega,
      solicitud_id: this.solicitudSeleccionadaId,
    };

    const peticion = this.editandoId
      ? this.crud.actualizarGestion(this.editandoId, payload)
      : this.crud.crearGestion(payload);

    peticion.subscribe({
      next: (res) => {
        const gestionGuardada = res?.gestion || payload;
        this.mensajeError = '';
        this.mensajeExitoDatos = {
          cantidad: gestionGuardada.cantidad_kg,
          tipo: gestionGuardada.tipo_residuo,
          nombre: nombreCampesino,
          fecha: gestionGuardada.fecha_asignacion
            ? new Date(gestionGuardada.fecha_asignacion).toLocaleString('es-CO')
            : 'programada',
          ubicacion: gestionGuardada.ubicacion_entrega || gestionGuardada.ubicacion || ubicacionEntrega || 'Barrrio',
        };
        this.mensajeExito = this.construirMensajeAceptacion(nombreCampesino, gestionGuardada);
        this.formAsignacion = this.nuevoFormulario();
        this.solicitudSeleccionadaId = null;
        this.cargarGestionesInventario();
        this.obtenerSolicitudesPendientes();
        this.obtenerResiduosAuditoria();
      },
      error: (err) => {
        const mensajeDetalle = err.error?.detail;
        const mensajeFecha = err.error?.fecha_asignacion?.[0];
        const mensajeNoCampo = err.error?.non_field_errors?.[0];
        const mensajeError = err.error?.error || err.error?.message;
        const mensajeTexto = typeof err.error === 'string' ? err.error : '';
        this.mensajeError = mensajeFecha || mensajeDetalle || mensajeNoCampo || mensajeError || mensajeTexto || 'No se pudo guardar la asignación.';
        this.mensajeExito = '';
        this.mensajeExitoDatos = null;
      }
    });
  }

  construirMensajeAceptacion(nombreCampesino: string, asignacionGuardada?: any): string {
    const cantidad = asignacionGuardada?.cantidad_kg ?? this.formAsignacion.cantidad_kg;
    const tipo = asignacionGuardada?.tipo_residuo ?? this.formAsignacion.tipo_residuo;
    const ubicacion = asignacionGuardada?.ubicacion_entrega ?? asignacionGuardada?.ubicacion ?? this.formAsignacion.ubicacion;
    const fechaBase = asignacionGuardada?.fecha_asignacion ?? this.formAsignacion.fecha_asignacion;
    const fecha = fechaBase
      ? new Date(fechaBase).toLocaleString('es-CO')
      : 'programada';

    return `Aceptaste la solicitud. Se va a entregar la cantidad de ${cantidad} kg de residuo ${tipo} al campesino ${nombreCampesino} el día ${fecha} en la ubicación ${ubicacion}.`;
  }

  editar(gestion: any): void {
    this.editandoId = gestion.id_gestion;
    this.solicitudSeleccionadaId = null;
    this.formAsignacion = {
      tipo_residuo: gestion.tipo_residuo,
      cantidad_kg: parseFloat(gestion.cantidad_kg),
      id_campesino: gestion.campesino_id,
      fecha_asignacion: gestion.fecha_asignacion?.slice(0, 16) || '',
      ubicacion: gestion.ubicacion_entrega || gestion.ubicacion || gestion.campesino?.ubicacion || ''
    };
    if (!this.formAsignacion.ubicacion) {
      this.autocompletarUbicacionCampesino(this.formAsignacion.id_campesino);
    }
    this.mensajeExitoDatos = null;
  }

  seleccionarSolicitud(solicitud: any): void {
    this.solicitudSeleccionadaId = solicitud.id_solicitud_residuo ?? solicitud.id ?? null;
    this.formAsignacion.tipo_residuo = solicitud.tipo_residuo;
    this.formAsignacion.cantidad_kg = parseFloat(solicitud.cantidad_kg);
    this.formAsignacion.id_campesino = solicitud.id_campesino;
    this.formAsignacion.ubicacion = solicitud.ubicacion_entrega || solicitud.ubicacion || solicitud.campesino?.ubicacion || '';
    if (!this.formAsignacion.ubicacion) {
      this.autocompletarUbicacionCampesino(solicitud.id_campesino);
    }
    this.mensajeError = '';
    this.mensajeExito = '';
    this.mensajeExitoDatos = null;
  }

  eliminar(id: number): void {
    if (!confirm('¿Deseas eliminar esta asignación?')) return;
    this.crud.eliminarGestion(id).subscribe({
      next: () => this.cargar(),
      error: () => this.mensajeError = 'No se pudo eliminar la asignación.'
    });
  }

  cancelar(): void {
    this.editandoId = null;
    this.solicitudSeleccionadaId = null;
    this.formAsignacion = this.nuevoFormulario();
    this.mensajeError = '';
    this.mensajeExito = '';
    this.mensajeExitoDatos = null;
  }

  obtenerMensajeError(err: any): string {
    const error = err?.error;
    if (!error) return '';
    if (typeof error === 'string') return error;
    if (error.detail || error.error || error.message) {
      return error.detail || error.error || error.message;
    }
    const primerCampo = Object.keys(error)[0];
    const valor = primerCampo ? error[primerCampo] : null;
    if (Array.isArray(valor)) return valor[0];
    if (typeof valor === 'string') return valor;
    return '';
  }
}
