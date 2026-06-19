import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { AuthService } from './auth';

export const authGuard: CanActivateFn = (route) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  return auth.validarSesion().pipe(
    map((esValida) => {
      if (!esValida) {
        return router.createUrlTree(['/login']);
      }

      const roles = (route.data['roles'] as string[] | undefined) || [];
      const usuario = auth.obtenerUsuario();
      const rol = usuario?.rol.toLowerCase().replace('í', 'i') || '';

      if (roles.length && !roles.includes(rol)) {
        return router.createUrlTree([auth.rutaPorRol(usuario?.rol)]);
      }

      return true;
    }),
    catchError(() => of(router.createUrlTree(['/login'])))
  );
};
