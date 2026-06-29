import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, DestroyRef, NgZone, OnInit, inject } from '@angular/core';
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
  imports: [CommonModule, FormsModule, RouterLink, GoogleSigninButtonModule],
  templateUrl: './login.html',
  styleUrl: './login.css'
})
export class LoginComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);
  private readonly ngZone = inject(NgZone);
  private readonly cdr = inject(ChangeDetectorRef);

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

        this.ngZone.run(() => {
          this.enviandoGoogle = true;
          this.mensajeError = '';
          this.cdr.detectChanges();
        });

        this.authService.loginConGoogle(user.idToken)
          .pipe(finalize(() => this.ngZone.run(() => {
            this.enviandoGoogle = false;
            this.cdr.detectChanges();
          })))
          .subscribe({
            next: (res) => {
              this.ngZone.run(() => {
                this.authService.guardarSesion(res);
                this.authService.irAlPanel();
              });
            },
            error: (err) => {
              const textoError = typeof err.error === 'string'
                ? err.error
                : err.error?.error || err.error?.detail || err.error?.message || 'No fue posible iniciar sesión con Google.';
              const mensaje = err.status === 0
                ? 'No se pudo conectar con el servidor.'
                : textoError;
              this.ngZone.run(() => {
                this.mensajeError = mensaje;
                this.cdr.detectChanges();
              });
            }
          });
      });
  }

  onLogin() {
    if (this.enviando || this.enviandoGoogle) return;

    this.ngZone.run(() => {
      this.enviando = true;
      this.mensajeError = '';
      this.cdr.detectChanges();
    });

    this.authService.login(this.credenciales)
      .pipe(timeout(20000))
      .pipe(finalize(() => this.enviando = false))
      .subscribe({
        next: (res) => {
          this.ngZone.run(() => {
            this.authService.guardarSesion(res);
            this.authService.irAlPanel();
          });
        },
        error: (err) => {
          const textoError = typeof err.error === 'string'
            ? err.error
            : err.error?.detail || err.error?.error || err.error?.message;
          const mensaje = err.name === 'TimeoutError'
            ? 'El servidor tardó demasiado en responder.'
            : err.status === 0
            ? 'No se pudo conectar con el servidor.'
            : textoError?.includes('No active account found with the given credentials')
              ? 'Usuario o contraseña incorrectos.'
              : textoError || 'Usuario o contraseña incorrectos.';
          this.ngZone.run(() => {
            this.mensajeError = mensaje;
            this.cdr.detectChanges();
          });
        }
      });
  }
}
