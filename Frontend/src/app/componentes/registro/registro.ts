import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { finalize, timeout } from 'rxjs';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-registro',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './registro.html'
})
export class RegistroComponent {
  enviando = false;
  mensajeError = '';

  datosUsuario = {
    username: '',
    email: '',
    password: '',
    nombre_completo: '',
    tipo_rol: 'Campesino'
  };

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  validarRegistro(): string[] {
    const errores: string[] = [];
    const email = this.datosUsuario.email?.trim();
    const password = this.datosUsuario.password || '';

    if (!this.datosUsuario.username?.trim()) {
      errores.push('El nombre de usuario es obligatorio.');
    }
    if (!this.datosUsuario.nombre_completo?.trim()) {
      errores.push('El nombre completo es obligatorio.');
    }
    if (!email) {
      errores.push('El correo es obligatorio.');
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errores.push('El correo debe tener un formato válido.');
    }
    if (!password) {
      errores.push('La contraseña es obligatoria.');
    } else {
      if (password.length < 6) {
        errores.push('La contraseña debe tener al menos 6 caracteres.');
      }
      if (!/[A-Z]/.test(password)) {
        errores.push('La contraseña debe contener al menos una letra mayúscula.');
      }
    }
    if (!this.datosUsuario.tipo_rol) {
      errores.push('Selecciona un tipo de rol.');
    }
    return errores;
  }

  onRegistro() {
    if (this.enviando) return;

    const errores = this.validarRegistro();
    if (errores.length) {
      const mensaje = errores.join(' ');
      this.mensajeError = mensaje;
      alert('Por favor completa todos los campos obligatorios.\n' + mensaje);
      return;
    }

    this.datosUsuario.username = this.datosUsuario.username?.trim() || '';
    this.datosUsuario.email = this.datosUsuario.email?.trim() || '';
    this.datosUsuario.nombre_completo = this.datosUsuario.nombre_completo?.trim() || '';

    this.enviando = true;
    this.mensajeError = '';

    this.authService.registrar(this.datosUsuario)
      .pipe(timeout(20000))
      .pipe(finalize(() => this.enviando = false))
      .subscribe({
        next: (res) => {
          alert(res.mensaje || 'Revisa tu correo para activar la cuenta.');
          this.router.navigate(['/login']);
        },
        error: (err) => {
          this.mensajeError = err.name === 'TimeoutError'
            ? 'El servidor tardó demasiado en responder. Revisa la configuración del correo.'
            : err.status === 0
            ? 'No se pudo conectar con el servidor.'
            : (err.error?.error || 'No fue posible completar el registro.');
        }
      });
  }
}
