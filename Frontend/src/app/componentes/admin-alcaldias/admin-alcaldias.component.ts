import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth';
import { AdminService, EstadoDictamen, RegistroAdmin } from '../../services/admin.service';

@Component({ selector: 'app-admin-alcaldias', standalone: true, imports: [CommonModule, FormsModule, RouterLink, RouterLinkActive], templateUrl: './admin-alcaldias.component.html', styleUrl: '../admin-dashboard/admin-dashboard.component.css' })
export class AdminAlcaldiasComponent implements OnInit {
  alcaldias: RegistroAdmin[] = []; busqueda = ''; mensajeError = ''; mensajeExito = '';
  constructor(public auth: AuthService, private adminService: AdminService, private cdr: ChangeDetectorRef) {}
  ngOnInit(): void { this.cargarDatos(); }
  cargarDatos(): void { this.mensajeError = ''; this.adminService.listarAlcaldias().subscribe({ next: datos => { this.alcaldias = datos; this.cdr.detectChanges(); }, error: () => { this.mensajeError = 'No se pudieron cargar las alcaldías.'; this.cdr.detectChanges(); } }); }
  dictaminar(id: number, estado: EstadoDictamen): void { this.adminService.dictaminarAlcaldia(id, estado).subscribe({ next: () => { this.mensajeExito = `Alcaldía ${estado === 'ACEPTADO' ? 'aceptada' : 'rechazada'} correctamente.`; this.cargarDatos(); }, error: () => this.mensajeError = 'No se pudo dictaminar la alcaldía.' }); }
  badgeClass(estado: string): string { const valor = (estado || '').toUpperCase(); return valor === 'ACEPTADO' ? 'badge badge-accepted' : valor === 'RECHAZADO' ? 'badge badge-rejected' : 'badge badge-pending'; }
  estaPendiente(estado: string): boolean { return (estado || '').toUpperCase() === 'PENDIENTE'; }
  tieneUbicacion(ubicacion: string | null): boolean { return Boolean((ubicacion || '').trim()); }
  get alcaldiasFiltradas(): RegistroAdmin[] { return this.alcaldias.filter(item => this.coincideBusqueda([item.nombre, item.correo, item.estado, item.ultima_ubicacion])); }
  private coincideBusqueda(valores: (string | null | undefined)[]): boolean { const termino = this.busqueda.trim().toLowerCase(); return !termino || valores.some(valor => (valor || '').toLowerCase().includes(termino)); }
}
