import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
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
  seccionActual: 'registro' | 'materiales' | 'residuos' = 'registro';
  formulario = this.nuevoFormulario();
  pdfUrlSegura: SafeResourceUrl = '';

  constructor(
    public auth: AuthService,
    private crud: CrudService,
    private sanitizer: DomSanitizer
  ) {
    this.usuario = this.auth.obtenerUsuario();
    this.pdfUrlSegura = this.sanitizer.bypassSecurityTrustResourceUrl('http://127.0.0.1:8000/media/materiales/Guia_Residuos-Solidos_Digital.pdf');
  }

  ngOnInit(): void {
    this.cargar();
  }

  nuevoFormulario() {
    return { tipo_residuo: '', cantidad_kg: null as number | null, estado: 'Pendiente' };
  }

  cargar(): void {
    this.crud.listarResiduos().subscribe({
      next: (datos) => this.residuos = datos,
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

  cambiarSeccion(seccion: 'registro' | 'materiales' | 'residuos'): void {
    this.seccionActual = seccion;
    this.mensajeError = '';
  }

  guardar(): void {
    const error = this.validarResiduo();
    if (error) {
      this.mensajeError = error;
      return;
    }

    const peticion = this.editandoId
      ? this.crud.actualizarResiduo(this.editandoId, this.formulario)
      : this.crud.crearResiduo(this.formulario);

    peticion.subscribe({
      next: () => {
        this.cancelar();
        this.seccionActual = 'residuos';
        this.cargar();
      },
      error: (err) => {
        this.mensajeError = err.error?.detail || 'No se pudo guardar el residuo.';
      }
    });
  }

  editar(residuo: any): void {
    this.editandoId = residuo.id_residuo;
    this.formulario = {
      tipo_residuo: residuo.tipo_residuo,
      cantidad_kg: Number(residuo.cantidad_kg),
      estado: residuo.estado
    };
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
  }
}
