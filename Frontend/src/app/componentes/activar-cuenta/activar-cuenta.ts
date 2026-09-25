import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-activar-cuenta',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './activar-cuenta.html'
})
export class ActivarCuentaComponent implements OnInit {
  procesando = true;
  activada = false;
  redireccionando = false;
  mensaje = 'Estamos verificando tu enlace...';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    const token = this.route.snapshot.queryParamMap.get('token');

    if (!token) {
      this.procesando = false;
      this.mensaje = 'El enlace de activación está incompleto.';
      return;
    }

    this.authService.activarCuenta(token).subscribe({
      next: (res) => {
        this.procesando = false;
        this.activada = true;
        this.mensaje = res.mensaje || 'Tu cuenta fue activada correctamente.';
        this.redireccionando = true;
        // El token no debe permanecer visible en el historial o en la barra de direcciones.
        window.history.replaceState({}, document.title, window.location.pathname);
        window.setTimeout(() => {
          this.router.navigate(['/login'], { replaceUrl: true });
        }, 2500);
      },
      error: (err) => {
        this.procesando = false;
        this.mensaje = err.status === 0
          ? 'No se pudo conectar con el servidor.'
          : (err.error?.error || 'No fue posible activar la cuenta.');
      }
    });
  }
}
