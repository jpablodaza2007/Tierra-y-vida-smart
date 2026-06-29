import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth';
import { CrudService } from '../../services/crud';

@Component({
  selector: 'app-panel-campesino',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './panel-campesino.html',
  styleUrl: '../panels.css'
})
export class PanelCampesinoComponent implements OnInit {
  usuario;
  sensores: any[] = [];
  residuosDisponibles: any[] = [];
  editandoId: number | null = null;
  tipoSensor = '';
  mensajeError = '';
  mensajeExito = '';
  seccionActual: 'sensores' | 'materiales' | 'solicitarSensor' | 'solicitarResiduo' = 'sensores';
  solicitud = { tipo_sensor: '' };
  solicitudResiduo = { tipo_residuo: '', cantidad_kg: null as number | null, ubicacion: '' };
  solicitudSensorEnviada = false;
  solicitudResiduoEnviada = false;
  asignaciones: any[] = [];
  pdfUrlSegura: SafeResourceUrl = '';

  constructor(
    public auth: AuthService,
    private crud: CrudService,
    private sanitizer: DomSanitizer
  ) {
    this.usuario = this.auth.obtenerUsuario();
    this.pdfUrlSegura = this.sanitizer.bypassSecurityTrustResourceUrl('http://127.0.0.1:8000/media/materiales/i3388s.pdf');
  }

  ngOnInit(): void {
    this.cargar();
  }

  cambiarSeccion(seccion: 'sensores' | 'materiales' | 'solicitarSensor' | 'solicitarResiduo'): void {
    this.seccionActual = seccion;
    this.mensajeError = '';
    this.mensajeExito = '';
  }

  cargar(): void {
    this.crud.listarSensores().subscribe({
      next: (datos) => this.sensores = datos,
      error: () => this.mensajeError = 'No se pudieron cargar los sensores.'
    });

    this.crud.listarResiduosDisponibles().subscribe({
      next: (datos) => this.residuosDisponibles = datos,
      error: () => this.mensajeError = 'No se pudieron cargar los residuos disponibles.'
    });

    this.crud.listarMisAsignaciones().subscribe({
      next: (datos) => this.asignaciones = datos,
      error: () => this.mensajeError = 'No se pudieron cargar las asignaciones.'
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
    return this.sensores.length > 0 || this.editandoId !== null;
  }

  solicitarSensor(): void {
    if (this.solicitudSensorEnviada) {
      this.mensajeExito = 'Ya se envió la solicitud de sensor. La alcaldía recibirá la solicitud.';
      return;
    }

    if (!this.solicitud.tipo_sensor) {
      this.mensajeError = 'Selecciona un tipo de sensor.';
      return;
    }

    this.crud.solicitarSensor({ tipo_sensor: this.solicitud.tipo_sensor }).subscribe({
      next: () => {
        this.solicitudSensorEnviada = true;
        this.mensajeExito = 'Ya se envió la solicitud de sensor. La alcaldía recibirá la solicitud.';
        this.mensajeError = '';
      },
      error: () => this.mensajeError = 'No se pudo enviar la solicitud.'
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
    if (!this.solicitudResiduo.ubicacion?.trim()) {
      this.mensajeError = 'Ingresa tu ubicación.';
      return;
    }

    this.crud.solicitarResiduo(this.solicitudResiduo).subscribe({
      next: () => {
        this.solicitudResiduoEnviada = true;
        this.mensajeExito = 'Ya se envió la solicitud de residuo. La alcaldía revisará la solicitud.';
        this.mensajeError = '';
      },
      error: () => this.mensajeError = 'No se pudo enviar la solicitud de residuo.'
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
}
