import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { finalize, timeout } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import {
  GoogleSigninButtonModule,
  SocialAuthService
} from '@abacritt/angularx-social-login';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, RouterLink, GoogleSigninButtonModule],
  templateUrl: './login.html'
})
export class LoginComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);

  credenciales = { username: '', password: '' };
  enviando = false;
  enviandoGoogle = false;
  mensajeError = '';

  constructor(
    private authService: AuthService,
    private socialAuthService: SocialAuthService
  ) {}

  ngOnInit(): void {
    this.socialAuthService.authState
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((user) => {
        if (!user?.idToken) return;

        this.enviandoGoogle = true;
        this.mensajeError = '';

        this.authService.loginConGoogle(user.idToken)
          .pipe(finalize(() => this.enviandoGoogle = false))
          .subscribe({
            next: (res) => {
              this.authService.guardarSesion(res);
              this.authService.irAlPanel();
            },
            error: (err) => {
              this.mensajeError = err.status === 0
                ? 'No se pudo conectar con el servidor.'
                : (err.error?.error || 'No fue posible iniciar sesión con Google.');
            }
          });
      });
  }

  onLogin() {
    if (this.enviando || this.enviandoGoogle) return;

    this.enviando = true;
    this.mensajeError = '';

    this.authService.login(this.credenciales)
      .pipe(timeout(20000))
      .pipe(finalize(() => this.enviando = false))
      .subscribe({
        next: (res) => {
          this.authService.guardarSesion(res);
          this.authService.irAlPanel();
        },
        error: (err) => {
          this.mensajeError = err.name === 'TimeoutError'
            ? 'El servidor tardó demasiado en responder.'
            : err.status === 0
            ? 'No se pudo conectar con el servidor.'
            : (err.error?.detail || 'Usuario o contraseña incorrectos.');
        }
      });
  }
}
