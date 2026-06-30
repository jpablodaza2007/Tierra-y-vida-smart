import { inject } from '@angular/core';
import {
  HttpClient,
  HttpErrorResponse,
  HttpHandlerFn,
  HttpInterceptorFn,
  HttpRequest
} from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, catchError, finalize, map, shareReplay, switchMap, throwError } from 'rxjs';

interface RefreshResponse {
  access: string;
  refresh?: string;
}

const REFRESH_URL = '/api/auth/login/refresh/';
const PUBLIC_AUTH_URLS = [
  '/auth/login/',
  '/auth/login/refresh/',
  '/auth/register/',
  '/auth/google/',
  '/auth/activate/'
];

let refreshRequest$: Observable<string> | null = null;

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const http = inject(HttpClient);
  const router = inject(Router);
  const accessToken = localStorage.getItem('access_token');
  const authRequest = shouldSkipAuth(request.url) || !accessToken
    ? request
    : addAuthorizationHeader(request, accessToken);

  return next(authRequest).pipe(
    catchError((error) => {
      if (!(error instanceof HttpErrorResponse) || error.status !== 401 || shouldSkipAuth(request.url)) {
        return throwError(() => error);
      }

      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        clearSessionAndRedirect(router);
        return throwError(() => error);
      }

      refreshRequest$ = refreshRequest$ || refreshAccessToken(http, router, refreshToken);
      return refreshRequest$.pipe(
        switchMap((token) => next(addAuthorizationHeader(request, token)))
      );
    })
  );
};

function shouldSkipAuth(url: string): boolean {
  return PUBLIC_AUTH_URLS.some((publicUrl) => url.includes(publicUrl));
}

function addAuthorizationHeader(request: HttpRequest<unknown>, token: string): HttpRequest<unknown> {
  return request.clone({
    setHeaders: {
      Authorization: `Bearer ${token}`
    }
  });
}

function refreshAccessToken(
  http: HttpClient,
  router: Router,
  refreshToken: string
): Observable<string> {
  return http.post<RefreshResponse>(REFRESH_URL, { refresh: refreshToken }).pipe(
    map((response) => {
      localStorage.setItem('access_token', response.access);

      if (response.refresh) {
        localStorage.setItem('refresh_token', response.refresh);
      }

      return response.access;
    }),
    catchError((refreshError) => {
      clearSessionAndRedirect(router);
      return throwError(() => refreshError);
    }),
    finalize(() => {
      refreshRequest$ = null;
    }),
    shareReplay({ bufferSize: 1, refCount: false })
  );
}

function clearSessionAndRedirect(router: Router): void {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('usuario');
  router.navigate(['/login']).catch(() => {});
}
