import { Component, OnInit } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth';
import { CrudService } from '../../services/crud';

@Component({
  selector: 'app-panel-alcaldia',
  standalone: true,
  imports: [FormsModule, DatePipe],
  templateUrl: './panel-alcaldia.html'
})
export class PanelAlcaldiaComponent implements OnInit {
  usuario;
  gestiones: any[] = [];
  residuos: any[] = [];
  campesinos: any[] = [];
  solicitudesResiduo: any[] = [];
  editandoId: number | null = null;
  mensajeError = '';
  formulario = this.nuevoFormulario();

  constructor(
    public auth: AuthService,
    private crud: CrudService
  ) {
    this.usuario = this.auth.obtenerUsuario();
  }

  ngOnInit(): void {
    this.cargar();
  }

  nuevoFormulario() {
    return {
      id_residuo_id: null as number | null,
      id_campesino_id: null as number | null,
      fecha_asignacion: ''
    };
  }

  cargar(): void {
    this.crud.listarGestiones().subscribe({
      next: (datos) => this.gestiones = datos,
      error: () => this.mensajeError = 'No se pudieron cargar las asignaciones.'
    });
    this.crud.opcionesLogistica().subscribe({
      next: (datos) => {
        this.residuos = datos.residuos;
        this.campesinos = datos.campesinos;
      }
    });
    this.crud.listarSolicitudesResiduo().subscribe({
      next: (datos) => this.solicitudesResiduo = datos,
      error: () => this.mensajeError = 'No se pudieron cargar las solicitudes de residuos.'
    });
  }

  guardar(): void {
    const peticion = this.editandoId
      ? this.crud.actualizarGestion(this.editandoId, this.formulario)
      : this.crud.crearGestion(this.formulario);

    peticion.subscribe({
      next: () => {
        this.cancelar();
        this.cargar();
      },
      error: (err) => this.mensajeError = err.error?.detail || 'No se pudo guardar la asignación.'
    });
  }

  editar(gestion: any): void {
    this.editandoId = gestion.id_gestion;
    this.formulario = {
      id_residuo_id: gestion.residuo.id_residuo,
      id_campesino_id: gestion.campesino_id,
      fecha_asignacion: gestion.fecha_asignacion?.slice(0, 16) || ''
    };
  }

  seleccionarSolicitud(solicitud: any): void {
    this.formulario.id_residuo_id = solicitud.id_residuo;
    this.mensajeError = '';
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
    this.formulario = this.nuevoFormulario();
    this.mensajeError = '';
  }
}
