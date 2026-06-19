import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth';
import { CrudService } from '../../services/crud';

@Component({
  selector: 'app-panel-campesino',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './panel-campesino.html'
})
export class PanelCampesinoComponent implements OnInit {
  usuario;
  sensores: any[] = [];
  editandoId: number | null = null;
  tipoSensor = '';
  mensajeError = '';

  constructor(
    public auth: AuthService,
    private crud: CrudService
  ) {
    this.usuario = this.auth.obtenerUsuario();
  }

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.crud.listarSensores().subscribe({
      next: (datos) => this.sensores = datos,
      error: () => this.mensajeError = 'No se pudieron cargar los sensores.'
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
        this.cargar();
      },
      error: () => this.mensajeError = 'No se pudo guardar el sensor.'
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
  }
}
