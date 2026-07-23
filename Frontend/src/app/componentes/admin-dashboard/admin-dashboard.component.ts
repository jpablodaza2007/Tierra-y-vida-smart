import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { AuthService } from '../../services/auth';
import {
  AdminService,
  EstadoDictamen,
  RegistroAdmin,
  SolicitudSensorAdmin
} from '../../services/admin.service';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './admin-dashboard.component.html',
  styleUrl: './admin-dashboard.component.css'
})
export class AdminDashboardComponent implements OnInit {
  contribuyentes: RegistroAdmin[] = [];
  alcaldias: RegistroAdmin[] = [];
  solicitudesSensores: SolicitudSensorAdmin[] = [];
  cargando = false;
  mensajeError = '';
  mensajeExito = '';

  constructor(
    public auth: AuthService,
    private adminService: AdminService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.cargarDatos();
  }

  cargarDatos(): void {
    this.cargando = true;
    this.mensajeError = '';

    this.adminService.listarContribuyentes().subscribe({
      next: (datos) => {
        this.contribuyentes = datos;
        this.finalizarCarga();
      },
      error: () => this.registrarError('No se pudieron cargar los contribuyentes.')
    });

    this.adminService.listarAlcaldias().subscribe({
      next: (datos) => {
        this.alcaldias = datos;
        this.finalizarCarga();
      },
      error: () => this.registrarError('No se pudieron cargar las alcaldias.')
    });

    this.adminService.listarSolicitudesSensores().subscribe({
      next: (datos) => {
        this.solicitudesSensores = datos;
        this.finalizarCarga();
      },
      error: () => this.registrarError('No se pudieron cargar las solicitudes de sensores.')
    });
  }

  dictaminarContribuyente(id: number, estado: EstadoDictamen): void {
    this.adminService.dictaminarContribuyente(id, estado).subscribe({
      next: () => this.refrescarConMensaje(`Contribuyente ${this.textoEstado(estado)} correctamente.`),
      error: () => this.mensajeError = 'No se pudo dictaminar el contribuyente.'
    });
  }

  dictaminarAlcaldia(id: number, estado: EstadoDictamen): void {
    this.adminService.dictaminarAlcaldia(id, estado).subscribe({
      next: () => this.refrescarConMensaje(`Alcaldia ${this.textoEstado(estado)} correctamente.`),
      error: () => this.mensajeError = 'No se pudo dictaminar la alcaldia.'
    });
  }

  dictaminarSensor(id: number, estado: EstadoDictamen): void {
    let motivoRechazo = '';
    if (estado === 'RECHAZADO') {
      const respuesta = window.prompt('Escribe el motivo del rechazo para el campesino:');
      if (respuesta === null) {
        return;
      }
      motivoRechazo = respuesta.trim();
    }

    this.adminService.dictaminarSolicitudSensor(id, estado, motivoRechazo).subscribe({
      next: () => this.refrescarConMensaje(`Solicitud de sensor ${this.textoEstado(estado)} correctamente.`),
      error: () => this.mensajeError = 'No se pudo dictaminar la solicitud de sensor.'
    });
  }

  badgeClass(estado: string): string {
    const normalizado = (estado || '').toUpperCase();
    if (normalizado === 'ACEPTADO') return 'badge badge-accepted';
    if (normalizado === 'RECHAZADO') return 'badge badge-rejected';
    return 'badge badge-pending';
  }

  estaPendiente(estado: string): boolean {
    return (estado || '').toUpperCase() === 'PENDIENTE';
  }

  tieneUltimaUbicacion(ubicacion: string | null | undefined): boolean {
    return Boolean((ubicacion || '').trim());
  }

  private refrescarConMensaje(mensaje: string): void {
    this.mensajeExito = mensaje;
    this.mensajeError = '';
    this.cargarDatos();
  }

  private finalizarCarga(): void {
    this.cargando = false;
    this.cdr.detectChanges();
  }

  private registrarError(mensaje: string): void {
    this.cargando = false;
    this.mensajeError = mensaje;
    this.cdr.detectChanges();
  }

  private textoEstado(estado: EstadoDictamen): string {
    return estado === 'ACEPTADO' ? 'aceptado' : 'rechazado';
  }
}
