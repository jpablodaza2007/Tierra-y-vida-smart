import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { NgIf } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth';
import { CrudService } from '../../services/crud';

@Component({
  selector: 'app-panel-contribuyente',
  standalone: true,
  imports: [FormsModule, NgIf, RouterLink],
  templateUrl: './panel-contribuyente.html',
  styleUrl: '../panels.css'
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
    private sanitizer: DomSanitizer,
    private cdr: ChangeDetectorRef
  ) {
    this.usuario = this.auth.obtenerUsuario();
    this.pdfUrlSegura = this.sanitizer.bypassSecurityTrustResourceUrl('http://127.0.0.1:8000/media/materiales/Guia_Residuos-Solidos_Digital.pdf');
  }

  ngOnInit(): void {
    this.cargar();
  }

  nuevoFormulario() {
    return {
      tipo_residuo: '',
      cantidad_kg: null as number | null,
      precio_sugerido_contribuyente: null as number | null,
      ubicacion: '',
      dias_almacenamiento: null as number | null,
      metodo_conservacion: '',
      lista_materiales: '',
      presencia_citricos: '',
      presencia_procesados: false,
      ausencia_origen_animal: false,
      presencia_plagas: '',
      bolsa_compostable: false,
      tamano_picado: '',
      estado: 'Pendiente'
    };
  }

  cargar(): void {
    this.crud.listarResiduos().subscribe({
      next: (datos) => {
        this.residuos = datos;
        this.cdr.detectChanges();
      },
      error: (err) => this.mensajeError = this.obtenerMensajeError(err) || 'No se pudieron cargar los residuos.'
    });
  }

  validarResiduo(): string | null {
    if (!this.formulario.tipo_residuo?.trim()) {
      return 'Debes seleccionar un tipo de residuo.';
    }
    if (this.formulario.cantidad_kg == null || Number(this.formulario.cantidad_kg) <= 0) {
      return 'Debes ingresar una cantidad mayor a cero.';
    }
    if (this.formulario.precio_sugerido_contribuyente == null || Number(this.formulario.precio_sugerido_contribuyente) <= 0) {
      return 'Debes ingresar el precio sugerido que esperas obtener.';
    }
    if (!this.formulario.ubicacion?.trim()) {
      return 'Debes ingresar tu ubicacion.';
    }
    if (this.formulario.dias_almacenamiento == null || Number(this.formulario.dias_almacenamiento) < 0) {
      return 'Debes indicar los dias de almacenamiento.';
    }
    if (!this.formulario.metodo_conservacion?.trim()) {
      return 'Debes seleccionar el metodo de conservacion.';
    }
    if (!this.formulario.lista_materiales?.trim()) {
      return 'Debes describir los materiales incluidos.';
    }
    if (!this.formulario.presencia_citricos?.trim()) {
      return 'Debes indicar la presencia de citricos.';
    }
    if (!this.formulario.presencia_procesados) {
      return 'Debes confirmar que el residuo esta libre de sal, aceite, aderezos o comida cocinada.';
    }
    if (!this.formulario.ausencia_origen_animal) {
      return 'Debes confirmar que el residuo esta libre de carnes, lacteos o grasas.';
    }
    if (!this.formulario.presencia_plagas?.trim()) {
      return 'Debes indicar si hay presencia de plagas.';
    }
    if (!this.formulario.tamano_picado?.trim()) {
      return 'Debes seleccionar el tamano del material.';
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
        this.mensajeError = this.obtenerMensajeError(err) || 'No se pudo guardar el residuo.';
      }
    });
  }

  editar(residuo: any): void {
    this.editandoId = residuo.id_residuo;
    this.formulario = {
      tipo_residuo: residuo.tipo_residuo,
      cantidad_kg: Number(residuo.cantidad_kg),
      precio_sugerido_contribuyente: residuo.precio_sugerido_contribuyente == null ? null : Number(residuo.precio_sugerido_contribuyente),
      ubicacion: residuo.ubicacion || '',
      dias_almacenamiento: residuo.dias_almacenamiento ?? null,
      metodo_conservacion: residuo.metodo_conservacion || '',
      lista_materiales: residuo.lista_materiales || '',
      presencia_citricos: residuo.presencia_citricos || '',
      presencia_procesados: Boolean(residuo.presencia_procesados),
      ausencia_origen_animal: Boolean(residuo.ausencia_origen_animal),
      presencia_plagas: residuo.presencia_plagas || '',
      bolsa_compostable: Boolean(residuo.bolsa_compostable),
      tamano_picado: residuo.tamano_picado || '',
      estado: residuo.estado
    };
  }

  eliminar(id: number): void {
    if (!confirm('Deseas eliminar este residuo?')) return;
    this.crud.eliminarResiduo(id).subscribe({
      next: () => this.cargar(),
      error: () => this.mensajeError = 'No se pudo eliminar el residuo.'
    });
  }

  responderContraoferta(residuo: any, decision: 'aceptar' | 'rechazar'): void {
    this.crud.responderContraofertaResiduo(residuo.id_residuo, decision).subscribe({
      next: () => {
        this.mensajeError = '';
        this.cargar();
      },
      error: (err) => {
        this.mensajeError = this.obtenerMensajeError(err) || 'No se pudo responder la contraoferta.';
      }
    });
  }

  cancelar(): void {
    this.editandoId = null;
    this.formulario = this.nuevoFormulario();
    this.mensajeError = '';
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
