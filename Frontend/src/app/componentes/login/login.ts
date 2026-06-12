import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { SocialAuthService, GoogleSigninButtonModule } from '@abacritt/angularx-social-login';
import { AuthService } from '../../services/auth'; // Tu ruta que sí sirve

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, GoogleSigninButtonModule],
  templateUrl: './login.html'
})
export class LoginComponent implements OnInit {
  credenciales = { username: '', password: '' };

  constructor(private authService: AuthService, private socialAuthService: SocialAuthService) {}

  ngOnInit() {
    this.socialAuthService.authState.subscribe((user) => {
      if (user && user.idToken) {
        this.authService.loginConGoogle(user.idToken).subscribe({
          next: (res) => {
            this.authService.guardarToken(res.access);
            alert('¡Autenticado con Gmail de forma exitosa!');
          },
          error: (err) => console.error('Error al validar token en Django', err)
        });
      } else if (user) {
        console.error('No se pudo obtener el idToken de Google.');
      }
    });
  }

  onLogin() {
    this.authService.login(this.credenciales).subscribe({
      next: (res) => {
        this.authService.guardarToken(res.access);
        alert('¡Inicio de sesión clásico exitoso!');
      },
      error: (err) => alert('Credenciales incorrectas.')
    });
  }
}
