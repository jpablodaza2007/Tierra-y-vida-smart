import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth';
import { AdminService, EstadoDictamen, SolicitudSensorAdmin } from '../../services/admin.service';

@Component({ selector: 'app-admin-sensores', standalone: true, imports: [CommonModule, FormsModule, RouterLink, RouterLinkActive], templateUrl: './admin-sensores.component.html', styleUrl: '../admin-dashboard/admin-dashboard.component.css' })
export class AdminSensoresComponent implements OnInit {
  solicitudesSensores: SolicitudSensorAdmin[] = []; busqueda = ''; mensajeError = ''; mensajeExito = '';
  constructor(public auth: AuthService, private adminService: AdminService, private cdr: ChangeDetectorRef) {}
  ngOnInit(): void { this.cargarDatos(); }
  cargarDatos(): void { this.mensajeError = ''; this.adminService.listarSolicitudesSensores().subscribe({ next: datos => { this.solicitudesSensores = datos; this.cdr.detectChanges(); }, error: () => { this.mensajeError = 'No se pudieron cargar las solicitudes de sensores.'; this.cdr.detectChanges(); } }); }
  dictaminar(id: number, estado: EstadoDictamen): void { let motivo_rechazo = ''; if (estado === 'RECHAZADO') { const respuesta = window.prompt('Escribe el motivo del rechazo para el campesino:'); if (respuesta === null) return; motivo_rechazo = respuesta.trim(); } this.adminService.dictaminarSolicitudSensor(id, estado, motivo_rechazo).subscribe({ next: () => { this.mensajeExito = `Solicitud de sensor ${estado === 'ACEPTADO' ? 'aceptada' : 'rechazada'} correctamente.`; this.cargarDatos(); }, error: () => this.mensajeError = 'No se pudo dictaminar la solicitud de sensor.' }); }
  actualizarEntrega(id: number, estado: 'EN_CAMINO' | 'ENTREGADO'): void { this.adminService.actualizarEntregaSensor(id, estado).subscribe({ next: () => { this.mensajeExito = `Sensor marcado como ${estado.replace('_', ' ').toLowerCase()}.`; this.cargarDatos(); }, error: () => this.mensajeError = 'No se pudo actualizar la entrega del sensor.' }); }
  badgeClass(estado: string): string { const valor = (estado || '').toUpperCase(); return valor === 'ACEPTADO' ? 'badge badge-accepted' : valor === 'RECHAZADO' ? 'badge badge-rejected' : 'badge badge-pending'; }
  estaPendiente(estado: string): boolean { return (estado || '').toUpperCase() === 'PENDIENTE'; }
  tieneUbicacion(ubicacion: string | null): boolean { return Boolean((ubicacion || '').trim()); }
  get solicitudesFiltradas(): SolicitudSensorAdmin[] { return this.solicitudesSensores.filter(item => this.coincideBusqueda([item.campesino_nombre, item.campesino_correo, item.tipo_sensor, item.estado, item.ultima_ubicacion, item.fecha_entrega_deseada])); }
  private coincideBusqueda(valores: (string | null | undefined)[]): boolean { const termino = this.busqueda.trim().toLowerCase(); return !termino || valores.some(valor => (valor || '').toLowerCase().includes(termino)); }
}
