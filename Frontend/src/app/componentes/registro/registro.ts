import { ChangeDetectorRef, Component, NgZone, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { finalize, timeout } from 'rxjs';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-registro',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './registro.html'
})
export class RegistroComponent implements OnInit {
  enviando = false;
  mensajeError = '';
  registroForm: FormGroup;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private ngZone: NgZone,
    private cdr: ChangeDetectorRef
  ) {
    this.registroForm = this.fb.group({
      nombre_completo: ['', Validators.required],
      username: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      tipo_rol: ['Campesino', Validators.required],
      comprobante_registro: [null]
    });
  }

  ngOnInit(): void {
    this.registroForm.get('tipo_rol')?.valueChanges.subscribe((rol) => {
      this.actualizarValidacionComprobante(rol);
    });
    this.actualizarValidacionComprobante(this.registroForm.get('tipo_rol')?.value);
  }

  get requiereComprobante(): boolean {
    const rol = (this.registroForm.get('tipo_rol')?.value || '').toString().trim();
    return ['Contribuyente', 'Contribuyente ecológico', 'Alcaldia', 'Alcaldía'].includes(rol);
  }

  private actualizarValidacionComprobante(rol: string | null): void {
    const control = this.registroForm.get('comprobante_registro');
    if (!control) return;

    if (this.requiereComprobanteSegunRol(rol)) {
      control.setValidators([Validators.required]);
    } else {
      control.clearValidators();
      control.setValue(null);
    }

    control.updateValueAndValidity({ emitEvent: false });
  }

  private requiereComprobanteSegunRol(rol: string | null): boolean {
    const valor = (rol || '').toString().trim();
    return ['Contribuyente', 'Contribuyente ecológico', 'Alcaldia', 'Alcaldía'].includes(valor);
  }

  onArchivoSeleccionado(event: Event): void {
    const input = event.target as HTMLInputElement;
    const archivo = input.files?.[0] ?? null;
    this.registroForm.get('comprobante_registro')?.setValue(archivo);
    this.registroForm.get('comprobante_registro')?.markAsTouched();
    this.registroForm.get('comprobante_registro')?.updateValueAndValidity();
  }

  onRegistro(): void {
    this.registroForm.markAllAsTouched();

    if (this.enviando) return;

    const controles = ['nombre_completo', 'username', 'email', 'password', 'tipo_rol', 'comprobante_registro'];
    controles.forEach((controlName) => this.registroForm.get(controlName)?.markAsTouched());

    if (this.registroForm.invalid) {
      this.ngZone.run(() => {
        this.mensajeError = 'Completa todos los campos obligatorios antes de continuar.';
        this.cdr.detectChanges();
      });
      return;
    }

    const valores = this.registroForm.getRawValue();
    const formData = new FormData();

    formData.append('username', (valores.username || '').trim());
    formData.append('email', (valores.email || '').trim());
    formData.append('password', valores.password || '');
    formData.append('nombre_completo', (valores.nombre_completo || '').trim());
    formData.append('tipo_rol', valores.tipo_rol || 'Campesino');

    if (this.requiereComprobante && valores.comprobante_registro) {
      formData.append('comprobante_registro', valores.comprobante_registro);
    }

    this.enviando = true;
    this.mensajeError = '';

    this.authService.registrar(formData)
      .pipe(timeout(20000))
      .pipe(finalize(() => this.enviando = false))
      .subscribe({
        next: (res) => {
          this.ngZone.run(() => {
            this.mensajeError = '';
            this.cdr.detectChanges();
          });
          alert(res.mensaje || 'Revisa tu correo para activar la cuenta.');
          this.router.navigate(['/login']);
        },
        error: (err) => {
          const mensaje = err.name === 'TimeoutError'
            ? 'El servidor tardó demasiado en responder. Revisa la configuración del correo.'
            : err.status === 0
            ? 'No se pudo conectar con el servidor.'
            : (err.error?.error || 'No fue posible completar el registro.');
          this.ngZone.run(() => {
            this.mensajeError = mensaje;
            this.cdr.detectChanges();
          });
        }
      });
  }
}
