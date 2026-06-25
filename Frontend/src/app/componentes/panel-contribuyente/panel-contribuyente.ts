import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth';
import { CrudService } from '../../services/crud';

@Component({
  selector: 'app-panel-contribuyente',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './panel-contribuyente.html'
})
export class PanelContribuyenteComponent implements OnInit {
  usuario;
  residuos: any[] = [];
  editandoId: number | null = null;
  mensajeError = '';
  formulario = this.nuevoFormulario();

  constructor(
    public auth: AuthService,
    private crud: CrudService,
    private cdr: ChangeDetectorRef
  ) {
    this.usuario = this.auth.obtenerUsuario();
  }

  ngOnInit(): void {
    this.cargar();
  }

  nuevoFormulario() {
    return { tipo_residuo: '', cantidad_kg: null as number | null };
  }

  cargar(): void {
    this.crud.listarResiduos().subscribe({
      next: (datos) => {
        this.residuos = datos;
        this.cdr.detectChanges();
      },
      error: (err) => this.mensajeError = err.error?.detail || 'No se pudieron cargar los residuos.'
    });
  }

  validarResiduo(): string | null {
    if (!this.formulario.tipo_residuo?.trim()) {
      return 'Debes ingresar un tipo de residuo.';
    }
    if (this.formulario.cantidad_kg == null || Number(this.formulario.cantidad_kg) <= 0) {
      return 'Debes ingresar una cantidad mayor a cero.';
    }
    return null;
  }

  guardar(): void {
    const error = this.validarResiduo();
    if (error) {
      this.mensajeError = error;
      return;
    }

    const payload = {
      tipo_residuo: this.formulario.tipo_residuo?.trim(),
      cantidad_kg: Number(this.formulario.cantidad_kg)
    };

    const peticion = this.editandoId
      ? this.crud.actualizarResiduo(this.editandoId, payload)
      : this.crud.crearResiduo(payload);

    peticion.subscribe({
      next: () => {
        this.mensajeError = '';
        this.cancelar();
        this.cargar();
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.mensajeError = err.error?.detail || 'No se pudo guardar el residuo.';
        this.cdr.detectChanges();
      }
    });
  }

  editar(residuo: any): void {
    this.editandoId = residuo.id_residuo;
    this.formulario = {
      tipo_residuo: residuo.tipo_residuo,
      cantidad_kg: Number(residuo.cantidad_kg)
    };
    this.cdr.detectChanges();
  }

  eliminar(id: number): void {
    if (!confirm('¿Deseas eliminar este residuo?')) return;
    this.crud.eliminarResiduo(id).subscribe({
      next: () => this.cargar(),
      error: () => this.mensajeError = 'No se pudo eliminar el residuo.'
    });
  }

  cancelar(): void {
    this.editandoId = null;
    this.formulario = this.nuevoFormulario();
    this.mensajeError = '';
    this.cdr.detectChanges();
  }
}
