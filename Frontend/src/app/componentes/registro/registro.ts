import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-registro',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './registro.html'
})
export class RegistroComponent {
  datosUsuario = {
    username: '',
    email: '',
    password: '',
    nombre_completo: '',
    tipo_rol: 'Campesino'
  };

  constructor(private authService: AuthService) {}

  onRegistro() {
    this.authService.registrar(this.datosUsuario).subscribe({
      next: (res) => alert('¡Usuario registrado con éxito en pgAdmin!'),
      error: (err) => alert('Error al registrar: ' + (err.error?.error || 'Error de conexión'))
    });
  }
}
