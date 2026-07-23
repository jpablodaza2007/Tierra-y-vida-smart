import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth';
import { AdminService, EstadoDictamen, RegistroAdmin } from '../../services/admin.service';

@Component({ selector: 'app-admin-contribuyentes', standalone: true, imports: [CommonModule, FormsModule, RouterLink, RouterLinkActive], templateUrl: './admin-contribuyentes.component.html', styleUrl: '../admin-dashboard/admin-dashboard.component.css' })
export class AdminContribuyentesComponent implements OnInit {
  contribuyentes: RegistroAdmin[] = []; busqueda = ''; mensajeError = ''; mensajeExito = '';
  constructor(public auth: AuthService, private adminService: AdminService, private cdr: ChangeDetectorRef) {}
  ngOnInit(): void { this.cargarDatos(); }
  cargarDatos(): void { this.mensajeError = ''; this.adminService.listarContribuyentes().subscribe({ next: datos => { this.contribuyentes = datos; this.cdr.detectChanges(); }, error: () => { this.mensajeError = 'No se pudieron cargar los contribuyentes.'; this.cdr.detectChanges(); } }); }
  dictaminar(id: number, estado: EstadoDictamen): void { this.adminService.dictaminarContribuyente(id, estado).subscribe({ next: () => { this.mensajeExito = `Contribuyente ${estado === 'ACEPTADO' ? 'aceptado' : 'rechazado'} correctamente.`; this.cargarDatos(); }, error: () => this.mensajeError = 'No se pudo dictaminar el contribuyente.' }); }
  badgeClass(estado: string): string { const valor = (estado || '').toUpperCase(); return valor === 'ACEPTADO' ? 'badge badge-accepted' : valor === 'RECHAZADO' ? 'badge badge-rejected' : 'badge badge-pending'; }
  estaPendiente(estado: string): boolean { return (estado || '').toUpperCase() === 'PENDIENTE'; }
  tieneUbicacion(ubicacion: string | null): boolean { return Boolean((ubicacion || '').trim()); }
  get contribuyentesFiltrados(): RegistroAdmin[] { return this.contribuyentes.filter(item => this.coincideBusqueda([item.nombre, item.correo, item.estado, item.ultima_ubicacion])); }
  private coincideBusqueda(valores: (string | null | undefined)[]): boolean { const termino = this.busqueda.trim().toLowerCase(); return !termino || valores.some(valor => (valor || '').toLowerCase().includes(termino)); }
}
